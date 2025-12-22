import os
import hashlib
import requests
import base64
import json
import time

from random import randint
from datetime import datetime, timezone, timedelta

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from dataclasses import dataclass

from app.service.crypto_helper import (
    encrypt_xdata,
    make_x_signature,
    make_x_signature_payment,
    make_ax_api_signature,
    make_x_signature_bounty,
    make_x_signature_loyalty,
    make_x_signature_bounty_allotment,
)

from app.service.crypto_helper import decrypt_xdata as dec_xdata
from app.service.crypto_helper import encrypt_circle_msisdn as encrypt_msisdn
from app.service.crypto_helper import decrypt_circle_msisdn as decrypt_msisdn

API_KEY = "vT8tINqHaOxXbGE7eOWAhA=="
AES_KEY_ASCII = ""
AX_FP_KEY = "18b4d589826af50241177961590e6693"
ENCRYPTED_FIELD_KEY="5dccbf08920a5527"
@dataclass
class DeviceInfo:
    manufacturer: str
    model: str
    lang: str
    resolution: str       # "WxH"
    tz_short: str         # "GMT07:00"
    ip: str
    font_scale: float     # 1.0
    android_release: str  # "13"
    msisdn: str
    
def build_fingerprint_plain(dev: DeviceInfo) -> str:
    return (
        f"{dev.manufacturer}|{dev.model}|{dev.lang}|{dev.resolution}|"
        f"{dev.tz_short}|{dev.ip}|{dev.font_scale}|Android {dev.android_release}|{dev.msisdn}"
    )

def ax_fingerprint(dev: DeviceInfo, secret_key_32hex_ascii: str) -> str:
    key = secret_key_32hex_ascii.encode("ascii")
    iv  = b"\x00" * 16
    pt  = build_fingerprint_plain(dev).encode("utf-8")
    ct  = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(pt, 16))
    return base64.b64encode(ct).decode("ascii")

def load_ax_fp() -> str:
    fp_path = "ax.fp"
    if os.path.exists(fp_path):
        with open(fp_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content
    
    # Generate new if not found/empty
    dev = DeviceInfo(
        manufacturer="samsung" + str(randint(1000, 9999)),
        model="SM-N93" + str(randint(1000, 9999)),
        lang="en",
        resolution="720x1540",
        tz_short="GMT07:00",
        ip="192.169.69.69",
        font_scale=1.0,
        android_release="13",
        msisdn="6281398370564"
    )
    
    new_fp = ax_fingerprint(dev, AX_FP_KEY)
    with open(fp_path, "w", encoding="utf-8") as f:
        f.write(new_fp)
    return new_fp
    

def random_iv_hex16() -> str:
    return os.urandom(8).hex()

def b64(data: bytes, urlsafe: bool) -> str:
    enc = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    return enc(data).decode("ascii")


def build_encrypted_field(iv_hex16: str | None = None, urlsafe_b64: bool = False) -> str:
    key = ENCRYPTED_FIELD_KEY.encode("ascii")
    iv_hex = iv_hex16 or random_iv_hex16()
    iv = iv_hex.encode("ascii") 

    pt = pad(b"", AES.block_size)
    ct = AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pt)

    return b64(ct, urlsafe_b64) + iv_hex

def java_like_timestamp(now: datetime) -> str:
    ms2 = f"{int(now.microsecond/10000):02d}"
    tz = now.strftime("%z"); tz_colon = tz[:-2] + ":" + tz[-2:] if tz else "+00:00"
    return now.strftime(f"%Y-%m-%dT%H:%M:%S.{ms2}") + tz_colon

def ts_gmt7_without_colon(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
    else:
        dt = dt.astimezone(timezone(timedelta(hours=7)))
    millis = f"{int(dt.microsecond / 1000):03d}"
    tz = dt.strftime("%z")
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{millis}") + tz

def ax_api_signature(
        api_key: str,
        ts_for_sign: str,
        contact: str,
        code: str,
        contact_type: str
    ) -> str:
    return make_ax_api_signature(ts_for_sign, contact, code, contact_type)
    
def encryptsign_xdata(
        api_key: str,
        method: str,
        path: str,
        id_token: str,
        payload: dict
) -> str:
    plain_body = json.dumps(payload, separators=(",", ":"))
    
    xtime = int(time.time() * 1000)
    xdata = encrypt_xdata(plain_body, xtime)

    sig_time_sec = xtime // 1000
    x_sig = make_x_signature(
        id_token, method, path, sig_time_sec
    )

    return {"x_signature": x_sig, "encrypted_body": {"xdata": xdata, "xtime": xtime}}

    
def decrypt_xdata(
    api_key: str,
    encrypted_payload: dict
    ) -> dict:
    if not isinstance(encrypted_payload, dict) or "xdata" not in encrypted_payload or "xtime" not in encrypted_payload:
        raise ValueError("Invalid encrypted data format. Expected a dictionary with 'xdata' and 'xtime' keys.")
    
    plaintext = dec_xdata(encrypted_payload["xdata"], int(encrypted_payload["xtime"]))

    return json.loads(plaintext)

def get_x_signature_payment(
        api_key: str,
        access_token: str,
        sig_time_sec: int,
        package_code: str,
        token_payment: str,
        payment_method: str,
        payment_for: str,
        path: str,
    ) -> str:
    
    return make_x_signature_payment(
        access_token,
        sig_time_sec,
        package_code,
        token_payment,
        payment_method,
        payment_for,
        path,
    )
    
def get_x_signature_bounty(
        api_key: str,
        access_token: str,
        sig_time_sec: int,
        package_code: str,
        token_payment: str
    ) -> str:
    return make_x_signature_bounty(
        access_token,
        sig_time_sec,
        package_code,
        token_payment,
    )

def get_x_signature_bounty_allotment(
        api_key: str,
        sig_time_sec: int,
        package_code: str,
        token_confirmation: str,
        destination_msisdn: str,
        path: str
    ) -> str:
    return make_x_signature_bounty_allotment(
        sig_time_sec,
        package_code,
        token_confirmation,
        path,
        destination_msisdn,
    )

def ax_device_id() -> str:
    android_id = load_ax_fp() # Actually just b*llsh*tting
    return hashlib.md5(android_id.encode("utf-8")).hexdigest()

def get_x_signature_loyalty(
        api_key: str,
        sig_time_sec: int,
        package_code: str,
        token_confirmation: str,
        path: str
    ) -> str:
    return make_x_signature_loyalty(
        sig_time_sec,
        package_code,
        token_confirmation,
        path,
    )
    
def encrypt_circle_msisdn(
        api_key: str,
        msisdn: str
    ) -> str:
    return encrypt_msisdn(msisdn)

def decrypt_circle_msisdn(
        api_key: str,
        encrypted_msisdn_b64: str
    ) -> str:
    return decrypt_msisdn(encrypted_msisdn_b64)