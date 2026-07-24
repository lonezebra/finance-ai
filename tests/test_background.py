from finance_ai.ai.background import BackgroundTask


class _FakeWidget:
    def after(self, ms, callback):
        pass


def test_background_task_delivers_success_result():
    results = []

    task = BackgroundTask(
        target=lambda: "done",
        on_success=results.append,
        on_error=lambda exc: None,
    )
    task.start()
    task.join(timeout=2)
    task.poll(_FakeWidget())

    assert results == ["done"]


def test_background_task_delivers_error_when_target_raises():
    errors = []

    def boom():
        raise ValueError("bad")

    task = BackgroundTask(
        target=boom,
        on_success=lambda result: None,
        on_error=errors.append,
    )
    task.start()
    task.join(timeout=2)
    task.poll(_FakeWidget())

    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)


def test_background_task_reschedules_poll_while_pending():
    scheduled = []

    class SlowWidget:
        def after(self, ms, callback):
            scheduled.append((ms, callback))

    task = BackgroundTask(
        target=lambda: "done",
        on_success=lambda result: None,
        on_error=lambda exc: None,
    )
    # Do not start the thread: queue stays empty, so poll() must reschedule via after().
    task.poll(SlowWidget())

    assert len(scheduled) == 1
