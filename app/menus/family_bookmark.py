from app.menus.util import clear_screen, pause
from app.service.family_bookmark import FamilyBookmarkInstance
from app.client.engsel import get_family
from app.service.auth import AuthInstance
from app.menus.purchase import purchase_loop

def show_family_bookmark_menu():
    while True:
        clear_screen()
        print("-------------------------------------------------------")
        print("Bookmark Family Paket")
        print("-------------------------------------------------------")
        
        bookmarks = FamilyBookmarkInstance.get_bookmarks()
        if not bookmarks:
            print("Tidak ada bookmark family paket tersimpan.")
        else:
            for idx, bm in enumerate(bookmarks):
                print(f"{idx + 1}. {bm['name']} ({bm['family_code']}/{bm['order']})")

        print("\nMenu:")
        print("a. Tambah Bookmark")
        print("d. Hapus Bookmark")
        print("0. Kembali")
        print("-------------------------------------------------------")

        if bookmarks:
            print("Pilih bookmark untuk dibeli, atau pilih menu (a/d/0).")
        
        choice = input("Pilihan Anda: ").strip().lower()

        if choice == '0':
            break
        elif choice == 'a':
            name = input("Masukkan Nama Bookmark: ").strip()
            family_code = input("Masukkan Family Code: ").strip()
            order_str = input("Masukkan Nomor Order: ").strip()
            if name and family_code and order_str.isdigit():
                order = int(order_str)
                FamilyBookmarkInstance.add_bookmark(name, family_code, order)
                pause()
            else:
                print("Nama, family code, dan nomor order harus diisi dengan benar.")
                pause()
        elif choice == 'd':
            if not bookmarks:
                print("Tidak ada bookmark untuk dihapus.")
                pause()
                continue
            del_choice = input("Masukkan nomor bookmark yang ingin dihapus: ")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                FamilyBookmarkInstance.remove_bookmark(int(del_choice) - 1)
            else:
                print("Input tidak valid.")
            pause()
        elif choice.isdigit() and bookmarks and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            print(f"Membeli paket: {selected_bm['name']}")
            
            use_decoy_str = input("Use decoy package? (y/n, default n): ").lower()
            use_decoy = use_decoy_str == 'y'

            delay_str = input("Masukkan delay antar pembelian (detik, default 5): ").strip()
            delay = int(delay_str) if delay_str.isdigit() else 5

            pause_on_success_str = input("Pause on each successful purchase? (y/n, default n): ").lower()
            pause_on_success = pause_on_success_str == 'y'
            
            purchase_loop(
                family_code=selected_bm['family_code'],
                order=selected_bm['order'],
                use_decoy=use_decoy,
                delay=delay,
                pause_on_success=pause_on_success
            )
        else:
            print("Pilihan tidak valid.")
            pause()
