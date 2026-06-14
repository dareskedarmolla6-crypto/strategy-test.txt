# ==========================================================
# BRAINSIGNAL GENERATOR (FUSION LAYER)
# ==========================================================

class BrainSignalGenerator:
    """
    Core fusion brain:
    merges prediction + inference + adaptive mode
    """

    def __init__(self, predictor, inference_engine, feature_engine):

        self.predictor = predictor
        self.inference_engine = inference_engine
        self.feature_engine = feature_engine


    def generate(self, data: dict):

        prediction, conf1 = self.predictor.predict(data)

        inference, conf2 = self.inference_engine.analyze(data)

        mode = self.feature_engine.adjust(
            data.get("win_rate", 0.5)
        )

        if prediction == inference:
            side = prediction
            confidence = int((conf1 + conf2) / 2)
        else:
            side = "HEDGE"
            confidence = 50

        return {
            "symbol": data.get("symbol"),
            "side": side,
            "confidence": confidence,
            "mode": mode,
        }


# ==========================================================
# CONSENSUS SIGNAL ENGINE
# ==========================================================

import time


class SignalGenerator:
    """
    Multi-model consensus + validation layer
    """

    def __init__(self, consensus_engine, validation_engine):

        self.consensus = consensus_engine
        self.validator = validation_engine


    def generate(self, signals, market_data):

        consensus = self.consensus.run(signals)

        final_signals = []

        for c in consensus:

            validation = self.validator.process(
                signal=c,
                market_data=market_data,
                higher_tf_trend=market_data.get("trend", "NEUTRAL"),
            )

            if validation["valid"]:

                final_signals.append({
                    "symbol": c["symbol"],
                    "side": c["side"],
                    "strength": c.get("strength", 0),
                    "quality": validation["quality_score"],
                    "ts": time.time(),
                })

        return final_signals


# ==========================================================
# MARKET REGIME AI
# ==========================================================

import random


class MarketRegimeAI:
    """
    Detects market conditions for risk filtering
    """

    def classify(self, data: dict):

        if data.get("volatility", 0) > 0.7:
            return "CHAOTIC"

        if data.get("momentum", 0) > 0.2:
            return "TRENDING_UP"

        if data.get("momentum", 0) < -0.2:
            return "TRENDING_DOWN"

        return "SIDEWAYS"


# ==========================================================
# CONFIDENCE ENGINE
# ==========================================================

class ConfidenceEngine:
    """
    Produces probability score for trade validity
    """

    def __init__(self):
        self.min_confidence = 0.65

    def score(self, structure: dict, signal: dict) -> float:

        base = 0.5

        if structure.get("trend") == "BULLISH" and signal["side"] == "BUY":
            base += 0.2

        if structure.get("trend") == "BEARISH" and signal["side"] == "SELL":
            base += 0.2

        vol = structure.get("volatility", "LOW")

        if vol == "HIGH":
            base += 0.1
        else:
            base -= 0.05

        return max(0.0, min(1.0, base))


# ==========================================================
# POSITION INTELLIGENCE ENGINE
# ==========================================================

class PositionIntelligence:
    """
    Dynamically adjusts position size
    based on confidence and balance
    """

    def adjust_size(self, signal: dict, balance: float) -> float:

        score = signal.get("score", 80)

        return round(balance * 0.01 * (score / 100), 2)


# ==========================================================
# INTELLIGENT SIGNAL FILTER
# ==========================================================

class IntelligentSignalFilter:
    """
    Filters weak or low-confidence trades
    """

    def __init__(self, conf_engine: ConfidenceEngine):

        self.conf = conf_engine

    def validate(self, structure: dict, signal: dict) -> bool:

        return (
            self.conf.score(structure, signal)
            >= self.conf.min_confidence
        )


# ==========================================================
# AI DECISION ENGINE
# ==========================================================

class AIDecisionEngine:
    """
    Final decision maker (risk + regime + filter aware)
    """

    def __init__(self, filter_layer, position_engine, regime_ai):

        self.filter = filter_layer
        self.position_engine = position_engine
        self.regime_ai = regime_ai

    def decide(
        self,
        symbol: str,
        structure: dict,
        market_data: dict,
        wallet: float,
    ):

        regime = self.regime_ai.classify(market_data)

        signal = {
            "symbol": symbol,
            "side": random.choice(["BUY", "SELL"]),
            "score": random.randint(60, 95),
        }

        if regime == "CHAOTIC":
            return None

        if not self.filter.validate(structure, signal):
            return None

        signal["qty"] = self.position_engine.adjust_size(signal, wallet)
        signal["regime"] = regime

        return signal


# ==========================================================
# CORE TRADING BOT ORCHESTRATION
# ==========================================================

class TradingBotCore:
    """
    Main execution brain connecting all systems
    """

    def __init__(
        self,
        data_engine,
        strategy_engine,
        risk_engine,
        execution_engine,
        portfolio_engine,
        monitor,
        telegram=None,
    ):

        self.data = data_engine
        self.strategy = strategy_engine
        self.risk = risk_engine
        self.execution = execution_engine
        self.portfolio = portfolio_engine
        self.monitor = monitor
        self.telegram = telegram
        self.running = False


    def run_once(self):

        market_data = self.data.get_snapshot()

        signals = self.strategy.generate(market_data)

        for signal in signals:

            if not self.risk.validate(signal, self.portfolio.state()):
                continue

            result = self.execution.execute_signal(signal)

            self.portfolio.update(result)

            self.monitor.record_trade()

            if self.telegram:

                self.telegram.notify_trade(
                    signal["symbol"],
                    signal["side"],
                    result.get("pnl", 0),
                )


    def start(self, interval: int = 3):

        self.running = True
        print("🚀 FSE BOT STARTED")

        while self.running:

            try:
                self.run_once()
                time.sleep(interval)

            except Exception as e:
                print("ERROR:", e)


    def stop(self):

        self.running = False


# ==========================================================
# PART 4 END — FULL FSE SIGNAL BRAIN COMPLETE
# ==========================================================
