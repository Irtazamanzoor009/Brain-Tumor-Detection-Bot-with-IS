from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile
import magic
import re
import bleach
from Crypto.Cipher import AES
import base64
import json
from base64 import b64decode
from Crypto.Util.Padding import unpad
import os

from dotenv import load_dotenv
load_dotenv()

def sanitize_text(text):
    clean = bleach.clean(text, tags=[], attributes={}, strip=True)
    clean = re.sub(r"[^\w\s.,!?@\-]", "", clean)
    return clean

def check_image_integrity(image_path):
    try:
        with open(image_path, "rb") as img_file:
            img = Image.open(img_file)
            img.verify()  # Verify the image integrity
        return True
    except Exception as e:
        print(f"Image Integrity Check Failed: {e}")
        return False

def check_metadata(image_path):
    try:
        with open(image_path, "rb") as img_file:
            img = Image.open(img_file)
            if isinstance(img, JpegImageFile):
                img.info.pop("exif", None)  # Remove EXIF data
        return True
    except Exception as e:
        print(f"Error removing metadata: {e}")
        return False

def check_file_type(image_path):
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(image_path)
        print(f"File type: {file_type}")
        if "image" in file_type:
            print("Valid image format")
            return True
        else:
            print("File is not a valid image")
            return False
    except Exception as e:
        print(f"Error checking file type: {e}")
        return False
 
SECRET_KEY = os.getenv("SECRET_KEY") 
if SECRET_KEY is None:
    raise ValueError("SECRET_KEY not set in .env")
SECRET_KEY = SECRET_KEY.encode()

def pad_pkcs7(data: str) -> bytes:
    pad_len = 16 - len(data.encode('utf-8')) % 16
    padding = chr(pad_len) * pad_len
    return (data + padding).encode('utf-8')

def encrypt_AES_CBC(plaintext):
    iv = AES.get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    padded_text = pad_pkcs7(plaintext)
    ciphertext = cipher.encrypt(padded_text)
    return base64.b64encode(ciphertext).decode("utf-8"), base64.b64encode(iv).decode("utf-8")

def decrypt_AES_CBC(ciphertext_b64, iv_b64):
    iv = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)
    
    padding_len = decrypted[-1]
    return decrypted[:-padding_len].decode("utf-8")

def decrypt_image(ciphertext_b64, iv_b64):
    try:
        print("IV:", iv_b64[:10], "Ciphertext:", ciphertext_b64[:10])
        ciphertext = base64.b64decode(ciphertext_b64)
        iv = base64.b64decode(iv_b64)

        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)

        unpadded = unpad(decrypted, AES.block_size)
        image_data = base64.b64decode(unpadded)

        return image_data
    except Exception as e:
        print("Decryption error:", str(e))
        raise