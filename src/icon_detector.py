"""Template registration and icon finding."""
from pathlib import Path
from botcity.core import DesktopBot

from .config import MATCHING_THRESHOLD, FIND_WAIT_TIME

# Icon cache for faster subsequent lookups / in case of the same coordinates
icon_cache = {}


def register_templates(bot: DesktopBot, directory: Path) -> bool:
    """Register all PNG templates from the given directory."""
    if not directory.is_dir():
        return False
    
    for img_path in directory.glob("*.png"):
        label = img_path.stem
        bot.add_image(label, str(img_path.resolve()))
    
    return True


def invalidate_cache(label: str = None):
    """Invalidate icon cache for a specific label or clear entire cache."""
    if label:
        icon_cache.pop(label, None)
    else:
        icon_cache.clear()


def find_icon(bot: DesktopBot, template_labels: list[str], use_cache: bool = True, click: bool = False) -> tuple[str, tuple[int, int]] | None:
    """Find an icon from the given template labels and return label with coordinates.
    
    Args:
        bot: DesktopBot instance
        template_labels: List of template labels to search
        use_cache: Whether to use cached coordinates
        click: Whether to double-click the icon after finding it
    
    Returns:
        Tuple of (label, (x, y)) or None if not found
    """
    if use_cache and icon_cache:
        for label in template_labels:
            if label in icon_cache:
                coords = icon_cache[label]
                if click:
                    # Re-find to enable double_click on last found element
                    if bot.find(label=label, matching=MATCHING_THRESHOLD, waiting_time=FIND_WAIT_TIME):
                        bot.double_click()
                    else:
                        # Cache invalid, remove and continue to search
                        invalidate_cache(label)
                        break
                return (label, coords)
    
    thresholds = [MATCHING_THRESHOLD, MATCHING_THRESHOLD - 0.1]
    for threshold in thresholds:
        for label in template_labels:
            if bot.find(label=label, matching=threshold, waiting_time=FIND_WAIT_TIME):
                # Get coordinates immediately after successful find
                coords = bot.get_element_coords(label, matching=threshold)
                if not coords:
                    coords = bot.get_element_coords(label)
                
                if coords:
                    x, y = int(coords[0]), int(coords[1])
                    icon_cache[label] = (x, y)
                    if click:
                        bot.double_click()
                    return (label, (x, y))
    
    return None

