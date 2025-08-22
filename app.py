from fastapi import FastAPI
from pybit.unified_trading import HTTP

app = FastAPI()

session = HTTP(
    demo=True,
    api_key="TU_API_KEY",
    api_secret="TU_API_SECRET",
)

@app.get("/test-balance")
def test_balance():
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": str(e)}
