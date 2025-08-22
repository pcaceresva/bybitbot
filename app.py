from fastapi import FastAPI, Request
import os
from pybit.unified_trading import HTTP
import math
import requests

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
    Ejecuta un trade usando precio de mercado en Demo Unified.
    """
    try:
        # Obtenemos precio de mercado
        ticker = session.get_tickers(category="linear", symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        qty = max(round(position_value / price, 3), 0.001)  # Ajusta decimales según el par

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        # Log para debugging
        print(f"Ejecutando trade → Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")

        # Ejecutamos la orden
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

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recibe alertas de TradingView en formato JSON:
    {
        "symbol": "BTCUSDT",
        "side": "LONG" or "SHORT"
    }
    """
    try:
        data = await request.json()
    except Exception as e:
        return {"error": f"JSON inválido: {str(e)}"}

    symbol = data.get("symbol")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Faltan datos en la alerta"}

    # Elimina el .P si tu ticker de TV lo incluye
    symbol = symbol.replace(".P", "")

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    symbol = "BTCUSDT"  # Cambia a un par válido en tu Demo Unified
    side = "LONG"        # o "SHORT"
    return execute_trade(symbol, side)

@app.get("/ping")
def ping():
    """
    Endpoint para mantener activo el webservice
    """
    return {"status": "alive"}

@app.get("/test-symbol")
def test_symbol(symbol: str = "BTCUSDT"):
    """
    Consulta información de un símbolo en Demo Unified.
    Devuelve precio actual, cantidad mínima y decimales permitidos.
    """
    try:
        # Obtenemos el ticker
        ticker = session.get_tickers(category="linear", symbol=symbol)
        last_price = float(ticker["result"]["list"][0]["lastPrice"])
        
        # Obtenemos info del símbolo
        info = session.get_symbol_info(category="linear", symbol=symbol)
        info_data = info["result"]["list"][0]

        min_qty = float(info_data["lotSizeFilter"]["minTrdQty"])
        qty_step = float(info_data["lotSizeFilter"]["qtyStep"])
        price_step = float(info_data["priceFilter"]["tickSize"])

        return {
            "symbol": symbol,
            "last_price": last_price,
            "min_qty": min_qty,
            "qty_step": qty_step,
            "price_step": price_step
        }

    except Exception as e:
        return {"error": f"Error al consultar la API: {str(e)}"}
