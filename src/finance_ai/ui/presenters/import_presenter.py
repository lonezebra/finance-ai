from dataclasses import dataclass, field
from pathlib import Path

from finance_ai.exports.excel_template import create_template
from finance_ai.imports.importer import ImportResult, import_dataset
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

    create_template_fn is injectable, same pattern as SettingsPresenter's backup functions,
    so tests can point it at a tmp_path instead of the real exports directory.
    """

    def __init__(self, create_template_fn=create_template):
        self._create_template_fn = create_template_fn

    def create_template(self, path: str | Path | None = None) -> Path:
        """Writes a blank import template to path (the default location if None) and
        returns where it landed. Safe to call repeatedly at the same path -- the template
        holds only column headers and illustrative example rows, never the user's own
        data, so overwriting a previous copy is never destructive."""

        if path is None:
            return self._create_template_fn()
        return self._create_template_fn(Path(path))

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

    def confirm_import(self, preview: ImportPreview) -> ImportResult:
        if preview.dataset is None:
            raise ValueError("Cannot import a workbook that failed validation.")

        return import_dataset(preview.dataset, source_file=preview.source_file)
