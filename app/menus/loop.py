from app.menus.purchase import purchase_loop
from app.menus.util import clear_screen, pause

WIDTH = 55

def bonus_kuota_malam():
    delay = int(input("Enter delay in seconds: "))
    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
    while True:
        if not purchase_loop(
            family_code='5412b964-474e-42d3-9c86-f5692da627db',
            order=211,
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            break

def bebas_puas_tiktok_yt():
    delay = int(input("Enter delay in seconds: "))
    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
    while True:
        if not purchase_loop(
            family_code='5412b964-474e-42d3-9c86-f5692da627db',
            order=212,
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            break

def kuota_pelanggan_baru():
    delay = int(input("Enter delay in seconds: "))
    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
    while True:
        if not purchase_loop(
            family_code='5412b964-474e-42d3-9c86-f5692da627db',
            order=210,
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            break

def bonus_kuota_utama_15gb():
    delay = int(input("Enter delay in seconds: "))
    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
    while True:
        if not purchase_loop(
            family_code='8080ddcf-18c5-4d6d-86a4-89eb8ca5f2d1',
            order=52,
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            break

def bonus_kuota_utama_45gb():
    delay = int(input("Enter delay in seconds: "))
    pause_on_success = input("Aktifkan mode pause? (y/n): ").lower() == 'y'
    while True:
        if not purchase_loop(
            family_code='5412b964-474e-42d3-9c86-f5692da627db',
            order=64,
            use_decoy=True,
            delay=delay,
            pause_on_success=pause_on_success
        ):
            break

