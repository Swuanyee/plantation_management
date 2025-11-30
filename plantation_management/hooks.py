app_name = "plantation_management"
app_title = "Plantation Management"
app_publisher = "Kyaw Swuan yee"
app_description = "Plantation Management app for forestry department of Myanmar"
app_email = "k.swuan.yee@gmail.com"
app_license = "mit"
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Plantation Management"]]
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "Plantation Management"]]
    },
    {
        "dt": "DocType",
        "filters": [["custom", "=", 1], ["module", "=", "Plantation Management"]]
    },
    {
        "dt": "Client Script",
        "filters": [["module", "=", "Plantation Management"]]
    },
    {
        "dt": "Print Format",
        "filters": [["module", "=", "Plantation Management"]]
    },
    {
        "dt": "Report",
        "filters": [["module", "=", "Plantation Management"]]
    },
    {
        "dt": "Workspace",
        "filters": [["module", "in", ["Plantation Management", "Frappe", "Custom"]]]
    }
]

app_include_js = [
    "/assets/plantation_management/js/burmese_dates.js"
]

