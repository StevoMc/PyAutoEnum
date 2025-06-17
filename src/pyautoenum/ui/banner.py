"""Banner and animation for PyAutoEnum."""

import curses
import random
import time


def show_banner():
    """Show the welcome banner."""
    try:
        curses.wrapper(animation_loop)
    except Exception:
        # Fall back to simple text banner if animation fails
        print(text_banner())


def text_banner():
    """Return a simple text banner."""
    return """
██████╗ ██╗   ██╗  █████╗ ██╗   ██╗████████╗ ██████╗   ███████╗███╗   ██╗██╗   ██╗███╗   ███╗
██╔══██╗╚██╗ ██╔╝ ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗  ██╔════╝████╗  ██║██║   ██║████╗ ████║
██████╔╝ ╚████╔╝  ███████║██║   ██║   ██║   ██║   ██║  █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║
██╔═══╝   ╚██╔╝   ██╔══██║██║   ██║   ██║   ██║   ██║  ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║
██║        ██║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝  ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║
╚═╝        ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝   ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝
                                                                                          
                           The prettiest Python Attack-Script                             
                                       By StevoMc                                      
    """


def animation_loop(stdscr):
    """Run the animation in a curses window."""
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    sh, sw = stdscr.getmaxyx()  # Get the height and width of the terminal window

    # Initialize the spaceship position
    spaceship = [
        "          _____",
        "      ___|_____|___",
        "    _|      |      |_",
        "   | |      |      | |",
        "   | |      |      | |",
        "   | |   |  |   |  | |",
        " V | |   O  |   O  | | V",
        " | |_|___|__|___|__|_| |",
        " | |   ./\\    / \\.  | |",
        "_|_|   |  |    |  |  |_|_",
        " \\ |   |__|    |__|  |  /",
        "  \\    . |_____|_.    /",
        "   \\______|    |______/",
        "    \\|   |.|  |.|   |/",
        "     |    _|  |_    |",
        "     |   |______|   |",
        "     |    /  .  \\   |",
        "     |   |   |   |  |",
        "    /|___|___|___|__|\\",
        "    |/***\\|    |/***\\|",
        "    / *** \\    / *** \\",
        "   |*** ***|  |*** ***|",
        "    *** ***    *** *** ",
        "    * *** *    * *** * ",
    ]

    spaceship_height = len(spaceship)
    spaceship_width = len(spaceship[0])
    spaceship_x = int(sw / 2) - spaceship_width
    spaceship_y = sh

    # Create a list of stars with random positions
    stars = [(random.randint(1, sh - 1), random.randint(1, sw - 1)) for _ in range(50)]

    # Create a list of meteors with random positions, speeds, and directions
    meteors = []
    for _ in range(25):
        meteor_x = random.randint(1, sw - 1)
        meteor_y = random.randint(1, sh - 1)
        meteor_speed_x = random.choice([-1, 1])
        meteor_speed_y = random.choice([-1, 1])
        meteors.append((meteor_x, meteor_y, meteor_speed_x, meteor_speed_y))

    # Static ASCII art text for "PyAutoEnum"
    pyautoenum_text = [
        "██████╗ ██╗   ██╗  █████╗ ██╗   ██╗████████╗ ██████╗   ███████╗███╗   ██╗██╗   ██╗███╗   ███╗",
        "██╔══██╗╚██╗ ██╔╝ ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗  ██╔════╝████╗  ██║██║   ██║████╗ ████║",
        "██████╔╝ ╚████╔╝  ███████║██║   ██║   ██║   ██║   ██║  █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║",
        "██╔═══╝   ╚██╔╝   ██╔══██║██║   ██║   ██║   ██║   ██║  ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║",
        "██║        ██║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝  ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║",
        "╚═╝        ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝   ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝",
        "                                                                                          ",
        "                           The prettiest Python Attack-Script                             ",
        "                                       By StevoMc                                      ",
    ]

    text_height = len(pyautoenum_text)
    text_width = len(pyautoenum_text[0])
    text_x = sw // 2 - text_width // 2
    text_y = sh // 6 - text_height // 2

    # Main animation loop
    while spaceship_y > 0 - spaceship_height:
        try:
            # Clear screen
            stdscr.clear()

            # Draw stars
            for y, x in stars:
                if 0 <= y < sh and 0 <= x < sw:
                    stdscr.addch(y, x, "*")

            # Draw meteors and update positions
            new_meteors = []
            for x, y, dx, dy in meteors:
                new_x = x + dx
                new_y = y + dy

                # Bounce off screen edges
                if new_x < 0 or new_x >= sw:
                    dx = -dx
                    new_x = x + dx

                if new_y < 0 or new_y >= sh:
                    dy = -dy
                    new_y = y + dy

                if 0 <= new_y < sh and 0 <= new_x < sw:
                    stdscr.addch(new_y, new_x, "+")
                    new_meteors.append((new_x, new_y, dx, dy))
                else:
                    # Replace meteors that go off screen
                    meteor_x = random.randint(1, sw - 1)
                    meteor_y = random.randint(1, sh - 1)
                    meteor_dx = random.choice([-1, 1])
                    meteor_dy = random.choice([-1, 1])
                    new_meteors.append((meteor_x, meteor_y, meteor_dx, meteor_dy))

            meteors = new_meteors

            # Draw ASCII art text
            for i, line in enumerate(pyautoenum_text):
                if text_y + i >= 0 and text_y + i < sh and text_x >= 0 and text_x + len(line) <= sw:
                    stdscr.addstr(text_y + i, text_x, line)

            # Draw the spaceship
            for i, line in enumerate(spaceship):
                if spaceship_y + i >= 0 and spaceship_y + i < sh:
                    for j, char in enumerate(line):
                        if char != " " and spaceship_x + j >= 0 and spaceship_x + j < sw:
                            stdscr.addch(spaceship_y + i, spaceship_x + j, char)

            # Update spaceship position
            spaceship_y -= 1

            # Refresh screen and wait
            stdscr.refresh()
            time.sleep(0.1)

            # Check for key press to skip animation
            key = stdscr.getch()
            if key != -1:
                break
        except curses.error:
            # Handle errors and continue
            pass

    # Wait for a key press at the end
    stdscr.nodelay(0)
    stdscr.getch()
    
    # Ensure cursor is visible when returning
    try:
        curses.curs_set(1)
    except curses.error:
        pass
