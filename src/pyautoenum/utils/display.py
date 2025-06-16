"""Display utility functions for PyAutoEnum."""

import shutil
from typing import Any


def truncate_value(value: Any, width: int) -> str:
    """
    Truncate a string to fit within a given width.
    
    Args:
        value: String to truncate
        width: Maximum width
        
    Returns:
        Truncated string with ellipsis if needed
    """
    value_str = str(value)
    if len(value_str) > width:
        return value_str[:width-3] + "..."
    return value_str


def get_console_width() -> int:
    """
    Get the width of the console.
    
    Returns:
        Console width or default value if not available
    """
    try:
        return shutil.get_terminal_size().columns
    except AttributeError:
        return 80  # Default fallback width
