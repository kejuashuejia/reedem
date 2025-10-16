from dotenv import load_dotenv

load_dotenv() 

import sys
import os
from datetime import datetime
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.menus.account import show_account_menu
from app.menus.purchase import purchase_by_family, purchase_loop
from app.menus.family_bookmark import show_family_bookmark_menu
import requests
from app.menus.loop import start_loop
from app.menus.bot import run_edubot
from app.util import get_api_key, save_api_key, PACKAGES_URL
from colorama import Fore, Style, init
import textwrap

WIDTH = 55

RUNNING_TEXT_URL = "https://pastebin.com/raw/2UfYSacE"


def fetch_running_text():
    """Fetch running text JSON from configured URL.

    Returns the parsed JSON (dict) or None on error.
    """
    try:
        resp = requests.get(RUNNING_TEXT_URL, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def render_marquee_frame(text, width):
    # Simple first frame: right-aligned (start from right)
    if not text:
        return ' ' * width
    padded = (' ' * width) + text
    return padded[:width]


def animate_marquee(text, width, stop_event, lines_up, color_code=''):
    """Animate marquee moving right-to-left.

    The function moves the cursor up `lines_up` lines from the current cursor
    position, writes the marquee line, then restores the cursor so the input
    prompt isn't disturbed.
    """
    # Build the scrolling buffer: spaces to start, the text, and some spaces to separate loops
    sep = ' ' * 8
    buffer = (' ' * width) + text + sep
    total = len(buffer)
    try:
        idx = 0
        while not stop_event.is_set():
            if idx >= total:
                idx = 0
            frame = buffer[idx: idx + width]
            if len(frame) < width:
                frame = frame.ljust(width)

            # Save cursor, move up, write, restore cursor
            # Move up `lines_up` lines then to column 1
            seq = f"\x1b[s\x1b[{lines_up}A{color_code}{frame}{Style.RESET_ALL}\x1b[u"
            print(seq, end='', flush=True)

            idx += 1
            stop_event.wait(0.08)
    except Exception:
        # Fail silently; animation is non-critical
        return


def input_with_marquee(prompt, running_text, width, lines_after_marquee):
    """Display input prompt while animating marquee in background.

    Returns the user input string.
    """
    if not running_text:
        return input(prompt)

    rt = running_text.get('running_text') or running_text
    text = rt.get('text', '')
    color = rt.get('color', '').upper()
    color_code = getattr(Fore, color, '')

    stop_event = __import__('threading').Event()
    t = __import__('threading').Thread(target=animate_marquee, args=(text, width, stop_event, lines_after_marquee, color_code))
    t.daemon = True
    t.start()
    try:
        return input(prompt)
    finally:
        stop_event.set()
        t.join(timeout=0.2)

def fetch_packages():
    try:
        response = requests.get(PACKAGES_URL, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("packages", [])
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengambil daftar paket: {e}")
        return []
    except ValueError:  # Catches JSON decoding errors
        print(f"Gagal mem-parsing data paket dari URL. Pastikan URL berisi JSON yang valid.")
        return []

def show_main_menu(packages, active_user):
    # placeholder for compatibility if running_text not provided
    show_main_menu_inner(packages, active_user, None)
    return


def show_main_menu_inner(packages, active_user, running_text):
    clear_screen()
    print("Menu Utama".center(WIDTH))
    print("=" * WIDTH)
    # Render running text directly under the header, separated by a spacer line
    if running_text and isinstance(running_text, dict):
        rt = running_text.get('running_text') or running_text
        text = rt.get('text', '')
        color = rt.get('color', '').upper()
        color_code = getattr(Fore, color, '')
        # Spacer line made of spaces to visually separate header and marquee
        spacer = ' ' * WIDTH
        print(spacer)
        # Print initial marquee line (will be updated by animator)
        marquee_line = render_marquee_frame(text, WIDTH)
        print(f"{color_code}{marquee_line}{Style.RESET_ALL}")
        print(spacer)
    if active_user and 'number' in active_user:
        print(f"Nomor Aktif: {Fore.YELLOW}{active_user['number']}{Style.RESET_ALL}")
        print("=" * WIDTH)
    print("Menu:")
    print("0. Original Menu")
    print("1. Login/Ganti akun")
    print("2. [Test] Purchase all packages in family code")
    print("-------------------------------------------------------")
    print("List Bot Auto Looping:")
    if packages:
        for i, pkg in enumerate(packages, start=3):
            status = pkg.get('status', 'Coid').lower()
            if status == 'good':
                status_color = Fore.GREEN
            elif status == 'test':
                status_color = Fore.YELLOW
            else:
                status_color = Fore.RED
            
            status_text = f"{status_color}({pkg.get('status', 'N/A')}){Style.RESET_ALL}"
            prefix = f"{i}. "
            
            # The visible length of the status text
            status_len = len(f"({pkg.get('status', 'N/A')})")
            
            # Available width for the name
            name_width = WIDTH - len(prefix) - status_len - 1 # for space
            
            wrapped_name = textwrap.wrap(pkg['name'], width=name_width)
            
            # Print the first line with the status
            if wrapped_name:
                print(f"{prefix}{wrapped_name[0]} {status_text}")
                # Print subsequent lines indented
                for line in wrapped_name[1:]:
                    print(f"{' ' * len(prefix)}{line}")
            else: # Should not happen if name is not empty
                print(f"{prefix} {status_text}")
    else:
        print(f"{Fore.YELLOW}Sorry Guys, belum nemu paket baru. Sabar ya!{Style.RESET_ALL}")
    
    custom_mode_number = len(packages) + 3 if packages else 3
    print(f"{custom_mode_number}. Mode Custom (family code dan nomer order)")
    print("-------------------------------------------------------")
    # Compute lines after the marquee so animator can move cursor up correctly.
    # We printed spacer (1), marquee (1), spacer (1) right after the header.
    # Now count how many lines will be printed until the input prompt.
    lines_after_marquee = 0

    # Lines from the rest of menu that appear after the marquee spacer
    # Fixed lines after marquee: the separator line, 'Menu:' label and base options
    fixed_lines = 8
    lines_after_marquee += fixed_lines

    # Approximate package lines: each package shown as 1-2 lines; use 2 to be safe
    if packages:
        lines_after_marquee += len(packages) * 2
    else:
        lines_after_marquee += 1

    # plus the header and top separators we printed earlier (so animator moves up to marquee)
    # we want to move up from prompt to the marquee's printed line: include the spacer and marquee and spacer
    lines_after_marquee += 3

    return lines_after_marquee
    bookmark_menu_number = custom_mode_number + 1
    edubot_menu_number = custom_mode_number + 2
    print(f"{bookmark_menu_number}. Bookmark Family Code")
    print(f"{edubot_menu_number}. Pantau Sisa Kuota")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")


def main():
    init()
    AuthInstance.api_key = get_api_key()
    
    packages = fetch_packages()
    running_text = None
    try:
        running_text = fetch_running_text()
    except Exception:
        # Non-fatal: keep running without running text
        running_text = None

    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is not None:
            # show menu with running text and get how many lines are after marquee
            lines_after_marquee = show_main_menu_inner(packages, active_user, running_text)

            # Prompt while animating marquee if available
            choice = input_with_marquee("Pilih menu: ", running_text, WIDTH, lines_after_marquee)
            
            # Static choices
            if choice == "0":
                os.system(f'"{sys.executable}" master.py')
                continue
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("No user selected or failed to load user.")
                continue
            elif choice == "2":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
                purchase_by_family(family_code, use_decoy, pause_on_success)
                continue
            elif choice == "99":
                print("Exiting the application.")
                sys.exit(0)

            # Dynamic choices
            try:
                choice_int = int(choice)
                
                # Package choices
                if 3 <= choice_int < 3 + len(packages):
                    selected_package = packages[choice_int - 3]
                    start_loop(selected_package)
                    continue

                custom_mode_number = len(packages) + 3
                bookmark_menu_number = custom_mode_number + 1
                edubot_menu_number = custom_mode_number + 2

                if choice_int == custom_mode_number:
                    family_code = input("Enter family code: ")
                    orders_input = input("Enter single/multiple order number(s) [ex: 1 or 1,2,3:] ")
                    orders = [int(o.strip()) for o in orders_input.split(',')]
                    delay = int(input("Enter delay in seconds: "))
                    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
                    while True:
                        for order in orders:
                            print(f"Processing order {order}...")
                            if not purchase_loop(
                                family_code=family_code,
                                order=order,
                                use_decoy=True,
                                delay=delay,
                                pause_on_success=pause_on_success
                            ):
                                print(f"Purchase for order {order} failed. Stopping loop.")
                                break 
                        else:
                            continue
                        break
                elif choice_int == bookmark_menu_number:
                    show_family_bookmark_menu()
                elif choice_int == edubot_menu_number:
                    run_edubot()
                else:
                    print("Invalid choice. Please try again.")
                    pause()

            except ValueError:
                print("Invalid choice. Please try again.")
                pause()
        else:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting the application.")
    # except Exception as e:
    #     print(f"An error occurred: {e}")