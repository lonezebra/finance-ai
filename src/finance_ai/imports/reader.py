from pathlib import Path

import pandas as pd

from finance_ai.imports.models import WorkbookData


def read_excel_workbook(path: str | Path) -> WorkbookData:
    workbook_path = Path(path)

    sheets = pd.read_excel(workbook_path, sheet_name=None)

    return WorkbookData(
        source_file=str(workbook_path),
        sheets=sheets,
    )