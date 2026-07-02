from dataclasses import dataclass, field

import pandas as pd


EXPECTED_SHEETS = [
    "Accounts",
    "Categories",
    "Transactions",
    "Debts",
    "Assets",
    "Budgets",
    "Goals",
]


@dataclass(frozen=True)
class WorkbookData:
    source_file: str
    sheets: dict[str, pd.DataFrame]

    def has_sheet(self, sheet_name: str) -> bool:
        return sheet_name in self.sheets

    def get_sheet(self, sheet_name: str) -> pd.DataFrame:
        return self.sheets[sheet_name]


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    sheet_name: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]


@dataclass(frozen=True)
class ImportSummary:
    source_file: str
    imported_counts: dict[str, int]
    validation_report: ValidationReport

    @property
    def total_imported(self) -> int:
        return sum(self.imported_counts.values())