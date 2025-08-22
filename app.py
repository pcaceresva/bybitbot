from fastapi import FastAPI, Request
import os
from pybit.unified_trading import HTTP
import math

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

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recibe alertas de TradingView en formato JSON:
    {
        "symbol": "BTCUSDT",
        "side": "LONG" or "SHORT",
        "price": 29000
    }
    """
    data = await request.json()
    
    symbol = data.get("symbol")
    side = data.get("side")
    price = float(data.get("price"))

    if not symbol or not side or not price:
        return {"error": "Faltan datos en la alerta"}

    return execute_trade(symbol, side, price)

@app.get("/test_order")
def test_order():
    symbol = "BTCUSDT.P"  # símbolo real en Demo Unified
    side = "LONG"
    
    try:
        # Obtenemos precio de mercado
        market_price = float(session.get_mark_price(symbol=symbol)["result"]["markPrice"])
        return execute_trade(symbol, side, market_price)
    except Exception as e:
        return {"error": str(e)}


def execute_trade(symbol: str, side: str, price: float):
    """
    Lógica para calcular cantidad, TP, SL y enviar orden
    """
    try:
        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición usando 10% del saldo
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        qty = round(position_value / price, 6)  # Ajustar decimales según el par

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:  # SHORT
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        # Enviamos orden de mercado
        order = session.place_order(
            category="linear",       # Perpetuo USDT-M
            symbol=symbol,
            side=order_side,
            orderType="Market",
            qty=str(qty),
            leverage=LEVERAGE,
            takeProfit=str(round(tp_price, 2)),
            stopLoss=str(round(sl_price, 2))
        )
        return {"status": "success", "order": order}
    except Exception as e:
        return {"error": str(e)}

