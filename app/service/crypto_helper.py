import hashlib, hmac, base64
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

XDATA_KEY="5dccbf08920a5527b99e222789c34bb7"
AX_API_SIG_KEY="18b4d589826af50241177961590e6693"
X_API_BASE_SECRET="mU1Y4n1vBjf3M7tMnRkFU08mVyUJHed8B5En3EAniu1mXLixeuASmBmKnkyzVziOye7rG5nIekMdthensbQMcOJ6SLnrkGyfXALD7mrBC6vuWv6G01pmD3XlU5rT7Tzx"
ENCRYPTED_FIELD_KEY="5dccbf08920a5527"

def derive_iv(xtime_ms: int) -> bytes:
    sha = hashlib.sha256(str(xtime_ms).encode()).hexdigest()
    return sha[:16].encode()

def encrypt_xdata(plaintext: str, xtime_ms: int) -> str:
    iv = derive_iv(xtime_ms)
    key_bytes = XDATA_KEY.encode()
    
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    return urlsafe_b64encode(cipher.encrypt(pad(plaintext.encode(), 16, style="pkcs7"))).decode()

def decrypt_xdata(xdata: str, xtime_ms: int) -> str:
    iv = derive_iv(xtime_ms)
    key_bytes = XDATA_KEY.encode()
    
    ct = urlsafe_b64decode(xdata + "=" * ((4 - len(xdata) % 4) % 4))
    pt = AES.new(key_bytes, AES.MODE_CBC, iv).decrypt(ct)
    return unpad(pt, 16, style="pkcs7").decode()

def make_x_signature(
    id_token: str,
    method: str,
    path:str,
    sig_time_sec:int
) -> str:
    key_str = f"{X_API_BASE_SECRET};{id_token};{method};{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")
    
    msg = f"{id_token};{sig_time_sec};".encode("utf-8")
    
    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()

def make_x_signature_payment(
    access_token: str,
    sig_time_sec: int,
    package_code: str,
    token_payment: str,
    payment_method: str,
    payment_for: str,
    path: str,
) -> str:
    key_str = f"{X_API_BASE_SECRET};{sig_time_sec}#ae-hei_9Tee6he+Ik3Gais5=;POST;{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")

    msg = f"{access_token};{token_payment};{sig_time_sec};{payment_for};{payment_method};{package_code};".encode("utf-8")

    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()

def make_ax_api_signature(
    ts_for_sign: str,
    contact: str,
    code: str,
    contact_type: str
) -> str:
    key_bytes = AX_API_SIG_KEY.encode("ascii")
    
    preimage = f"{ts_for_sign}password{contact_type}{contact}{code}openid"
    digest = hmac.new(key_bytes, preimage.encode("utf-8"), hashlib.sha256).digest()
    b64res = base64.b64encode(digest).decode("ascii")
    return b64res

def make_x_signature_bounty(
    access_token: str,
    sig_time_sec: int,
    package_code: str,
    token_payment: str,
    ) -> str:
    path = "api/v8/personalization/bounties-exchange"

    key_str = f"{X_API_BASE_SECRET};{access_token};{sig_time_sec}#ae-hei_9Tee6he+Ik3Gais5=;POST;{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")

    msg = f"{access_token};{token_payment};{sig_time_sec};{package_code};".encode("utf-8")

    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()

def make_x_signature_loyalty(
    sig_time_sec: int,
    package_code: str,
    token_confirmation: str,
    path: str,
) -> str:
    key_str = f"{X_API_BASE_SECRET};{sig_time_sec}#ae-hei_9Tee6he+Ik3Gais5=;POST;{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")
    
    msg = f"{token_confirmation};{sig_time_sec};{package_code};".encode("utf-8")
    
    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()

def decrypt_circle_msisdn(encrypted_msisdn_b64: str) -> str:
    iv_ascii = encrypted_msisdn_b64[-16:]
    b64_part = encrypted_msisdn_b64[:-16]
    key = ENCRYPTED_FIELD_KEY.encode('ascii')
    iv = iv_ascii.encode('ascii')
    
    padding = len(b64_part) % 4
    if padding:
        b64_part += '=' * (4 - padding)
    try:
        ct = base64.urlsafe_b64decode(b64_part)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt_padded = cipher.decrypt(ct)
        pt = unpad(pt_padded, AES.block_size, style='pkcs7')
        return pt.decode('utf-8')
    except Exception as e:
        return ""

def encrypt_circle_msisdn(msisdn: str) -> str:
    key = ENCRYPTED_FIELD_KEY.encode('ascii')
    iv_ascii = os.urandom(8).hex()
    iv = iv_ascii.encode('ascii')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(msisdn.encode('utf-8'), AES.block_size))
    ct_b64 = base64.urlsafe_b64encode(ct).decode('ascii')
    return ct_b64 + iv_ascii

def make_x_signature_bounty_allotment(
    sig_time_sec: int,
    package_code: str,
    token_confirmation: str,
    path: str,
    destination_msisdn: str,
    ) -> str:    
    key_str = f"{X_API_BASE_SECRET};{sig_time_sec}#ae-hei_9Tee6he+Ik3Gais5=;{destination_msisdn};POST;{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")
    
    msg = f"{token_confirmation};{sig_time_sec};{destination_msisdn};{package_code};".encode("utf-8")
    
    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()

def make_x_signature_basic(
    method: str,
    path: str,
    sig_time_sec: int,
) -> str:
    key_str = f"{X_API_BASE_SECRET};{method};{path};{sig_time_sec}"
    key_bytes = key_str.encode("utf-8")

    msg = f"{sig_time_sec};en;".encode("utf-8")

    return hmac.new(key_bytes, msg, hashlib.sha512).hexdigest()
