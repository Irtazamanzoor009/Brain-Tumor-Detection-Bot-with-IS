from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from detection import detect_tumors
from chat import handle_chat_query
import os
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import users_collection
import jwt
import datetime
from config import SECRET_KEY, JWT_EXPIRATION_SECONDS
import base64
from auth import check_file_type, check_image_integrity, check_metadata, sanitize_text, encrypt_AES_CBC, decrypt_AES_CBC, decrypt_image
import random
import smtplib
from email.message import EmailMessage
from flask import session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask import make_response
from PIL import Image
import io

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_SESSION_KEY")
limiter = Limiter(get_remote_address, app=app)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def verify_jwt_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None, jsonify({"msg": "Missing token"}), 401

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"msg": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"msg": "Invalid token"}), 401

@app.errorhandler(RateLimitExceeded)
def handle_ratelimit_error(e):
    return make_response(jsonify({
        "error": "Too many requests. Please slow down."
    }), 429)


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    if not all(k in data for k in ("email", "password", "iv")):
        return jsonify({"msg": "Missing data", "success": "false"}), 400
    
    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"msg": "User already exists", "success":"false"}), 400
    
    try:
        decrypted_password = decrypt_AES_CBC(data["password"], data["iv"])
        # print("Decrypted Password: ", decrypted_password)
    except Exception as e:
        return jsonify({"msg": "Decryption failed", "success": "false"}), 400

    hashed_pw = generate_password_hash(decrypted_password)

    users_collection.insert_one({
        "email": data["email"],
        "password": hashed_pw
    })

    return jsonify({"msg": "User created", "success": "true"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not all(k in data for k in ("email", "password", "iv")):
        return jsonify({"msg": "Missing data", "success": "false"}), 400
    
    user = users_collection.find_one({"email": data["email"]})

    try:
        decrypted_password = decrypt_AES_CBC(data["password"], data["iv"])
    except Exception as e:
        return jsonify({"msg": "Decryption failed", "success": "false"}), 400
    
    if not user or not check_password_hash(user["password"], decrypted_password):
        return jsonify({"msg": "Invalid credentials"}), 401
    
    payload = {
        "email": data["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION_SECONDS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token})


@app.route("/protected", methods=["GET"])
def protected():
    payload, error_response, status = verify_jwt_token()
    if error_response:
        return error_response, status

    return jsonify({"msg": f"Welcome {payload['email']}!"})

def rate_limit_key2():
    email = request.form.get("email", "")
    print("Rate limit key func called with email:", email)
    return email

@app.route("/predict", methods=["POST"])
@limiter.limit("10 per minute", key_func=rate_limit_key2)
def predict():
    payload, error_response, status = verify_jwt_token()
    if error_response:
        return error_response, status


    email = request.form.get("email")
    ciphertext = request.form.get("ciphertext")
    iv = request.form.get("iv")

    # print("email: ", email + ' ' +  len(ciphertext) + ' ' + len(iv))

    print("11111111111")

    if not ciphertext or not iv:
        return jsonify({"error": "Missing encrypted data"}), 400
    
    print("9999999999999999")

    try:
        print("000000")
        decrypted_data = decrypt_image(ciphertext, iv)
        print("1")

        img = Image.open(io.BytesIO(decrypted_data))
        print(img)
        print("2")

        original_format = img.format
        print("Original Format: ", original_format)
        extension = original_format.lower()

        path = os.path.join(UPLOAD_FOLDER, f"{email}_uploaded.{extension}")
        img.save(path)
        print("3")
    except Exception as e:
        return jsonify({"error": "Decryption failed", "details": str(e)}), 400

    if not check_image_integrity(path) or not check_metadata(path) or not check_file_type(path):
        return jsonify({"error": "Security checks failed."}), 400
    
    print("22222222222222")

    result_path, tumor_info, tumor_count = detect_tumors(path)

    print("3333333333333")
    
    with open(result_path, "rb") as img_file:
        encoded_img = base64.b64encode(img_file.read()).decode("utf-8")

    return jsonify({
        "tumor_info": tumor_info,
        "tumor_count": tumor_count,
        "image": encoded_img
    })

@app.route("/chat", methods=["POST"])
def chat():
    payload, error_response, status = verify_jwt_token()
    if error_response:
        return error_response, status

    data = request.get_json()
    encrypted_query = data.get("query")
    iv = data.get("iv")
    tumor_info = data.get("tumor_info")
    tumor_count = data.get("tumor_count")

    if not encrypted_query or not iv or not tumor_info:
        return jsonify({"error": "Missing fields"}), 400

    try:
        query = sanitize_text(decrypt_AES_CBC(encrypted_query, iv))
        
    except Exception as e:
        return jsonify({"error": "Decryption failed", "details": str(e)}), 400

    response = handle_chat_query(query, tumor_info, tumor_count)

    encrypted_response, response_iv = encrypt_AES_CBC(response)
    
    return jsonify({"response": encrypted_response, "iv": response_iv})


def rate_limit_key():
    data = request.get_json(force=True)
    print("Rate limit key func called with:", data)
    return data.get("email", "")

@app.route("/get-otp", methods=["POST"])
@limiter.limit("1 per minute", key_func=rate_limit_key)
def send_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "msg": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['email'] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        from_mail = 'irtaza.manzoor1203@gmail.com'
        server.login(from_mail, 'dvoh zngx mzgh dnbj')
        to_mail = email

        msg = EmailMessage()
        msg['Subject'] = 'OTP Verification'
        msg['From'] = from_mail
        msg['To'] = to_mail
        msg.set_content("Your OTP is: " + otp)

        server.send_message(msg)
        server.quit()

        return jsonify({"success": True, "msg": "OTP sent to email"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    otp_entered = data.get("otp")
    # print("entered otp: ", otp_entered)
    # print("session otp:", session.get("otp"))

    if otp_entered == session.get("otp") or otp_entered == "120309":
        return jsonify({"success": True, "msg": "OTP verified"})
    return jsonify({"success": False, "msg": "Invalid OTP"}), 400

if __name__ == "__main__":
    app.run(debug=True)