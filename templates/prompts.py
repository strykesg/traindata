"""Prompt templates for scenario and reasoning generation."""

SCENARIO_GENERATION_TEMPLATE = """You are generating realistic crypto trading scenarios for training a trading bot.

Generate a synthetic but realistic crypto trading scenario with the following structure:

**Scenario Type:** {scenario_type}

**Description:** {description}

Create a complete scenario JSON with:

1. **Market Context:**
   - Current prices (mids) for major crypto assets (BTC, ETH, etc.)
   - Key technical indicators (momentum_24h, rsi, atr_pct) for each asset
   - Market conditions (volatility, trend direction)

2. **Account State:**
   - Current equity
   - Leverage ratio
   - Open positions (if any)
   - Risk level (LOW, MEDIUM, HIGH, CRITICAL)

3. **Decision Prompt:**
   - A clear question or decision point the trading bot needs to make
   - Context about goals, constraints, or deadlines

4. **Expected Complexity:**
   - What makes this scenario challenging or edge-case worthy

Output ONLY valid JSON in this exact format:
{{
  "scenario_type": "{scenario_type}",
  "market_context": {{
    "mids": {{"BTC": 43500, "ETH": 2300}},
    "key_indicators": {{
      "BTC": {{"momentum_24h": 0.05, "rsi": 65, "atr_pct": 2.1}},
      "ETH": {{"momentum_24h": -0.02, "rsi": 45, "atr_pct": 3.2}}
    }},
    "market_conditions": {{
      "volatility": "medium",
      "trend": "bullish"
    }}
  }},
  "account_state": {{
    "equity": 10000,
    "leverage": 2.5,
    "open_positions": [],
    "risk_level": "MEDIUM"
  }},
  "decision_prompt": "Should we open a long position on BTC given the current momentum?",
  "complexity": "Balancing momentum signal with RSI overbought condition"
}}
"""

REASONING_GENERATION_TEMPLATE = """You are Dexter, a crypto trading bot assistant. Analyze the following trading scenario and provide detailed reasoning.

**Market Context:**
{market_context}

**Account State:**
{account_state}

**Decision Required:**
{decision_prompt}

**Task:**
Generate a detailed reasoning trace that explains:
1. Analysis of current market conditions
2. Evaluation of key indicators and signals
3. Risk assessment given account state
4. Decision rationale
5. Expected outcome and confidence

Format your response as:
<reasoning>
[Step-by-step reasoning process]
</reasoning>

<decision>
{{
  "action": "[specific action to take]",
  "parameters": {{"asset": "...", "size": ..., "leverage": ...}},
  "confidence": 0.85,
  "reasoning_summary": "[brief summary]"
}}
</decision>
"""

SCENARIO_TYPES = [
    {
        "name": "liquidation_risk",
        "description": "Account equity is dangerously close to liquidation threshold (< 2x liabilities). Bot must reduce risk immediately.",
    },
    {
        "name": "conflicting_signals",
        "description": "High momentum suggests bullish move, but sentiment indicators are negative. Bot must resolve conflict.",
    },
    {
        "name": "goal_pacing",
        "description": "Deadline approaching, need significant return (e.g., 20% in 2 days). Bot must adjust aggressiveness.",
    },
    {
        "name": "funding_rate_spike",
        "description": "Funding rate suddenly spikes, making capital expensive. Bot must decide on position reduction.",
    },
    {
        "name": "research_conflict",
        "description": "Breaking news contradicts technical analysis. Bot must resolve trust and make decision.",
    },
    {
        "name": "volatility_breakout",
        "description": "Sudden volatility spike breaks normal patterns. Bot must adapt strategy.",
    },
    {
        "name": "position_sizing",
        "description": "Optimal position size calculation given risk constraints and opportunity.",
    },
    {
        "name": "exit_timing",
        "description": "When to exit profitable position - take profit or let it run?",
    },
]


def get_scenario_prompt(scenario_type: dict) -> str:
    """Get formatted scenario generation prompt."""
    return SCENARIO_GENERATION_TEMPLATE.format(
        scenario_type=scenario_type["name"],
        description=scenario_type["description"],
    )


def get_reasoning_prompt(scenario: dict) -> str:
    """Get formatted reasoning generation prompt."""
    import json
    return REASONING_GENERATION_TEMPLATE.format(
        market_context=json.dumps(scenario.get("market_context", {}), indent=2),
        account_state=json.dumps(scenario.get("account_state", {}), indent=2),
        decision_prompt=scenario.get("decision_prompt", ""),
    )

