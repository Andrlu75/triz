from apps.ariz_engine.modes.autopilot import AutopilotMode
from apps.ariz_engine.modes.express import ExpressMode
from apps.ariz_engine.modes.full import FullARIZMode

MODE_CLASSES = {
    "express": ExpressMode,
    "full": FullARIZMode,
    "autopilot": AutopilotMode,
}


def get_mode_class(mode: str) -> type:
    """Return the mode class for a given mode name."""
    return MODE_CLASSES.get(mode, ExpressMode)


__all__ = [
    "AutopilotMode",
    "ExpressMode",
    "FullARIZMode",
    "MODE_CLASSES",
    "get_mode_class",
]
