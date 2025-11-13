import frappe
from frappe import _
from collections import OrderedDict

# Column labels
fields = {
    "reporting_division": "ပြည်နယ်/တိုင်းဒေသကြီး",
    "reporting_district": "ခရိုင်",
    "township": "မြို့နယ်",
    "plantation_type": "စိုက်ခင်းအမျိုးအစား",
    "plantation_serial": "စိုက်ခင်းအမှတ်",
    "species_grown": "စိုက်ပျိုးသည့် သစ်မျိုး",
    "planting_distance": "ပန္နက်အကွာအဝေး",
    "total_plant": "ပင်အရေအတွက်",
    "total_area": "ဧက",
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
            "label": _(fields["plantation_serial"]),
            "fieldname": "plantation_serial",
            "fieldtype": "Link",
            "options": "Plantation Record",
            "width": 160,
        },
        {
            "label": _(fields["species_grown"]),
            "fieldname": "species_grown",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _(fields["planting_distance"]),
            "fieldname": "planting_distance",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _(fields["total_plant"]),
            "fieldname": "total_plant",
            "fieldtype": "Data",  # display as Burmese digits
            "width": 120,
        },
        {
            "label": _(fields["total_area"]),
            "fieldname": "total_area",
            "fieldtype": "Data",  # display as Burmese digits
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

    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)

    # Base query: one row per child entry, aggregate per Plantation Record
    query = f"""
        SELECT
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.plantation_type,
            pr.name AS plantation_serial,
            pr.total_plant,
            pr.total_area,
            ptt.species_grown,
            ptt.planting_distance
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
            pr.plantation_type,
            pr.name,
            ptt.idx
    """

    rows = frappe.db.sql(query, params, as_dict=True)

    # Aggregate per Plantation Record
    aggregated = OrderedDict()

    for r in rows:
        key = r.get("plantation_serial") or f"_missing_{id(r)}"

        if key not in aggregated:
            aggregated[key] = {
                "reporting_division": r.get("reporting_division"),
                "reporting_district": r.get("reporting_district"),
                "township": r.get("township"),
                "plantation_type": r.get("plantation_type"),
                "plantation_serial": r.get("plantation_serial"),
                "species_list": [],
                "distance_list": [],
                "total_plant": r.get("total_plant"),
                "total_area": r.get("total_area"),
            }

        ag = aggregated[key]

        # Distinct species
        species = (r.get("species_grown") or "").strip()
        if species and species not in ag["species_list"]:
            ag["species_list"].append(species)

        # Distinct planting distances
        dist = (r.get("planting_distance") or "").strip()
        if dist and dist not in ag["distance_list"]:
            ag["distance_list"].append(dist)

    # Build final rows
    data = []
    for ag in aggregated.values():
        data.append({
            "reporting_division": ag["reporting_division"],
            "reporting_district": ag["reporting_district"],
            "township": ag["township"],
            "plantation_type": ag["plantation_type"],
            "plantation_serial": ag["plantation_serial"],
            "species_grown": "၊ ".join(ag["species_list"]),       # <- Burmese comma
            "planting_distance": "၊ ".join(ag["distance_list"]),  # <- Burmese comma
            "total_plant": convert_to_burmese(ag["total_plant"]),
            "total_area": convert_to_burmese(ag["total_area"]),
        })

    return data

