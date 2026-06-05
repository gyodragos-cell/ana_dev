from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ANA_MAX = ROOT / "ANA_MAX"
if str(ANA_MAX) not in sys.path:
    sys.path.insert(0, str(ANA_MAX))

from tools import desktop_control_tool  # noqa: E402
from tools.desktop_control_tool import DesktopControlTool  # noqa: E402


def test_move_mouse_accepts_target_coordinates(monkeypatch):
    monkeypatch.setattr(desktop_control_tool, "HAS_DESKTOP_LIBS", True)

    moves = []

    class FakePyAutoGui:
        FAILSAFE = False

        @staticmethod
        def moveTo(x, y):
            moves.append((x, y))

    monkeypatch.setattr(desktop_control_tool, "pyautogui", FakePyAutoGui)

    result = DesktopControlTool().execute(operation="move_mouse", target="10, 20")

    assert result.is_success
    assert result.message == "Mouse mutat la (10, 20)"
    assert moves == [(10, 20)]


def test_move_mouse_keeps_x_y_coordinates(monkeypatch):
    monkeypatch.setattr(desktop_control_tool, "HAS_DESKTOP_LIBS", True)

    moves = []

    class FakePyAutoGui:
        FAILSAFE = False

        @staticmethod
        def moveTo(x, y):
            moves.append((x, y))

    monkeypatch.setattr(desktop_control_tool, "pyautogui", FakePyAutoGui)

    result = DesktopControlTool().execute(operation="move_mouse", x="30", y="40")

    assert result.is_success
    assert result.message == "Mouse mutat la (30, 40)"
    assert moves == [(30, 40)]
