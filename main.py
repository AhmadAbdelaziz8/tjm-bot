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
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)


def process_post(post: dict, bot: DesktopBot, template_labels: list[str]):
    """Process a single post: launch Notepad, write content, and close."""
    print(f"Processing Post ID: {post['id']}")
    
    close_existing_notepad()
    
    if not launch_notepad(bot, template_labels):
        print(f"Skipping post {post['id']} due to launch failure.")
        return

    try:
        write_post_to_notepad(post, PROJECT_PATH)
        close_notepad_fully()
    except Exception as e:
        print(f"Error processing post {post['id']}: {e}")


def main():
    """Main execution function."""
    pyautogui.hotkey('win', 'd')
    time.sleep(0.5)
    
    setup_environment()
    bot = DesktopBot()
    
    if not register_templates(bot, TEMPLATE_DIR):
        print("Error: No templates found.")
        return
    
    template_labels = [img_path.stem for img_path in TEMPLATE_DIR.glob("*.png")]
    if not template_labels:
        print("Error: No templates found.")
        return

    posts = fetch_posts()
    if not posts:
        print("Error: API failure.")
        return

    time.sleep(3)

    for post in posts[:10]:
        process_post(post, bot, template_labels)


if __name__ == "__main__":
    main()
