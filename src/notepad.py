"""Notepad window management functions."""
import time
import pyautogui
import pyperclip
import pygetwindow as gw
import requests
from pathlib import Path
from botcity.core import DesktopBot

from .icon_detector import icon_cache, get_icon_coordinates, find_icon
from .config import MATCHING_THRESHOLD, FIND_WAIT_TIME, API_URL, PROJECT_PATH


def get_notepad_windows():
    """Get all Notepad windows, excluding Cursor/Code windows."""
    all_windows = gw.getWindowsWithTitle("Notepad")
    notepad_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        if title == "notepad" or title.endswith(" - notepad"):
            if "cursor" not in title and "code" not in title:
                notepad_windows.append(window)
    
    return notepad_windows


def _is_valid_notepad(window) -> bool:
    """Check if window is a valid Notepad window."""
    title = window.title.lower()
    return "cursor" not in title and "code" not in title


def close_existing_notepad():
    """Close all existing Notepad windows."""
    active_windows = get_notepad_windows()
    if not active_windows:
        return
    
    print(f"Found {len(active_windows)} existing Notepad window(s). Closing...")
    for window in active_windows:
        if window.visible and _is_valid_notepad(window):
            window.close()
            time.sleep(0.5)
            try:
                pyautogui.press('n')
                time.sleep(0.3)
            except:
                pass
    
    time.sleep(0.5)
    
    # Force close remaining windows
    remaining_windows = get_notepad_windows()
    if remaining_windows:
        for window in remaining_windows:
            if window.visible and _is_valid_notepad(window):
                window.activate()
                time.sleep(0.2)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.3)
                pyautogui.press('n')
                time.sleep(0.3)
    
    print("Existing Notepad windows closed.")


def close_notepad_fully() -> bool:
    """Close Notepad windows with verification."""
    print("Closing Notepad...")
    active_windows = get_notepad_windows()
    
    if not active_windows:
        print("No Notepad windows found to close.")
        return True
    
    # Initial close attempt
    for window in active_windows:
        if window.visible and _is_valid_notepad(window):
            try:
                window.close()
                time.sleep(0.5)
            except:
                window.activate()
                time.sleep(0.2)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.5)
    
    # Verify closure
    timeout = time.time() + 5
    while time.time() < timeout:
        remaining_windows = get_notepad_windows()
        if not remaining_windows or not any(win.visible for win in remaining_windows):
            print("Notepad successfully closed and verified.")
            time.sleep(0.5)
            return True
        time.sleep(0.2)
    
    # Aggressive close if still open
    remaining_windows = get_notepad_windows()
    if remaining_windows:
        print("Warning: Notepad still open, trying aggressive close...")
        for window in remaining_windows:
            if window.visible and _is_valid_notepad(window):
                window.activate()
                time.sleep(0.2)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.3)
                pyautogui.press('n')
                time.sleep(0.5)
        
        final_check = get_notepad_windows()
        if not final_check or not any(win.visible for win in final_check):
            print("Notepad closed after aggressive attempt.")
            return True
        else:
            print("Error: Failed to close Notepad completely.")
            return False
    
    return True


