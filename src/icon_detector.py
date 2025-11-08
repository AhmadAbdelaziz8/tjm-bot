"""Template registration and icon finding."""
import pyautogui
from pathlib import Path
from botcity.core import DesktopBot

from .config import TEMPLATE_DIR, MATCHING_THRESHOLD, FIND_WAIT_TIME

# Icon cache for faster subsequent lookups
icon_cache = {}


def register_templates(bot: DesktopBot, directory: Path) -> bool:
    """Register all PNG templates from the given directory."""
    if not directory.is_dir():
        return False
        
    for img_path in directory.glob("*.png"):
        label = img_path.stem
        bot.add_image(label, str(img_path.resolve()))
    
    return True


def find_icon(bot: DesktopBot, template_labels: list[str], use_cache: bool = True) -> str | None:
    """Find an icon from the given template labels."""
    if use_cache and icon_cache:
        for label in template_labels:
            if label in icon_cache:
                return label
    
    thresholds = [MATCHING_THRESHOLD, MATCHING_THRESHOLD - 0.1]
    for threshold in thresholds:
        for label in template_labels:
            if bot.find(label=label, matching=threshold, waiting_time=FIND_WAIT_TIME):
                return label
    
    return None


def get_icon_coordinates(label: str) -> tuple[int, int] | None:
    """Get the screen coordinates of an icon by label."""
    template_path = TEMPLATE_DIR / f"{label}.png"
    if not template_path.exists():
        return None
    
    try:
        location = pyautogui.locateCenterOnScreen(
            str(template_path), 
            confidence=MATCHING_THRESHOLD - 0.1
        )
    except (TypeError, ValueError):
        try:
            location = pyautogui.locateCenterOnScreen(str(template_path))
        except:
            return None
    
    if location:
        return (int(location[0]), int(location[1]))
    return None

