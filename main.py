import requests
import time
import pyautogui
from pathlib import Path
from botcity.core import DesktopBot
from automation import (
    register_templates, launch_notepad, close_existing_notepad,
    close_notepad_fully, write_post_to_notepad, TEMPLATE_DIR
)

API_URL = "https://jsonplaceholder.typicode.com/posts"
PROJECT_PATH = Path.home() / "Desktop" / "tjm-project"


def fetch_posts():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API is unavailable. {e}")
        return None


def setup_environment():
    print(f"Ensuring project directory exists: {PROJECT_PATH}")
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)


def process_post(post, bot, template_labels):
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
