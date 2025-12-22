from app.client.ciam import get_otp, submit_otp
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.colors import bcolors

def show_login_menu():
    clear_screen()
    print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
    print(f"{bcolors.BOLD}Login ke MyXL{bcolors.ENDC}")
    print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
    print("1. Request OTP")
    print("2. Submit OTP")
    print(f"99. {bcolors.FAIL}Tutup aplikasi{bcolors.ENDC}")
    print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
    
def login_prompt(api_key: str):
    clear_screen()
    print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
    print(f"{bcolors.BOLD}Login ke MyXL{bcolors.ENDC}")
    print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
    print("Masukan nomor XL (Contoh 6281234567890):")
    phone_number = input("Nomor: ")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print(f"{bcolors.FAIL}Nomor tidak valid. Pastikan nomor diawali dengan '628' dan memiliki panjang yang benar.{bcolors.ENDC}")
        return None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None
        print(f"{bcolors.OKGREEN}OTP Berhasil dikirim ke nomor Anda.{bcolors.ENDC}")
        
        try_count = 5
        while try_count > 0:
            print(f"Sisa percobaan: {try_count}")
            otp = input("Masukkan OTP yang telah dikirim: ")
            if not otp.isdigit() or len(otp) != 6:
                print(f"{bcolors.FAIL}OTP tidak valid. Pastikan OTP terdiri dari 6 digit angka.{bcolors.ENDC}")
                continue
            
            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if not tokens:
                print(f"{bcolors.FAIL}OTP salah. Silahkan coba lagi.{bcolors.ENDC}")
                try_count -= 1
                continue
            
            print(f"{bcolors.OKGREEN}Berhasil login!{bcolors.ENDC}")
            return phone_number, tokens["refresh_token"]

        print(f"{bcolors.FAIL}Gagal login setelah beberapa percobaan. Silahkan coba lagi nanti.{bcolors.ENDC}")
        return None, None
    except Exception as e:
        print(f"{bcolors.FAIL}Gagal login: {e}{bcolors.ENDC}")
        return None, None

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
        
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        print(f"{bcolors.HEADER}-------------------------------------------------------{bcolors.ENDC}")
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print(f"{bcolors.FAIL}Gagal menambah akun. Silahkan coba lagi.{bcolors.ENDC}")
                pause()
                continue
            
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            
            
            if add_user:
                add_user = False
            continue
        
        print(f"{bcolors.BOLD}Akun Tersimpan:{bcolors.ENDC}")
        if not users or len(users) == 0:
            print("Tidak ada akun tersimpan.")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            active_marker = f"{bcolors.OKGREEN}✅{bcolors.ENDC}" if is_active else ""
            
            number = str(user.get("number", ""))
            number = number + " " * (14 - len(number))
            
            sub_type = user.get("subscription_type", "").center(12)
            print(f"{idx + 1}. {number} [{bcolors.OKCYAN}{sub_type}{bcolors.ENDC}] {active_marker}")
        
        print(f"{bcolors.HEADER}{'-' * 55}{bcolors.ENDC}")
        print(f"{bcolors.BOLD}Command:{bcolors.ENDC}")
        print("0: Tambah Akun")
        print("Masukan nomor urut akun untuk berganti.")
        print(f"{bcolors.WARNING}Masukan del <nomor urut> untuk menghapus akun tertentu.{bcolors.ENDC}")
        print("00: Kembali ke menu utama")
        print(f"{bcolors.HEADER}{'-' * 55}{bcolors.ENDC}")
        input_str = input("Pilihan:")
        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        elif input_str.startswith("del "):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])
                
                # Prevent deleting the active user here
                if active_user and users[del_index - 1]["number"] == active_user["number"]:
                    print(f"{bcolors.FAIL}Tidak dapat menghapus akun aktif. Silahkan ganti akun terlebih dahulu.{bcolors.ENDC}")
                    pause()
                    continue
                
                if 1 <= del_index <= len(users):
                    user_to_delete = users[del_index - 1]
                    confirm = input(f"Yakin ingin menghapus akun {user_to_delete['number']}? (y/n): ")
                    if confirm.lower() == 'y':
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        # AuthInstance.load_tokens()
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print(f"{bcolors.OKGREEN}Akun berhasil dihapus.{bcolors.ENDC}")
                        pause()
                    else:
                        print("Penghapusan akun dibatalkan.")
                        pause()
                else:
                    print(f"{bcolors.FAIL}Nomor urut tidak valid.{bcolors.ENDC}")
                    pause()
            else:
                print(f"{bcolors.FAIL}Perintah tidak valid. Gunakan format: del <nomor urut>{bcolors.ENDC}")
                pause()
            continue
        else:
            print(f"{bcolors.FAIL}Input tidak valid. Silahkan coba lagi.{bcolors.ENDC}")
            pause()
            continue