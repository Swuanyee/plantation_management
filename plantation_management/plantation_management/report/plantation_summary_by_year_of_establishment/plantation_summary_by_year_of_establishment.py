# File: plantation_management/plantation_management/report/plantation_summary_by_year_of_establishment/plantation_summary_by_year_of_establishment.py

import frappe
from frappe import _
from decimal import Decimal

# Column labels and order
fields = {
    "reporting_division": "ပြည်နယ်/တိုင်းဒေသကြီး",
    "reporting_district": "ခရိုင်",
    "township": "မြို့နယ်",
    "year_of_establishment": "စိုက်ပျိုးသည့်ဘဏ္ဍာရေးနှစ်",
    "plantation_serial": "စိုက်ခင်းအမှတ်",
    "plantation_type": "စိုက်ခင်းအမျိုးအစား",
    "species_grown": "စိုက်ပျိုးသည့် သစ်မျိုး",
    "planting_distance": "ပန္နက်အကွာအဝေး",
    "acre": "ဧရိယာ (ဧက)",
    "no_of_plants": "ပင်အရေအတွက်",
}


def convert_to_burmese(num):
    """Convert a numeric value to a string with Burmese digits."""
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


def to_number(val):
    """
    Safely convert a value (possibly Myanmar-digit string) to a float.
    Used for numeric aggregation (totals).
    """
    if val is None:
        return 0

    if isinstance(val, (int, float)):
        return val

    if isinstance(val, Decimal):
        return float(val)

    if isinstance(val, str):
        s = val.strip()
        if not s:
            return 0

        burmese_to_eng = {
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
        s2 = "".join(burmese_to_eng.get(ch, ch) for ch in s)
        s2 = s2.replace(",", "")

        try:
            return float(s2)
        except ValueError:
            return 0

    return 0


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
            "label": _(fields["year_of_establishment"]),
            "fieldname": "year_of_establishment",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": _(fields["plantation_serial"]),
            "fieldname": "plantation_serial",
            "fieldtype": "Link",
            "options": "Plantation Record",
            "width": 160,
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
            "width": 160,
        },
        {
            "label": _(fields["planting_distance"]),
            "fieldname": "planting_distance",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _(fields["acre"]),
            "fieldname": "acre",
            "fieldtype": "Data",  # Myanmar number string
            "width": 120,
        },
        {
            "label": _(fields["no_of_plants"]),
            "fieldname": "no_of_plants",
            "fieldtype": "Data",  # Myanmar number string
            "width": 120,
        },
    ]


