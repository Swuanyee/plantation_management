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
    "fiscal_year_name": "ဘဏ္ဍာရေးနှစ်",
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
    """Safely convert DB value to float for summing total_expenditure."""
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
            # short display, JS formatter will turn it into a link using plantation_serial
            "label": _(fields["plantation_serial_shortform"]),
            "fieldname": "plantation_serial_shortform",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _(fields["fiscal_year_name"]),
            "fieldname": "fiscal_year_name",
            "fieldtype": "Data",
            "width": 120,
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
            "fieldtype": "Float",  # numeric sum of total_expenditure
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

    # Parent: Annual Plantation Update (apu)
    # Plantation Record: pr
    # Species Child Table: sct
    # Child Plantation Maintenance: m (work_done + total_expenditure)
    query = f"""
        SELECT
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.plantation_type,
            pr.name AS plantation_serial,
            apu.name AS annual_update_name,
            apu.fiscal_year_name,
            sct.species_grown,
            m.work_done AS maintenance,
            m.total_expenditure
        FROM `tabAnnual Plantation Update` apu
        JOIN `tabPlantation Record` pr
            ON apu.plantation_serial = pr.name
        LEFT JOIN `tabSpecies Child Table` sct
            ON sct.parent = pr.name
           AND sct.parenttype = 'Plantation Record'
           AND sct.parentfield = 'plantation_type_table'
        LEFT JOIN `tabChild Plantation Maintenance` m
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
            sct.idx,
            m.idx
    """

    rows = frappe.db.sql(query, params, as_dict=True)

    # Aggregate per Annual Plantation Update (apu.name)
    aggregated = OrderedDict()

    for r in rows:
        key = r.get("annual_update_name") or f"_missing_{id(r)}"

        if key not in aggregated:
            full_serial = r.get("plantation_serial")
            aggregated[key] = {
                "reporting_division": r.get("reporting_division"),
                "reporting_district": r.get("reporting_district"),
                "township": r.get("township"),
                "plantation_type": r.get("plantation_type"),
                "plantation_serial": full_serial,
                "plantation_serial_shortform": get_short_serial(full_serial),
                "fiscal_year_name": r.get("fiscal_year_name"),
                "species_list": [],
                "maintenance_list": [],
                "total_expenditure": 0.0,
            }

        ag = aggregated[key]

        species = (r.get("species_grown") or "").strip()
        if species and species not in ag["species_list"]:
            ag["species_list"].append(species)

        maint = (r.get("maintenance") or "").strip()
        if maint and maint not in ag["maintenance_list"]:
            ag["maintenance_list"].append(maint)

        # Sum total_expenditure across all maintenance rows
        ag["total_expenditure"] += to_number(r.get("total_expenditure"))

    data = []
    for ag in aggregated.values():
        data.append({
            "reporting_division": ag["reporting_division"],
            "reporting_district": ag["reporting_district"],
            "township": ag["township"],
            "plantation_type": ag["plantation_type"],
            "species_grown": "၊ ".join(ag["species_list"]),
            "plantation_serial": ag["plantation_serial"],  # used by JS formatter
            "plantation_serial_shortform": ag["plantation_serial_shortform"],
            "fiscal_year_name": ag["fiscal_year_name"],
            "maintenance": "၊ ".join(ag["maintenance_list"]),
            "total_expenditure": ag["total_expenditure"],
        })

    return data
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
    "fiscal_year_name": "ဘဏ္ဍာရေးနှစ်",
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
    """Safely convert DB value to float for summing total_expenditure."""
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
            # short display, JS formatter will turn it into a link using plantation_serial
            "label": _(fields["plantation_serial_shortform"]),
            "fieldname": "plantation_serial_shortform",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _(fields["fiscal_year_name"]),
            "fieldname": "fiscal_year_name",
            "fieldtype": "Data",
            "width": 120,
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

    # Parent: Annual Plantation Update (apu)
    # Plantation Record: pr
    # Species Child Table: sct
    # Child Plantation Maintenance: m (work_done + total_expenditure)
    query = f"""
        SELECT
            pr.reporting_division,
            pr.reporting_district,
            pr.township,
            pr.plantation_type,
            pr.name AS plantation_serial,
            apu.name AS annual_update_name,
            apu.fiscal_year_name,
            sct.species_grown,
            m.work_done AS maintenance,
            m.total_expenditure
        FROM `tabAnnual Plantation Update` apu
        JOIN `tabPlantation Record` pr
            ON apu.plantation_serial = pr.name
        LEFT JOIN `tabSpecies Child Table` sct
            ON sct.parent = pr.name
           AND sct.parenttype = 'Plantation Record'
           AND sct.parentfield = 'plantation_type_table'
        LEFT JOIN `tabChild Plantation Maintenance` m
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
            sct.idx,
            m.idx
    """

    rows = frappe.db.sql(query, params, as_dict=True)

    # Aggregate per Annual Plantation Update (apu.name)
    aggregated = OrderedDict()

    for r in rows:
        key = r.get("annual_update_name") or f"_missing_{id(r)}"

        if key not in aggregated:
            full_serial = r.get("plantation_serial")
            aggregated[key] = {
                "reporting_division": r.get("reporting_division"),
                "reporting_district": r.get("reporting_district"),
                "township": r.get("township"),
                "plantation_type": r.get("plantation_type"),
                "plantation_serial": full_serial,
                "plantation_serial_shortform": get_short_serial(full_serial),
                "fiscal_year_name": r.get("fiscal_year_name"),
                "species_list": [],
                "maintenance_list": [],
                "total_expenditure": 0.0,
            }

        ag = aggregated[key]

        species = (r.get("species_grown") or "").strip()
        if species and species not in ag["species_list"]:
            ag["species_list"].append(species)

        maint = (r.get("maintenance") or "").strip()
        if maint and maint not in ag["maintenance_list"]:
            ag["maintenance_list"].append(maint)

        # Sum total_expenditure across all maintenance rows (numeric)
        ag["total_expenditure"] += to_number(r.get("total_expenditure"))

    data = []
    for ag in aggregated.values():
        # round to nearest whole number and convert to Burmese digits
        total_exp_rounded = int(round(ag["total_expenditure"] or 0))

        data.append({
            "reporting_division": ag["reporting_division"],
            "reporting_district": ag["reporting_district"],
            "township": ag["township"],
            "plantation_type": ag["plantation_type"],
            "species_grown": "၊ ".join(ag["species_list"]),
            "plantation_serial": ag["plantation_serial"],  # used by JS formatter
            "plantation_serial_shortform": ag["plantation_serial_shortform"],
            "fiscal_year_name": ag["fiscal_year_name"],
            "maintenance": "၊ ".join(ag["maintenance_list"]),
            "total_expenditure": convert_to_burmese(total_exp_rounded),
        })

    return data

