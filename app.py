from fastapi import FastAPI, Request
import requests, hmac, hashlib, time, os

app = FastAPI()

# Parámetros de riesgo
TP_PERCENT = 0.5
SL_PERCENT = 0.5
LEVERAGE = 10
TRADE_RISK_PERCENT = 2.0  # 2% de tu capital

# API Bybit
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE_URL = "https://api.bybit.com"  # Cuenta real

def sign(params, secret):
    qs = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

def get_trade_qty():
    # Consulta balance disponible
    r = requests.get(BASE_URL + "/v2/private/wallet/balance", params={
        "api_key": API_KEY,
        "timestamp": int(time.time() * 1000)
    })
    r.raise_for_status()
    balance = float(r.json()["result"]["USDT"]["available_balance"])
    
    # Calcula 2% del capital × apalancamiento
    trade_amount = balance * (TRADE_RISK_PERCENT / 100) * LEVERAGE
    return round(trade_amount, 2)  # ajusta según pares

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    symbol = data["symbol"]
    side = data["side"]  # 'Buy' o 'Sell'

    qty = get_trade_qty()

    # Precio actual
    r = requests.get(BASE_URL + "/v2/public/tickers", params={"symbol": symbol})
    last_price = float(r.json()["result"][0]["last_price"])

    # Calcula TP y SL
    if side == "Buy":
        tp_price = last_price * (1 + TP_PERCENT/100)
        sl_price = last_price * (1 - SL_PERCENT/100)
    else:
        tp_price = last_price * (1 - TP_PERCENT/100)
        sl_price = last_price * (1 + SL_PERCENT/100)

    # Orden de entrada
    order = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": side,
        "order_type": "Market",
        "qty": qty,
        "time_in_force": "GoodTillCancel",
        "reduce_only": False,
        "close_on_trigger": False,
        "timestamp": int(time.time() * 1000)
    }
    order["sign"] = sign(order, API_SECRET)
    entry_res = requests.post(BASE_URL + "/v2/private/order/create", data=order)

    # Orden TP
    tp = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": "Sell" if side == "Buy" else "Buy",
        "order_type": "Limit",
        "qty": qty,
        "price": round(tp_price, 2),
        "time_in_force": "GoodTillCancel",
        "reduce_only": True,
        "timestamp": int(time.time() * 1000)
    }
    tp["sign"] = sign(tp, API_SECRET)
    tp_res = requests.post(BASE_URL + "/v2/private/order/create", data=tp)

    # Orden SL
    sl = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": "Sell" if side == "Buy" else "Buy",
        "order_type": "StopMarket",
        "qty": qty,
        "stop_px": round(sl_price, 2),
        "base_price": round(last_price, 2),
        "time_in_force": "GoodTillCancel",
        "reduce_only": True,
        "timestamp": int(time.time() * 1000)
    }
    sl["sign"] = sign(sl, API_SECRET)
    sl_res = requests.post(BASE_URL + "/v2/private/stop-order/create", data=sl)

    return {
        "entry": entry_res.json(),
        "tp": tp_res.json(),
        "sl": sl_res.json()
    }
