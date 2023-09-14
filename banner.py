import curses
import time
import random

def animation_loop(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    sh, sw = stdscr.getmaxyx() # Get the height and width of the terminal window

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
        " | |   ./\\    / \.  | |",
        "_|_|   |  |    |  |  |_|_",
        " \ |   |__|    |__|  |  /",
        "  \    . |_____| .     /",
        "   \______|    |______/",
        "    \|   |.|  |.|   |/",
        "     |    _|  |_    |",
        "     |   |______|   |",
        "     |    /  .  \   |",
        "     |   |   |   |  |",
        "    /|___|___|___|__|\\",
        "    |/***\|    |/***\\|",
        "    / *** \    / *** \\",
        "   |*** ***|  |*** ***|",
        "    *** ***    *** *** ",
        "    * *** *    * *** * "
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
        meteor_x = random.randint(1,sw-1)
        meteor_y = random.randint(1,sh-1)
        meteor_speed_x = 1
        meteor_speed_y = 1
        meteors.append((meteor_y, meteor_x, meteor_speed_x, meteor_speed_y))

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
        "                                       By Seidon4210                                      "
    ]

    text_height = len(pyautoenum_text)
    text_width = len(pyautoenum_text[0])
    text_x = sw // 2 - text_width // 2
    text_y = sh // 6 - text_height // 2

    while spaceship_y > 0 - spaceship_height:
        stdscr.clear() # Clear the screen

        # Move the spaceship
        spaceship_y -= 1

        # Print the spaceship at its current position
        for i, line in enumerate(spaceship):
            try: stdscr.addstr(spaceship_y + i, spaceship_x, line)
            except: pass

        # Print the static ASCII art text for "PyAutoEnum"
        for i, line in enumerate(pyautoenum_text):
            stdscr.addstr(text_y + i, text_x, line)

        # Print stars
        for star_y, star_x in stars:
            if 0 <= star_y < sh and 0 <= star_x < sw:
                stdscr.addstr(star_y, star_x, '✮')

         # Update and print meteors
        new_pos_meteors = []
        for meteor_y, meteor_x, speed_x, speed_y in meteors:
            if 0 <= meteor_y < sh and 0 <= meteor_x < sw:
                try: stdscr.addstr(int(meteor_y), int(meteor_x), 'O')
                except: pass
                # Move the meteor according to its speed and direction
                meteor_x += meteor_speed_x
                meteor_y += meteor_speed_y
                new_pos_meteors.append((meteor_y, meteor_x, meteor_speed_x,meteor_speed_y))
        meteors = new_pos_meteors

        # Update star positions (simulate a twinkling effect)
        if random.random() < 0.1:
            stars = [(y, x) for y, x in stars if 0 <= y < sh and 0 <= x < sw and random.random() < 0.8]
            new_star = (random.randint(1, sh - 1), random.randint(1, sw - 1))
            stars.append(new_star)

        # Refresh the screen
        stdscr.refresh()

        # Add a sleep to control the animation speed
        time.sleep(0.02)
