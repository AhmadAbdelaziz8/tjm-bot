"""Configuration constants and settings."""
from pathlib import Path

# Paths
TEMPLATE_DIR = Path("assets/templates")
PROJECT_PATH = Path.home() / "Desktop" / "tjm-project"

# API
API_URL = "https://jsonplaceholder.typicode.com/posts"

# Template matching
MATCHING_THRESHOLD = 0.85
FIND_WAIT_TIME = 400