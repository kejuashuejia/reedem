from app.colors import bcolors

from app.service.git import check_for_updates

import sys, json, time, os, requests
from collections import Counter
from datetime import datetime
from app.menus.util import clear_screen, pause, format_quota_byte
from app.client.engsel import (
    get_balance,
    get_tiering_info,
)
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details, get_my_packages_quota
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redeemables import show_redeemables_menu
from app.client.registration import dukcapil
from app.menus.util import format_quota_byte

WIDTH = 55

def check_internet_connection():
    """
    Checks for internet connection by sending a request to http://www.google.com/generate_204.
    Returns True if connection is available, False otherwise.
    """
    print(f"\n{bcolors.OKCYAN}Checking internet connection...{bcolors.ENDC}")
    try:
        response = requests.get("http://www.google.com/generate_204", timeout=10)
        if response.status_code == 204:
            print(f"{bcolors.OKGREEN}Internet connection is available.{bcolors.ENDC}")
            return True
        else:
            print(f"{bcolors.FAIL}Internet connection check failed with status code: {response.status_code}{bcolors.ENDC}")
            return False
    except requests.exceptions.RequestException:
        print(f"{bcolors.FAIL}No internet connection.{bcolors.ENDC}")
        return False

def show_main_menu(profile, total_remaining_quota, total_quota, is_unlimited):
    clear_screen()
    print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    print(f"{bcolors.OKBLUE}Nomor: {profile['number']} | Type: {profile['subscription_type']}{bcolors.ENDC}".center(WIDTH + len(bcolors.OKBLUE) + len(bcolors.ENDC)))
    print(f"{bcolors.OKBLUE}Pulsa: Rp {profile['balance']} | Aktif sampai: {expired_at_dt}{bcolors.ENDC}".center(WIDTH + len(bcolors.OKBLUE) + len(bcolors.ENDC)))
    print(f"{bcolors.OKGREEN}{profile['point_info']}{bcolors.ENDC}".center(WIDTH + len(bcolors.OKGREEN) + len(bcolors.ENDC)))
    
    remaining_str = format_quota_byte(total_remaining_quota)
    total_str = format_quota_byte(total_quota)
    unlimited_str = " (unlimited)" if is_unlimited else ""
    quota_info = f"Kuota : {remaining_str} / {total_str}{unlimited_str}"
    colored_quota_info = f"{bcolors.OKGREEN}{quota_info}{bcolors.ENDC}"
    print(colored_quota_info.center(WIDTH + len(bcolors.OKGREEN) + len(bcolors.ENDC)))

    if is_unlimited:
        bar_width = 40
        bar = bcolors.OKGREEN + '█' * bar_width + bcolors.ENDC
        progress_str = f"[{bar}]"
        
        uncolored_len = 2 + bar_width
        padding = (WIDTH - uncolored_len) // 2
        print(' ' * padding + progress_str)
        
    elif total_quota > 0:
        percentage = (total_remaining_quota / total_quota) * 100
        bar_width = 40
        filled_length = int(bar_width * percentage / 100)
        
        if percentage > 50:
            bar_color = bcolors.OKGREEN
        elif percentage > 20:
            bar_color = bcolors.WARNING
        else:
            bar_color = bcolors.FAIL

        bar = bar_color + '█' * filled_length + bcolors.ENDC + '─' * (bar_width - filled_length)
        
        percentage_str = f" {percentage:.2f}%"
        
        uncolored_len = 2 + bar_width + len(percentage_str)
        padding = (WIDTH - uncolored_len) // 2
        
        print(' ' * padding + f"[{bar}]" + percentage_str)

    print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
    print(f"{bcolors.BOLD}Menu:{bcolors.ENDC}")
    print("1. Login/Ganti akun")
    print("2. Lihat Paket Saya")
    print(f"3. Beli Paket {bcolors.WARNING}🔥 HOT 🔥{bcolors.ENDC}")
    print(f"4. Beli Paket {bcolors.WARNING}🔥 HOT-2 🔥{bcolors.ENDC}")
    print("5. Beli Paket Berdasarkan Option Code")
    print("6. Beli Paket Berdasarkan Family Code")
    print("7. Beli Semua Paket di Family Code (loop)")
    print("8. Riwayat Transaksi")
    print("9. Family Plan/Akrab Organizer")
    print("10. Circle")
    print("11. Store Segments")
    print("12. Store Family List")
    print("13. Store Packages")
    print("14. Redemables")
    print(f"{bcolors.OKCYAN}{'-' * WIDTH}{bcolors.ENDC}")
    print(f"{bcolors.BOLD}Bebas Puas:{bcolors.ENDC}")
    print("15. Auto Reedem")
    print("16. Custom loops Redeem BP")
    print("17. Redeem by Target Quota")
    print(f"{bcolors.OKCYAN}{'-' * WIDTH}{bcolors.ENDC}")
    print("R. Register")
    print("N. Notifikasi")
    print("V. Validate msisdn")
    print("00. Bookmark Paket")
    print(f"99. {bcolors.FAIL}Tutup aplikasi{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}{'-' * WIDTH}{bcolors.ENDC}")

