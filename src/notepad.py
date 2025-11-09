"""Notepad window management functions."""
import time
import pyautogui
import pyperclip
import pygetwindow as gw
import requests
from pathlib import Path
from botcity.core import DesktopBot

from .icon_detector import icon_cache, find_icon, invalidate_cache
from .config import API_URL, SPACING


# ============================================================================
# Helper Functions
# ============================================================================

def _wait(delay: float = SPACING):
    """Wait for the default spacing time."""
    time.sleep(delay)


def _activate_and_click_center(window):
    """Activate a window and click its center."""
    window.activate()
    _wait()
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2
    pyautogui.click(center_x, center_y)
    _wait()


def _wait_for_dialog(title: str, timeout: float) -> bool:
    """Wait for a dialog window to appear. Returns True if found."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        dialogs = gw.getWindowsWithTitle(title)
        if dialogs:
            dialogs[0].activate()
            _wait()
            return True
        _wait()
    return False


def _close_window_with_fallback(window):
    """Close a window with fallback to Alt+F4 and press 'n'."""
    try:
        window.close()
        _wait()
        pyautogui.press('n')
        _wait()
    except:
        window.activate()
        _wait()
        pyautogui.hotkey('alt', 'f4')
        _wait()
        pyautogui.press('n')
        _wait()


# ============================================================================
# Window Management
# ============================================================================

def get_notepad_windows():
    all_windows = gw.getWindowsWithTitle("Notepad")
    notepad_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        if title == "notepad" or title.endswith(" - notepad"):
            notepad_windows.append(window)
    
    return notepad_windows


def _is_valid_notepad(window) -> bool:
    """Check if window is a valid Notepad window."""
    title = window.title.lower()
    return "cursor" not in title and "code" not in title


# ============================================================================
# Window Closing
# ============================================================================

def close_notepad(verify: bool = False) -> bool:
    """Close all existing Notepad windows. If verify=True, returns success status."""
    active_windows = get_notepad_windows()
    if not active_windows:
        return True
    
    for window in active_windows:
        if window.visible and _is_valid_notepad(window):
            _close_window_with_fallback(window)
    
    if not verify:
        return True
    
    # Verification: wait for windows to close
    timeout = time.time() + 5
    while time.time() < timeout:
        remaining_windows = get_notepad_windows()
        if not remaining_windows or not any(win.visible for win in remaining_windows):
            _wait()
            return True
        _wait()
    
    # Final attempt with fallback
    remaining_windows = get_notepad_windows()
    if remaining_windows:
        for window in remaining_windows:
            if window.visible and _is_valid_notepad(window):
                _close_window_with_fallback(window)
        
        final_check = get_notepad_windows()
        return not final_check or not any(win.visible for win in final_check)
    
    return True


def close_existing_notepad():
    """Close all existing Notepad windows (no verification)."""
    close_notepad(verify=False)


def close_notepad_fully() -> bool:
    """Close Notepad windows with verification."""
    return close_notepad(verify=True)


# ============================================================================
# Icon Detection & Launching
# ============================================================================

def launch_notepad(bot: DesktopBot, template_labels: list[str]) -> bool:
    """Launch Notepad by finding and clicking the icon."""
    for attempt in range(3):
        result = find_icon(bot, template_labels, use_cache=True, click=True)
        if result:
            found_label, coords = result
            if _verify_notepad_launched(found_label, coords):
                return True
            # Cache may be stale, invalidate and retry
            invalidate_cache(found_label)
        _wait()
    
    # Final attempt without cache
    result = find_icon(bot, template_labels, use_cache=False, click=True)
    if result:
        found_label, coords = result
        return _verify_notepad_launched(found_label, coords)
    
    return False


def _verify_notepad_launched(label: str, coords: tuple[int, int] | None) -> bool:
    """Verify that Notepad launched successfully."""
    timeout = time.time() + 5
    while time.time() < timeout:
        active_windows = get_notepad_windows()
        if any(win.visible for win in active_windows):
            if coords and label:
                icon_cache[label] = coords
            _wait()
            return True
        _wait()
    return False


# ============================================================================
# Content Writing
# ============================================================================

def _prepare_notepad_window():
    """Prepare Notepad window by activating and clicking center."""
    active_windows = get_notepad_windows()
    if active_windows:
        _activate_and_click_center(active_windows[0])


def _paste_content(content: str):
    """Paste content into Notepad using clipboard."""
    pyperclip.copy(content)
    _wait()
    pyautogui.hotkey('ctrl', 'a')
    _wait()
    pyautogui.press('delete')
    _wait()
    pyautogui.hotkey('ctrl', 'v')
    _wait()


def _save_file(filepath: str) -> bool:
    """Save file via Save As dialog. Returns True if successful."""
    pyautogui.hotkey('ctrl', 's')
    _wait()
    
    if not _wait_for_dialog("Save As", 3):
        return False
    
    pyautogui.hotkey('ctrl', 'a')
    _wait()
    pyperclip.copy(filepath)
    _wait()
    pyautogui.hotkey('ctrl', 'v')
    _wait()
    pyautogui.press('enter')
    _wait()
    
    # Handle confirmation dialog if file exists
    confirm_window = gw.getWindowsWithTitle("Confirm Save As")
    if confirm_window:
        confirm_window[0].activate()
        _wait()
        pyautogui.press('y')
        _wait()
    
    # Wait for dialog to close
    end_time = time.time() + 2
    while time.time() < end_time:
        if not gw.getWindowsWithTitle("Save As"):
            break
        _wait()
    return True


def write_post_to_notepad(post: dict, project_path: Path):
    """Write post content to Notepad and save it."""
    _prepare_notepad_window()
    
    # Wait for any existing Save As dialogs to close
    if gw.getWindowsWithTitle("Save As"):
        end_time = time.time() + 2
        while time.time() < end_time:
            if not gw.getWindowsWithTitle("Save As"):
                break
            _wait()
    
    pyautogui.hotkey('ctrl', 'n')
    _wait()
    _prepare_notepad_window()
    
    content = f"Title: {post['title']}\n\n{post['body']}"
    _paste_content(content)
    
    filename = f"post_{post['id']}.txt"
    filepath = str(project_path / filename)
    
    if not _save_file(filepath):
        print(f"Warning: Save As dialog not found for post {post['id']}")
        return
    
    _prepare_notepad_window()
    
    # Close the tab/document
    pyautogui.hotkey('ctrl', 'w')
    _wait()
    
    # Force close any remaining windows
    active_windows = get_notepad_windows()
    if active_windows:
        for window in active_windows:
            if window.visible:
                window.activate()
                _wait()
                pyautogui.hotkey('alt', 'f4')
                _wait()
                if window.visible:
                    window.close()
                    _wait()


# API fetching
def fetch_posts() -> list[dict] | None:
    """Fetch posts from the API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API is unavailable. {e}")
        return None
