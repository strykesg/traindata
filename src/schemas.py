"""JSON schemas for structured outputs."""
SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario_type": {
            "type": "string",
            "description": "Type of trading scenario"
        },
        "market_context": {
            "type": "object",
            "properties": {
                "mids": {
                    "type": "object",
                    "description": "Current market prices (mids) for crypto assets",
                    "additionalProperties": {
                        "type": "number"
                    }
                },
                "key_indicators": {
                    "type": "object",
                    "description": "Technical indicators for each asset",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "momentum_24h": {
                                "type": "number",
                                "description": "24-hour momentum (-1.0 to 1.0)"
                            },
                            "rsi": {
                                "type": "number",
                                "description": "Relative Strength Index (0-100)"
                            },
                            "atr_pct": {
                                "type": "number",
                                "description": "Average True Range percentage (0-50)"
                            }
                        },
                        "required": ["momentum_24h", "rsi", "atr_pct"]
                    }
                },
                "market_conditions": {
                    "type": "object",
                    "description": "Overall market conditions",
                    "properties": {
                        "volatility": {"type": "string"},
                        "trend": {"type": "string"}
                    }
                }
            },
            "required": ["mids", "key_indicators"]
        },
        "account_state": {
            "type": "object",
            "properties": {
                "equity": {
                    "type": "number",
                    "description": "Current account equity"
                },
                "leverage": {
                    "type": "number",
                    "description": "Current leverage ratio (1-100)"
                },
                "open_positions": {
                    "type": "array",
                    "description": "List of open positions",
                    "items": {"type": "object"},
                    "default": []
                },
                "risk_level": {
                    "type": "string",
                    "description": "Risk level: LOW, MEDIUM, HIGH, or CRITICAL",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                }
            },
            "required": ["equity", "leverage", "risk_level", "open_positions"]
        },
        "decision_prompt": {
            "type": "string",
            "description": "The trading decision question or prompt"
        },
        "complexity": {
            "type": "string",
            "description": "What makes this scenario challenging"
        }
    },
    "required": ["scenario_type", "market_context", "account_state", "decision_prompt"],
    "additionalProperties": False
}

REASONING_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {
            "type": "string",
            "description": "Detailed step-by-step reasoning (200-500 words) explaining the trading decision"
        },
        "decision": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Trading action: open_long, open_short, close_position, increase_leverage, etc."
                },
                "parameters": {
                    "type": "object",
                    "description": "Action parameters (asset, size, leverage, entry_price, stop_loss, take_profit)",
                    "properties": {
                        "asset": {"type": "string"},
                        "size": {"type": "number"},
                        "leverage": {"type": "number"},
                        "entry_price": {"type": "number"},
                        "stop_loss": {"type": "number"},
                        "take_profit": {"type": "number"}
                    }
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level (0.0 to 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "reasoning_summary": {
                    "type": "string",
                    "description": "Brief 2-3 sentence summary of why this aggressive move makes sense"
                }
            },
            "required": ["action", "parameters", "confidence", "reasoning_summary"]
        }
    },
    "required": ["reasoning", "decision"],
    "additionalProperties": False
}

