import time
import pyautogui
from botcity.core import DesktopBot

from src.icon_detector import register_templates
from src.notepad import (
    close_existing_notepad,
    close_notepad_fully,
    fetch_posts,
    launch_notepad,
    write_post_to_notepad,
)
from src.config import TEMPLATE_DIR, PROJECT_PATH


def setup_environment():
    """Ensure project directory exists."""
    print(f"Ensuring project directory exists: {PROJECT_PATH}")
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)


def process_post(post: dict, bot: DesktopBot, template_labels: list[str]):
    """Process a single post: launch Notepad, write content, and close."""
    print(f"\n{'='*60}")
    print(f"Processing Post ID: {post['id']}")
    print(f"{'='*60}")
    
    close_existing_notepad()
    
    if not launch_notepad(bot, template_labels):
        print(f"Skipping post {post['id']} due to launch failure.")
        return

    try:
        write_post_to_notepad(post, PROJECT_PATH)
        
        if not close_notepad_fully():
            print(f"Warning: Notepad may not have closed completely for post {post['id']}")
        
        print(f"Successfully processed Post ID: {post['id']}")
        
    except Exception as e:
        print(f"An error occurred during post processing: {e}")


def main():
    """Main execution function."""
    # Show desktop to ensure clean state
    print("Showing desktop (Windows+D)...")
    pyautogui.hotkey('win', 'd')
    time.sleep(0.5)
    
    setup_environment()
    
    bot = DesktopBot()
    
    if not register_templates(bot, TEMPLATE_DIR):
        print("Exiting, no templates found. Check the 'assets/templates' folder.")
        return
    
    template_labels = [img_path.stem for img_path in TEMPLATE_DIR.glob("*.png")]
    if not template_labels:
        print("Exiting, no templates found. Check the 'assets/templates' folder.")
        return
    
    print(f"Registered {len(template_labels)} template(s): {', '.join(template_labels)}")

    posts = fetch_posts()
    if not posts:
        print("Exiting due to API failure.")
        return

    print("Starting automation. Please do not move the mouse.")
    time.sleep(3)

    for post in posts[:10]:
        process_post(post, bot, template_labels)


if __name__ == "__main__":
    main()
