from agents.agent_functions import Agent
from agents.skill_selector import SkillSelector
from agents.evaluator_agent import ValidationResult
from skill_engineering.instructions.refactoring_instruction import refactoring_instruction_system_instruction, fixing_instruction_system_instruction
from skill_engineering.instructions.misconfiguration_handling_instruction import misconfiguration_handling_instruction_system_instruction
from skill_engineering.load_skill import load_skill
import helpers.auxiluary as auxiluary
import helpers.misconfiguration_detection as misconfiguration_detection
import helpers.helper as helper
import helpers.postprocessing as postprocessing
from typing import Tuple, Optional, List, Dict, Any

class ArchitectureDesigner(Agent):
    def __init__(self):
        super().__init__("ArchitectureDesigner", model="claude-sonnet-4-20250514", system_prompt=refactoring_instruction_system_instruction)
        self.skill_selector = SkillSelector()

        # Configuration for enabling/disabling functions
        self.config = {
            "fix_syntax_enabled": True,
            "correct_validation_enabled": True,
            "misconfiguration_handling_enabled": True
        }

        # Track usage for separate calls
        self.usage_log = []

    def disable_function(self, function_name: str):
        """
        Disable a specific refactoring function.

        Args:
            function_name (str): "fix_syntax", "correct_validation", or "misconfiguration_handling"
        """
        config_map = {
            "fix_syntax": "fix_syntax_enabled",
            "correct_validation": "correct_validation_enabled",
            "misconfiguration_handling": "misconfiguration_handling_enabled"
        }

        if function_name in config_map:
            self.config[config_map[function_name]] = False
            print(f"Disabled: {function_name}")
        else:
            raise ValueError(f"Unknown function: {function_name}. Available: {list(config_map.keys())}")

    def enable_function(self, function_name: str):
        """
        Enable a specific refactoring function.

        Args:
            function_name (str): "fix_syntax", "correct_validation", or "misconfiguration_handling"
        """
        config_map = {
            "fix_syntax": "fix_syntax_enabled",
            "correct_validation": "correct_validation_enabled",
            "misconfiguration_handling": "misconfiguration_handling_enabled"
        }

        if function_name in config_map:
            self.config[config_map[function_name]] = True
            print(f"Enabled: {function_name}")
        else:
            raise ValueError(f"Unknown function: {function_name}. Available: {list(config_map.keys())}")

    def get_config_status(self):
        """Get current configuration status."""
        print("ArchitectureDesigner Configuration:")
        print(f"  fix_syntax: {'enabled' if self.config['fix_syntax_enabled'] else 'disabled'}")
        print(f"  correct_validation: {'enabled' if self.config['correct_validation_enabled'] else 'disabled'}")
        print(f"  misconfiguration_handling: {'enabled' if self.config['misconfiguration_handling_enabled'] else 'disabled'}")

    def get_separate_usage_records(self) -> List[Dict[str, Any]]:
        """
        Get all separate usage records from the current process() call.

        Returns:
            List[Dict]: List of usage records for each LLM call
        """
        records = self.usage_log.copy()
        self.usage_log.clear()  # Clear for next process() call
        return records

    def process(self, adl_name: str = None, new_requirement: str = None, current_adl: str = None,
                result_enum: ValidationResult = None, non_existing_properties: List[str] = None) -> Tuple[str, str]:
        """
        Unified processing function that determines and executes the appropriate refactoring task.
        Respects configuration settings for enabled/disabled functions.
        Records separate usage for each LLM call.

        Args:
            adl_name (str, optional): Name of the ADL file (for initial refactoring)
            new_requirement (str, optional): New requirement (for initial refactoring)
            current_adl (str, optional): Current ADL content (for corrections/fixes)
            result_enum (ValidationResult, optional): Previous evaluation result
            non_existing_properties (List[str], optional): Non-existing properties from validation

        Returns:
            Tuple[str, str]: (processed_adl, task_name)
        """
        # Clear usage log for this process call
        self.usage_log.clear()

        # Determine task based on context
        if result_enum is None:
            # Initial refactoring
            task = "refactor"
        else:
            # Determine task based on evaluation results and configuration
            task = self._determine_task_with_config(result_enum, non_existing_properties)

        print(f"ArchitectureDesigner executing task: {self.skill_selector.get_task_description(task)}")

        # Execute the determined task
        if task == "refactor":
            if adl_name is None or new_requirement is None:
                raise ValueError("adl_name and new_requirement required for refactoring task")
            processed_adl = self._execute_until_success(self.refactor_adl, adl_name, new_requirement)
            # Record usage for main task
            self._record_task_usage(task)

        elif task == "fix_syntax":
            if current_adl is None:
                raise ValueError("current_adl required for syntax fixing")
            processed_adl = self._execute_until_success(self.fix_syntax_rules_violation, current_adl)
            # Record usage for main task
            self._record_task_usage(task)

        elif task == "correct_validation":
            if current_adl is None or non_existing_properties is None:
                raise ValueError("current_adl and non_existing_properties required for validation correction")
            properties_str = '\n'.join(non_existing_properties)
            try:
                processed_adl = self._execute_until_success(self.correct_adl, current_adl, properties_str)
                # Record usage for main task
                self._record_task_usage(task)
            except RuntimeError as e:
                # If correction fails repeatedly (e.g., extractor returns None), don't crash the whole pipeline.
                # Keep the current ADL so the outer loop can continue with evaluation/other repairs.
                print(f"correct_validation failed after retries: {e}")
                processed_adl = current_adl
                self._record_task_usage("correct_validation_failed")

        elif task == "no_action":
            return current_adl, task

        else:
            raise ValueError(f"Unknown task: {task}")

        # Apply misconfiguration handling if enabled
        if self.config["misconfiguration_handling_enabled"]:
            processed_adl, misconfiguration_handling_usage = self.fix_misconfiguration(processed_adl)
            # Only record usage if LLM calls were actually made (non-empty usage)
            if misconfiguration_handling_usage:
                self._record_task_usage(f"misconfiguration_handling({misconfiguration_handling_usage})")
            else:
                print("No misconfiguration handling LLM calls needed - no misconfiguration detected")
        else:
            print("Misconfiguration handling disabled - skipping")

        return processed_adl, task

    def _record_task_usage(self, task_description: str):
        """
        Record usage for a specific task.

        Args:
            task_description (str): Description of the task
        """
        usage_record = self.record_latest_usage()
        if usage_record:
            usage_record['agent_name'] = usage_record['agent_name'] + f" ({task_description})"
            self.usage_log.append(usage_record)

    def _determine_task_with_config(self, result_enum: ValidationResult, non_existing_properties: Optional[List[str]]) -> str:
        """
        Determine task based on evaluation results and current configuration.

        Args:
            result_enum (ValidationResult): The evaluation result
            non_existing_properties (List[str], optional): Non-existing properties

        Returns:
            str: Task to execute, considering disabled functions
        """
        # Get the normal task recommendation
        normal_task = self.skill_selector.determine_task(result_enum, non_existing_properties)

        # Check if the recommended task is disabled
        if normal_task == "fix_syntax" and not self.config["fix_syntax_enabled"]:
            print("fix_syntax is disabled - skipping to no_action")
            return "no_action"
        elif normal_task == "correct_validation" and not self.config["correct_validation_enabled"]:
            print("correct_validation is disabled - skipping to no_action")
            return "no_action"

        return normal_task

    def _execute_until_success(self, func, *args):
        """
        Execute a function until it returns a non-None result.

        Args:
            func: The function to execute
            *args: Arguments to pass to the function

        Returns:
            The successful result from the function
        """
        result = None
        attempt = 0
        max_attempts = 3

        while result is None and attempt < max_attempts:
            attempt += 1
            result = func(*args)
            if result is None:
                print(f"Attempt {attempt} failed, retrying...")

        if result is None:
            raise RuntimeError(f"Function {func.__name__} failed after {max_attempts} attempts")

        return result

    def refactor_adl(self, adl_name, new_requirement):
        """
        Refactor ADL based on new requirements.

        Args:
            adl_name (str): Name of the ADL file
            new_requirement (str): New requirement to implement

        Returns:
            str: Refactored ADL content
        """
        # Generate refactoring instruction
        refactoring_user_instruction = load_skill("refactoring", adl_name=adl_name, new_requirement=new_requirement)
        refactoring_response = self.query(refactoring_user_instruction)
        refactored_adl = auxiluary.extract_adl(refactoring_response)

        return refactored_adl

    def correct_adl(self, adl, liveness_properties):
        """
        Correct ADL based on liveness properties.

        Args:
            adl (str): ADL content
            liveness_properties (str): Liveness properties

        Returns:
            str: Corrected ADL content
        """
        # Generate correction instruction
        correction_user_instruction = load_skill("correction", adl=adl, liveness_properties=liveness_properties)
        correction_response = self.query(correction_user_instruction)
        corrected_adl = auxiluary.extract_adl(correction_response)

        return corrected_adl

    def fix_syntax_rules_violation(self, adl):
        """
        Fix syntax/compliance violations in ADL.

        Args:
            adl (str): ADL content

        Returns:
            str: Fixed ADL content
        """
        # Reset system instruction
        self.set_system_prompt(fixing_instruction_system_instruction)
        # Generate fixing instruction
        fixing_user_instruction = load_skill("fixing_syntax", adl=adl)
        fixing_response = self.query(fixing_user_instruction)
        fixed_adl = auxiluary.extract_adl(fixing_response)

        self.set_system_prompt(refactoring_instruction_system_instruction)

        return fixed_adl

    def fix_misconfiguration(self, refactored_adl):
        """
        Fix misconfiguration issues in the refactored ADL.

        Args:
            refactored_adl (str): The refactored ADL content

        Returns:
            tuple: (fixed_adl, usage_string)
        """
        # Store the original system instruction
        original_system_instruction = self.system_prompt

        # Set misconfiguration handling system instruction
        self.set_system_prompt(misconfiguration_handling_instruction_system_instruction)

        # store usage record
        usage = ""
        # check the misconfiguration issues
        issues_1, illegal_pattern_1 = misconfiguration_detection.get_misconfiguration_information1(refactored_adl)
        issues_2, illegal_pattern_2 = misconfiguration_detection.get_misconfiguration_information2(refactored_adl)

        if not issues_1 and not issues_2:
            # Restore original system instruction
            self.set_system_prompt(original_system_instruction)
            return refactored_adl, usage

        # write a while loop to fix until no misconfiguration detected
        while issues_1 or issues_2:
            if issues_1:
                misconfiguration_handling_user_instruction = load_skill("misconfiguration_1", adl=refactored_adl)
                misconfiguration_handling_response = self.query(misconfiguration_handling_user_instruction)
                usage += 'fix misconfiguration 1! '
                new_attachments = auxiluary.extract_declare_attach_statements(misconfiguration_handling_response)
                refactored_adl = postprocessing.replace_attachments_in_adl(refactored_adl, illegal_pattern_1, new_attachments)

            elif issues_2:
                misconfiguration_handling_user_instruction = load_skill("misconfiguration_2", adl=refactored_adl)
                misconfiguration_handling_response = self.query(misconfiguration_handling_user_instruction)
                usage += 'fix misconfiguration 2! '
                new_attachments = auxiluary.extract_declare_attach_statements(misconfiguration_handling_response)
                refactored_adl = postprocessing.replace_attachments_in_adl(refactored_adl, illegal_pattern_2, new_attachments)

            # remove duplicate declare statements
            refactored_adl = postprocessing.remove_duplicate_declare_statements(refactored_adl)
            # remove parameters from input roles, this could lead to syntax error
            refactored_adl = postprocessing.remove_parameters_from_input_roles(refactored_adl)
            # ensure the parameters of output roles are number
            refactored_adl = postprocessing.ensure_parameters_correct_output_roles(refactored_adl)
            # make sure every component and port are defined
            refactored_adl = postprocessing.extract_fix_undefined_component_port(refactored_adl)
            # secure_execution
            refactored_adl = helper.secure_execution(refactored_adl)

            # check the misconfiguration issues again
            issues_1, illegal_pattern_1 = misconfiguration_detection.get_misconfiguration_information1(refactored_adl)
            issues_2, illegal_pattern_2 = misconfiguration_detection.get_misconfiguration_information2(refactored_adl)

        # Restore original system instruction
        self.set_system_prompt(original_system_instruction)

        return refactored_adl, usage