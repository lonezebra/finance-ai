import threading
import tkinter

from finance_ai.ui.presenters.chat_presenter import ChatPresenter, ChatRole


class _FakeWidget:
    def after(self, ms, callback):
        pass


class _FakeAdvisor:
    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.calls = []

    def chat(self, month, messages):
        self.calls.append((month, list(messages)))
        if self.error:
            raise self.error
        return self.reply


class _BlockingFakeAdvisor:
    def __init__(self, reply: str):
        self.reply = reply
        self.calls = 0
        self._release = threading.Event()

    def chat(self, month, messages):
        self.calls += 1
        self._release.wait()
        return self.reply

    def release(self):
        self._release.set()


def _drain(presenter):
    presenter._task.join(timeout=2)
    presenter._task.poll(_FakeWidget())


def test_send_appends_user_message_and_delivers_assistant_reply():
    presenter = ChatPresenter()
    presenter.advisor = _FakeAdvisor(reply="You're in good shape.")
    received = []
    presenter.attach(
        on_message=received.append,
        on_thinking_change=lambda thinking: None,
    )

    presenter.send("How am I doing?", _FakeWidget())
    _drain(presenter)

    assert [m.content for m in received] == ["How am I doing?", "You're in good shape."]
    assert received[0].role == ChatRole.USER
    assert received[1].role == ChatRole.ASSISTANT
    assert presenter.is_thinking is False


def test_send_passes_full_history_to_advisor_on_second_turn():
    presenter = ChatPresenter()
    advisor = _FakeAdvisor(reply="Second reply.")
    presenter.advisor = advisor
    presenter.attach(on_message=lambda m: None, on_thinking_change=lambda t: None)

    presenter.send("First question", _FakeWidget())
    _drain(presenter)
    presenter.send("Follow-up", _FakeWidget())
    _drain(presenter)

    assert [m["content"] for m in advisor.calls[1][1]] == [
        "First question",
        "Second reply.",
        "Follow-up",
    ]


def test_send_ignored_when_empty_or_whitespace():
    presenter = ChatPresenter()
    presenter.advisor = _FakeAdvisor(reply="unused")
    presenter.attach(on_message=lambda m: None, on_thinking_change=lambda t: None)

    presenter.send("   ", _FakeWidget())

    assert presenter.messages == []
    assert presenter._task is None


def test_send_ignored_while_already_thinking():
    presenter = ChatPresenter()
    advisor = _BlockingFakeAdvisor(reply="Reply")
    presenter.advisor = advisor
    presenter.attach(on_message=lambda m: None, on_thinking_change=lambda t: None)

    presenter.send("First", _FakeWidget())
    presenter.send("Second, while first is still running", _FakeWidget())

    assert advisor.calls == 1
    assert len(presenter.messages) == 1

    advisor.release()
    _drain(presenter)


def test_error_becomes_friendly_assistant_message():
    presenter = ChatPresenter()
    presenter.advisor = _FakeAdvisor(error=ValueError("boom"))
    received = []
    presenter.attach(on_message=received.append, on_thinking_change=lambda t: None)

    presenter.send("Question", _FakeWidget())
    _drain(presenter)

    assert received[-1].role == ChatRole.ASSISTANT
    assert "boom" in received[-1].content
    assert presenter.is_thinking is False


def test_reattaching_replays_full_message_history():
    presenter = ChatPresenter()
    presenter.advisor = _FakeAdvisor(reply="Reply")
    presenter.attach(on_message=lambda m: None, on_thinking_change=lambda t: None)
    presenter.send("Question", _FakeWidget())
    _drain(presenter)
    presenter.detach()

    replayed = []
    presenter.attach(on_message=replayed.append, on_thinking_change=lambda t: None)

    assert [m.content for m in replayed] == ["Question", "Reply"]


def test_dead_widget_callback_self_heals_instead_of_raising():
    presenter = ChatPresenter()
    presenter.advisor = _FakeAdvisor(reply="Reply")

    def dead_widget_callback(message):
        raise tkinter.TclError("invalid command name \".!label\"")

    presenter.attach(on_message=dead_widget_callback, on_thinking_change=lambda t: None)

    presenter.send("Question", _FakeWidget())
    _drain(presenter)  # must not raise

    assert presenter._listener is None
