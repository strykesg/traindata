"""JSON schema validation for scenarios and reasoning."""
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError, Field

logger = logging.getLogger(__name__)


class MarketIndicator(BaseModel):
    """Market indicator model with value normalization."""
    momentum_24h: float
    rsi: float
    atr_pct: float
    
    @classmethod
    def normalize_momentum(cls, v: float) -> float:
        """Normalize momentum to [-1.0, 1.0] range."""
        return max(-1.0, min(1.0, float(v)))
    
    @classmethod
    def normalize_rsi(cls, v: float) -> float:
        """Normalize RSI to [0.0, 100.0] range."""
        return max(0.0, min(100.0, float(v)))
    
    @classmethod
    def normalize_atr(cls, v: float) -> float:
        """Normalize ATR to [0.0, 50.0] range."""
        return max(0.0, min(50.0, float(v)))
    
    def __init__(self, **data):
        # Normalize values before validation
        if "momentum_24h" in data:
            data["momentum_24h"] = self.normalize_momentum(data["momentum_24h"])
        if "rsi" in data:
            data["rsi"] = self.normalize_rsi(data["rsi"])
        if "atr_pct" in data:
            data["atr_pct"] = self.normalize_atr(data["atr_pct"])
        super().__init__(**data)


class MarketContext(BaseModel):
    """Market context model."""
    mids: Dict[str, float] = Field(..., min_items=1)
    key_indicators: Dict[str, MarketIndicator] = Field(..., min_items=1)
    market_conditions: Optional[Dict[str, str]] = None


class AccountState(BaseModel):
    """Account state model with value normalization."""
    equity: float = Field(..., gt=0.0)
    leverage: float
    open_positions: List[Dict[str, Any]] = Field(default_factory=list)
    risk_level: str = Field(...)
    
    @classmethod
    def normalize_leverage(cls, v: float) -> float:
        """Normalize leverage to [1.0, 100.0] range."""
        return max(1.0, min(100.0, float(v)))
    
    @classmethod
    def normalize_risk_level(cls, v: str) -> str:
        """Normalize risk level."""
        if not isinstance(v, str):
            return "MEDIUM"
        v = v.upper().strip()
        valid_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if v in valid_levels:
            return v
        # Try to normalize
        if "low" in v.lower():
            return "LOW"
        elif "medium" in v.lower():
            return "MEDIUM"
        elif "high" in v.lower():
            return "HIGH"
        elif "critical" in v.lower():
            return "CRITICAL"
        return "MEDIUM"  # Default
    
    def __init__(self, **data):
        # Normalize values before validation
        if "leverage" in data:
            data["leverage"] = self.normalize_leverage(data["leverage"])
        if "risk_level" in data:
            data["risk_level"] = self.normalize_risk_level(data["risk_level"])
        super().__init__(**data)


class ScenarioSchema(BaseModel):
    """Scenario schema validation."""
    scenario_type: str
    market_context: MarketContext
    account_state: AccountState
    decision_prompt: str = Field(..., min_length=10)
    complexity: Optional[str] = None


class DecisionSchema(BaseModel):
    """Decision schema validation."""
    action: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning_summary: str = Field(..., min_length=10)


class ReasoningSchema(BaseModel):
    """Reasoning trace schema validation."""
    reasoning: str = Field(..., min_length=50)
    decision: DecisionSchema


class SchemaValidator:
    """Validate JSON schemas."""
    
    @staticmethod
    def validate_scenario(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate scenario structure."""
        try:
            ScenarioSchema(**data)
            return True, None
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            return False, f"Schema validation failed: {error_msg}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_reasoning(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate reasoning structure."""
        try:
            ReasoningSchema(**data)
            return True, None
        except ValidationError as e:
            error_msg = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            return False, f"Schema validation failed: {error_msg}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