def fetch_posts() -> list[dict] | None:
    """Fetch posts from the API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API is unavailable. {e}")
        return None


def launch_notepad(bot: DesktopBot, template_labels: list[str]) -> bool:
    """Launch Notepad by finding and clicking the icon."""
    found_label = None
    
    # Try to find icon with retries
    for attempt in range(3):
        found_label = find_icon(bot, template_labels)
        if found_label:
            break
        print(f"Icon not found (Attempt {attempt + 1}/3). Retrying...")
        time.sleep(0.5)  # Reduced from 1s for faster retries
        
    if not found_label:
        print("Error: Icon not found after 3 attempts.")
        return False
        
    print(f"Double-clicking Notepad icon: '{found_label}'")
    
    # Try cached coordinates first
    clicked_coords = None
    used_cache = False
    
    if found_label in icon_cache:
        cached_x, cached_y = icon_cache[found_label]
        cached_x, cached_y = int(cached_x), int(cached_y)
        clicked_coords = (cached_x, cached_y)
        used_cache = True
        
        try:
            pyautogui.doubleClick(cached_x, cached_y)
            time.sleep(0.3)
        except:
            if found_label in icon_cache:
                del icon_cache[found_label]
            clicked_coords = None
            used_cache = False
    
    # If cache failed, find icon fresh
    if not clicked_coords:
        clicked_coords = _click_icon(bot, found_label)
        if not clicked_coords:
            return False
    
    # Verify launch
    if _verify_notepad_launched(found_label, clicked_coords):
        return True
    
    # Retry if cache was used and failed
    if used_cache:
        return _retry_launch_without_cache(bot, template_labels, found_label)
    
    print("Error: Notepad window not detected after launch.")
    return False


def _click_icon(bot: DesktopBot, label: str) -> tuple[int, int] | None:
    """Click on an icon and return its coordinates."""
    thresholds = [MATCHING_THRESHOLD, MATCHING_THRESHOLD - 0.1]
    for threshold in thresholds:
        if bot.find(label=label, matching=threshold, waiting_time=FIND_WAIT_TIME):
            coords = get_icon_coordinates(label)
            if coords:
                pyautogui.doubleClick(coords[0], coords[1])
                return coords
            else:
                bot.double_click()
                return None
    print("Error: Could not click on icon.")
    return None


def _verify_notepad_launched(label: str, coords: tuple[int, int] | None) -> bool:
    """Verify that Notepad launched successfully."""
    timeout = time.time() + 5
    while time.time() < timeout:
        active_windows = get_notepad_windows()
        if any(win.visible for win in active_windows):
            print("Notepad successfully launched and validated.")
            if coords and label:
                icon_cache[label] = coords
            time.sleep(0.5)  # Reduced from 1s for faster processing
            return True
        time.sleep(0.2)
    return False


def _retry_launch_without_cache(bot: DesktopBot, template_labels: list[str], old_label: str) -> bool:
    """Retry launching Notepad after cache invalidation."""
    print("Warning: Notepad did not launch after using cached coordinates. Invalidating cache and retrying...")
    if old_label in icon_cache:
        del icon_cache[old_label]
    
    found_label = find_icon(bot, template_labels, use_cache=False)
    if not found_label:
        print("Error: Icon not found after cache invalidation.")
        return False
    
    print(f"Retrying with fresh detection: '{found_label}'")
    clicked_coords = _click_icon(bot, found_label)
    if not clicked_coords:
        print("Error: Could not click on icon after retry.")
        return False
    
    if _verify_notepad_launched(found_label, clicked_coords):
        return True
    
    return False


def write_post_to_notepad(post: dict, project_path: Path):
    """Write post content to Notepad and save it."""
    active_windows = get_notepad_windows()
    if active_windows:
        window = active_windows[0]
        window.activate()
        time.sleep(0.5)
        
        center_x = window.left + window.width // 2
        center_y = window.top + window.height // 2
        pyautogui.click(center_x, center_y)
        time.sleep(0.3)
    
    # Clear and write content
    pyautogui.hotkey('ctrl', 'n')
    time.sleep(0.5)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.2)
    
    content = f"Title: {post['title']}\n\n{post['body']}"
    pyperclip.copy(content)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)
    
    # Save file
    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)
    
    filename = f"post_{post['id']}.txt"
    filepath = str(project_path / filename)
    pyautogui.write(filepath, interval=0.01)
    pyautogui.press('enter')
    time.sleep(0.5)
    
    # Handle overwrite confirmation
    confirm_window = gw.getWindowsWithTitle("Confirm Save As")
    if confirm_window:
        print("File exists. Overwriting.")
        pyautogui.press('y')
        time.sleep(0.5)

