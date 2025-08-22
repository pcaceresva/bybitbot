from fastapi import FastAPI, Request
import os
import requests
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

def execute_trade(symbol: str, side: str):
    """
    Ejecuta un trade usando precio de mercado en Demo Unified,
    ajustando cantidad mínima y decimales según la información disponible.
    """
    try:
        # Intentamos obtener el precio de mercado
        ticker = session.get_tickers(category="linear", symbol=symbol)
        last_price = ticker["result"]["list"][0].get("lastPrice")
        price = float(last_price) if last_price else 1.0  # fallback a 1 si es null

        # Información de cantidad y decimales
        symbol_info = session.get_symbol_info(category="linear", symbol=symbol)
        qty_step = float(symbol_info["result"]["list"][0].get("qtyStep", 0.001))
        min_qty = float(symbol_info["result"]["list"][0].get("minOrderQty", qty_step))

        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        qty = max(round(position_value / price / qty_step) * qty_step, min_qty)

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        print(f"Ejecutando trade → Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")

        # Ejecutamos la orden
        order = session.place_order(
            category="linear",
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

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recibe alertas de TradingView en formato JSON:
    {
        "symbol": "USELESSUSDT",
        "side": "LONG" or "SHORT"
    }
    """
    data = await request.json()
    symbol = data.get("symbol").replace(".P", "")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Faltan datos en la alerta"}

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    symbol = "USELESSUSDT"
    side = "LONG"  # o "SHORT"
    return execute_trade(symbol, side)

@app.get("/test-symbol")
def test_symbol(symbol: str = "USELESSUSDT"):
    """
    Consulta información del símbolo demo mediante API REST directa
    """
    try:
        url = f"https://api.bybit.com/v5/market/instruments-info?category=linear&symbol={symbol}"
        resp = requests.get(url)
        if resp.status_code != 200:
            return {"error": f"Error al consultar la API: {resp.status_code}"}
        data = resp.json()
        # Devolver solo lo relevante
        info = data.get("result", {}).get("list", [{}])[0]
        return {
            "symbol": info.get("symbol"),
            "lastPrice": info.get("lastPrice"),
            "minOrderQty": info.get("minOrderQty"),
            "maxOrderQty": info.get("maxOrderQty"),
            "qtyStep": info.get("qtyStep"),
            "priceScale": info.get("priceScale")
        }
    except Exception as e:
        return {"error": str(e)}


