import time
import uuid
import hashlib


# ==========================================================
# IDEMPOTENCY KEY
# ==========================================================
def generate_idempotency_key(symbol, side, qty, strategy_id, bucket):
    raw = f"{symbol}:{side}:{qty}:{strategy_id}:{bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ==========================================================
# BINANCE GATEWAY
# ==========================================================
class BinanceGateway:
    def __init__(self, client):
        self.client = client

    def place_order(self, symbol, side, qty, leverage=20, idempotency_key=None):
        self.client.futures_change_leverage(
            symbol=symbol,
            leverage=min(leverage, 20)
        )

        return self.client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
            newClientOrderId=idempotency_key
        )

    def query_order(self, symbol, order_id):
        try:
            return self.client.futures_get_order(symbol=symbol, orderId=order_id)
        except:
            return None

    def query_position(self, symbol):
        positions = self.client.futures_position_information(symbol=symbol)
        return positions[0] if positions else None

    def close_position(self, symbol):
        pos = self.query_position(symbol)
        if not pos:
            return None

        qty = abs(float(pos["positionAmt"]))
        if qty == 0:
            return None

        side = "SELL" if float(pos["positionAmt"]) > 0 else "BUY"

        return self.client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty
        )


# ==========================================================
# EXECUTION COORDINATOR
# ==========================================================
class ExecutionCoordinator:
    def __init__(self, risk_engine, gateway, store, verifier, lock):
        self.risk = risk_engine
        self.gateway = gateway
        self.store = store
        self.verifier = verifier
        self.lock = lock

    def execute_signal(self, signal):
        if self.store.get("system_status") in ["STOP", "EMERGENCY"]:
            raise Exception("SYSTEM HALTED")

        with self.lock.acquire(signal["portfolio_id"]):

            if not self.risk.validate_new_position(signal):
                return None

            trade_id = f"BOT_{uuid.uuid4().hex[:16]}"

            key = generate_idempotency_key(
                signal["symbol"],
                signal["side"],
                signal["qty"],
                signal["strategy_id"],
                int(time.time() // 60)
            )

            resp = self.gateway.place_order(
                symbol=signal["symbol"],
                side=signal["side"],
                qty=signal["qty"],
                leverage=signal.get("leverage", 20),
                idempotency_key=key
            )

            self.store.save({
                "trade_id": trade_id,
                "order_id": resp["orderId"],
                "symbol": signal["symbol"],
                "status": "OPEN",
                "ts": time.time()
            })

            return self.verifier.verify_order(
                trade_id,
                signal["symbol"],
                resp["orderId"]
            )


# ==========================================================
# LIVE SYNC ENGINE
# ==========================================================
class LiveSyncEngine:
    def __init__(self, gateway, store):
        self.gateway = gateway
        self.store = store

    def sync(self):
        for trade in self.store.get_active_trades():

            order = self.gateway.query_order(
                trade["symbol"],
                trade["order_id"]
            )

            position = self.gateway.query_position(trade["symbol"])

            if order and order.get("status") == "FILLED":
                trade["status"] = "FILLED"

            if position and float(position.get("positionAmt", 0)) == 0:
                trade["status"] = "CLOSED"

            self.store.update(trade)
