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
    
@app.get("/symbol-info/{symbol}")
def symbol_info(symbol: str):
    """
    Devuelve información del símbolo desde Bybit Demo (o mainnet según tu API)
    """
    try:
        # Eliminamos ".P" si viene desde TV
        symbol_clean = symbol.replace(".P", "")
        
        # Usamos el endpoint de símbolos
        response = session.get_instruments(category="linear", symbol=symbol_clean)
        
        # Revisamos si hay resultado
        if "result" in response and "list" in response["result"] and response["result"]["list"]:
            info = response["result"]["list"][0]
            return {
                "symbol": info["name"],
                "baseCurrency": info["baseCurrency"],
                "quoteCurrency": info["quoteCurrency"],
                "minOrderQty": info["lotSizeFilter"]["minOrderQty"],
                "maxOrderQty": info["lotSizeFilter"]["maxOrderQty"],
                "qtyPrecision": info["lotSizeFilter"]["qtyPrecision"],
                "pricePrecision": info["priceFilter"]["tickSize"]
            }
        else:
            return {"error": "Símbolo no encontrado"}
    except Exception as e:
        return {"error": str(e)}


