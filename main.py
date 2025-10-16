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
    clear_screen()
    print("=" * WIDTH)
    print("Menu Utama".center(WIDTH))
    print("=" * WIDTH)
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

    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is not None:
            show_main_menu(packages, active_user)

            choice = input("Pilih menu: ")
            
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