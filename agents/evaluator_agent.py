from agents.agent_functions import Agent
import helpers.querygrag as querygrag
import helpers.preprocessing as preprocessing
from typing import Tuple, List, Optional
from enum import Enum

class ValidationResult(Enum):
    """Enum representing validation results."""
    VALID = "valid"
    VALIDATION_FAILED = "validation_failed"
    VERIFICATION_INVALID = "verification_invalid"
    BOTH_INVALID = "both_invalid"

class EvaluatorAgent(Agent):
    """
    Agent responsible for evaluating ADL specifications through validation and verification.
    
    This agent uses the existing querygrag.validation_verification function to:
    1. Perform verification using formal verification tools
    2. Perform validation by generating and checking liveness properties
    3. Provide structured feedback on what needs to be fixed
    """
    
    def __init__(self):
        super().__init__("evaluator", model="claude-sonnet-4-20250514")

    def evaluate_adl(self, original_adl_name: str, adl: str, new_requirement: str) -> Tuple[str, Optional[List[str]], ValidationResult]:
        """
        Comprehensive evaluation of ADL specification using existing validation_verification function.
        
        Args:
            adl (str): The ADL specification to evaluate
            new_requirement (str): The new requirement to validate against
            
        Returns:
            Tuple[str, Optional[List[str]], ValidationResult]: 
                (detailed_result_message, non_existing_properties, result_enum)
        """
        print("Starting ADL evaluation...")
        
        # Use the existing validation_verification function
        try:
            original_adl = preprocessing.load_adl(original_adl_name)
            detailed_result, non_existing_properties, asserts = querygrag.validation_verification(original_adl, adl, new_requirement)
            result_enum = self._parse_result_to_enum(detailed_result)

            assert_statements = "\n".join(asserts)
            
            print(f"Evaluation completed: {self.get_evaluation_summary(result_enum, non_existing_properties)}")
            
            return detailed_result, non_existing_properties, result_enum, assert_statements
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            error_result = f"Evaluation Error: {str(e)}\n{adl}"
            return error_result, [], ValidationResult.BOTH_INVALID, ""

    def _parse_result_to_enum(self, detailed_result: str) -> ValidationResult:
        """
        Parse the detailed result string to determine the ValidationResult enum.
        
        Args:
            detailed_result (str): The detailed result from validation_verification
            
        Returns:
            ValidationResult: The corresponding enum value
        """
        if detailed_result.startswith("Both Validation and Verification:valid"):
            return ValidationResult.VALID
        elif detailed_result.startswith("Both Validation and Verification:invalid"):
            return ValidationResult.BOTH_INVALID
        elif detailed_result.startswith("Validation: Failed"):
            return ValidationResult.VALIDATION_FAILED
        else:
            # Default to verification invalid for any other case
            return ValidationResult.VERIFICATION_INVALID

    def get_evaluation_summary(self, result_enum: ValidationResult, non_existing_properties: Optional[List[str]] = None) -> str:
        """
        Get a human-readable summary of the evaluation results.
        
        Args:
            result_enum (ValidationResult): The evaluation result
            non_existing_properties (List[str], optional): List of non-existing properties
            
        Returns:
            str: Human-readable summary
        """
        summaries = {
            ValidationResult.VALID: "ADL specification is valid and meets all requirements",
            ValidationResult.VALIDATION_FAILED: f"Validation failed - {len(non_existing_properties) if non_existing_properties else 0} properties not satisfied",
            ValidationResult.VERIFICATION_INVALID: "Verification failed - syntax or compliance issues detected",
            ValidationResult.BOTH_INVALID: "Both validation and verification failed"
        }
        
        summary = summaries.get(result_enum, "Unknown evaluation result")
        
        if non_existing_properties and len(non_existing_properties) > 0:
            summary += f"\nMissing properties:\n"
            for prop in non_existing_properties:
                summary += f"  - {prop}\n"
        
        return summary

    def needs_correction(self, result_enum: ValidationResult) -> bool:
        """
        Determine if the ADL needs correction based on evaluation results.
        
        Args:
            result_enum (ValidationResult): The evaluation result
            
        Returns:
            bool: True if correction is needed
        """
        return result_enum != ValidationResult.VALID
