import time
import requests
from app.client.engsel import get_family, get_package_details
from app.menus.util import pause
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance

# Purchase
def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        # Balance; Decoy XCP
        url = "https://me.mashu.lol/pg-decoy-xcp.json"
        
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Transaksi Gagal")
            return None
        
        decoy_data = response.json()
    
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print("Transaksi Gagal")
        return None
    
    variants = family_data["package_variants"]
    
    for variant in variants:
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            
            payment_items = []
            
            try:
                if use_decoy:
                    decoy_package_detail = get_package_details(
                        api_key,
                        tokens,
                        decoy_data["family_code"],
                        decoy_data["variant_code"],
                        decoy_data["order"],
                        decoy_data["is_enterprise"],
                        decoy_data["migration_type"],
                    )
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                    family_data=family_data,
                )
            except Exception as e:
                print(f"Transaksi Gagal")
                continue
            
            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(option["order"]) + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )
            
            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(option["order"]) + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
            
            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy:
                overwrite_amount += decoy_package_detail["package_option"]["price"]

            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    False,
                    overwrite_amount,
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "Unknown error")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "BUY_PACKAGE",
                            False,
                            valid_amount,
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            print("Transaksi Sukses")
                        else:
                            print(f"Transaksi Gagal")
                    else:
                        print(f"Transaksi Gagal")
                else:
                    print("Transaksi Sukses")

            except Exception as e:
                print(f"Transaksi Gagal")

def purchase_loop(
    family_code: str,
    order: int,
    use_decoy: bool,
    delay: int = 0,
    pause_on_success: bool = False,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    # Find the package variant and option from family data
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print("Transaksi Gagal")
        return

    target_variant = None
    target_option = None
    for variant in family_data["package_variants"]:
        for option in variant["package_options"]:
            if option["order"] == order:
                target_variant = variant
                target_option = option
                break
        if target_option:
            break
    
    if not target_variant or not target_option:
        print("Transaksi Gagal")
        return

    variant_code = target_variant["package_variant_code"]

    if use_decoy:
        url = "https://me.mashu.lol/pg-decoy-xcp.json"
        
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Transaksi Gagal")
            return None
        
        decoy_data = response.json()

    tokens = AuthInstance.get_active_tokens()
    
    try:
        target_package_detail = get_package_details(
            api_key,
            tokens,
            family_code,
            variant_code,
            order,
            None,
            None,
            family_data=family_data,
        )
    except Exception as e:
        print("Transaksi Gagal")
        return

    payment_items = []
    payment_items.append(
        PaymentItem(
            item_code=target_package_detail["package_option"]["package_option_code"],
            product_type="",
            item_price=target_package_detail["package_option"]["price"],
            item_name=str(order) + target_package_detail["package_option"]["name"],
            tax=0,
            token_confirmation=target_package_detail["token_confirmation"],
        )
    )

    if use_decoy:
        decoy_package_detail = get_package_details(
            api_key,
            tokens,
            decoy_data["family_code"],
            decoy_data["variant_code"],
            decoy_data["order"],
            decoy_data["is_enterprise"],
            decoy_data["migration_type"],
        )
        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=str(decoy_data["order"]) + decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

    overwrite_amount = target_package_detail["package_option"]["price"]
    if use_decoy:
        overwrite_amount += decoy_package_detail["package_option"]["price"]

    try:
        res = settlement_balance(
            api_key,
            tokens,
            payment_items,
            "BUY_PACKAGE",
            False,
            overwrite_amount,
        )
        
        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Unknown error")
            if "Bizz-err.Amount.Total" in error_msg:
                error_msg_arr = error_msg.split("=")
                valid_amount = int(error_msg_arr[1].strip())
                
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    False,
                    valid_amount,
                )
                if res and res.get("status", "") == "SUCCESS":
                    print("Transaksi Sukses")
                else:
                    print(f"Transaksi Gagal")
            else:
                print(f"Transaksi Gagal")

        else:
            print("Transaksi Sukses")

    except Exception as e:
        print(f"Transaksi Gagal")
    
    time.sleep(delay)
    return True