show_menu = True
def main():
    
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            balance_remaining = balance.get("remaining")
            balance_expired_at = balance.get("expired_at")
            
            point_info = "Points: N/A | Tier: N/A"
            
            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            total_remaining_quota, total_quota, is_unlimited = get_my_packages_quota()
            show_main_menu(profile, total_remaining_quota, total_quota, is_unlimited)

            choice = input(f"{bcolors.BOLD}Pilih menu: {bcolors.ENDC}")
            # Testing shortcuts
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print(f"{bcolors.FAIL}No user selected or failed to load user.{bcolors.ENDC}")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("Enter option code (or '99' to cancel): ")
                if option_code == "99":
                    continue
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice == "6":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue

                start_from_option = input("Start purchasing from option number (default 1): ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1

                use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("Pause on each successful purchase? (y/n): ").lower() == 'y'
                delay_seconds = input("Delay seconds between purchases (0 for no delay): ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                input_11 = input("Is enterprise store? (y/n): ").lower()
                is_enterprise = input_11 == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                input_12_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_12_1 == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "13":
                input_13_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_13_1 == 'y'
                
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "14":
                input_14_1 = input("Is enterprise? (y/n): ").lower()
                is_enterprise = input_14_1 == 'y'
                
                show_redeemables_menu(is_enterprise)
            elif choice == "15":
                try:
                    is_enterprise = False
                    while True:
                        print("Starting auto-redeem bot...")
                        
                        # Purchase 1
                        print("Purchasing item 1...")
                        choices1 = ['A1', '3', 'b']
                        show_redeemables_menu(is_enterprise=is_enterprise, choices=choices1, is_bot_mode=True)
                        time.sleep(3)
                        
                        # Purchase 2
                        print("Purchasing item 2...")
                        choices2 = ['A1', '2', 'b']
                        show_redeemables_menu(is_enterprise=is_enterprise, choices=choices2, is_bot_mode=True)
                        time.sleep(3)

                        # Purchase 3
                        print("Purchasing item 3...")
                        choices3 = ['A1', '1', 'b']
                        show_redeemables_menu(is_enterprise=is_enterprise, choices=choices3, is_bot_mode=True)
                        
                        # Countdown
                        print("Starting 11-minute countdown...")
                        for i in range(10, 0, -1):
                            sys.stdout.write(f"\rTime remaining: {i} seconds")
                            sys.stdout.flush()
                            time.sleep(1)
                        print("\nCountdown finished.")

                        # Check internet connection
                        while not check_internet_connection():
                            print("Retrying in 6 seconds...")
                            time.sleep(6)

                        # Renew token
                        print("Renewing token...")
                        AuthInstance.renew_active_user_token()
                except KeyboardInterrupt:
                    print(f"\n{bcolors.WARNING}Bot stopped by user.{bcolors.ENDC}")
                    pause()
            elif choice == "16":
                try:
                    with open('bebaspuas.json', 'r') as f:
                        redeem_timestamps = json.load(f)

                    quota_map = {
                        "199": {"name": "Kuota Malam", "size": 3.75},
                        "200": {"name": "Kuota Youtube & Tiktok", "size": 3.13},
                        "201": {"name": "Kuota Utama", "size": 1.25}
                    }

                    order_numbers_str = input("Enter custom order numbers (or leave empty for all):\n"
                                              "- 199: Kuota Malam 3.75GB\n"
                                              "- 200: Kuota Youtube & Tiktok 3.13GB\n"
                                              "- 201: Kuota Utama 1.25GB\n"
                                              "Your choice: ")
                    
                    if not order_numbers_str.strip():
                        order_numbers = list(quota_map.keys())
                        print("No input detected, selecting all order numbers.")
                    else:
                        order_numbers = [num.strip() for num in order_numbers_str.split(',')]

                    loop_count_str = input("Enter the number of loops (leave empty for infinite): ")
                    
                    import itertools
                    iterator = None
                    loop_display = ""

                    if not loop_count_str:
                        iterator = itertools.count()
                        loop_display = "∞"
                    else:
                        try:
                            loop_count = int(loop_count_str)
                            iterator = range(loop_count)
                            loop_display = str(loop_count)
                        except ValueError:
                            print("Invalid number, defaulting to 1 loop.")
                            iterator = range(1)
                            loop_display = "1"
                    
                    famcode = "7e5eb288-58a0-44d0-8002-b66bad210f21|VPROG"
                    
                    first_session_dt = datetime.now()
                    
                    BOLD = '\033[1m'
                    RESET = '\033[0m'
                    
                    successful_redemptions = Counter()

                    for i in iterator:
                        print(f"Loop {i + 1}/{loop_display}")
                        print("Starting claim bonus bot...")
                        
                        for order_number in order_numbers:
                            print(f"Processing order number: {order_number}")

                            last_redeem_time_str = redeem_timestamps.get(order_number)
                            if last_redeem_time_str:
                                last_redeem_time = datetime.fromisoformat(last_redeem_time_str)
                                time_since_redeem = (datetime.now() - last_redeem_time).total_seconds()
                                if time_since_redeem < 600:
                                    wait_time = 600 - time_since_redeem
                                    print(f"Waiting for {int(wait_time)} seconds before next redeem for order {order_number}")
                                    for j in range(int(wait_time), 0, -1):
                                        minutes, seconds = divmod(j, 60)
                                        time_str = f"{minutes:02d}:{seconds:02d}"
                                        label = "Time remaining: "
                                        padding = " " * ((WIDTH - len(label) - len(time_str)) // 2)
                                        sys.stdout.write(f"\r{padding}{label}{BOLD}{time_str}{RESET}")
                                        sys.stdout.flush()
                                        time.sleep(1)
                                    print()

                            choices = [order_number, 'b']
                            result = get_packages_by_family(
                                family_code=famcode,
                                choices=choices,
                                is_bot_mode=True
                            )

                            if result and isinstance(result, dict) and result.get('status') == 'SUCCESS':
                                successful_redemptions[order_number] += 1
                                print(f"Successfully processed order number: {order_number}")
                                redeem_timestamps[order_number] = datetime.now().isoformat()
                                with open('bebaspuas.json', 'w') as f:
                                    json.dump(redeem_timestamps, f, indent=4)
                            else:
                                print(f"Failed to process order number: {order_number}")

                            print(f"Finished processing order number: {order_number}. Waiting 3 seconds.")
                            time.sleep(1)

                        is_last_loop = (isinstance(iterator, range) and i == len(iterator) - 1)

                        # --- Summary ---
                        print("=" * WIDTH)
                        
                        def print_centered_bold(label, value, end=""):
                            padding = " " * ((WIDTH - len(label) - len(str(value)) - len(end)) // 2)
                            print(f"{padding}{label}{BOLD}{value}{RESET}{end}")

                        # Loop finished line
                        print_centered_bold("Loop ", f"{i + 1}/{loop_display}", " finished.")
                        
                        print("Estimated SUCCESSFUL redeemed quota:".center(WIDTH))
                        for order_num, count in sorted(successful_redemptions.items()):
                            if order_num in quota_map:
                                info = quota_map[order_num]
                                name = info["name"]
                                accumulated_quota = info["size"] * count
                                print_centered_bold(f"- {name}: ", f"{accumulated_quota:.2f} GB")

                        last_session_dt = datetime.now()
                        duration = last_session_dt - first_session_dt
                        
                        first_session_str = first_session_dt.strftime("%H:%M:%S")
                        last_session_str = last_session_dt.strftime("%H:%M:%S")
                        duration_str = str(duration).split('.')[0]

                        print_centered_bold("first session : ", first_session_str)
                        print_centered_bold("last session : ", last_session_str)
                        print_centered_bold("session duration: ", duration_str)

                        if not is_last_loop:
                            # Countdown for non-last loops
                            print("=" * WIDTH)
                            for j in range(600, 0, -1):
                                minutes, seconds = divmod(j, 60)
                                time_str = f"{minutes:02d}:{seconds:02d}"
                                label = "Time remaining: "
                                padding = " " * ((WIDTH - len(label) - len(time_str)) // 2)
                                sys.stdout.write(f"\r{padding}{label}{BOLD}{time_str}{RESET}")
                                sys.stdout.flush()
                                time.sleep(1)
                            print()
                            print("=" * WIDTH)
                            print("Countdown finished.".center(WIDTH))
                            print("=" * WIDTH)

                            # Check internet connection
                            while not check_internet_connection():
                                print("Retrying in 6 seconds...")
                                time.sleep(6)

                            # Renew token
                            print("Renewing token...")
                            AuthInstance.renew_active_user_token()
                        else:
                            # Actions for the very last loop
                            print("=" * WIDTH)
                            print("All loops completed.".center(WIDTH))
                            pause()
                except KeyboardInterrupt:
                    print(f"\n{bcolors.WARNING}Bot stopped by user.{bcolors.ENDC}")
                    pause()
            elif choice == "17":
                try:
                    with open('bebaspuas.json', 'r') as f:
                        redeem_timestamps = json.load(f)
                        
                    quota_map = {
                        "199": {"name": "Kuota Malam", "size": 3.75},
                        "200": {"name": "Kuota Youtube & Tiktok", "size": 3.13},
                        "201": {"name": "Kuota Utama", "size": 1.25}
                    }

                    order_numbers_str = input("Enter custom order numbers (or leave empty for all):\n"
                                              "- 199: Kuota Malam 3.75GB\n"
                                              "- 200: Kuota Youtube & Tiktok 3.13GB\n"
                                              "- 201: Kuota Utama 1.25GB\n"
                                              "Your choice: ")
                    
                    if not order_numbers_str.strip():
                        order_numbers = list(quota_map.keys())
                        print("No input detected, selecting all order numbers.")
                    else:
                        order_numbers = [num.strip() for num in order_numbers_str.split(',')]

                    # Get target quotas from user
                    target_quotas = {}
                    for order_num in sorted(list(set(order_numbers))):
                        if order_num in quota_map:
                            name = quota_map[order_num]["name"]
                            while True:
                                try:
                                    target_gb_str = input(f"Enter target quota in GB for {name} ({order_num}): ")
                                    target_quotas[order_num] = float(target_gb_str)
                                    break
                                except ValueError:
                                    print("Invalid input. Please enter a number.")
                    
                    famcode = "7e5eb288-58a0-44d0-8002-b66bad210f21|VPROG"
                    first_session_dt = datetime.now()
                    BOLD = '\033[1m'
                    RESET = '\033[0m'
                    successful_redemptions = Counter()
                    
                    loop_counter = 0
                    while True:
                        loop_counter += 1
                        print(f"Loop {loop_counter}")
                        print("Starting target quota bot...")
                        
                        all_targets_met = True
                        
                        for order_number in order_numbers:
                            current_quota = successful_redemptions.get(order_number, 0) * quota_map.get(order_number, {}).get("size", 0)
                            target_quota = target_quotas.get(order_number, 0)

                            if current_quota < target_quota:
                                all_targets_met = False # At least one target is not met
                                print(f"Processing order number: {order_number} (Target: {target_quota} GB)")

                                last_redeem_time_str = redeem_timestamps.get(order_number)
                                if last_redeem_time_str:
                                    last_redeem_time = datetime.fromisoformat(last_redeem_time_str)
                                    time_since_redeem = (datetime.now() - last_redeem_time).total_seconds()
                                    if time_since_redeem < 600:
                                        wait_time = 600 - time_since_redeem
                                        print(f"Waiting for {int(wait_time)} seconds before next redeem for order {order_number}")
                                        for j in range(int(wait_time), 0, -1):
                                            minutes, seconds = divmod(j, 60)
                                            time_str = f"{minutes:02d}:{seconds:02d}"
                                            label = "Time remaining: "
                                            padding = " " * ((WIDTH - len(label) - len(time_str)) // 2)
                                            sys.stdout.write(f"\r{padding}{label}{BOLD}{time_str}{RESET}")
                                            sys.stdout.flush()
                                            time.sleep(1)
                                        print()

                                choices = [order_number, 'b']
                                result = get_packages_by_family(
                                    family_code=famcode,
                                    choices=choices,
                                    is_bot_mode=True
                                )

                                if result and isinstance(result, dict) and result.get('status') == 'SUCCESS':
                                    successful_redemptions[order_number] += 1
                                    print(f"Successfully processed order number: {order_number}")
                                    redeem_timestamps[order_number] = datetime.now().isoformat()
                                    with open('bebaspuas.json', 'w') as f:
                                        json.dump(redeem_timestamps, f, indent=4)
                                else:
                                    print(f"Failed to process order number: {order_number}")
                                
                                print(f"Finished processing order number: {order_number}. Waiting 3 seconds.")
                                time.sleep(1)

                        # --- Summary ---
                        print("=" * WIDTH)
                        
                        def print_centered_bold(label, value, end=""):
                            padding = " " * ((WIDTH - len(label) - len(str(value)) - len(end)) // 2)
                            print(f"{padding}{label}{BOLD}{value}{RESET}{end}")

                        print_centered_bold("Loop ", f"{loop_counter}", " finished.")
                        
                        print("Redeemed Quota / Target:".center(WIDTH))
                        for order_num in sorted(target_quotas.keys()):
                            if order_num in quota_map:
                                info = quota_map[order_num]
                                name = info["name"]
                                current_quota = successful_redemptions.get(order_num, 0) * info["size"]
                                target_quota = target_quotas[order_num]
                                progress_str = f"{current_quota:.2f} / {target_quota:.2f} GB"
                                print_centered_bold(f"- {name}: ", progress_str)

                        last_session_dt = datetime.now()
                        duration = last_session_dt - first_session_dt
                        
                        first_session_str = first_session_dt.strftime("%H:%M:%S")
                        last_session_str = last_session_dt.strftime("%H:%M:%S")
                        duration_str = str(duration).split('.')[0]

                        print_centered_bold("first session : ", first_session_str)
                        print_centered_bold("last session : ", last_session_str)
                        print_centered_bold("session duration: ", duration_str)

                        if all_targets_met:
                            print("=" * WIDTH)
                            print("All targets met.".center(WIDTH))
                            pause()
                            break
                        else:
                            # Countdown for non-last loops
                            print("=" * WIDTH)
                            for j in range(600, 0, -1):
                                minutes, seconds = divmod(j, 60)
                                time_str = f"{minutes:02d}:{seconds:02d}"
                                label = "Time remaining: "
                                padding = " " * ((WIDTH - len(label) - len(time_str)) // 2)
                                sys.stdout.write(f"\r{padding}{label}{BOLD}{time_str}{RESET}")
                                sys.stdout.flush()
                                time.sleep(1)
                            print()
                            print("=" * WIDTH)
                            print("Countdown finished.".center(WIDTH))
                            print("=" * WIDTH)

                            # Check internet connection
                            while not check_internet_connection():
                                print("Retrying in 6 seconds...")
                                time.sleep(6)

                            # Renew token
                            print("Renewing token...")
                            AuthInstance.renew_active_user_token()

                except KeyboardInterrupt:
                    print(f"\n{bcolors.WARNING}Bot stopped by user.{bcolors.ENDC}")
                    pause()
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                print(f"{bcolors.FAIL}Exiting the application.{bcolors.ENDC}")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("Enter msisdn (628xxxx): ")
                nik = input("Enter NIK: ")
                kk = input("Enter KK: ")
                
                res = dukcapil(
                    AuthInstance.api_key,
                    msisdn,
                    kk,
                    nik,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "v":
                msisdn = input("Enter the msisdn to validate (628xxxx): ")
                res = validate_msisdn(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    msisdn,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                print(f"{bcolors.FAIL}Invalid choice. Please try again.{bcolors.ENDC}")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print(f"{bcolors.FAIL}No user selected or failed to load user.{bcolors.ENDC}")

if __name__ == "__main__":
    try:
        print(f"{bcolors.OKCYAN}Checking for updates...{bcolors.ENDC}")
        need_update = check_for_updates()
        if need_update:
            pause()

        main()
    except KeyboardInterrupt:
        print(f"\n{bcolors.FAIL}Exiting the application.{bcolors.ENDC}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")
