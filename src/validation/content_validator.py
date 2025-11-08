"""Content quality validation."""
import logging
from typing import Dict, Any, Tuple, Optional
import re

logger = logging.getLogger(__name__)


class ContentValidator:
    """Validate content quality and coherence."""
    
    MIN_REASONING_LENGTH = 100
    MIN_DECISION_SUMMARY_LENGTH = 20
    MAX_REASONING_LENGTH = 5000
    
    @staticmethod
    def validate_reasoning_coherence(reasoning: str) -> Tuple[bool, Optional[str]]:
        """Check reasoning coherence and quality."""
        if not reasoning:
            return False, "Reasoning is empty"
        
        length = len(reasoning)
        if length < ContentValidator.MIN_REASONING_LENGTH:
            return False, f"Reasoning too short: {length} chars (min {ContentValidator.MIN_REASONING_LENGTH})"
        
        if length > ContentValidator.MAX_REASONING_LENGTH:
            return False, f"Reasoning too long: {length} chars (max {ContentValidator.MAX_REASONING_LENGTH})"
        
        # Check for basic structure (sentences)
        sentences = re.split(r'[.!?]+', reasoning)
        if len([s for s in sentences if len(s.strip()) > 10]) < 3:
            return False, "Reasoning lacks sufficient structure (too few sentences)"
        
        # Check for trading-related keywords (basic quality check)
        trading_keywords = ["price", "market", "risk", "position", "signal", "indicator", "trade"]
        has_keywords = any(keyword.lower() in reasoning.lower() for keyword in trading_keywords)
        if not has_keywords:
            return False, "Reasoning lacks trading-related content"
        
        return True, None
    
    @staticmethod
    def validate_decision_context_match(
        scenario: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify decision matches scenario context."""
        # Check if decision mentions assets from scenario
        scenario_assets = set(scenario.get("market_context", {}).get("mids", {}).keys())
        
        decision_str = str(decision).lower()
        decision_assets = [asset for asset in scenario_assets if asset.lower() in decision_str]
        
        # Decision should reference at least one asset from scenario
        if not decision_assets and scenario_assets:
            return False, "Decision does not reference any assets from scenario"
        
        # Check risk level consistency
        scenario_risk = scenario.get("account_state", {}).get("risk_level", "").upper()
        decision_action = decision.get("action", "").lower()
        
        if scenario_risk == "CRITICAL":
            # Critical risk should lead to risk reduction actions
            risk_reduction_actions = ["reduce", "close", "exit", "decrease", "stop"]
            if not any(action in decision_action for action in risk_reduction_actions):
                return False, "Critical risk scenario should lead to risk reduction action"
        
        return True, None
    
    @staticmethod
    def validate_market_data_realism(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate market data is realistic."""
        if "market_context" not in data:
            return False, "Missing market_context"
        
        context = data["market_context"]
        
        # Check price relationships (ETH should be cheaper than BTC typically)
        mids = context.get("mids", {})
        if "BTC" in mids and "ETH" in mids:
            btc_price = mids["BTC"]
            eth_price = mids["ETH"]
            if eth_price > btc_price:
                return False, "ETH price cannot be higher than BTC price"
            if btc_price < 1000 or eth_price < 10:
                return False, "Prices seem unrealistically low"
        
        # Check indicator consistency
        indicators = context.get("key_indicators", {})
        for asset, ind in indicators.items():
            if isinstance(ind, dict):
                rsi = ind.get("rsi")
                momentum = ind.get("momentum_24h", 0)
                
                # High RSI (>70) with positive momentum is somewhat inconsistent
                if rsi and rsi > 70 and momentum > 0.1:
                    # This is actually valid (overbought but still bullish), so we allow it
                    pass
        
        return True, None
    
    @staticmethod
    def validate_confidence_range(confidence: float) -> Tuple[bool, Optional[str]]:
        """Validate confidence is in reasonable range."""
        if confidence < 0.0 or confidence > 1.0:
            return False, f"Confidence out of range: {confidence} (must be 0.0-1.0)"
        
        # Warn about extreme confidence (but allow it)
        if confidence > 0.95:
            logger.warning(f"Very high confidence: {confidence}")
        
        if confidence < 0.3:
            logger.warning(f"Very low confidence: {confidence}")
        
        return True, None

