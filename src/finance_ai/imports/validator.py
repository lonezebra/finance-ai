import pandas as pd

from finance_ai.imports.models import EXPECTED_SHEETS, ValidationIssue, ValidationReport, WorkbookData


REQUIRED_COLUMNS = {
    "Accounts": ["Name", "Account Type", "Current Balance"],
    "Categories": ["Name", "Category Type"],
    "Transactions": ["Transaction Date", "Amount", "Account Name", "Category Name"],
    "Debts": ["Name", "Balance"],
    "Assets": ["Name", "Asset Type", "Current Value"],
    "Budgets": ["Month", "Category Name", "Budgeted Amount"],
    "Goals": ["Name"],
}


NUMERIC_COLUMNS = {
    "Accounts": ["Current Balance"],
    "Transactions": ["Amount"],
    "Debts": ["Balance", "Interest Rate", "Minimum Payment", "Due Day"],
    "Assets": ["Current Value"],
    "Budgets": ["Budgeted Amount"],
    "Goals": ["Target Amount", "Current Amount"],
}


DATE_COLUMNS = {
    "Transactions": ["Transaction Date"],
    "Goals": ["Target Date"],
}


def validate_workbook(workbook: WorkbookData) -> ValidationReport:
    issues: list[ValidationIssue] = []

    issues.extend(_validate_required_sheets(workbook))

    for sheet_name in EXPECTED_SHEETS:
        if not workbook.has_sheet(sheet_name):
            continue

        df = workbook.get_sheet(sheet_name)

        issues.extend(_validate_required_columns(sheet_name, df))
        issues.extend(_validate_required_values(sheet_name, df))
        issues.extend(_validate_numeric_columns(sheet_name, df))
        issues.extend(_validate_date_columns(sheet_name, df))

    return ValidationReport(
        is_valid=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )


def _validate_required_sheets(workbook: WorkbookData) -> list[ValidationIssue]:
    issues = []

    for sheet_name in EXPECTED_SHEETS:
        if not workbook.has_sheet(sheet_name):
            issues.append(
                ValidationIssue(
                    severity="error",
                    sheet_name=sheet_name,
                    message=f"V001 Missing required sheet: {sheet_name}",
                )
            )

    return issues


def _validate_required_columns(sheet_name: str, df: pd.DataFrame) -> list[ValidationIssue]:
    issues = []
    required_columns = REQUIRED_COLUMNS.get(sheet_name, [])

    for column in required_columns:
        if column not in df.columns:
            issues.append(
                ValidationIssue(
                    severity="error",
                    sheet_name=sheet_name,
                    message=f"V002 Missing required column: {column}",
                )
            )

    return issues


def _validate_required_values(sheet_name: str, df: pd.DataFrame) -> list[ValidationIssue]:
    issues = []
    required_columns = REQUIRED_COLUMNS.get(sheet_name, [])

    for column in required_columns:
        if column not in df.columns:
            continue

        missing_rows = df[df[column].isna()].index.tolist()

        for row_index in missing_rows:
            issues.append(
                ValidationIssue(
                    severity="error",
                    sheet_name=sheet_name,
                    message=f"V003 Missing required value in column '{column}' on row {row_index + 2}",
                )
            )

    return issues


def _validate_numeric_columns(sheet_name: str, df: pd.DataFrame) -> list[ValidationIssue]:
    issues = []
    numeric_columns = NUMERIC_COLUMNS.get(sheet_name, [])

    for column in numeric_columns:
        if column not in df.columns:
            continue

        values = df[column].dropna()
        invalid_values = pd.to_numeric(values, errors="coerce").isna()

        for row_index in values[invalid_values].index.tolist():
            issues.append(
                ValidationIssue(
                    severity="error",
                    sheet_name=sheet_name,
                    message=f"V004 Invalid number in column '{column}' on row {row_index + 2}",
                )
            )

    return issues


def _validate_date_columns(sheet_name: str, df: pd.DataFrame) -> list[ValidationIssue]:
    issues = []
    date_columns = DATE_COLUMNS.get(sheet_name, [])

    for column in date_columns:
        if column not in df.columns:
            continue

        values = df[column].dropna()
        invalid_values = pd.to_datetime(values, errors="coerce").isna()

        for row_index in values[invalid_values].index.tolist():
            issues.append(
                ValidationIssue(
                    severity="error",
                    sheet_name=sheet_name,
                    message=f"V005 Invalid date in column '{column}' on row {row_index + 2}",
                )
            )

    return issues