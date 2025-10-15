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
from app.menus.loop import bonus_kuota_malam, bebas_puas_tiktok_yt, kuota_pelanggan_baru, bonus_kuota_utama_15gb, bonus_kuota_utama_45gb
from app.util import get_api_key, save_api_key
from colorama import Fore, Style, init

WIDTH = 55

def show_main_menu():
    clear_screen()
    print("Menu Utama".center(WIDTH))
    print("=" * WIDTH)
    print("Menu:")
    print("0. Original Menu")
    print("1. Login/Ganti akun")
    print("2. [Test] Purchase all packages in family code")
    print("-------------------------------------------------------")
    print("List Bot Auto Looping:")
    print(f"3. Tiktok 1GB dari Xtra Combo Mini {Fore.GREEN}(Good){Style.RESET_ALL}")
    print(f"4. Youtube 1GB dari Xtra Combo Mini {Fore.GREEN}(Good){Style.RESET_ALL}")
    print(f"5. Whatsapp 1GB dari 1GB dari Xtra Combo Mini {Fore.GREEN}(Good){Style.RESET_ALL}")
    print(f"6. Bonus Kuota Utama 15GB {Fore.RED}(Coid){Style.RESET_ALL}")
    print(f"7. Bonus Kuota Utama 45GB {Fore.RED}(Coid){Style.RESET_ALL}")
    print("8. Mode Custom (family code dan nomer order)")
    print("-------------------------------------------------------")
    print("9. Bookmark Family Code")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")

def main():
    init()
    AuthInstance.api_key = get_api_key()
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            show_main_menu()

            choice = input("Pilih menu: ")
            if choice == "0":
                os.system(f'"{sys.executable}" master.py')
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
            elif choice == "3":
                bonus_kuota_malam()
            elif choice == "4":
                bebas_puas_tiktok_yt()
            elif choice == "5":
                kuota_pelanggan_baru()
            elif choice == "6":
                bonus_kuota_utama_15gb()
            elif choice == "7":
                bonus_kuota_utama_45gb()
            elif choice == "8":
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
                            break # break inner loop
                    else:
                        # This block executes if the inner loop completes without a break
                        continue
                    break # break outer loop
            elif choice == "9":
                show_family_bookmark_menu()
            elif choice == "99":
                print("Exiting the application.")
                sys.exit(0)
            else:
                print("Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
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