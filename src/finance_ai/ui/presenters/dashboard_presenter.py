import tkinter
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from finance_ai.finance.dashboard import DashboardData, create_dashboard_data


@dataclass(frozen=True)
class StatusMessage:
    text: str
    is_error: bool = False


class DashboardPresenter:
    """Read path for the Dashboard page.

    Everything here is a synchronous SQLite read -- fast enough to redo on every page visit,
    unlike the Executive Briefing's AI narrative. No in-flight state to preserve across
    navigation, so unlike BriefingPresenter/ChatPresenter/ScenarioPresenter this doesn't need
    to be owned by MainWindow; a fresh instance per visit is fine.

    create_dashboard_data_fn is injectable for testing, same pattern as SettingsPresenter's
    backup functions.
    """

    def __init__(self, create_dashboard_data_fn=create_dashboard_data):
        self._create_dashboard_data = create_dashboard_data_fn

        self.data: DashboardData | None = None
        self.status: StatusMessage | None = None
        self._on_change = None

    def attach(self, on_change) -> None:
        self._on_change = on_change
        self.refresh()

    def detach(self) -> None:
        self._on_change = None

    def refresh(self) -> None:
        """Reload dashboard data. Never raises -- a read failure becomes a status message,
        since the Dashboard failing to open outright is worse than it opening with a note
        that the data couldn't be read (CLAUDE.md Rule 8)."""

        try:
            self.data = self._create_dashboard_data()
            self.status = None
        except (SQLAlchemyError, OSError) as exc:
            self.data = None
            self.status = StatusMessage(f"Could not read the database: {exc}", is_error=True)

        self._notify()

    def _notify(self) -> None:
        if not self._on_change:
            return

        try:
            self._on_change()
        except tkinter.TclError:
            # Same race as the other presenters: <Destroy> and an already-scheduled callback
            # aren't strictly ordered, so this can fire against a torn-down widget.
            self._on_change = None
