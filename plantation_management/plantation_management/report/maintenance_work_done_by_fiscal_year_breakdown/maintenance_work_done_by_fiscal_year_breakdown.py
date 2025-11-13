import re
import frappe
from frappe import _
from collections import OrderedDict
from decimal import Decimal

fields = {
    "reporting_division": "ပြည်နယ်/တိုင်းဒေသကြီး",
    "reporting_district": "ခရိုင်",
    "township": "မြို့နယ်",
    "plantation_type": "စိုက်ခင်းအမျိုးအစား",
    "species_grown": "စိုက်ပျိုးသည့် သစ်မျိုး",
    "plantation_serial_shortform": "စိုက်ခင်းအမှတ်",
    "year_of_establishment": "စိုက်ပျိုးသည့်မိုးရာသီ",
    "fiscal_year_name": "ဘဏ္ဍာရေးနှစ် (စိုက်ပျိုးပြီး မည်နှစ်မြောက်)",
    "maintenance": "ပြုပြင်ထိန်းသိမ်း ပန်းနွယ်အလုပ်",
    "total_expenditure": "စုစုပေါင်းအသုံးစရိတ်",
}


def get_short_serial(full_name: str) -> str:
    """Return the middle segment between 2nd and 3rd dash, or original if not enough parts."""
    if not full_name:
        return ""
    parts = str(full_name).split("-")
    if len(parts) >= 3:
        return parts[2]
    return full_name


def to_number(val):
    """Safely convert DB value to float for total_expenditure."""
    if val is None:
        return 0

    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, Decimal):
        return float(val)

    if isinstance(val, str):
        s = val.strip().replace(",", "")
        if not s:
            return 0
        try:
            return float(s)
        except ValueError:
            return 0

    return 0


def convert_to_burmese(num):
    """Convert a numeric value to a Burmese-digit string."""
    if num is None:
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
    s = str(num)
    return "".join(mapping.get(ch, ch) for ch in s)


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


def parse_fiscal_start_year(fy_str: str):
    """
    Extract the starting year (first 4-digit year) from a fiscal year string.
    Handles Burmese digits like '၂၀၂၂-၂၀၂၃'.
    """
    if not fy_str:
        return None
    norm = burmese_to_english_digits(fy_str)
    match = re.search(r"(\d{4})", norm)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def compute_year_index(year_of_establishment: str, fiscal_year_name: str):
    """
    Compute how many fiscal years since establishment.
    If fiscal_year_name == year_of_establishment -> 1
    Next fiscal year -> 2, etc.
    Returns an integer or None.
    """
    est_year = parse_fiscal_start_year(year_of_establishment)
    fy_year = parse_fiscal_start_year(fiscal_year_name)
    if est_year is None or fy_year is None:
        return None

    diff = fy_year - est_year + 1
    if diff < 1:
        return None
    return diff


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": _(fields["reporting_division"]),
            "fieldname": "reporting_division",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _(fields["reporting_district"]),
            "fieldname": "reporting_district",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["township"]),
            "fieldname": "township",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["plantation_type"]),
            "fieldname": "plantation_type",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["species_grown"]),
            "fieldname": "species_grown",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _(fields["plantation_serial_shortform"]),
            "fieldname": "plantation_serial_shortform",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _(fields["year_of_establishment"]),
            "fieldname": "year_of_establishment",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            # shows "1", "2", "3"... in Burmese digits = years since establishment
            "label": _(fields["fiscal_year_name"]),
            "fieldname": "fiscal_year_name",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["maintenance"]),
            "fieldname": "maintenance",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _(fields["total_expenditure"]),
            "fieldname": "total_expenditure",
            "fieldtype": "Data",  # Burmese whole-number string
            "width": 130,
        },
    ]


