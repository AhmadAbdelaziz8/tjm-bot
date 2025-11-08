import pyautogui
import time
import pygetwindow as gw
from pathlib import Path
import pyperclip
from botcity.core import DesktopBot

TEMPLATE_DIR = Path("assets/templates")
MATCHING_THRESHOLD = 0.80
FIND_WAIT_TIME = 1500

icon_cache = {}


def register_templates(bot, directory):
    if not directory.is_dir():
        print(f"Error: Template directory not found at {directory}")
        return False
        
    for img_path in directory.glob("*.png"):
        label = img_path.stem
        bot.add_image(label, str(img_path.resolve()))
        print(f"Registered template: {img_path.name} as '{label}'")
    
    return True


def find_icon(bot, template_labels, use_cache=True):
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


def get_icon_coordinates(label):
    template_path = TEMPLATE_DIR / f"{label}.png"
    if not template_path.exists():
        return None
    
    try:
        location = pyautogui.locateCenterOnScreen(str(template_path), confidence=MATCHING_THRESHOLD - 0.1)
    except (TypeError, ValueError):
        try:
            location = pyautogui.locateCenterOnScreen(str(template_path))
        except:
            return None
    
    if location:
        return (int(location[0]), int(location[1]))
    return None


def get_notepad_windows():
    all_windows = gw.getWindowsWithTitle("Notepad")
    notepad_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        if title == "notepad" or title.endswith(" - notepad"):
            if "cursor" not in title and "code" not in title:
                notepad_windows.append(window)
    
    return notepad_windows


def close_existing_notepad():
    active_windows = get_notepad_windows()
    if not active_windows:
        return
    
    print(f"Found {len(active_windows)} existing Notepad window(s). Closing...")
    for window in active_windows:
        if window.visible:
            title = window.title.lower()
            if "cursor" in title or "code" in title:
                continue
            window.close()
            time.sleep(0.5)
            try:
                pyautogui.press('n')
                time.sleep(0.3)
            except:
                pass
    
    time.sleep(0.5)
    
    remaining_windows = get_notepad_windows()
    if remaining_windows:
        for window in remaining_windows:
            if window.visible:
                title = window.title.lower()
                if "cursor" in title or "code" in title:
                    continue
                window.activate()
                time.sleep(0.2)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.3)
                pyautogui.press('n')
                time.sleep(0.3)
    
    print("Existing Notepad windows closed.")


def close_notepad_fully():
    print("Closing Notepad...")
    active_windows = get_notepad_windows()
    
    if not active_windows:
        print("No Notepad windows found to close.")
        return True
    
    for window in active_windows:
        if window.visible:
            try:
                title = window.title.lower()
                if "cursor" in title or "code" in title:
                    continue
                window.close()
                time.sleep(0.5)
            except:
                title = window.title.lower()
                if "cursor" not in title and "code" not in title:
                    window.activate()
                    time.sleep(0.2)
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(0.5)
    
    timeout = time.time() + 5
    while time.time() < timeout:
        remaining_windows = get_notepad_windows()
        if not remaining_windows or not any(win.visible for win in remaining_windows):
            print("Notepad successfully closed and verified.")
            time.sleep(0.5)
            return True
        time.sleep(0.2)
    
    remaining_windows = get_notepad_windows()
    if remaining_windows:
        print("Warning: Notepad still open, trying aggressive close...")
        for window in remaining_windows:
            if window.visible:
                title = window.title.lower()
                if "cursor" in title or "code" in title:
                    continue
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


def launch_notepad(bot, template_labels):
    found_label = None
    
    for attempt in range(3):
        found_label = find_icon(bot, template_labels)
        if found_label:
            break
        print(f"Icon not found (Attempt {attempt + 1}/3). Retrying...")
        time.sleep(1)
        
    if not found_label:
        print("Error: Icon not found after 3 attempts.")
        return False
        
    print(f"Double-clicking Notepad icon: '{found_label}'")
    
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
    
    if not clicked_coords:
        thresholds = [MATCHING_THRESHOLD, MATCHING_THRESHOLD - 0.1]
        for threshold in thresholds:
            if bot.find(label=found_label, matching=threshold, waiting_time=FIND_WAIT_TIME):
                coords = get_icon_coordinates(found_label)
                if coords:
                    clicked_coords = coords
                    pyautogui.doubleClick(coords[0], coords[1])
                else:
                    bot.double_click()
                break
        else:
            print("Error: Could not click on icon.")
            return False
    
    timeout = time.time() + 5
    while time.time() < timeout:
        active_windows = get_notepad_windows()
        if any(win.visible for win in active_windows):
            print("Notepad successfully launched and validated.")
            if clicked_coords and found_label:
                icon_cache[found_label] = clicked_coords
            time.sleep(1)
            return True
        time.sleep(0.2)
    
    # Edge case: Cache failed - icon might have moved
    if used_cache and found_label in icon_cache:
        print("Warning: Notepad did not launch after using cached coordinates. Invalidating cache and retrying...")
        del icon_cache[found_label]
        
        # Retry detection without cache
        found_label = find_icon(bot, template_labels, use_cache=False)
        if not found_label:
            print("Error: Icon not found after cache invalidation.")
            return False
        
        print(f"Retrying with fresh detection: '{found_label}'")
        thresholds = [MATCHING_THRESHOLD, MATCHING_THRESHOLD - 0.1]
        for threshold in thresholds:
            if bot.find(label=found_label, matching=threshold, waiting_time=FIND_WAIT_TIME):
                coords = get_icon_coordinates(found_label)
                if coords:
                    pyautogui.doubleClick(coords[0], coords[1])
                    clicked_coords = coords
                else:
                    bot.double_click()
                break
        else:
            print("Error: Could not click on icon after retry.")
            return False
        
        # Verify launch again
        timeout = time.time() + 5
        while time.time() < timeout:
            active_windows = get_notepad_windows()
            if any(win.visible for win in active_windows):
                print("Notepad successfully launched after cache invalidation.")
                if clicked_coords and found_label:
                    icon_cache[found_label] = clicked_coords
                time.sleep(1)
                return True
            time.sleep(0.2)
    
    print("Error: Notepad window not detected after launch.")
    return False


def write_post_to_notepad(post, project_path):
    active_windows = get_notepad_windows()
    if active_windows:
        window = active_windows[0]
        window.activate()
        time.sleep(0.5)
        
        center_x = window.left + window.width // 2
        center_y = window.top + window.height // 2
        pyautogui.click(center_x, center_y)
        time.sleep(0.3)
    
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
    
    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)
    
    filename = f"post_{post['id']}.txt"
    filepath = str(project_path / filename)
    pyautogui.write(filepath, interval=0.01)
    pyautogui.press('enter')
    time.sleep(0.5)
    
    confirm_window = gw.getWindowsWithTitle("Confirm Save As")
    if confirm_window:
        print("File exists. Overwriting.")
        pyautogui.press('y')
        time.sleep(0.5)

