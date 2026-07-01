from finance_ai.finance.confidence import calculate_financial_confidence_score
from finance_ai.finance.health import calculate_financial_health_score


def confidence_summary() -> str:
    confidence = calculate_financial_confidence_score()

    lines = [
        f"Financial Confidence: {confidence.score}/100",
        f"Label: {confidence.label}",
        "",
        "Issues:",
    ]

    if not confidence.issues:
        lines.append("- No major data quality issues detected.")
    else:
        for issue in confidence.issues:
            lines.append(f"- [{issue.severity}] {issue.message}")

    return "\n".join(lines)


def health_summary(month: str) -> str:
    health = calculate_financial_health_score(month)

    lines = [
        f"Financial Health: {health.score}/100",
        f"Label: {health.label}",
        "",
        "Issues:",
    ]

    if not health.issues:
        lines.append("- No major financial health issues detected.")
    else:
        for issue in health.issues:
            lines.append(f"- [{issue.severity}] {issue.message}")

    return "\n".join(lines)