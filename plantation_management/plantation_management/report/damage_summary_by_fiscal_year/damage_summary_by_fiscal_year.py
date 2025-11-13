import frappe
from frappe import _
from decimal import Decimal


fields = {
    "fiscal_year": "ဘဏ္ဍာရေးနှစ်",
    "reporting_division": "ပြည်နယ်/တိုင်းဒေသကြီး",
    "reporting_district": "ခရိုင်",
    "township": "မြို့နယ်",
    "disease_or_pest": "ရောဂါ / ပိုးမွှား သို့ ကျောရိုးရှိသတ္တဝါ",
    "area_of_destruction": "ပျက်စီးမှု ဧရိယာ (ဧက)",
}


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": _(fields["fiscal_year"]),
            "fieldname": "fiscal_year",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["reporting_division"]),
            "fieldname": "reporting_division",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _(fields["reporting_district"]),
            "fieldname": "reporting_district",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _(fields["township"]),
            "fieldname": "township",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _(fields["disease_or_pest"]),
            "fieldname": "disease_or_pest",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _(fields["area_of_destruction"]),
            "fieldname": "area_of_destruction",
            "fieldtype": "Data",  # Burmese digits string
            "width": 140,
        },
    ]


def normalize_list_filter(val):
    """Turn incoming filter into a clean list of strings."""
    if not val:
        return []
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    if isinstance(val, (list, tuple, set)):
        return [str(v).strip() for v in val if str(v).strip()]
    return [str(val).strip()]


def burmese_to_english_digits(s: str) -> str:
    """Convert Burmese digits in a string to English digits."""
    if not s:
        return ""
    mapping = {
        "၀": "0",
        "၁": "1",
        "၂": "2",
        "၃": "3",
        "၄": "4",
        "၅": "5",
        "၆": "6",
        "၇": "7",
        "၈": "8",
        "၉": "9",
    }
    return "".join(mapping.get(ch, ch) for ch in s)


def to_number_from_burmese(val):
    """Convert a Burmese-digit number (possibly with commas) to float."""
    if val is None:
        return 0.0

    if isinstance(val, (int, float, Decimal)):
        return float(val)

    s = str(val).strip()
    if not s:
        return 0.0

    s = burmese_to_english_digits(s).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def convert_to_burmese(num):
    """Convert a numeric value to a Burmese-digit string."""
    if num is None:
        return ""
    try:
        val = float(num)
    except Exception:
        return str(num)

    # integer vs decimal display
    if abs(val - round(val)) < 1e-9:
        s = str(int(round(val)))
    else:
        s = f"{val:.2f}"

    mapping = {
        "0": "၀",
        "1": "၁",
        "2": "၂",
        "3": "၃",
        "4": "၄",
        "5": "၅",
        "6": "၆",
        "7": "၇",
        "8": "၈",
        "9": "၉",
        ".": ".",
    }
    return "".join(mapping.get(ch, ch) for ch in s)


