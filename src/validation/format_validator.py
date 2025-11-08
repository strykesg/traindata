"""Format validation for training data."""
import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class FormatValidator:
    """Validate format requirements."""
    
    @staticmethod
    def validate_reasoning_tags(text: str) -> Tuple[bool, Optional[str]]:
        """Check for required XML tags in reasoning."""
        has_reasoning = bool(re.search(r'<reasoning>', text, re.IGNORECASE))
        has_decision = bool(re.search(r'<decision>', text, re.IGNORECASE))
        
        if not has_reasoning and not has_decision:
            return False, "Missing required tags: <reasoning> and/or <decision>"
        
        if not has_reasoning:
            return False, "Missing <reasoning> tag"
        
        if not has_decision:
            return False, "Missing <decision> tag"
        
        return True, None
    
    @staticmethod
    def validate_numeric_ranges(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate numeric ranges in scenario."""
        # Check prices
        if "market_context" in data:
            mids = data["market_context"].get("mids", {})
            for asset, price in mids.items():
                if not isinstance(price, (int, float)) or price <= 0:
                    return False, f"Invalid price for {asset}: {price}"
                if price > 1000000:  # Sanity check
                    return False, f"Unrealistic price for {asset}: {price}"
        
        # Check indicators
        if "market_context" in data:
            indicators = data["market_context"].get("key_indicators", {})
            for asset, ind in indicators.items():
                if isinstance(ind, dict):
                    rsi = ind.get("rsi")
                    if rsi is not None and (rsi < 0 or rsi > 100):
                        return False, f"Invalid RSI for {asset}: {rsi}"
        
        # Check account state
        if "account_state" in data:
            equity = data["account_state"].get("equity")
            if equity is not None and (equity <= 0 or equity > 10000000):
                return False, f"Invalid equity: {equity}"
            
            leverage = data["account_state"].get("leverage")
            if leverage is not None and (leverage < 1 or leverage > 100):
                return False, f"Invalid leverage: {leverage}"
        
        return True, None
    
    @staticmethod
    def validate_outcome_label(label: str) -> Tuple[bool, Optional[str]]:
        """Validate outcome label."""
        valid_labels = {"SUCCESS", "FAILURE", "UNKNOWN"}
        if label not in valid_labels:
            return False, f"Invalid outcome label: {label}. Must be one of {valid_labels}"
        return True, None
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required: list) -> Tuple[bool, Optional[str]]:
        """Check for required fields."""
        missing = [field for field in required if field not in data or data[field] is None]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        return True, None
    
    @staticmethod
    def validate_timestamp(timestamp: Any) -> Tuple[bool, Optional[str]]:
        """Validate timestamp format."""
        if timestamp is None:
            return False, "Timestamp is required"
        
        # Accept Unix timestamp (int/float) or ISO string
        if isinstance(timestamp, (int, float)):
            if timestamp < 0 or timestamp > 2147483647:  # Reasonable range
                return False, f"Invalid timestamp value: {timestamp}"
            return True, None
        
        if isinstance(timestamp, str):
            # Try to parse ISO format
            try:
                from datetime import datetime
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return True, None
            except ValueError:
                return False, f"Invalid timestamp format: {timestamp}"
        
        return False, f"Invalid timestamp type: {type(timestamp)}"