def get_data(filters):
    conditions = []
    params = {}

    # Filters based on Plantation Record fields via join
    if filters.get("reporting_division"):
        divisions = filters.get("reporting_division")
        if isinstance(divisions, str):
            divisions = [d.strip() for d in divisions.split(",") if d.strip()]
        if divisions:
            conditions.append("pr.reporting_division IN %(reporting_division)s")
            params["reporting_division"] = tuple(divisions)

    if filters.get("reporting_district"):
        districts = filters.get("reporting_district")
        if isinstance(districts, str):
            districts = [d.strip() for d in districts.split(",") if d.strip()]
        if districts:
            conditions.append("pr.reporting_district IN %(reporting_district)s")
            params["reporting_district"] = tuple(districts)

    if filters.get("township"):
        townships = filters.get("township")
        if isinstance(townships, str):
            townships = [t.strip() for t in townships.split(",") if t.strip()]
        if townships:
            conditions.append("pr.township IN %(township)s")
            params["township"] = tuple(townships)

    if filters.get("plantation_type"):
        pl_types = filters.get("plantation_type")
        if isinstance(pl_types, str):
            pl_types = [p.strip() for p in pl_types.split(",") if p.strip()]
        if pl_types:
            conditions.append("pr.plantation_type IN %(plantation_type)s")
            params["plantation_type"] = tuple(pl_types)

    if filters.get("fiscal_year_name"):
        conditions.append("apu.fiscal_year_name = %(fiscal_year_name)s")
        params["fiscal_year_name"] = filters.get("fiscal_year_name")

    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)

    # Base query: one row per maintenance child row
    query = f"""
        SELECT
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.plantation_type,
            pr.year_of_establishment,
            pr.name AS plantation_serial,
            apu.name AS annual_update_name,
            apu.fiscal_year_name,
            m.work_done AS maintenance,
            m.total_expenditure
        FROM `tabAnnual Plantation Update` apu
        JOIN `tabPlantation Record` pr
            ON apu.plantation_serial = pr.name
        JOIN `tabChild Plantation Maintenance` m
            ON m.parent = apu.name
           AND m.parenttype = 'Annual Plantation Update'
           AND m.parentfield = 'maintenance_work'
        WHERE 1 = 1
        {where_clause}
        ORDER BY
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.plantation_type,
            pr.name,
            apu.fiscal_year_name,
            m.idx
    """

    rows = frappe.db.sql(query, params, as_dict=True)

    if not rows:
        return []

    # Get species per plantation (no grouping with maintenance)
    plantation_names = {r.get("plantation_serial") for r in rows if r.get("plantation_serial")}
    species_map = {}

    if plantation_names:
        species_rows = frappe.db.sql(
            """
            SELECT parent, species_grown
            FROM `tabSpecies Child Table`
            WHERE parent IN %(parents)s
              AND parenttype = 'Plantation Record'
              AND parentfield = 'plantation_type_table'
            ORDER BY parent, idx
            """,
            {"parents": tuple(plantation_names)},
            as_dict=True,
        )

        for sr in species_rows:
            parent = sr.get("parent")
            species = (sr.get("species_grown") or "").strip()
            if not parent or not species:
                continue
            species_map.setdefault(parent, [])
            if species not in species_map[parent]:
                species_map[parent].append(species)

    data = []

    for r in rows:
        full_serial = r.get("plantation_serial")
        short_serial = get_short_serial(full_serial)
        year_of_establishment = r.get("year_of_establishment")
        fy_name_raw = r.get("fiscal_year_name")

        index = compute_year_index(year_of_establishment, fy_name_raw)
        fy_index_burmese = convert_to_burmese(index) if index is not None else ""

        total_exp_val = int(round(to_number(r.get("total_expenditure") or 0)))
        total_exp_burmese = convert_to_burmese(total_exp_val)

        species_list = species_map.get(full_serial, [])
        species_joined = "၊ ".join(species_list)

        data.append({
            "reporting_division": r.get("reporting_division"),
            "reporting_district": r.get("reporting_district"),
            "township": r.get("township"),
            "plantation_type": r.get("plantation_type"),
            "species_grown": species_joined,
            "plantation_serial": full_serial,  # for JS formatter
            "plantation_serial_shortform": short_serial,
            "year_of_establishment": year_of_establishment,
            "fiscal_year_name": fy_index_burmese,
            "maintenance": r.get("maintenance"),
            "total_expenditure": total_exp_burmese,
        })

    return data

