// plantation_management/public/js/burmese_dates.js

(function () {
  // Map English ↔ Myanmar digits
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

  // Wait until desk is ready
  $(document).on("app_ready", function () {
    console.log("[Burmese Dates] patching ControlDate/ControlDatetime & formatters");

    // =============== INPUT CONTROLS (Form + child tables) ===============

    if (!frappe.ui || !frappe.ui.form || !frappe.ui.form.ControlDate) {
      console.warn("[Burmese Dates] ControlDate not found");
    } else {
      // ---- DATE ----
      const OriginalControlDate = frappe.ui.form.ControlDate;

      frappe.ui.form.ControlDate = class MyanmarControlDate extends OriginalControlDate {
        // When Frappe sets formatted value into the input
        set_formatted_input(value) {
          // Let the original logic run first (sets ASCII digits)
          super.set_formatted_input(value);

          // Then convert what the user SEES into Myanmar digits
          if (this.$input && this.$input.val()) {
            const current = this.$input.val();
            this.$input.val(to_mm_digits(current));
          }
        }

        // When Frappe parses user-typed text back to value
        parse(value) {
          // Allow user to type Myanmar digits
          const ascii_value = to_en_digits(value);
          return super.parse(ascii_value);
        }
      };

      // ---- DATETIME ----
      if (frappe.ui.form.ControlDatetime) {
        const OriginalControlDatetime = frappe.ui.form.ControlDatetime;

        frappe.ui.form.ControlDatetime = class MyanmarControlDatetime extends OriginalControlDatetime {
          set_formatted_input(value) {
            super.set_formatted_input(value);
            if (this.$input && this.$input.val()) {
              const current = this.$input.val();
              this.$input.val(to_mm_digits(current));
            }
          }

          parse(value) {
            const ascii_value = to_en_digits(value);
            return super.parse(ascii_value);
          }
        };
      }
    }

    // =============== DISPLAY FORMATTERS (list view, child table grid, reports) ===============

    if (frappe.form && frappe.form.formatters) {
      // Patch Date formatter
      if (frappe.form.formatters.Date && !frappe.form.formatters.__mm_date_patched) {
        const origDateFormatter = frappe.form.formatters.Date;
        frappe.form.formatters.Date = function (value, df, options, doc) {
          const out = origDateFormatter(value, df, options, doc);
          // out may contain HTML; just convert digits in the string
          return to_mm_digits(out);
        };
        frappe.form.formatters.__mm_date_patched = true;
      }

      // Patch Datetime formatter
      if (frappe.form.formatters.Datetime && !frappe.form.formatters.__mm_datetime_patched) {
        const origDatetimeFormatter = frappe.form.formatters.Datetime;
        frappe.form.formatters.Datetime = function (value, df, options, doc) {
          const out = origDatetimeFormatter(value, df, options, doc);
          return to_mm_digits(out);
        };
        frappe.form.formatters.__mm_datetime_patched = true;
      }
    }

    console.log("[Burmese Dates] patch applied");
  });
})();

