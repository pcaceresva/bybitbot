from fastapi import FastAPI, Request
from pybit.unified_trading import HTTP
import time

app = FastAPI()

API_KEY = "kAEstgmtlzcLtBUC9D"
API_SECRET = "Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG"

# Sesión de demo Unified
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True
)

@app.get("/demo-balance")
def get_demo_balance():
    return session.get_wallet_balance(accountType="UNIFIED")

@app.post("/alert")
async def alert(request: Request):
    """
    Endpoint para recibir alertas de TradingView.
    Espera JSON con:
    {
        "symbol": "BTCUSDT",
        "signal": "LONG"  # o "SHORT"
    }
    """
    data = await request.json()
    symbol = data.get("symbol")
    signal = data.get("signal")

    # Obtener saldo disponible
    balance_data = session.get_wallet_balance(accountType="UNIFIED")
    usdt_balance = float(balance_data['result']['list'][0]['coin'][0]['walletBalance'])
    
    # Usar 10% del saldo
    qty_usdt = usdt_balance * 0.10

    # Parámetros TP y SL
    tp_percent = 0.005  # 0.5%
    sl_percent = 0.005  # 0.5%
    leverage = 10

    # Precio actual de mercado
    market_price = float(session.get_mark_price(symbol=symbol)['result']['markPrice'])

    # Calcular TP y SL según LONG o SHORT
    if signal.upper() == "LONG":
        side = "Buy"
        tp_price = market_price * (1 + tp_percent)
        sl_price = market_price * (1 - sl_percent)
    elif signal.upper() == "SHORT":
        side = "Sell"
        tp_price = market_price * (1 - tp_percent)
        sl_price = market_price * (1 + sl_percent)
    else:
        return {"error": "Signal debe ser LONG o SHORT"}

    # Colocar orden de mercado con apalancamiento
    order = session.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        orderType="Market",
        qty=str(qty_usdt),
        leverage=leverage,
        timeInForce="ImmediateOrCancel",
        takeProfit=str(tp_price),
        stopLoss=str(sl_price)
    )

    return {
        "signal": signal,
        "symbol": symbol,
        "order": order
    }
