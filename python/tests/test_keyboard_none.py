import inspect

import pytest

from PiFinder import keyboard_none


@pytest.mark.unit
def test_keyboard_none_accepts_main_process_arguments():
    signature = inspect.signature(keyboard_none.run_keyboard)

    assert list(signature.parameters) == [
        "q",
        "shared_state",
        "log_queue",
    ]
