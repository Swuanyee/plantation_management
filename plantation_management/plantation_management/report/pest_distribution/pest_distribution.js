frappe.query_reports["Pest Distribution"] = {
  "filters": [
    {
      "fieldname": "pest",
      "label": __("Pest"),
      "fieldtype": "MultiSelectList",
      "get_data": function (txt) {
        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Pest",
            fields: ["name"],
            order_by: "name asc",
            limit_page_length: 0
          }
        }).then(r => {
          return (r.message || []).map(item => ({
            value: item.name,
            description: item.name
          }));
        });
      }
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
          "ကိုးကန့် ကိုယ်ပိုင်အုပ်ချုပ်ခွင့်

