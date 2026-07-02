from finance_ai.imports.models import ValidationReport


def format_validation_report(report: ValidationReport) -> str:
    lines = [
        "Workbook Validation Report",
        "",
        f"Valid: {'Yes' if report.is_valid else 'No'}",
        f"Errors: {len(report.errors)}",
        f"Warnings: {len(report.warnings)}",
        "",
    ]

    if not report.issues:
        lines.append("No validation issues found.")
        return "\n".join(lines)

    lines.append("Issues:")

    for issue in report.issues:
        lines.append(f"- [{issue.severity}] {issue.sheet_name}: {issue.message}")

    return "\n".join(lines)