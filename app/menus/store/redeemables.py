import json
from app.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.package import show_package_details, get_packages_by_family
from app.client.engsel import get_package
from app.client.purchase.redeem import settlement_loyalty
from datetime import datetime

WIDTH = 55

def handle_loyalty_redeem(api_key, tokens, package_option_code, is_enterprise):
    """Handles the redemption of a loyalty package."""
    print("Fetching package details for loyalty redemption...")
    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print("Failed to get package details for loyalty redemption.")
        pause()
        return

    token_confirmation = package.get("token_confirmation")
    ts_to_sign = package.get("timestamp")
    price = package.get("package_option", {}).get("price")

    if not all([token_confirmation, ts_to_sign, price is not None]):
        print("Missing required information for loyalty redemption.")
        pause()
        return

    settlement_loyalty(
        api_key=api_key,
        tokens=tokens,
        token_confirmation=token_confirmation,
        ts_to_sign=ts_to_sign,
        payment_target=package_option_code,
        price=price,
    )
    pause()

def show_redeemables_menu(is_enterprise: bool = False, choices: list = None, is_bot_mode: bool = False):
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        print("Fetching redeemables...")
        redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
        if not redeemables_res:
            print("No redeemables found.")
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        
        clear_screen()
        
        print("=" * WIDTH)
        print("Redeemables:")
        print("=" * WIDTH)
        
        packages = {}
        for i, category in enumerate(categories):
            category_name = category.get("category_name", "N/A")
            category_code = category.get("category_code", "N/A")
            redemables = category.get("redeemables", [])
            
            letter = chr(65 + i)
            print("-" * WIDTH)
            print(f"{letter}. Category: {category_name}")
            print(f"Code: {category_code}")
            print("-" * WIDTH)
            
            if len(redemables) == 0:
                print("  No redeemables in this category.")
                continue
            
            for j, redemable in enumerate(redemables):
                name = redemable.get("name", "N/A")
                valid_until = redemable.get("valid_until", 0)
                valid_until_date = datetime.strftime(
                    datetime.fromtimestamp(valid_until), "%Y-%m-%d"
                )
                
                action_param = redemable.get("action_param", "")
                action_type = redemable.get("action_type", "")
                
                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }
                
                print(f"  {letter}{j + 1}. {name}")
                print(f"     Valid Until: {valid_until_date}")
                print(f"     Action Type: {action_type}")
                print("-" * WIDTH)
                
                print(json.dumps(redemable, indent=4))  # Debug: Show full redemable data
                
        print("00. Back")
        print("=" * WIDTH)
        print("Enter your choice to view package details (e.g., A1, B2): ")
        
        if choices:
            choice = choices.pop(0)
            print(f"Bot choice: {choice}")
        else:
            choice = input()

        if choice == "00":
            in_redeemables_menu = False
            continue
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            print("Invalid choice. Please enter a valid package code.")
            pause()
            continue
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PLP":
            purchase_success = get_packages_by_family(action_param, is_enterprise, "", choices=choices, is_bot_mode=is_bot_mode)
            if is_bot_mode and purchase_success:
                in_redeemables_menu = False
                continue
        elif action_type == "PDP":
            purchase_success = show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise,
                choices=choices,
                is_bot_mode=is_bot_mode
            )
            if is_bot_mode and purchase_success:
                in_redeemables_menu = False
                continue
        elif action_type == "LOYALTY":
            handle_loyalty_redeem(api_key, tokens, action_param, is_enterprise)
            if is_bot_mode:
                in_redeemables_menu = False
        else:
            print("=" * WIDTH)
            print("Unhandled Action Type")
            print(f"Action type: {action_type}\nParam: {action_param}")
            pause()
