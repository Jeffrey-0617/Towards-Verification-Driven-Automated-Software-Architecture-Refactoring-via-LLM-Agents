from skill_engineering.instructions.unified_instruction import unified_instruction_instruct, Unified_artifact, simplified_wrighthash_documentation
import helpers.preprocessing as preprocessing
import helpers.misconfiguration_detection as misconfiguration_detection
import os

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

def _save_skill(filename, content):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, filename), "w") as f:
        f.write(content)

def generate_unified_instruction(adl_name=None, new_requirement=None, current_adl=None,
                          task_type="refactor", original_adl=None, specific_issues_1=None, specific_issues_2=None):
    """
    Generate unified instruction with all necessary artifacts.

    Args:
        adl_name (str, optional): Name of ADL file for loading original ADL
        new_requirement (str, optional): New requirement for refactoring
        current_adl (str, optional): Current ADL content (error ADL)
        task_type (str): Type of task ("refactor", "fix_syntax", "correct_validation", "misconfiguration_1", "misconfiguration_2")
        original_adl (str, optional): Original ADL content if already loaded
        specific_issues_1 (list, optional): Specific misconfiguration 1 issues to focus on
        specific_issues_2 (list, optional): Specific misconfiguration 2 issues to focus on

    Returns:
        str: Complete unified instruction
    """

    # Load original ADL if not provided
    if original_adl is None and adl_name is not None:
        original_adl = preprocessing.load_adl(adl_name)
    elif original_adl is None:
        original_adl = current_adl if current_adl else ""

    # Generate execution paths from original ADL
    formatted_paths = ""
    if original_adl:
        try:
            all_paths = preprocessing.preprocess_with_adl(original_adl)
            formatted_paths = "\n".join([f"Path {idx}: {' -> '.join(path)}" for idx, path in enumerate(all_paths, 1)])
        except Exception:
            formatted_paths = "Unable to generate execution paths"

    # Use current_adl as error ADL, fallback to original_adl
    error_adl = current_adl if current_adl else original_adl

    # Generate connector information from error ADL
    connector_information = ""
    if error_adl:
        try:
            connector_information = preprocessing.format_connector_information(error_adl)
        except Exception:
            connector_information = "Unable to extract connector information"

    # Generate misconfiguration analysis - exactly following the original logic
    issues_string1 = ""
    issues_string2 = ""

    if task_type == "misconfiguration_1":
        # For misconfiguration 1: use specific issues if provided, otherwise generate fresh
        if specific_issues_1 is not None:
            issues_string1 = "\n".join(issue + "\n" for issue in specific_issues_1)
        elif error_adl:
            try:
                issues_1, _ = misconfiguration_detection.get_misconfiguration_information1(error_adl)
                issues_string1 = "\n".join(issue + "\n" for issue in issues_1)
            except Exception:
                issues_string1 = "Unable to analyze misconfiguration type 1"
        issues_string2 = "Not analyzed for this task"

    elif task_type == "misconfiguration_2":
        # For misconfiguration 2: use specific issues if provided, otherwise generate fresh
        if specific_issues_2 is not None:
            issues_string2 = "\n".join(issue + "\n" for issue in specific_issues_2)
        elif error_adl:
            try:
                issues_2, _ = misconfiguration_detection.get_misconfiguration_information2(error_adl)
                issues_string2 = "\n".join(issue + "\n" for issue in issues_2)
            except Exception:
                issues_string2 = "Unable to analyze misconfiguration type 2"
        issues_string1 = "Not analyzed for this task"

    elif error_adl:
        # Generate both types for general tasks
        try:
            issues_1, _ = misconfiguration_detection.get_misconfiguration_information1(error_adl)
            issues_string1 = "\n".join(issue + "\n" for issue in issues_1) if issues_1 else "No misconfiguration type 1 detected"

            issues_2, _ = misconfiguration_detection.get_misconfiguration_information2(error_adl)
            issues_string2 = "\n".join(issue + "\n" for issue in issues_2) if issues_2 else "No misconfiguration type 2 detected"
        except Exception:
            issues_string1 = "Unable to analyze misconfiguration type 1"
            issues_string2 = "Unable to analyze misconfiguration type 2"

    # Format the unified artifact
    full_unified_instruction = unified_instruction_instruct + "\n" + simplified_wrighthash_documentation + "\n" + Unified_artifact.format(
        original_adl=original_adl or "Not provided",
        new_requirement=new_requirement or "Not provided",
        formatted_paths=formatted_paths or "Not available",
        adl=error_adl or "Not provided",
        connector_information=connector_information or "Not available",
        issues_string1=issues_string1 or "Not analyzed",
        issues_string2=issues_string2 or "Not analyzed"
    )

    _save_skill("unified_skill.md", full_unified_instruction)
    return full_unified_instruction
