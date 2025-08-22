from fastapi import FastAPI, Request
import os
from pybit.unified_trading import HTTP
import requests
import math
import json
import logging

logging.basicConfig(level=logging.INFO)

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

@app.get("/ping")
def ping():
    """
    Endpoint para mantener activo el servicio
    """
    return {"status": "ok"}

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
    Ajusta automáticamente la cantidad según los decimales y mínimo permitido del símbolo.
    """
    try:
        # --- 1. Obtener información del símbolo ---
        url_symbols = "https://api-demo.bybit.com/v5/market/symbols?category=linear"
        r = requests.get(url_symbols)
        symbols_data = r.json()

        symbol_info = next((s for s in symbols_data["result"]["list"] if s["name"] == symbol), None)
        if not symbol_info:
            return {"error": f"Símbolo {symbol} no encontrado en Bybit Demo"}

        min_qty = float(symbol_info["minOrderQty"])
        qty_precision = int(symbol_info["qtyPrecision"])

        # --- 2. Obtener precio de mercado ---
        url_ticker = f"https://api-demo.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
        r = requests.get(url_ticker)
        ticker_data = r.json()
        price = float(ticker_data["result"]["list"][0]["lastPrice"])

        # --- 3. Obtener saldo ---
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # --- 4. Calcular cantidad ---
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        qty = round(position_value / price, qty_precision)
        qty = max(qty, min_qty)  # Asegura que sea >= mínimo permitido

        # --- 5. Calcular TP y SL ---
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        # --- 6. Debug ---
        logging.info(f"Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")
        # --- 7. Ejecutar orden ---
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

import json

import json

@app.post("/webhook")
async def webhook(request: Request):
    # Leemos el body como texto plano
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8").strip()  # Limpiamos saltos de línea
    try:
        data = json.loads(body_text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON inválido: {str(e)}", "raw": body_text}

    symbol = data.get("symbol", "").replace(".P", "")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Faltan datos en la alerta"}

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    symbol = "USELESSUSDT"  # Cambia al token que quieras probar
    side = "LONG"  # o "SHORT"
    return execute_trade(symbol, side)






