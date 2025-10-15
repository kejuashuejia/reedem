from app.menus.purchase import purchase_loop
from app.menus.util import clear_screen, pause

def start_loop(package):
    """
    Starts a generic purchase loop for a given package.

    Args:
        package (dict): A dictionary containing package details 
                        like 'name', 'family_code', and 'order'.
    """
    clear_screen()
    print(f"Memulai loop untuk paket: {package['name']}")
    print("=" * 55)
    
    try:
        delay = int(input("Masukkan jeda (delay) dalam detik: "))
    except ValueError:
        print("Input tidak valid, menggunakan jeda default 1 detik.")
        delay = 1
        
    pause_on_success = input("Aktifkan mode jeda setelah sukses (pause)? (y/n): ").lower() == 'y'
    
    while True:
        if not purchase_loop(
            family_code=package['family_code'],
            order=package['order'],
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            print(f"Loop untuk paket '{package['name']}' berhenti.")
            pause()
            break