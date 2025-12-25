
import time
import sys
import select
import requests
from datetime import datetime

from app.colors import bcolors
from app.menus.util import clear_screen, print_header, pause, format_quota, wrap_text
from app.client.engsel import send_api_request, get_package
from app.service.auth import AuthInstance
from app.client.purchase.balance import settlement_balance
                                      
from app.client.engsel import get_balance

def _fetch_my_packages():

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print(f"{bcolors.FAIL}Tidak ada akun aktif. Silakan login terlebih dahulu.{bcolors.ENDC}")
        pause()
        return []

    id_token = tokens.get("id_token")
                                                                  
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    print("Mengambil data paket saya...")
    res = send_api_request(api_key, path, payload, id_token, "POST")
    if not (isinstance(res, dict) and res.get("status") == "SUCCESS"):
        print(f"{bcolors.FAIL}Gagal mengambil paket.{bcolors.ENDC}")
        print(f"Respon: {res}")
        pause()
        return []

    quotas = res["data"].get("quotas", [])
    packages = []
    idx = 1
    for quota in quotas:
        quota_code = quota.get("quota_code")
        group_code = quota.get("group_code", "")
        initial_name = quota.get("name", "")
                                                                             
        detail = get_package(api_key, tokens, quota_code)
        name = initial_name
        if detail and "package_option" in detail:
            name = detail["package_option"].get("name", initial_name)
                              
        benefits_data = []
        for benefit in quota.get("benefits", []):
            benefits_data.append({
                "name": benefit.get("name", ""),
                "data_type": benefit.get("data_type", ""),
                "remaining": benefit.get("remaining", 0),
                "total": benefit.get("total", 0)
            })
        packages.append({
            "index": idx,
            "quota_code": quota_code,
            "group_code": group_code,
            "name": name,
            "benefits": benefits_data,
            "detail": detail
        })
        idx += 1

    return packages

def _print_opening():

    clear_screen()
            
    print_header("🤖 BOT AUTO BUY BY QUOTA 🤖")
    print(wrap_text(f"{bcolors.WARNING}🥷 TOOL INI DIGUNAKAN UNTUK AUTO REBUY PAKET 🥷{bcolors.ENDC}"))
    print(wrap_text(f"{bcolors.WARNING}Cara pakai:{bcolors.ENDC}"))
    print(wrap_text(f"{bcolors.WARNING}1. Pilih paket yang kamu akan rebuy pada list paket kamu yang tersedia{bcolors.ENDC}"))
    print(wrap_text(f"{bcolors.WARNING}2. Set sisa Quota Minimum untuk Auto Rebuy{bcolors.ENDC}"))
    print(f"{'-'*55}")                   
    print(wrap_text(f"{bcolors.OKGREEN}Gunakan secara bijak!{bcolors.ENDC}"))
    print(wrap_text(f"{bcolors.WARNING}Gunakan via Termux atau install di STB kamu. bot tetap aktif selama tidak dihapus dari background{bcolors.ENDC}"))
    print(f"{'-'*55}")
                                 
    quote = "🙏 Kenapa mata kamu kayak Google? Karena semua yang aku cari ada di situ.💓 "
                                                              
    colors = [bcolors.OKCYAN, bcolors.HEADER, bcolors.WARNING, bcolors.OKGREEN]
    for i, ch in enumerate(quote):
        color = colors[i % len(colors)]
        sys.stdout.write(f"{color}{ch}{bcolors.ENDC}")
        sys.stdout.flush()
        time.sleep(0.01)                      
    print("\n" + "-"*55)

