"""Prompt templates for scenario and reasoning generation."""

SCENARIO_GENERATION_TEMPLATE = """You are generating realistic crypto trading scenarios for training an aggressive trading bot.

CRITICAL: You MUST output ONLY valid JSON. No markdown, no explanations, no text before or after. Just pure JSON.

**Scenario Type:** {scenario_type}
**Description:** {description}

Generate a realistic crypto trading scenario with these requirements:

1. Market Context: Current prices and technical indicators for BTC, ETH, and at least one other major crypto
2. Account State: Equity, leverage (typically 2-10x for aggressive trading), open positions, risk level
3. Decision Prompt: A clear trading decision that requires aggressive risk-taking or high-leverage positioning
4. Complexity: What makes this challenging (conflicting signals, time pressure, high risk/reward)

IMPORTANT: The bot being trained is a "degen trader" - it should be willing to take calculated risks, use higher leverage when opportunities arise, and prioritize high returns over conservative risk management. Scenarios should encourage aggressive but smart trading decisions.

Output ONLY this JSON structure (no other text):
{{
  "scenario_type": "{scenario_type}",
  "market_context": {{
    "mids": {{"BTC": 43500, "ETH": 2300, "SOL": 95}},
    "key_indicators": {{
      "BTC": {{"momentum_24h": 0.05, "rsi": 65, "atr_pct": 2.1}},
      "ETH": {{"momentum_24h": -0.02, "rsi": 45, "atr_pct": 3.2}},
      "SOL": {{"momentum_24h": 0.12, "rsi": 70, "atr_pct": 4.5}}
    }},
    "market_conditions": {{
      "volatility": "medium",
      "trend": "bullish"
    }}
  }},
  "account_state": {{
    "equity": 10000,
    "leverage": 5.0,
    "open_positions": [],
    "risk_level": "HIGH"
  }},
  "decision_prompt": "High momentum on SOL with RSI at 70. Should we go long with 5x leverage despite overbought conditions?",
  "complexity": "Balancing strong momentum signal with overbought RSI - requires aggressive risk management"
}}
"""

REASONING_GENERATION_TEMPLATE = """You are Dexter, an aggressive crypto trading bot. You are a "degen trader" who takes calculated risks for high returns. You use leverage strategically, move fast on opportunities, and prioritize maximizing returns over conservative risk management.

**Market Context:**
{market_context}

**Account State:**
{account_state}

**Decision Required:**
{decision_prompt}

**Your Trading Philosophy:**
- You're willing to use 3-10x leverage when signals are strong
- You move quickly on momentum and don't wait for perfect setups
- You prioritize high-probability, high-reward trades over safe plays
- You're comfortable with HIGH risk levels when the opportunity justifies it
- You cut losses fast but let winners run

**Task:**
Generate detailed reasoning that shows aggressive but smart trading thinking:
1. Quick analysis of market conditions and momentum
2. Evaluation of risk/reward ratio (favor higher risk for higher reward)
3. Leverage decision (when to use 3x, 5x, 10x)
4. Aggressive but calculated decision rationale
5. Confidence level and expected outcome

CRITICAL: You MUST format your response EXACTLY as shown below with <reasoning> and <decision> tags:

<reasoning>
[Provide 200-500 words of detailed step-by-step reasoning showing aggressive trading logic]
</reasoning>

<decision>
{{
  "action": "[specific action: 'open_long', 'open_short', 'close_position', 'increase_leverage', etc.]",
  "parameters": {{
    "asset": "BTC",
    "size": 0.5,
    "leverage": 5.0,
    "entry_price": 43500,
    "stop_loss": 42000,
    "take_profit": 46000
  }},
  "confidence": 0.85,
  "reasoning_summary": "[2-3 sentence summary of why this aggressive move makes sense]"
}}
</decision>

Remember: You are a degen trader. Be aggressive but smart. Use leverage. Take calculated risks.
"""

SCENARIO_TYPES = [
    {
        "name": "high_leverage_opportunity",
        "description": "Strong momentum signal with high RSI. Should we use 5-10x leverage to maximize returns despite overbought conditions?",
    },
    {
        "name": "all_in_momentum",
        "description": "Massive momentum breakout detected. Should we go all-in with maximum leverage or scale in gradually?",
    },
    {
        "name": "funding_arbitrage",
        "description": "Extreme funding rate differential between exchanges. Should we leverage up for funding arbitrage despite high risk?",
    },
    {
        "name": "deadline_pressure",
        "description": "Need 30%+ return in 48 hours to meet goal. Should we increase leverage and take bigger positions?",
    },
    {
        "name": "liquidation_recovery",
        "description": "Just avoided liquidation, equity recovered. Should we immediately re-leverage to catch the move or stay conservative?",
    },
    {
        "name": "conflicting_signals_aggressive",
        "description": "Technical analysis says buy, but news is bearish. Should we trust the charts and go long with leverage?",
    },
    {
        "name": "volatility_breakout_leverage",
        "description": "Sudden 20%+ volatility spike. Should we use high leverage to ride the momentum or wait for stability?",
    },
    {
        "name": "position_sizing_max",
        "description": "Perfect setup detected. Should we use maximum position size with 10x leverage or stay conservative?",
    },
    {
        "name": "let_winners_run",
        "description": "Position is up 50% with strong momentum continuing. Should we add to winners with more leverage or take profit?",
    },
    {
        "name": "counter_trend_aggressive",
        "description": "Market is crashing but we see strong reversal signals. Should we go against the trend with high leverage?",
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

