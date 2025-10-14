from app.menus.util import clear_screen, pause
from app.service.family_bookmark import FamilyBookmarkInstance
from app.client.engsel import get_family
from app.service.auth import AuthInstance
from app.menus.purchase import purchase_by_family

def show_family_bookmark_menu():
    while True:
        clear_screen()
        print("-------------------------------------------------------")
        print("Bookmark Family Code")
        print("-------------------------------------------------------")
        
        bookmarks = FamilyBookmarkInstance.get_bookmarks()
        if not bookmarks:
            print("Tidak ada bookmark family code tersimpan.")
        else:
            for idx, bm in enumerate(bookmarks):
                print(f"{idx + 1}. {bm['family_name']} ({bm['family_code']})")

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
            family_code = input("Masukkan Family Code yang ingin di-bookmark: ").strip()
            if family_code:
                # Get family name for user-friendly display
                tokens = AuthInstance.get_active_tokens()
                family_data = get_family(AuthInstance.api_key, tokens, family_code)
                if family_data and "package_family" in family_data:
                    family_name = family_data["package_family"]["name"]
                    FamilyBookmarkInstance.add_bookmark(family_code, family_name)
                else:
                    print("Gagal mendapatkan data family. Pastikan family code valid.")
                pause()
            else:
                print("Family code tidak boleh kosong.")
                pause()
        elif choice == 'd':
            if not bookmarks:
                print("Tidak ada bookmark untuk dihapus.")
                pause()
                continue
            del_choice = input("Masukkan nomor bookmark yang ingin dihapus: ")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                bm_to_delete = bookmarks[int(del_choice) - 1]
                FamilyBookmarkInstance.remove_bookmark(bm_to_delete['family_code'])
            else:
                print("Input tidak valid.")
            pause()
        elif choice.isdigit() and bookmarks and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            print(f"Membeli paket dari family: {selected_bm['family_name']}")
            # Here we call the purchase flow
            use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
            pause_on_success = input("Pause on each successful purchase? (y/n): ").lower() == 'y'
            purchase_by_family(selected_bm['family_code'], use_decoy, pause_on_success)
        else:
            print("Pilihan tidak valid.")
            pause()
