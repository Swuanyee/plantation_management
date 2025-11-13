// File: plantation_management/plantation_management/report/plantation_summary/plantation_summary.js

frappe.query_reports["Plantation Summary"] = {
  "filters": [
    {
      "fieldname": "reporting_division",
      "label": __("Reporting Division"),
      "fieldtype": "MultiSelectList",
      "get_data": function (txt) {
        let divisions = [
          "ကချင်ပြည်နယ်", "ကယားပြည်နယ်", "ကရင်ပြည်နယ်", "ချင်းပြည်နယ်",
          "စစ်ကိုင်းတိုင်းဒေသကြီး", "တနင်္သာရီတိုင်းဒေသကြီး",
          "ပဲခူးတိုင်းဒေသကြီး (အရှေ့)", "ပဲခူးတိုင်းဒေသကြီး (အနောက်)",
          "မကွေးတိုင်းဒေသကြီး", "မန္တလေးတိုင်းဒေသကြီး", "မွန်ပြည်နယ်",
          "ရခိုင်ပြည်နယ်", "ရန်ကုန်တိုင်းဒေသကြီး", "ရှမ်းပြည်နယ် (တောင်)",
          "ရှမ်းပြည်နယ် (မြောက်)", "ရှမ်းပြည်နယ် (အရှေ့)", "ဧရာဝတီတိုင်းဒေသကြီး",
          "နေပြည်တော်", "ပဲခူးတိုင်းဒေသကြီး", "ရှမ်းပြည်နယ်",
          "နာဂကိုယ်ပိုင်အုပ်ချုပ်ခွင့်ရဒေသ", "ဓနု ကိုယ်ပိုင်အုပ်ချုပ်ခွင့်ရဒေသ",
          "ပအိုဝ်း ကိုယ်ပိုင်အုပ်ချုပ်ခွင့်ရဒေသ", "ပလောင် ကိုယ်ပိုင်အုပ်ချုပ်ခွင့်ရဒေသ",
          "ကိုးကန့် ကိုယ်ပိုင်အုပ်ချုပ်ခွင့်ရဒေသ"
        ];
        return divisions.map(div => ({
          "value": div,
          "description": div
        }));
      }
    },
    {
      "fieldname": "reporting_district",
      "label": __("Reporting District"),
      "fieldtype": "MultiSelectList",
      "get_data": function (txt) {
        let divisions = frappe.query_report.get_filter_value("reporting_division") || [];
        let filters = {};

        if (divisions && divisions.length) {
          filters = { "burmese_region_name": ["in", divisions] };
        }

        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Township Data",
            filters: filters,
            fields: ["burmese_district_name"],
            distinct: true,
            order_by: "burmese_district_name asc",
            limit_page_length: 0
          }
        }).then(r => {
          return (r.message || []).map(item => ({
            "value": item.burmese_district_name,
            "description": item.burmese_district_name
          }));
        });
      }
    },
    {
      "fieldname": "township",
      "label": __("Township"),
      "fieldtype": "MultiSelectList",
      "get_data": function (txt) {
        let divisions = frappe.query_report.get_filter_value("reporting_division") || [];
        let districts = frappe.query_report.get_filter_value("reporting_district") || [];
        let filters = {};

        if (districts && districts.length) {
          filters["burmese_district_name"] = ["in", districts];
        } else if (divisions && divisions.length) {
          filters["burmese_region_name"] = ["in", divisions];
        }

        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Township Data",
            filters: filters,
            fields: ["burmese_township_name"],
            distinct: true,
            order_by: "burmese_township_name asc",
            limit_page_length: 0
          }
        }).then(r => {
          return (r.message || []).map(item => ({
            "value": item.burmese_township_name,
            "description": item.burmese_township_name
          }));
        });
      }
    },
    {
      "fieldname": "plantation_type",
      "label": __("Plantation Type"),
      "fieldtype": "MultiSelectList",
      "get_data": function (txt) {
        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Plantation Record",
            fields: ["plantation_type"],
            distinct: true,
            order_by: "plantation_type asc",
            limit_page_length: 0
          }
        }).then(r => {
          return (r.message || [])
            .filter(d => d.plantation_type)
            .map(d => ({
              "value": d.plantation_type,
              "description": d.plantation_type
            }));
        });
      }
    }
  ],

  formatter: function (value, row, column, data, default_formatter) {
    // Only customize plantation_serial
    if (column.fieldname !== "plantation_serial" || !value || !data) {
      return default_formatter(value, row, column, data);
    }

    // Any subtotal / total row should not be a link
    if (String(value).startsWith("စုစုပေါင်း")) {
      return `<span>${frappe.utils.escape_html(value)}</span>`;
    }

    const full_name = data.plantation_serial || value;

    // Shorten display: take the part between 2nd and 3rd dash
    let short = full_name;
    const parts = String(full_name).split("-");
    if (parts.length >= 3) {
      short = parts[2]; // between 2nd and 3rd dash
    }

    const doctype = "Plantation Record";
    const route = frappe.utils.get_form_link(doctype, full_name);

    // Normal rows: clickable link with short text
    return `<a href="${route}"
              data-doctype="${doctype}"
              data-name="${frappe.utils.escape_html(full_name)}"
              class="grey-link">
              ${frappe.utils.escape_html(short)}
            </a>`;
  }
};

