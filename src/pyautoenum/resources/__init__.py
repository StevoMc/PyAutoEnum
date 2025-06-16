"""Init file for resources package."""

import os
import shutil
from pathlib import Path

# Ensure modules.yml is available in the resources directory
if not os.path.exists(os.path.join(os.path.dirname(__file__), "modules.yml")):
    # Try to copy from project root if it exists there
    root_modules_yml = os.path.join(Path(__file__).parents[3], "modules.yml")
    if os.path.exists(root_modules_yml):
        try:
            shutil.copy2(root_modules_yml, os.path.join(os.path.dirname(__file__), "modules.yml"))
        except Exception:
            pass
