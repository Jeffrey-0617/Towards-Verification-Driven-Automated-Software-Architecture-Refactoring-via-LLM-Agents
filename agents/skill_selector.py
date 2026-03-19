from agents.evaluator_agent import ValidationResult
from typing import Optional, List

class SkillSelector:
    """
    Component to handle condition checking and determine which refactoring task to execute.
    This is not an LLM agent, just a utility class with functions for decision making.
    """
    
    @staticmethod
    def determine_task(result_enum: ValidationResult, non_existing_properties: Optional[List[str]] = None) -> str:
        """
        Determine which refactoring task should be executed based on evaluation results.
        
        Args:
            result_enum (ValidationResult): The evaluation result
            non_existing_properties (List[str], optional): Non-existing properties from validation
            
        Returns:
            str: Task to execute ("refactor", "correct_validation", "fix_syntax", "no_action")
        """
        if result_enum == ValidationResult.BOTH_INVALID or result_enum == ValidationResult.VERIFICATION_INVALID:
            return "fix_syntax"
        elif result_enum == ValidationResult.VALIDATION_FAILED and non_existing_properties:
            return "correct_validation"
        elif result_enum == ValidationResult.VALID:
            return "no_action"
        else:
            return "refactor"  # Default to refactoring for any other case
    
    @staticmethod
    def get_task_description(task: str) -> str:
        """
        Get a human-readable description of the task.
        
        Args:
            task (str): The task name
            
        Returns:
            str: Description of the task
        """
        descriptions = {
            "refactor": "Initial refactoring",
            "correct_validation": "Correct validation issues",
            "fix_syntax": "Fix syntax violations",
            "no_action": "No action required"
        }
        return descriptions.get(task, "Unknown task")
    
    @staticmethod
    def should_continue(task: str) -> bool:
        """
        Determine if processing should continue based on the task.
        
        Args:
            task (str): The task name
            
        Returns:
            bool: True if processing should continue, False if complete
        """
        return task != "no_action" 