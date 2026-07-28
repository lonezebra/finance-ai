import tkinter
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

from finance_ai.ai.advisor import StrategicAdvisor
from finance_ai.ai.background import BackgroundTask
from finance_ai.ai.errors import describe_ai_error


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


class ChatListener(NamedTuple):
    on_message: object
    on_thinking_change: object


class ChatPresenter:
    """Owns the chat conversation's lifecycle independent of any one view, same reasoning
    as BriefingPresenter: ChatView is destroyed and recreated every time the sidebar
    navigates away and back, so the conversation (and any in-flight request) needs to live
    somewhere that survives that -- MainWindow, not the view. In-memory only for v1: lost on
    app restart, kept for the running session.
    """

    def __init__(self, month: str | None = None):
        # None means "whatever month the data is about", resolved downstream inside
        # create_executive_report() on every send -- not once at construction, since this
        # presenter is built at app start and the user may import data afterwards.
        self.month = month
        self.advisor = StrategicAdvisor()
        self.messages: list[ChatMessage] = []
        self.is_thinking = False
        self._task: BackgroundTask | None = None
        self._listener: ChatListener | None = None

    def attach(self, on_message, on_thinking_change) -> None:
        self._listener = ChatListener(on_message, on_thinking_change)

        for message in self.messages:
            on_message(message)

        if self.is_thinking:
            on_thinking_change(True)

    def detach(self) -> None:
        self._listener = None

    def send(self, text: str, widget) -> None:
        text = text.strip()
        if not text or self.is_thinking:
            return

        user_message = ChatMessage(role=ChatRole.USER, content=text)
        self.messages.append(user_message)
        self._notify(lambda listener: listener.on_message(user_message))

        self.is_thinking = True
        self._notify(lambda listener: listener.on_thinking_change(True))

        history = [{"role": message.role.value, "content": message.content} for message in self.messages]

        self._task = BackgroundTask(
            target=lambda: self.advisor.chat(self.month, history),
            on_success=self._handle_success,
            on_error=self._handle_error,
        )
        self._task.start()
        self._task.poll(widget)

    def _handle_success(self, text: str) -> None:
        self._finish(ChatMessage(role=ChatRole.ASSISTANT, content=text))

    def _handle_error(self, exc: Exception) -> None:
        self._finish(ChatMessage(role=ChatRole.ASSISTANT, content=describe_ai_error(exc)))

    def _finish(self, assistant_message: ChatMessage) -> None:
        self.is_thinking = False
        self.messages.append(assistant_message)
        self._notify(lambda listener: listener.on_thinking_change(False))
        self._notify(lambda listener: listener.on_message(assistant_message))

    def _notify(self, call) -> None:
        if not self._listener:
            return

        try:
            call(self._listener)
        except tkinter.TclError:
            # Same race as BriefingPresenter: <Destroy> and an already-scheduled callback
            # aren't strictly ordered, so this can fire against a torn-down widget. Treat
            # that as an implicit detach instead of crashing the callback.
            self._listener = None
