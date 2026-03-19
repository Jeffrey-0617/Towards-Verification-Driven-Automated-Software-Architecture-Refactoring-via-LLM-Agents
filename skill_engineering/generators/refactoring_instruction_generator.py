from skill_engineering.instructions.refactoring_instruction import refactoring_instruction_instruct, refactoring_architecture_artifacts, simplified_wrighthash_documentation, syntax_rules_violation_fixing_artifacts, syntax_rules_violation_fixing_instruction
import helpers.preprocessing as preprocessing
import os

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

def _save_skill(filename, content):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, filename), "w") as f:
        f.write(content)

def generate_refactoring_instruction(adl_name, new_requirement):
    # get the formatted paths
    adl = preprocessing.load_adl(adl_name)
    all_paths = preprocessing.preprocess_with_adl(adl)
    formatted_paths = "\n".join([f"Path {idx}: {' -> '.join(path)}" for idx, path in enumerate(all_paths, 1)])
    full_refactoring_instruction =refactoring_instruction_instruct + "\n" + simplified_wrighthash_documentation+ "\n" + refactoring_architecture_artifacts.format(adl=adl, new_requirement=new_requirement, formatted_paths=formatted_paths)
    _save_skill("refactoring_skill.md", full_refactoring_instruction)
    return full_refactoring_instruction

def generate_correction_instruction(adl, liveness_properties):
    # get the formatted paths
    all_paths = preprocessing.preprocess_with_adl(adl)
    formatted_paths = "\n".join([f"Path {idx}: {' -> '.join(path)}" for idx, path in enumerate(all_paths, 1)])
    full_correction_instruction =refactoring_instruction_instruct + "\n" + simplified_wrighthash_documentation+ "\n" + refactoring_architecture_artifacts.format(adl=adl, new_requirement=liveness_properties, formatted_paths=formatted_paths)
    _save_skill("correction_skill.md", full_correction_instruction)
    return full_correction_instruction

def generate_refactoring_instruction_baseline(adl_name, new_requirement):
    adl = preprocessing.load_adl(adl_name)
    full_refactoring_instruction =refactoring_instruction_instruct + "\n" + "Please refactor the provided Software architecture in Wright# Specification to accomodate the new requirement." + "\n" + "Original ADL:\n " + adl + "\n" + "New Requirement: " + new_requirement
    _save_skill("refactoring_baseline_skill.md", full_refactoring_instruction)
    return full_refactoring_instruction

def generate_fixing_syntax_rules_violation_instruction(adl):
    full_fixing_instruction =syntax_rules_violation_fixing_instruction + "\n" + syntax_rules_violation_fixing_artifacts.format(adl=adl)
    _save_skill("fixing_syntax_skill.md", full_fixing_instruction)
    return full_fixing_instruction