def run_edubot():
    """
    Memulai proses bot auto-buy untuk paket edukasi.
    """
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print(f"{bcolors.FAIL}Anda belum login. Silakan login terlebih dahulu melalui menu utama.{bcolors.ENDC}")
        pause()
        return

    _print_opening()
                     
    confirm = input("Jalankan bot sekarang? (y/n) > ").strip().lower()
    if confirm != "y":
        print("Bot dibatalkan. Kembali ke menu.")
        pause()
        return

                        
    packages = _fetch_my_packages()
    if not packages:
        return
                            
    clear_screen()
    print_header("📦 Daftar Paket Saya")
    for pkg in packages:
        print(wrap_text(f"{bcolors.OKCYAN}[{pkg['index']}] {bcolors.ENDC}{pkg['name']} (Quota Code: {pkg['quota_code']})"))
                                                     
        for benefit in pkg["benefits"]:
            if benefit["data_type"] == "DATA":
                remaining_str = format_quota(benefit["remaining"])
                total_str = format_quota(benefit["total"])
                print(wrap_text(f"   - {bcolors.WARNING}{benefit['name']}{bcolors.ENDC}: {remaining_str} / {total_str}"))
        print("-"*55)
    print(f"{bcolors.OKCYAN}[99]{bcolors.ENDC} Keluar ke menu utama")
    choice = input("Pilih nomor paket untuk dipantau > ").strip()
    if choice == "99":
        return
    selected_pkg = None
    for pkg in packages:
        if str(pkg["index"]) == choice:
            selected_pkg = pkg
            break
    if not selected_pkg:
        print(f"{bcolors.FAIL}Pilihan tidak valid.{bcolors.ENDC}")
        pause()
        return

    quota_code = selected_pkg["quota_code"]
                                                                
    detail = selected_pkg["detail"]
    if not detail:
        detail = get_package(AuthInstance.api_key, AuthInstance.get_active_tokens(), quota_code)
        if not detail:
            print(f"{bcolors.FAIL}Gagal mengambil detail paket.{bcolors.ENDC}")
            pause()
            return
    package_option = detail.get("package_option", {})
    price = package_option.get("price", 0)
    option_name = package_option.get("name", "")
    token_confirmation = detail.get("token_confirmation", "")
                                
    payment_items = [{
        "item_code": quota_code,
        "product_type": "",
        "item_price": price,
        "item_name": option_name,
        "tax": 0,
        "token_confirmation": token_confirmation,
    }]

                                                                          
    print(wrap_text("\nMemulai pemantauan paket '{0}'.".format(option_name)))
    print(wrap_text("Bot akan memeriksa sisa kuota secara berkala dan melakukan pembelian ulang otomatis ketika sisa kuota di bawah ambang minimal yang Anda tetapkan."))
    print(wrap_text("Anda dapat menentukan minimum kuota (dalam GB) sebelum auto-purchase dilakukan.\n"))
                                                                                
    min_quota_gb = 1.0
    user_input_quota = input("Masukkan minimum kuota (GB) sebelum auto-buy [default 1] > ").strip()
    if user_input_quota:
        try:
            min_quota_gb = float(user_input_quota)
        except ValueError:
            print(f"{bcolors.WARNING}Input tidak valid. Menggunakan default 1 GB.{bcolors.ENDC}")
            min_quota_gb = 1.0
                                     
    threshold_bytes = int(min_quota_gb * (1024 ** 3))
                                    
    refresh_seconds = 60

    def _format_balance(balance: dict) -> str:
        
        if not balance or not isinstance(balance, dict):
            return "N/A"
                                                     
        for key in ["balance", "balance_amount", "credit", "remaining", "value", "quota"]:
            val = balance.get(key)
            if isinstance(val, (int, float)):
                try:
                                                                    
                    return f"{val:,}".replace(",", ".")
                except Exception:
                    return str(val)
        return str(balance)

                                                                      
                                                                     
                                                                    
                                   
    payment_pending = False
    try:
        while True:
            try:
                # 1. Cek koneksi internet sebelum melakukan request
                requests.get("https://google.com", timeout=5)
            except (requests.ConnectionError, requests.Timeout):
                clear_screen()
                print_header(f"📡 Pemantauan Paket: {option_name}")
                print(f"\n{bcolors.FAIL}Tidak ada koneksi internet. Mencoba lagi dalam {refresh_seconds} detik...{bcolors.ENDC}")
                time.sleep(refresh_seconds)
                continue

                                                                                               
            tokens = AuthInstance.get_active_tokens()
            if not tokens:
                print(f"{bcolors.FAIL}Token tidak tersedia. Hentikan bot.{bcolors.ENDC}")
                break
                                                               
            try:
                payload_update = {
                    "is_enterprise": False,
                    "lang": "en",
                    "family_member_id": ""
                }
                res_update = send_api_request(AuthInstance.api_key, "api/v8/packages/quota-details", payload_update, tokens.get("id_token"), "POST")
            except Exception:
                res_update = None
            remaining_bytes = None
            total_bytes = None
            if isinstance(res_update, dict) and res_update.get("status") == "SUCCESS":
                quotas_update = res_update.get("data", {}).get("quotas", [])
                for q in quotas_update:
                                                                                         
                    if q.get("quota_code") == quota_code or (
                        selected_pkg.get("group_code") and q.get("group_code") == selected_pkg.get("group_code")
                    ):
                                                                          
                        rem = q.get("remaining")
                        tot = q.get("total")
                        if rem is not None and tot is not None:
                            remaining_bytes = rem
                            total_bytes = tot
                                                                                                
                        if remaining_bytes is None or total_bytes is None or total_bytes == 0:
                            max_total_val = -1
                            chosen_benefit = None
                            for b in q.get("benefits", []):
                                tval = b.get("total")
                                if tval is not None and tval > max_total_val:
                                    max_total_val = tval
                                    chosen_benefit = b
                            if chosen_benefit:
                                remaining_bytes = chosen_benefit.get("remaining")
                                total_bytes = chosen_benefit.get("total")
                        break
                                    
            clear_screen()
            print_header(f"📡 Pemantauan Paket: {option_name}")
                                            
            balance_data = None
            try:
                balance_data = get_balance(AuthInstance.api_key, tokens.get("id_token"))
            except Exception:
                balance_data = None
            if balance_data:
                saldo_str = _format_balance(balance_data)
                print(f"  Sisa Pulsa : {bcolors.WARNING}{saldo_str}{bcolors.ENDC}")
            else:
                print(f"  Sisa Pulsa : {bcolors.WARNING}N/A{bcolors.ENDC}")
                                                    
            if remaining_bytes is not None:
                remaining_str = format_quota(remaining_bytes)
                total_str = format_quota(total_bytes)
                print(f"  Sisa Kuota : {bcolors.WARNING}{remaining_str}{bcolors.ENDC} / {bcolors.OKGREEN}{total_str}{bcolors.ENDC}")
            else:
                print("  Tidak ditemukan data kuota.")
                                    
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"  Waktu Update : {now_str}")
            print(f"  {bcolors.FAIL}Set Min Quota{bcolors.ENDC}  : {min_quota_gb:.2f} GB")
                        
            print("-"*55)

                                                                                        
                                                                                        
            need_purchase = False
            if payment_pending:
                                                                            
                if remaining_bytes is not None and remaining_bytes >= threshold_bytes:
                    payment_pending = False
            else:
                                                                              
                if remaining_bytes is not None and remaining_bytes < threshold_bytes:
                    need_purchase = True

            if need_purchase:
                                                                               
                print(f"{bcolors.WARNING}Sisa kuota kurang dari {min_quota_gb:.2f} GB. Memulai pembelian ulang otomatis...{bcolors.ENDC}")
                                                                                    
                try:
                    updated_detail = get_package(AuthInstance.api_key, AuthInstance.get_active_tokens(), quota_code, silent=True)
                except Exception:
                    updated_detail = None
                if updated_detail and "package_option" in updated_detail:
                    new_price = updated_detail["package_option"].get("price", price)
                    new_token_conf = updated_detail.get("token_confirmation", token_confirmation)
                                                                        
                    payment_items[0]["item_price"] = new_price
                    payment_items[0]["token_confirmation"] = new_token_conf
                    price = new_price
                    token_confirmation = new_token_conf
                                                                                    
                settlement_response = settlement_balance(
                    AuthInstance.api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    ask_overwrite=False,
                    overwrite_amount=price
                )
                if not settlement_response or settlement_response.get("status") != "SUCCESS":
                    print(f"{bcolors.FAIL}Gagal melakukan pembayaran dengan pulsa.{bcolors.ENDC}")
                    print(f"Error: {settlement_response}")
                else:
                    print(f"{bcolors.OKGREEN}Pembelian paket berhasil menggunakan pulsa.{bcolors.ENDC}")
                                                                                                        
                    payment_pending = True

            else:
                print(f"{bcolors.OKGREEN}Sisa kuota masih aman, pemantauan dilanjutkan.{bcolors.ENDC}")
                                                                                                
            print("\nTekan Ctrl+C untuk keluar, atau tekan Enter untuk menunggu update berikutnya...")
                                                                    
            if sys.platform == "win32":
                import msvcrt
                end_time = time.time() + refresh_seconds
                while time.time() < end_time:
                    rem = int(end_time - time.time())
                    countdown_text = f"  {bcolors.WARNING}Sisa waktu refresh : {rem} detik{bcolors.ENDC}    "
                    sys.stdout.write(countdown_text + "\r")
                    sys.stdout.flush()

                    if msvcrt.kbhit():
                        msvcrt.getch()
                    time.sleep(1)
            else:
                for rem in range(refresh_seconds, 0, -1):
                                                                    
                    countdown_text = f"  {bcolors.WARNING}Sisa waktu refresh : {rem} detik{bcolors.ENDC}    "
                    sys.stdout.write(countdown_text + "\r")
                    sys.stdout.flush()
                                                            
                    try:
                        rlist, _, _ = select.select([sys.stdin], [], [], 1)
                        if rlist:
                            # Consume the input to prevent it from affecting subsequent prompts
                            sys.stdin.readline()
                    except KeyboardInterrupt:
                        # This KeyboardInterrupt will be caught by the outer try-except block
                        raise
                    time.sleep(1)
            sys.stdout.write("\n") # Ensure a newline after countdown is finished.

    except KeyboardInterrupt:
        print("\nBot dihentikan oleh pengguna.")
    except Exception as e:
        print(f"\n{bcolors.FAIL}Terjadi kesalahan tak terduga: {e}{bcolors.ENDC}")
    finally:
        pause()