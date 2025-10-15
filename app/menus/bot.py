
import time
import sys
import select
import requests
from datetime import datetime

from app.menus.util import clear_screen, print_header, Style, pause, format_quota
from app.client.engsel import send_api_request, get_package
from app.service.auth import AuthInstance
from app.client.balance import settlement_balance
                                      
from app.client.engsel import get_balance

def _fetch_my_packages():

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print(f"{Style.RED}Tidak ada akun aktif. Silakan login terlebih dahulu.{Style.RESET}")
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
        print(f"{Style.RED}Gagal mengambil paket.{Style.RESET}")
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
    print(f"{Style.YELLOW}🥷 TOOL INI DIGUNAKAN UNTUK AUTO REBUY PAKET 🥷{Style.RESET}")
    print(f"{Style.YELLOW}Cara pakai:{Style.RESET}")
    print(f"{Style.YELLOW}1. Pilih paket yang kamu akan rebuy pada list paket kamu yang tersedia{Style.RESET}")
    print(f"{Style.YELLOW}2. Set sisa Quota Minimum untuk Auto Rebuy{Style.RESET}")
    print(f"{'-'*55}")                   
    print(f"{Style.GREEN}Gunakan secara bijak!{Style.RESET}")
    print(f"{Style.YELLOW}Gunakan via Termux atau install di STB kamu. bot tetap aktif selama tidak dihapus dari background{Style.RESET}")
    print(f"{'-'*55}")
                                 
    quote = "🙏 Kenapa mata kamu kayak Google? Karena semua yang aku cari ada di situ.💓 "
                                                              
    colors = [Style.CYAN, Style.MAGENTA, Style.YELLOW, Style.GREEN]
    for i, ch in enumerate(quote):
        color = colors[i % len(colors)]
        sys.stdout.write(f"{color}{ch}{Style.RESET}")
        sys.stdout.flush()
        time.sleep(0.01)                      
    print("\n" + "-"*55)

def run_edubot():
    """
    Memulai proses bot auto-buy untuk paket edukasi.
    """
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print(f"{Style.RED}Anda belum login. Silakan login terlebih dahulu melalui menu utama.{Style.RESET}")
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
        print(f"{Style.CYAN}[{pkg['index']}] {Style.RESET}{pkg['name']} (Quota Code: {pkg['quota_code']})")
                                                     
        for benefit in pkg["benefits"]:
            if benefit["data_type"] == "DATA":
                remaining_str = format_quota(benefit["remaining"])
                total_str = format_quota(benefit["total"])
                print(f"   - {Style.YELLOW}{benefit['name']}{Style.RESET}: {remaining_str} / {total_str}")
        print("-"*55)
    print(f"{Style.CYAN}[99]{Style.RESET} Keluar ke menu utama")
    choice = input("Pilih nomor paket untuk dipantau > ").strip()
    if choice == "99":
        return
    selected_pkg = None
    for pkg in packages:
        if str(pkg["index"]) == choice:
            selected_pkg = pkg
            break
    if not selected_pkg:
        print(f"{Style.RED}Pilihan tidak valid.{Style.RESET}")
        pause()
        return

    quota_code = selected_pkg["quota_code"]
                                                                
    detail = selected_pkg["detail"]
    if not detail:
        detail = get_package(AuthInstance.api_key, AuthInstance.get_active_tokens(), quota_code)
        if not detail:
            print(f"{Style.RED}Gagal mengambil detail paket.{Style.RESET}")
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

                                                                          
    print("\nMemulai pemantauan paket '{0}'.".format(option_name))
    print("Bot akan memeriksa sisa kuota secara berkala dan melakukan pembelian ulang otomatis ketika sisa kuota di bawah ambang minimal yang Anda tetapkan.")
    print("Anda dapat menentukan minimum kuota (dalam GB) sebelum auto-purchase dilakukan.")
    print("Masukkan '99' kemudian tekan Enter kapan saja untuk keluar.\n")
                                                                                
    min_quota_gb = 1.0
    user_input_quota = input("Masukkan minimum kuota (GB) sebelum auto-buy [default 1] > ").strip()
    if user_input_quota:
        try:
            min_quota_gb = float(user_input_quota)
        except ValueError:
            print(f"{Style.YELLOW}Input tidak valid. Menggunakan default 1 GB.{Style.RESET}")
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
    while True:
        try:
            # 1. Cek koneksi internet sebelum melakukan request
            requests.get("https://google.com", timeout=5)
        except (requests.ConnectionError, requests.Timeout):
            clear_screen()
            print_header(f"📡 Pemantauan Paket: {option_name}")
            print(f"\n{Style.RED}Tidak ada koneksi internet. Mencoba lagi dalam {refresh_seconds} detik...{Style.RESET}")
            time.sleep(refresh_seconds)
            continue

                                                                                               
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            print(f"{Style.RED}Token tidak tersedia. Hentikan bot.{Style.RESET}")
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
            print(f"  Sisa Pulsa : {Style.YELLOW}{saldo_str}{Style.RESET}")
        else:
            print(f"  Sisa Pulsa : {Style.YELLOW}N/A{Style.RESET}")
                                                   
        if remaining_bytes is not None:
            remaining_str = format_quota(remaining_bytes)
            total_str = format_quota(total_bytes)
            print(f"  Sisa Kuota : {Style.YELLOW}{remaining_str}{Style.RESET} / {Style.GREEN}{total_str}{Style.RESET}")
        else:
            print("  Tidak ditemukan data kuota.")
                                   
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  Waktu Update : {now_str}")
        print(f"  {Style.RED}Set Min Quota{Style.RESET}  : {min_quota_gb:.2f} GB")
                       
        print("-"*55)

                                                                                     
                                                                                     
        need_purchase = False
        if payment_pending:
                                                                         
            if remaining_bytes is not None and remaining_bytes >= threshold_bytes:
                payment_pending = False
        else:
                                                                             
            if remaining_bytes is not None and remaining_bytes < threshold_bytes:
                need_purchase = True

        if need_purchase:
                                                                              
            print(f"{Style.YELLOW}Sisa kuota kurang dari {min_quota_gb:.2f} GB. Memulai pembelian ulang otomatis...{Style.RESET}")
                                                                                  
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
                amount_used="first"
            )
            if not settlement_response or settlement_response.get("status") != "SUCCESS":
                print(f"{Style.RED}Gagal melakukan pembayaran dengan pulsa.{Style.RESET}")
                print(f"Error: {settlement_response}")
            else:
                print(f"{Style.GREEN}Pembelian paket berhasil menggunakan pulsa.{Style.RESET}")
                                                                                                  
                payment_pending = True

        else:
            print(f"{Style.GREEN}Sisa kuota masih aman, pemantauan dilanjutkan.{Style.RESET}")
                                                                                               
        print("\nMasukkan '99' dan tekan Enter untuk keluar, atau tekan Enter untuk menunggu update berikutnya...")
                                                                
        exit_requested = False
        for rem in range(refresh_seconds, 0, -1):
                                                               
            countdown_text = f"  {Style.YELLOW}Sisa waktu refresh : {rem} detik{Style.RESET}    "
            sys.stdout.write(countdown_text + "\r")
            sys.stdout.flush()
                                                        
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 1)
                if rlist:
                    user_in = sys.stdin.readline().strip()
                    if user_in == "99":
                        print("\nMengakhiri bot dan kembali ke menu.")
                        exit_requested = True
                        break
            except KeyboardInterrupt:
                print("\nBot dihentikan oleh pengguna.")
                exit_requested = True
                break
                                
        sys.stdout.write("\n")
        if exit_requested:
            break
                                                  
        continue