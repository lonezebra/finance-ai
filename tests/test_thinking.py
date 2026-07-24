from finance_ai.ai.thinking import EXECUTIVE_BRIEFING_THINKING_STEPS, ThinkingAnimator


class _FakeWidget:
    def __init__(self):
        self.scheduled = []

    def after(self, ms, callback):
        self.scheduled.append((ms, callback))


def test_animator_emits_first_step_immediately_on_start():
    updates = []
    widget = _FakeWidget()
    animator = ThinkingAnimator(EXECUTIVE_BRIEFING_THINKING_STEPS, on_update=updates.append)

    animator.start(widget)

    assert updates == [EXECUTIVE_BRIEFING_THINKING_STEPS[0]]
    assert len(widget.scheduled) == 1


def test_animator_cycles_through_all_steps_in_order():
    updates = []
    widget = _FakeWidget()
    animator = ThinkingAnimator(EXECUTIVE_BRIEFING_THINKING_STEPS, on_update=updates.append)

    animator.start(widget)

    while widget.scheduled:
        _, callback = widget.scheduled.pop(0)
        callback()

    assert updates == EXECUTIVE_BRIEFING_THINKING_STEPS


def test_animator_stop_prevents_further_updates():
    updates = []
    widget = _FakeWidget()
    animator = ThinkingAnimator(EXECUTIVE_BRIEFING_THINKING_STEPS, on_update=updates.append)

    animator.start(widget)
    animator.stop()

    _, callback = widget.scheduled.pop(0)
    callback()

    assert len(updates) == 1
