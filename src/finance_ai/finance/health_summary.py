from finance_ai.finance.confidence import calculate_financial_confidence_score


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