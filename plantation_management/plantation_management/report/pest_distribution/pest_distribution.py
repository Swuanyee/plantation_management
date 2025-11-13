import frappe
from frappe import _


fields = {
    "pest": "ပိုးအမည်",
    "reporting_division": "ပြည်နယ်/တိုင်းဒေသကြီး",
    "reporting_district": "ခရိုင်",
    "township": "မြို့နယ်",
    "observed_date": "တွေ့ရှိသည့်နေ့",
    "area_of_destruction": "ပျက်စီးမှု ဧရိယာ (acre)",
    "source": "Annual Plantation Update",
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
            "label": _(fields["pest"]),
            "fieldname": "pest",
            "fieldtype": "Data",
            "width": 200,
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
            "label": _(fields["observed_date"]),
            "fieldname": "observed_date",
            "fieldtype": "Data",  # Burmese date string dd-mm-yyyy
            "width": 140,
        },
        {
            # second-to-last data column
            "label": _(fields["area_of_destruction"]),
            "fieldname": "area_of_destruction",
            "fieldtype": "Data",  # always shown in Burmese digits
            "width": 140,
        },
        {
            # Link to Annual Plantation Update; blank for rows that come only from Pest Observed Location
            "label": _(fields["source"]),
            "fieldname": "source",
            "fieldtype": "Link",
            "options": "Annual Plantation Update",
            "width": 200,
        },
    ]


def normalize_list_filter(val):
    """Turn incoming filter into a clean list of strings."""
    if not val:
        return []
    if isinstance(val, str):
        # MultiSelectList usually sends comma-separated string
        return [v.strip() for v in val.split(",") if v.strip()]
    if isinstance(val, (list, tuple, set)):
        return [str(v).strip() for v in val if str(v).strip()]
    return [str(val).strip()]


def convert_date_to_burmese_ddmmyyyy(date_val):
    """
    Convert a date/datetime/'YYYY-MM-DD' to Burmese digits
    in dd-mm-yyyy order.
    """
    if not date_val:
        return ""
    try:
        s = str(date_val)[:10]  # 'YYYY-MM-DD'
    except Exception:
        return ""

    parts = s.split("-")
    if len(parts) == 3:
        y, m, d = parts
        s = f"{d}-{m}-{y}"  # dd-mm-yyyy

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
    }

    return "".join(mapping.get(ch, ch) for ch in s)


def convert_any_number_to_burmese(val):
    """
    Convert any numeric-ish value (int/float/str with digits)
    to a string with Burmese digits. Keeps non-digit chars (., +, -, spaces).
    """
    if val is None:
        return ""

    s = str(val).strip()
    if not s:
        return ""

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
    }

    return "".join(mapping.get(ch, ch) for ch in s)


def get_data(filters):
    params = {}

    # Common filter values
    pest_filter = normalize_list_filter(filters.get("pest"))
    div_filter = normalize_list_filter(filters.get("reporting_division"))
    dist_filter = normalize_list_filter(filters.get("reporting_district"))
    ts_filter = normalize_list_filter(filters.get("township"))

    obs_conds = []
    ann_conds = []

    # Pest filter (applies to both)
    if pest_filter:
        obs_conds.append("p.name IN %(pest)s")
        ann_conds.append("p.name IN %(pest)s")
        params["pest"] = tuple(pest_filter)

    # Division filter
    if div_filter:
        obs_conds.append("col.burmese_division_name IN %(reporting_division)s")
        ann_conds.append("pr.reporting_division IN %(reporting_division)s")
        params["reporting_division"] = tuple(div_filter)

    # District filter
    if dist_filter:
        obs_conds.append("col.burmese_district_name IN %(reporting_district)s")
        ann_conds.append("pr.reporting_district IN %(reporting_district)s")
        params["reporting_district"] = tuple(dist_filter)

    # Township filter
    if ts_filter:
        obs_conds.append("col.burmese_township_name IN %(township)s")
        ann_conds.append("pr.township IN %(township)s")
        params["township"] = tuple(ts_filter)

    obs_where = " AND " + " AND ".join(obs_conds) if obs_conds else ""
    ann_where = " AND " + " AND ".join(ann_conds) if ann_conds else ""

    data = []

    # -----------------------------------
    # 1) From Pest → Child Observed Location (no date, no APU link, no area)
    # -----------------------------------
    observed_query = f"""
        SELECT
            p.name AS pest,
            col.burmese_division_name AS reporting_division,
            col.burmese_district_name AS reporting_district,
            col.burmese_township_name AS township
        FROM `tabPest` p
        JOIN `tabChild Observed Location` col
            ON col.parent = p.name
           AND col.parenttype = 'Pest'
        WHERE 1 = 1
        {obs_where}
    """

    observed_rows = frappe.db.sql(observed_query, params, as_dict=True)

    for r in observed_rows:
        data.append({
            "pest": r.get("pest"),
            "reporting_division": r.get("reporting_division"),
            "reporting_district": r.get("reporting_district"),
            "township": r.get("township"),
            "observed_date": "",
            "area_of_destruction": "",
            "source": "",  # no Annual Plantation Update link for pure observed rows
        })

    # -----------------------------------
    # 2) From Annual Plantation Update → Child Pest Destruction Table → Plantation Record
    # -----------------------------------
    annual_query = f"""
        SELECT
            p.name AS pest,
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            apu.name AS annual_update_name,
            cpd.start_date,
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
        {ann_where}
    """

    annual_rows = frappe.db.sql(annual_query, params, as_dict=True)

    for r in annual_rows:
        observed_date_burmese = convert_date_to_burmese_ddmmyyyy(r.get("start_date"))
        # always show acreage in Burmese digits regardless of original language
        area_burmese = convert_any_number_to_burmese(r.get("area_of_destruction"))

        data.append({
            "pest": r.get("pest"),
            "reporting_division": r.get("reporting_division"),
            "reporting_district": r.get("reporting_district"),
            "township": r.get("township"),
            "observed_date": observed_date_burmese,
            "area_of_destruction": area_burmese,
            "source": r.get("annual_update_name"),  # Link to Annual Plantation Update
        })

    # Optional sort
    data.sort(
        key=lambda d: (
            d.get("pest") or "",
            d.get("reporting_division") or "",
            d.get("reporting_district") or "",
            d.get("township") or "",
            d.get("observed_date") or "",
            d.get("source") or "",
        )
    )

    return data

