from skill_engineering.instructions.misconfiguration_handling_instruction import misconfiguration_handling_instruction_instruct_1, misconfiguration_handling_architecture_artifacts_1, misconfiguration_rule_1
from skill_engineering.instructions.misconfiguration_handling_instruction import misconfiguration_handling_instruction_instruct_2, misconfiguration_handling_architecture_artifacts_2, misconfiguration_rule_2
import helpers.preprocessing as preprocessing
import helpers.misconfiguration_detection as misconfiguration_detection
import os

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

def _save_skill(filename, content):
    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(os.path.join(SKILLS_DIR, filename), "w") as f:
        f.write(content)

def generate_misconfiguration_handling_instruction_1(adl_text):
    adl = adl_text
    connector_information = preprocessing.format_connector_information(adl)
    issues, illegal_pattern = misconfiguration_detection.get_misconfiguration_information1(adl)
    issues_string = "\n".join(issue +"\n" for issue in issues)
    full_misconfiguration_handling_instruction = misconfiguration_handling_instruction_instruct_1 + "\n" + misconfiguration_rule_1+ "\n" + misconfiguration_handling_architecture_artifacts_1.format(connector_information=connector_information, issues_string=issues_string)
    _save_skill("misconfiguration_1_skill.md", full_misconfiguration_handling_instruction)
    return full_misconfiguration_handling_instruction

def generate_misconfiguration_handling_instruction_2(adl_text):
    adl = adl_text
    issues, illegal_pattern = misconfiguration_detection.get_misconfiguration_information2(adl)
    issues_string = "\n".join(issue +"\n" for issue in issues)
    full_misconfiguration_handling_instruction = misconfiguration_handling_instruction_instruct_2 + "\n" + misconfiguration_rule_2+ "\n" + misconfiguration_handling_architecture_artifacts_2.format(issues_string=issues_string)
    _save_skill("misconfiguration_2_skill.md", full_misconfiguration_handling_instruction)
    return full_misconfiguration_handling_instruction
