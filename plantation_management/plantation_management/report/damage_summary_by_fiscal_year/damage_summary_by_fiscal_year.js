frappe.query_reports["Damage Summary by Fiscal Year"] = {
  "filters": [
    {
      "fieldname": "fiscal_year_name",
      "label": __("Fiscal Year"),
      "fieldtype": "Link",
      "options": "Fiscal Year"
    },
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
          value: div,
          description: div
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
            value: item.burmese_district_name,
            description: item.burmese_district_name
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
            value: item.burmese_township_name,
            description: item.burmese_township_name
          }));
        });
      }
    }
  ]
};

