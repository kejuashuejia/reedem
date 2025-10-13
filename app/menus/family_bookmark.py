from app.menus.util import clear_screen, pause
from app.service.family_bookmark import FamilyBookmarkInstance
from app.menus.purchase import purchase_loop

def add_family_bookmark_menu():
    clear_screen()
    print("-------------------------------------------------------")
    print("Tambah Bookmark Keluarga Baru")
    print("-------------------------------------------------------")
    name = input("Masukkan nama untuk bookmark ini: ")
    family_code = input("Masukkan family code: ")
    try:
        order = int(input("Masukkan nomor order: "))
    except ValueError:
        print("Nomor order harus berupa angka.")
        pause()
        return

    if FamilyBookmarkInstance.add_bookmark(name, family_code, order):
        print(f"Bookmark '{name}' berhasil ditambahkan.")
    else:
        print("Gagal menambahkan bookmark. Mungkin sudah ada.")
    pause()

def show_family_bookmark_menu():
    in_menu = True
    while in_menu:
        clear_screen()
        print("-------------------------------------------------------")
        print("Bookmark Keluarga")
        print("-------------------------------------------------------")
        bookmarks = FamilyBookmarkInstance.get_bookmarks()
        if not bookmarks:
            print("Tidak ada bookmark keluarga tersimpan.")
        else:
            for idx, bm in enumerate(bookmarks):
                print(f"{idx + 1}. {bm['name']} (Code: {bm['family_code']}, Order: {bm['order']})")
        
        print("-------------------------------------------------------")
        print("a. Tambah Bookmark Baru")
        print("d. Hapus Bookmark")
        print("0. Kembali ke Menu Utama")
        print("-------------------------------------------------------")

        choice = input("Pilih bookmark untuk memulai loop, atau pilih menu (a/d/0): ").lower()

        if choice == '0':
            in_menu = False
        elif choice == 'a':
            add_family_bookmark_menu()
        elif choice == 'd':
            if not bookmarks:
                print("Tidak ada bookmark untuk dihapus.")
                pause()
                continue
            del_choice = input("Masukkan nomor bookmark yang ingin dihapus: ")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                bm_to_del = bookmarks[int(del_choice) - 1]
                FamilyBookmarkInstance.remove_bookmark(bm_to_del['family_code'], bm_to_del['order'])
            else:
                print("Input tidak valid.")
                pause()
        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            delay = int(input("Masukkan jeda waktu (detik): "))
            pause_on_success = input("Aktifkan mode pause setelah sukses? (y/n): ").lower() == 'y'
            
            while True:
                if not purchase_loop(
                    family_code=selected_bm['family_code'],
                    order=selected_bm['order'],
                    use_decoy=True,
                    delay=delay,
                    pause_on_success=pause_on_success
                ):
                    break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")
            pause()
