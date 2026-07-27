from pathlib import Path

from finance_ai.imports.importer import import_dataset
from finance_ai.imports.mapper import map_workbook
from finance_ai.imports.reader import read_excel_workbook
from finance_ai.imports.report import format_validation_report
from finance_ai.imports.validator import validate_workbook


def run_excel_import(path: str | Path) -> dict[str, int]:
    workbook = read_excel_workbook(path)
    validation_report = validate_workbook(workbook)

    print(format_validation_report(validation_report))

    if not validation_report.is_valid:
        raise ValueError("Workbook validation failed. Import cancelled.")

    dataset = map_workbook(workbook)
    imported_counts = import_dataset(dataset, source_file=workbook.source_file)

    print()
    print("Import Complete")
    for name, count in imported_counts.items():
        print(f"- {name}: {count}")

    return imported_counts


if __name__ == "__main__":
    run_excel_import("data/exports/finance_template.xlsx")