"""CLI behind `make briefing`: prints the deterministic Executive Report as plain text.

Replaces the retired Opportunity Engine chain (briefing_summary -> open_cfo ->
opportunities), which produced a *separate* set of recommendations from the ones the desktop
app and the AI advisor work from. Printing the same formatted report those consume means the
command line and the product can't disagree about what the numbers say.

Uses persist=False: reading a briefing shouldn't write a snapshot to history every time.
"""

import argparse

from finance_ai.logging_config import configure_logging
from finance_ai.reports.engine import create_executive_report
from finance_ai.reports.formatter import format_executive_report_for_ai

def print_briefing(month: str | None = None) -> str:
    report = create_executive_report(month, persist=False)
    text = format_executive_report_for_ai(report)
    print(text)
    return text


def main(argv: list[str] | None = None) -> int:
    configure_logging()

    parser = argparse.ArgumentParser(prog="finance_ai.reports.run_briefing")
    parser.add_argument(
        "--month",
        default=None,
        help="Month to report on, as YYYY-MM "
        "(defaults to the month of your most recent transaction)",
    )
    args = parser.parse_args(argv)

    print_briefing(args.month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
