// plantation_management/public/js/burmese_numbers.js

(function () {
  const en_to_mm = {
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
  };

  const mm_to_en = {
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
  };

  function to_mm_digits(str) {
    if (!str) return str;
    return String(str).replace(/[0-9]/g, d => en_to_mm[d] || d);
  }

  function to_en_digits(str) {
    if (!str) return str;
    return String(str).replace(/[၀-၉]/g, d => mm_to_en[d] || d);
  }

  frappe.after_ajax(() => {
    try {
      console.log("[Burmese Numbers] patching Int/Float/Currency");

      // helper to patch numeric controls
      function patch_numeric_control(ctrl_name) {
        const Ctrl = frappe.ui?.form?.[ctrl_name];
        if (!Ctrl) return;

        const proto = Ctrl.prototype;
        const original_set_formatted_input = proto.set_formatted_input;
        const original_parse = proto.parse || function (value) { return value; };

        proto.set_formatted_input = function (value) {
          // 1) let core logic run
          if (original_set_formatted_input) {
            original_set_formatted_input.call(this, value);
          }

          // 2) DO NOT touch filter inputs' display
          if (this.df && this.df.is_filter) {
            return;
          }

          // 3) For normal form/child-table fields: show Burmese digits
          if (this.$input && this.$input.val()) {
            const current = this.$input.val();
            this.$input.val(to_mm_digits(current));
          }
        };

        proto.parse = function (value) {
          // Empty -> leave as-is
          if (value == null || value === "") {
            return original_parse.call(this, value);
          }

          // ALWAYS normalize Burmese → ASCII, even for filters
          const ascii = to_en_digits(value);
          return original_parse.call(this, ascii);
        };

        console.log(`[Burmese Numbers] patched ${ctrl_name}`);
      }

      // Patch numeric controls (forms + child tables + filter controls)
      patch_numeric_control("ControlInt");
      patch_numeric_control("ControlFloat");
      patch_numeric_control("ControlCurrency");

      // --------- formatters for displaying values (list/grid/reports) ---------
      if (frappe.form && frappe.form.formatters) {
        function patch_formatter(name) {
          const orig = frappe.form.formatters[name];
          if (!orig || orig.__mm_patched) return;

          frappe.form.formatters[name] = function (value, df, options, doc) {
            const out = orig(value, df, options, doc);
            return to_mm_digits(out);
          };
          frappe.form.formatters[name].__mm_patched = true;
          console.log(`[Burmese Numbers] patched formatter ${name}`);
        }

        patch_formatter("Int");
        patch_formatter("Float");
        patch_formatter("Currency");
      }

    } catch (e) {
      console.error("[Burmese Numbers] error", e);
    }
  });
})();

