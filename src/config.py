"""Configuration constants and settings."""
from pathlib import Path

# Paths
TEMPLATE_DIR = Path("assets/templates")
PROJECT_PATH = Path.home() / "Desktop" / "tjm-project"

# API
API_URL = "https://jsonplaceholder.typicode.com/posts"

# Template matching
MATCHING_THRESHOLD = 0.85
FIND_WAIT_TIME = 150 # milliseconds

# Spacing (time delays in seconds)
SPACING = 0.2
INITIAL_DELAY = 0.5  # Delay after minimizing windows
STARTUP_DELAY = 3.0  # Delay before starting to process posts