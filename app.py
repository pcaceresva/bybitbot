from fastapi import FastAPI
from pybit.unified_trading import HTTP

app = FastAPI()

# Configura tus credenciales demo de Bybit Unified
API_KEY = "kAEstgmtlzcLtBUC9D"
API_SECRET = "Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG"

# Creamos la sesión con demo=True
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True
)

@app.get("/demo-balance")
def get_demo_balance():
    """
    Devuelve el saldo de la cuenta demo Unified.
    """
    try:
        # Obtenemos el balance
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": "No se pudo obtener el saldo", "exception": str(e)}
