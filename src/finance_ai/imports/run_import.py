from pathlib import Path

from finance_ai.imports.importer import ImportResult, import_dataset
from finance_ai.imports.mapper import map_workbook
from finance_ai.imports.reader import read_excel_workbook
from finance_ai.imports.report import format_validation_report
from finance_ai.imports.validator import validate_workbook
from finance_ai.logging_config import configure_logging


def run_excel_import(path: str | Path) -> ImportResult:
    workbook = read_excel_workbook(path)
    validation_report = validate_workbook(workbook)

    print(format_validation_report(validation_report))

    if not validation_report.is_valid:
        raise ValueError("Workbook validation failed. Import cancelled.")

    dataset = map_workbook(workbook)
    result = import_dataset(dataset, source_file=workbook.source_file)

    print()
    print("Import Complete")
    for label, entity_result in result.by_label():
        if entity_result.created:
            print(f"- {label}: {entity_result.created} created")
        if entity_result.updated:
            print(f"- {label}: {entity_result.updated} updated")
        if entity_result.skipped_duplicate:
            print(f"- {label}: {entity_result.skipped_duplicate} duplicate skipped")

    return result


if __name__ == "__main__":
    configure_logging()
    run_excel_import("data/exports/finance_template.xlsx")