def get_data(filters):
    params = {}

    fy_filter = filters.get("fiscal_year_name")
    div_filter = normalize_list_filter(filters.get("reporting_division"))
    dist_filter = normalize_list_filter(filters.get("reporting_district"))
    ts_filter = normalize_list_filter(filters.get("township"))

    conds = []

    if fy_filter:
        conds.append("apu.fiscal_year_name = %(fiscal_year_name)s")
        params["fiscal_year_name"] = fy_filter

    if div_filter:
        conds.append("pr.reporting_division IN %(reporting_division)s")
        params["reporting_division"] = tuple(div_filter)

    if dist_filter:
        conds.append("pr.reporting_district IN %(reporting_district)s")
        params["reporting_district"] = tuple(dist_filter)

    if ts_filter:
        conds.append("pr.township IN %(township)s")
        params["township"] = tuple(ts_filter)

    where_clause = " AND " + " AND ".join(conds) if conds else ""

    # ---------------------------------------------------
    # 1) Fetch raw rows for PEST damage
    # ---------------------------------------------------
    pest_query = f"""
        SELECT
            apu.fiscal_year_name AS fiscal_year,
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            p.name AS agent_name,
            cpd.area_of_destruction
        FROM `tabAnnual Plantation Update` apu
        JOIN `tabChild Pest Destruction Table` cpd
            ON cpd.parent = apu.name
           AND cpd.parenttype = 'Annual Plantation Update'
        JOIN `tabPest` p
            ON cpd.pest_or_predator = p.name
        JOIN `tabPlantation Record` pr
            ON apu.plantation_serial = pr.name
        WHERE 1 = 1
        {where_clause}
    """

    pest_rows = frappe.db.sql(pest_query, params, as_dict=True)

    # ---------------------------------------------------
    # 2) Fetch raw rows for DISEASE damage
    # ---------------------------------------------------
    disease_query = f"""
        SELECT
            apu.fiscal_year_name AS fiscal_year,
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            d.name AS agent_name,
            cdd.area_of_destruction
        FROM `tabAnnual Plantation Update` apu
        JOIN `tabChild Disease Destruction Table` cdd
            ON cdd.parent = apu.name
           AND cdd.parenttype = 'Annual Plantation Update'
        JOIN `tabDisease` d
            ON cdd.plant_disease_name = d.name
        JOIN `tabPlantation Record` pr
            ON apu.plantation_serial = pr.name
        WHERE 1 = 1
        {where_clause}
    """

    disease_rows = frappe.db.sql(disease_query, params, as_dict=True)

    # ---------------------------------------------------
    # 3) Aggregate numeric totals per key
    #    key = (fiscal_year, division, district, township, agent_name)
    # ---------------------------------------------------
    totals = {}

    def accumulate(rows):
        for r in rows:
            fy = (r.get("fiscal_year") or "").strip()
            div = (r.get("reporting_division") or "").strip()
            dist = (r.get("reporting_district") or "").strip()
            ts = (r.get("township") or "").strip()
            agent = (r.get("agent_name") or "").strip()
            area_raw = r.get("area_of_destruction")

            if not agent:
                continue

            key = (fy, div, dist, ts, agent)
            val = to_number_from_burmese(area_raw)

            totals[key] = totals.get(key, 0.0) + val

    accumulate(pest_rows)
    accumulate(disease_rows)

    # ---------------------------------------------------
    # 4) Build sorted detail rows with numeric area
    # ---------------------------------------------------
    rows = []
    for (fy, div, dist, ts, agent), area in totals.items():
        rows.append({
            "fiscal_year": fy,
            "reporting_division": div,
            "reporting_district": dist,
            "township": ts,
            "disease_or_pest": agent,
            "area_numeric": area,
        })

    rows.sort(
        key=lambda d: (
            d.get("fiscal_year") or "",
            d.get("reporting_division") or "",
            d.get("reporting_district") or "",
            d.get("township") or "",
            d.get("disease_or_pest") or "",
        )
    )

    # ---------------------------------------------------
    # 5) Add fiscal-year subtotal rows
    # ---------------------------------------------------
    final_data = []
    current_fy = None
    subtotal_area = 0.0

    for r in rows:
        fy = r.get("fiscal_year") or ""

        if current_fy is None:
            current_fy = fy

        # new fiscal year: flush previous subtotal
        if fy != current_fy:
            # append subtotal row for previous fiscal year
            final_data.append({
                "fiscal_year": current_fy,
                "reporting_division": "",
                "reporting_district": "",
                "township": "",
                "disease_or_pest": "စုစုပေါင်း",
                "area_of_destruction": convert_to_burmese(subtotal_area),
            })
            # reset
            current_fy = fy
            subtotal_area = 0.0

        # normal detail row
        area_val = r.get("area_numeric") or 0.0
        subtotal_area += area_val

        final_data.append({
            "fiscal_year": r.get("fiscal_year"),
            "reporting_division": r.get("reporting_division"),
            "reporting_district": r.get("reporting_district"),
            "township": r.get("township"),
            "disease_or_pest": r.get("disease_or_pest"),
            "area_of_destruction": convert_to_burmese(area_val),
        })

    # final subtotal for last fiscal year
    if current_fy is not None:
        final_data.append({
            "fiscal_year": current_fy,
            "reporting_division": "",
            "reporting_district": "",
            "township": "",
            "disease_or_pest": "စုစုပေါင်း",
            "area_of_destruction": convert_to_burmese(subtotal_area),
        })

    return final_data