def get_data(filters):
    conditions = []
    params = {}

    # --- Reporting Division
    if filters.get("reporting_division"):
        divisions = filters.get("reporting_division")
        if isinstance(divisions, str):
            divisions = [d.strip() for d in divisions.split(",") if d.strip()]
        if divisions:
            conditions.append("pr.reporting_division IN %(reporting_division)s")
            params["reporting_division"] = tuple(divisions)

    # --- Reporting District
    if filters.get("reporting_district"):
        districts = filters.get("reporting_district")
        if isinstance(districts, str):
            districts = [d.strip() for d in districts.split(",") if d.strip()]
        if districts:
            conditions.append("pr.reporting_district IN %(reporting_district)s")
            params["reporting_district"] = tuple(districts)

    # --- Township
    if filters.get("township"):
        townships = filters.get("township")
        if isinstance(townships, str):
            townships = [t.strip() for t in townships.split(",") if t.strip()]
        if townships:
            conditions.append("pr.township IN %(township)s")
            params["township"] = tuple(townships)

    # --- Plantation Type
    if filters.get("plantation_type"):
        pl_types = filters.get("plantation_type")
        if isinstance(pl_types, str):
            pl_types = [p.strip() for p in pl_types.split(",") if p.strip()]
        if pl_types:
            conditions.append("pr.plantation_type IN %(plantation_type)s")
            params["plantation_type"] = tuple(pl_types)

    # --- Year Of Establishment
    if filters.get("year_of_establishment"):
        years = filters.get("year_of_establishment")
        if isinstance(years, str):
            years = [y.strip() for y in years.split(",") if y.strip()]
        if years:
            conditions.append("pr.year_of_establishment IN %(year_of_establishment)s")
            params["year_of_establishment"] = tuple(years)

    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)

    # Detail query (one row per child row from Species Child Table)
    query = f"""
        SELECT
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.year_of_establishment,
            pr.plantation_type,
            pr.name AS plantation_serial,
            ptt.species_grown,
            ptt.planting_distance,
            ptt.no_of_plants,
            ptt.acre,
            pr.total_area,
            pr.total_plant
        FROM `tabPlantation Record` pr
        LEFT JOIN `tabSpecies Child Table` ptt
            ON ptt.parent = pr.name
           AND ptt.parenttype = 'Plantation Record'
           AND ptt.parentfield = 'plantation_type_table'
        WHERE 1 = 1
        {where_clause}
        ORDER BY
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.year_of_establishment,
            pr.plantation_type,
            pr.name,
            ptt.idx
    """

    rows = frappe.db.sql(query, params, as_dict=True)

    data = []

    # Current grouping state
    current_division = None
    current_district = None
    current_township = None
    current_parent = None
    current_parent_total_area = None
    current_parent_total_plant = None

    # Totals
    division_total_area = 0
    division_total_plant = 0
    district_total_area = 0
    district_total_plant = 0
    township_total_area = 0
    township_total_plant = 0

    overall_total_area = 0
    overall_total_plant = 0

    def flush_parent_subtotal():
        nonlocal current_parent, current_parent_total_area, current_parent_total_plant, data
        if not current_parent:
            return
        data.append({
            "reporting_division": "",
            "reporting_district": "",
            "township": "",
            "year_of_establishment": "",
            "plantation_type": "",
            "plantation_serial": _("စုစုပေါင်း (စိုက်ခင်း)"),
            "species_grown": "",
            "planting_distance": "",
            "no_of_plants": convert_to_burmese(current_parent_total_plant),
            "acre": convert_to_burmese(current_parent_total_area),
        })
        current_parent = None
        current_parent_total_area = None
        current_parent_total_plant = None

    def flush_township_subtotal():
        nonlocal township_total_area, township_total_plant, current_township, data
        if current_township is None:
            return
        data.append({
            "reporting_division": current_division,
            "reporting_district": current_district,
            "township": current_township,
            "year_of_establishment": "",
            "plantation_type": "",
            "plantation_serial": _("စုစုပေါင်း (မြို့နယ်)"),
            "species_grown": "",
            "planting_distance": "",
            "no_of_plants": convert_to_burmese(township_total_plant),
            "acre": convert_to_burmese(township_total_area),
        })
        township_total_area = 0
        township_total_plant = 0

    def flush_district_subtotal():
        nonlocal district_total_area, district_total_plant, current_district, data
        if current_district is None:
            return
        data.append({
            "reporting_division": current_division,
            "reporting_district": current_district,
            "township": "",
            "year_of_establishment": "",
            "plantation_type": "",
            "plantation_serial": _("စုစုပေါင်း (ခရိုင်)"),
            "species_grown": "",
            "planting_distance": "",
            "no_of_plants": convert_to_burmese(district_total_plant),
            "acre": convert_to_burmese(district_total_area),
        })
        district_total_area = 0
        district_total_plant = 0

    def flush_division_subtotal():
        nonlocal division_total_area, division_total_plant, current_division, data
        if current_division is None:
            return
        data.append({
            "reporting_division": current_division,
            "reporting_district": "",
            "township": "",
            "year_of_establishment": "",
            "plantation_type": "",
            "plantation_serial": _("စုစုပေါင်း (ပြည်နယ်/တိုင်း)"),
            "species_grown": "",
            "planting_distance": "",
            "no_of_plants": convert_to_burmese(division_total_plant),
            "acre": convert_to_burmese(division_total_area),
        })
        division_total_area = 0
        division_total_plant = 0

    for r in rows:
        div = r.get("reporting_division")
        dist = r.get("reporting_district")
        town = r.get("township")
        parent = r.get("plantation_serial")

        # Initialize on first row
        if current_division is None:
            current_division = div
            current_district = dist
            current_township = town
            current_parent = None

        # Handle group changes (outermost to inner)
        if div != current_division:
            flush_parent_subtotal()
            flush_township_subtotal()
            flush_district_subtotal()
            flush_division_subtotal()
            current_division = div
            current_district = dist
            current_township = town
            current_parent = None

        elif dist != current_district:
            flush_parent_subtotal()
            flush_township_subtotal()
            flush_district_subtotal()
            current_district = dist
            current_township = town
            current_parent = None

        elif town != current_township:
            flush_parent_subtotal()
            flush_township_subtotal()
            current_township = town
            current_parent = None

        elif parent != current_parent:
            flush_parent_subtotal()

        # New plantation group?
        if parent != current_parent:
            current_parent = parent
            current_parent_total_area = r.get("total_area")
            current_parent_total_plant = r.get("total_plant")

            val_area = to_number(current_parent_total_area)
            val_plant = to_number(current_parent_total_plant)

            division_total_area += val_area
            division_total_plant += val_plant
            district_total_area += val_area
            district_total_plant += val_plant
            township_total_area += val_area
            township_total_plant += val_plant
            overall_total_area += val_area
            overall_total_plant += val_plant

        # Detail row
        data.append({
            "reporting_division": r.get("reporting_division"),
            "reporting_district": r.get("reporting_district"),
            "township": r.get("township"),
            "year_of_establishment": r.get("year_of_establishment"),
            "plantation_type": r.get("plantation_type"),
            "plantation_serial": r.get("plantation_serial"),
            "species_grown": r.get("species_grown"),
            "planting_distance": r.get("planting_distance"),
            "no_of_plants": r.get("no_of_plants"),
            "acre": r.get("acre"),
        })

    # Flush remaining groups
    if current_division is not None:
        flush_parent_subtotal()
        flush_township_subtotal()
        flush_district_subtotal()
        flush_division_subtotal()

    # Grand total row
    if data:
        data.append({
            "reporting_division": "",
            "reporting_district": "",
            "township": "",
            "year_of_establishment": "",
            "plantation_type": "",
            "plantation_serial": _("စုစုပေါင်း (အားလုံး)"),
            "species_grown": "",
            "planting_distance": "",
            "no_of_plants": convert_to_burmese(overall_total_plant),
            "acre": convert_to_burmese(overall_total_area),
        })

    return data

