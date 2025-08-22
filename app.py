from fastapi import FastAPI
import requests
import time
import hmac
import hashlib

app = FastAPI()

API_KEY = "kAEstgmtlzcLtBUC9D"
API_SECRET = "Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG"
BASE_URL = "https://api-demo.bybit.com"

def generate_signature(secret, method, path, expires, query_string=""):
    """
    Genera la firma HMAC_SHA256 para Bybit v5 Demo Unified
    """
    origin = f"{method}{path}{expires}{query_string}"
    return hmac.new(secret.encode(), origin.encode(), hashlib.sha256).hexdigest()

@app.get("/demo-balance")
def get_demo_balance():
    path = "/v5/account/wallet-balance"
    method = "GET"
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"

    # Query string exacta
    query_string = f"accountType=UNIFIED&recvWindow={recv_window}&timestamp={timestamp}"

    # Firma
    signature = generate_signature(API_SECRET, method, path, timestamp, query_string)

    # Headers
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window
    }

    url = f"{BASE_URL}{path}?{query_string}"

    r = requests.get(url, headers=headers)

    try:
        return r.json()
    except Exception as e:
        return {"error": "No se pudo decodificar JSON", "raw_text": r.text, "exception": str(e)}
