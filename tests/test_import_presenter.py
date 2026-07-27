from openpyxl import Workbook

from finance_ai.ui.presenters.import_presenter import ImportPresenter

VALID_SHEETS = {
    "Accounts": (
        ["Name", "Account Type", "Institution", "Current Balance", "Notes"],
        [["Checking", "checking", "Bank", 1000, ""]],
    ),
    "Categories": (
        ["Name", "Category Type"],
        [["Salary", "income"], ["Groceries", "expense"]],
    ),
    "Transactions": (
        ["Transaction Date", "Merchant", "Description", "Amount", "Account Name", "Category Name", "Notes"],
        [["2026-06-01", "Employer", "Paycheck", 2000, "Checking", "Salary", ""]],
    ),
    "Debts": (
        ["Name", "Lender", "Balance", "Interest Rate", "Minimum Payment", "Due Day", "Notes"],
        [["Credit Card", "Bank", 500, 20.0, 25, 5, ""]],
    ),
    "Assets": (
        ["Name", "Asset Type", "Current Value", "Notes"],
        [["Car", "vehicle", 8000, ""]],
    ),
    "Budgets": (
        ["Month", "Category Name", "Budgeted Amount"],
        [["2026-06", "Groceries", 400]],
    ),
    "Goals": (
        ["Name", "Target Amount", "Current Amount", "Target Date", "Notes"],
        [["Emergency Fund", 10000, 2000, "2027-01-01", ""]],
    ),
}


def _write_workbook(path, sheets: dict) -> str:
    wb = Workbook()
    wb.remove(wb.active)

    for sheet_name, (headers, rows) in sheets.items():
        ws = wb.create_sheet(sheet_name)
        ws.append(headers)
        for row in rows:
            ws.append(row)

    wb.save(path)
    return str(path)


def test_load_preview_for_valid_workbook(tmp_path):
    path = _write_workbook(tmp_path / "valid.xlsx", VALID_SHEETS)

    preview = ImportPresenter().load_preview(path)

    assert preview.validation_report.is_valid
    assert preview.dataset is not None
    assert preview.counts["Accounts"] == 1
    assert preview.counts["Categories"] == 2
    assert preview.counts["Transactions"] == 1
    assert preview.total_count == 8


def test_load_preview_for_workbook_missing_required_sheet(tmp_path):
    incomplete_sheets = {k: v for k, v in VALID_SHEETS.items() if k != "Debts"}
    path = _write_workbook(tmp_path / "missing_sheet.xlsx", incomplete_sheets)

    preview = ImportPresenter().load_preview(path)

    assert not preview.validation_report.is_valid
    assert preview.dataset is None
    assert preview.counts == {}
    assert any("Debts" in issue.message for issue in preview.validation_report.errors)


def test_load_preview_for_workbook_with_missing_required_value(tmp_path):
    sheets = dict(VALID_SHEETS)
    sheets["Accounts"] = (
        ["Name", "Account Type", "Institution", "Current Balance", "Notes"],
        [[None, "checking", "Bank", 1000, ""]],
    )
    path = _write_workbook(tmp_path / "missing_value.xlsx", sheets)

    preview = ImportPresenter().load_preview(path)

    assert not preview.validation_report.is_valid
    assert preview.dataset is None
