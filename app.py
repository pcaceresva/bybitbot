from fastapi import FastAPI
import requests
import time
import hmac
import hashlib

app = FastAPI()

# --- Configura tus claves API de Demo aquí ---
API_KEY = "kAEstgmtlzcLtBUC9D"
API_SECRET = "Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG"
BASE_URL = "https://api-demo.bybit.com"

# --- Función para generar firma ---
def generate_signature(secret, params):
    """
    Genera firma HMAC SHA256 para Bybit v5
    """
    param_str = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    return hmac.new(secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()

@app.get("/test-balance")
def test_balance():
    timestamp = int(time.time() * 1000)
    
    # Parámetros requeridos
    params = {
        "accountType": "UNIFIED",
        "timestamp": timestamp,
        "recvWindow": 5000
    }

    # Generar la firma
    signature = generate_signature(API_SECRET, params)
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": "5000"
    }

    url = f"{BASE_URL}/v5/account/wallet-balance"

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

