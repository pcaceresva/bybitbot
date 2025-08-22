# app.py
from fastapi import FastAPI
from pybit.unified_trading import HTTP

app = FastAPI()

# Inicializa sesión Demo de Bybit Unified Trading
session = HTTP(
    demo=True,
    api_key="kAEstgmtlzcLtBUC9D",
    api_secret="Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG",
)

@app.get("/test-balance")
def test_balance():
    try:
        balance = session.get_wallet_balance(category="spot")
        return balance
    except Exception as e:
        return {"error": str(e)}
