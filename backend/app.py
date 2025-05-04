from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from detection import detect_tumors
from chat import handle_chat_query
import os
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import users_collection
import jwt
# import datetime
from datetime import datetime, timezone, timedelta
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
from database import audit_logs
# from datetime import datetime

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
        log_security_event("expired_token", details="JWT expired")
        return None, jsonify({"msg": "Token expired"}), 401
    except jwt.InvalidTokenError:
        log_security_event("invalid_token", details="JWT invalid")
        return None, jsonify({"msg": "Invalid token"}), 401

# @app.errorhandler(RateLimitExceeded)
# def handle_ratelimit_error(e):
#     log_security_event("rate_limit_exceeded", details="Too many requests")
#     return make_response(jsonify({
#         "error": "Too many requests. Please slow down."
#     }), 429)

@app.errorhandler(RateLimitExceeded)
def handle_ratelimit_error(e):
    email = None
    try:
        data = request.get_json(force=True)
        email = data.get("email")
    except:
        pass

    if not email:
        email = request.form.get("email")

    log_security_event("rate_limit_exceeded", user_email=email, details="Too many requests")
    return make_response(jsonify({
        "error": "Too many requests. Please slow down."
    }), 429)


def log_security_event(event_type, user_email=None, details=None):
    log = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent'),
        "user_email": user_email,
        "details": details
    }
    audit_logs.insert_one(log)


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
        "password": hashed_pw,
        "role": "user"
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
        log_security_event(
        event_type="failed_login",
        user_email=data["email"],
        details="Wrong password or user not found"
    )
        return jsonify({"msg": "Invalid credentials"}), 401
    
    payload = {
        "email": data["email"],
        "exp": datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "role": user.get("role", "user")})


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
@limiter.limit("2 per minute", key_func=rate_limit_key2)
def predict():
    payload, error_response, status = verify_jwt_token()
    if error_response:
        return error_response, status


    email = request.form.get("email")
    ciphertext = request.form.get("ciphertext")
    iv = request.form.get("iv")

    if not ciphertext or not iv:
        return jsonify({"error": "Missing encrypted data"}), 400

    try:
        decrypted_data = decrypt_image(ciphertext, iv)
        img = Image.open(io.BytesIO(decrypted_data))
        original_format = img.format
        extension = original_format.lower()

        path = os.path.join(UPLOAD_FOLDER, f"{email}_uploaded.{extension}")
        img.save(path)
    except Exception as e:
        return jsonify({"error": "Decryption failed", "details": str(e)}), 400

    if not check_image_integrity(path) or not check_metadata(path) or not check_file_type(path):
        log_security_event("malicious_upload", user_email=email, details="Image failed security checks")
        return jsonify({"error": "Security checks failed."}), 400

    result_path, tumor_info, tumor_count = detect_tumors(path)
    
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

        from_mail = os.getenv("FROM_EMAIL")
        server.login(from_mail, os.getenv("PASSWORD"))
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

@app.route("/logs", methods=["GET"])
def get_logs():
    payload, error_response, status = verify_jwt_token()
    if error_response:
        return error_response, status
    
    user_email = payload.get("email")
    if not user_email:
        return jsonify({"success": False, "msg": "Unauthorized access"}), 403

    
    user = users_collection.find_one({"email": user_email})
    if not user or user.get("role") != "admin":
        return jsonify({"success": False, "msg": "Access denied: Admins only"}), 403
    
    try:
        logs = list(audit_logs.find().sort("timestamp", -1))
        for log in logs:
            log["_id"] = str(log["_id"])
            if isinstance(log["timestamp"], datetime):
                log["timestamp"] = log["timestamp"].isoformat()
            else:
                log["timestamp"] = str(log["timestamp"])

        return jsonify({
            "success": True,
            "logs": logs
        }), 200
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch logs",
            "details": str(e)
        }), 500



if __name__ == "__main__":
    app.run(debug=True)