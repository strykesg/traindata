"""Main validation orchestrator."""
import logging
from typing import Dict, Any, Tuple, Optional

from src.validation.schema_validator import SchemaValidator
from src.validation.format_validator import FormatValidator
from src.validation.content_validator import ContentValidator

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Multi-stage validation pipeline."""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.format_validator = FormatValidator()
        self.content_validator = ContentValidator()
    
    def validate_scenario(self, scenario: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate scenario through all stages."""
        # Stage 1: Schema validation
        valid, error = self.schema_validator.validate_scenario(scenario)
        if not valid:
            return False, f"Stage 1 (Schema): {error}"
        
        # Stage 2: Format validation
        valid, error = self.format_validator.validate_numeric_ranges(scenario)
        if not valid:
            return False, f"Stage 2 (Format): {error}"
        
        valid, error = self.format_validator.validate_required_fields(
            scenario,
            ["scenario_type", "market_context", "account_state", "decision_prompt"]
        )
        if not valid:
            return False, f"Stage 2 (Format): {error}"
        
        # Stage 3: Content validation
        valid, error = self.content_validator.validate_market_data_realism(scenario)
        if not valid:
            return False, f"Stage 3 (Content): {error}"
        
        return True, None
    
    def validate_reasoning(
        self,
        reasoning_data: Dict[str, Any],
        scenario: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate reasoning through all stages."""
        # Stage 1: Schema validation
        valid, error = self.schema_validator.validate_reasoning(reasoning_data)
        if not valid:
            return False, f"Stage 1 (Schema): {error}"
        
        # Stage 2: Format validation
        reasoning_text = reasoning_data.get("reasoning", "")
        valid, error = self.format_validator.validate_reasoning_tags(
            reasoning_text + "\n" + str(reasoning_data.get("decision", {}))
        )
        if not valid:
            return False, f"Stage 2 (Format): {error}"
        
        decision = reasoning_data.get("decision", {})
        confidence = decision.get("confidence")
        if confidence is not None:
            valid, error = self.format_validator.validate_outcome_label(
                "SUCCESS" if confidence > 0.5 else "FAILURE"
            )
            # This is just a check, not critical
        
        # Stage 3: Content validation
        valid, error = self.content_validator.validate_reasoning_coherence(reasoning_text)
        if not valid:
            return False, f"Stage 3 (Content): {error}"
        
        if confidence is not None:
            valid, error = self.content_validator.validate_confidence_range(confidence)
            if not valid:
                return False, f"Stage 3 (Content): {error}"
        
        # Cross-validation: decision matches scenario
        if scenario:
            valid, error = self.content_validator.validate_decision_context_match(
                scenario,
                decision
            )
            if not valid:
                return False, f"Stage 3 (Content): {error}"
        
        return True, None
    
    def validate_complete_example(
        self,
        scenario: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate complete example (scenario + reasoning)."""
        # Validate scenario
        valid, error = self.validate_scenario(scenario)
        if not valid:
            return False, error
        
        # Validate reasoning with scenario context
        valid, error = self.validate_reasoning(reasoning, scenario)
        if not valid:
            return False, error
        
        return True, None

