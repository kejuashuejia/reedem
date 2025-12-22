import json
from app.client.engsel import send_api_request
from app.colors import bcolors

BASE_API_URL = "https://api.myxl.xlaxiata.co.id"
AX_FP = ""
UA = "myXL / 8.9.0(1202); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)"

def get_payment_methods(
    api_key: str,
    tokens: dict,
    token_confirmation: str,
    payment_target: str,
):
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": payment_target,
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation
    }
    
    payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")
    if payment_res["status"] != "SUCCESS":
        print(f"{bcolors.FAIL}Failed to fetch payment methods.{bcolors.ENDC}")
        print(f"Error: {payment_res}")
        return None

    return payment_res["data"]
