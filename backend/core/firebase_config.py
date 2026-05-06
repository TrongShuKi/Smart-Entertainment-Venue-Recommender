import toml
import firebase_admin
from firebase_admin import credentials, firestore
import os

secret_path = ".streamlit/secrets.toml"
if not os.path.exists(secret_path):
    secret_path = "../.streamlit/secrets.toml"

with open(secret_path, "r", encoding="utf-8") as f:
    config = toml.load(f)

FIREBASE_CLIENT_CFG = config["firebase_client"]
FIREBASE_API_KEY = FIREBASE_CLIENT_CFG["apiKey"]
GOOGLE_CONFIG = config["google-login"]

def init_firebase_admin():
    if not firebase_admin._apps:
        cred_dict = dict(config["firebase_admin"])
        
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

def get_firestore():
    init_firebase_admin()
    return firestore.client()

db = get_firestore()