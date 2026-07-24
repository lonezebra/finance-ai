import threading

from finance_ai.ui.presenters.briefing_presenter import BriefingPresenter, BriefingRequestState


class _FakeWidget:
    def after(self, ms, callback):
        pass


class _FakeAdvisor:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def executive_briefing(self, month):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class _BlockingFakeAdvisor:
    """Doesn't return until release() is called, so tests can hold a request RUNNING
    for as long as needed instead of racing against how fast a fake call completes."""

    def __init__(self, result: str):
        self.result = result
        self.calls = 0
        self._release = threading.Event()

    def executive_briefing(self, month):
        self.calls += 1
        self._release.wait()
        return self.result

    def release(self):
        self._release.set()


def _drain(presenter):
    presenter._task.join(timeout=2)
    presenter._task.poll(_FakeWidget())


def test_generate_delivers_success_to_attached_listener():
    presenter = BriefingPresenter()
    presenter.advisor = _FakeAdvisor(result="Briefing text")
    successes = []
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=successes.append,
        on_error=lambda message: None,
    )

    presenter.generate(_FakeWidget())
    _drain(presenter)

    assert successes == ["Briefing text"]
    assert presenter.state == BriefingRequestState.DONE
    assert presenter.result_text == "Briefing text"


def test_generate_delivers_friendly_error_to_attached_listener():
    presenter = BriefingPresenter()
    presenter.advisor = _FakeAdvisor(error=ValueError("boom"))
    errors = []
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=lambda text: None,
        on_error=errors.append,
    )

    presenter.generate(_FakeWidget())
    _drain(presenter)

    assert presenter.state == BriefingRequestState.ERROR
    assert "boom" in errors[0]


def test_second_generate_call_is_ignored_while_running():
    presenter = BriefingPresenter()
    advisor = _BlockingFakeAdvisor(result="Briefing text")
    presenter.advisor = advisor
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=lambda text: None,
        on_error=lambda message: None,
    )

    presenter.generate(_FakeWidget())
    first_task = presenter._task
    presenter.generate(_FakeWidget())

    assert presenter._task is first_task
    assert advisor.calls == 1
    assert presenter.state == BriefingRequestState.RUNNING

    advisor.release()
    _drain(presenter)


def test_reattaching_after_completion_replays_result_without_rerunning():
    presenter = BriefingPresenter()
    presenter.advisor = _FakeAdvisor(result="Briefing text")
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=lambda text: None,
        on_error=lambda message: None,
    )
    presenter.generate(_FakeWidget())
    _drain(presenter)
    presenter.detach()

    successes = []
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=successes.append,
        on_error=lambda message: None,
    )

    assert successes == ["Briefing text"]
    assert presenter.advisor.calls == 1


def test_detach_prevents_crash_on_late_delivery():
    presenter = BriefingPresenter()
    presenter.advisor = _FakeAdvisor(result="Briefing text")
    presenter.attach(
        on_thinking_update=lambda state: None,
        on_success=lambda text: None,
        on_error=lambda message: None,
    )
    presenter.generate(_FakeWidget())
    presenter.detach()

    # Should not raise even though no listener is attached to receive the result.
    _drain(presenter)

    assert presenter.state == BriefingRequestState.DONE
