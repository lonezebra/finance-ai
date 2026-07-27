from dataclasses import dataclass, field

from finance_ai.imports.importer import import_dataset
from finance_ai.imports.mapper import ImportDataset, map_workbook
from finance_ai.imports.models import ValidationReport
from finance_ai.imports.reader import read_excel_workbook
from finance_ai.imports.validator import validate_workbook

SHEET_LABELS = ["Accounts", "Categories", "Transactions", "Debts", "Assets", "Budgets", "Goals"]


@dataclass(frozen=True)
class ImportPreview:
    source_file: str
    validation_report: ValidationReport
    dataset: ImportDataset | None
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_count(self) -> int:
        return sum(self.counts.values())


class ImportPresenter:
    """Read path (choose + preview): pure file I/O and validation, no DB writes.

    confirm_import() is the only step that touches the database -- kept as a separate
    call so the preview can be shown, and re-shown, without risk of committing anything.
    """

    def load_preview(self, path: str) -> ImportPreview:
        workbook = read_excel_workbook(path)
        validation_report = validate_workbook(workbook)

        if not validation_report.is_valid:
            return ImportPreview(
                source_file=workbook.source_file,
                validation_report=validation_report,
                dataset=None,
            )

        dataset = map_workbook(workbook)
        counts = {
            "Accounts": len(dataset.accounts),
            "Categories": len(dataset.categories),
            "Transactions": len(dataset.transactions),
            "Debts": len(dataset.debts),
            "Assets": len(dataset.assets),
            "Budgets": len(dataset.budgets),
            "Goals": len(dataset.goals),
        }

        return ImportPreview(
            source_file=workbook.source_file,
            validation_report=validation_report,
            dataset=dataset,
            counts=counts,
        )

    def confirm_import(self, preview: ImportPreview) -> dict[str, int]:
        if preview.dataset is None:
            raise ValueError("Cannot import a workbook that failed validation.")

        return import_dataset(preview.dataset, source_file=preview.source_file)
