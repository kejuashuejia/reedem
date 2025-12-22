from app.menus.util import clear_screen
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
from app.colors import bcolors

WIDTH = 55

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        print(f"{bcolors.OKCYAN}Fetching notifications...{bcolors.ENDC}")
        
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        notifications_res = dashboard_segments(api_key, tokens)
        if not notifications_res:
            print(f"{bcolors.FAIL}No notifications found.{bcolors.ENDC}")
            return
        
        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            print("No notifications available.")
            return
        
        print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
        print(f"{bcolors.BOLD}Notifications:{bcolors.ENDC}")
        print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
        unread_count = 0
        for idx, notification in enumerate(notifications):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time = notification.get("timestamp", "")
            
            status = ""
            if is_read:
                status = f"{bcolors.OKGREEN}READ{bcolors.ENDC}"
            else:
                status = f"{bcolors.WARNING}UNREAD{bcolors.ENDC}"
                unread_count += 1

            print(f"{idx + 1}. [{status}] {brief_message}")
            print(f"- Time: {time}")
            print(f"- {full_message}")
            print("-" * WIDTH)
        print(f"Total notifications: {len(notifications)} | Unread: {bcolors.WARNING}{unread_count}{bcolors.ENDC}")
        print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
        print("1. Read All Unread Notifications")
        print(f"00. {bcolors.OKCYAN}Back to Main Menu{bcolors.ENDC}")
        print(f"{bcolors.HEADER}{'=' * WIDTH}{bcolors.ENDC}")
        choice = input("Enter your choice: ")
        if choice == "1":
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print(f"Mark as READ notification ID: {notification_id}")
            input("Press Enter to return to the notification menu...")
        elif choice == "00":
            in_notification_menu = False
        else:
            print(f"{bcolors.FAIL}Invalid choice. Please try again.{bcolors.ENDC}")
