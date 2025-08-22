from fastapi import FastAPI, Request
import os
from pybit.unified_trading import HTTP

app = FastAPI()

# Variables de entorno
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Inicializamos sesión de Unified Demo
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True
)

# Configuración de trading
RISK_PERCENT = 0.10       # 10% del saldo
TP_PERCENT = 0.005        # 0.5%
SL_PERCENT = 0.005        # 0.5%
LEVERAGE = 10

@app.get("/demo-balance")
def get_demo_balance():
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": str(e)}

def execute_trade(symbol: str, side: str):
    # Precio de mercado real
    ticker = session.get_tickers(symbol=symbol)
    price = float(ticker["result"]["list"][0]["lastPrice"])

    # Obtenemos saldo
    wallet = session.get_wallet_balance(accountType="UNIFIED")
    total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

    # Calculamos tamaño de la posición usando 10% del saldo
    position_value = total_balance * RISK_PERCENT * LEVERAGE
    qty = round(position_value / price, 6)

    # TP y SL
    if side.upper() == "LONG":
        tp_price = price * (1 + TP_PERCENT)
        sl_price = price * (1 - SL_PERCENT)
    else:
        tp_price = price * (1 - TP_PERCENT)
        sl_price = price * (1 + SL_PERCENT)

    # Ejecutamos orden de mercado
    order = session.place_order(
        category="linear",
        symbol=symbol,
        side="Buy" if side.upper() == "LONG" else "Sell",
        orderType="Market",
        qty=str(qty),
        leverage=LEVERAGE,
        takeProfit=str(round(tp_price, 2)),
        stopLoss=str(round(sl_price, 2))
    )
    return order

@app.get("/test-order")
def test_order():
    """
    Ejecuta un trade de prueba rápido a precio de mercado
    """
    symbol = "BTCUSDT"
    side = "LONG"
    try:
        order = execute_trade(symbol, side)
        return {"status": "success", "order": order}
    except Exception as e:
        return {"error": str(e)}

