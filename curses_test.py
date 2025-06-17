#!/usr/bin/env python3
"""
Standalone test script to check curses functionality.
Run this script to verify that curses is working properly on your system.
"""

import curses
import os
import sys


def main(stdscr):
    # Clear screen
    stdscr.clear()
    
    # Get terminal size
    height, width = stdscr.getmaxyx()
    
    # Print terminal info
    stdscr.addstr(0, 0, f"Terminal Type: {os.environ.get('TERM', 'Not set')}")
    stdscr.addstr(1, 0, f"Terminal Size: {width}x{height}")
    stdscr.addstr(2, 0, "Color Support: " + ("Yes" if curses.has_colors() else "No"))
    
    # Check color capability
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        stdscr.addstr(4, 0, "Red Text", curses.color_pair(1))
        stdscr.addstr(5, 0, "Green Text", curses.color_pair(2))
        stdscr.addstr(6, 0, "Yellow Text", curses.color_pair(3))
    
    # Instructions
    stdscr.addstr(8, 0, "Press any key to exit...")
    
    # Refresh the screen
    stdscr.refresh()
    
    # Wait for key press
    stdscr.getch()

if __name__ == "__main__":
    print("Starting curses test...")
    try:
        curses.wrapper(main)
        print("Curses test completed successfully!")
    except Exception as e:
        print(f"Error in curses: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
