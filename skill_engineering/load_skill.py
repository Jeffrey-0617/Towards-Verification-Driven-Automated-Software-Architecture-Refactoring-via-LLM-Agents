import os

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

# Mapping from skill name to (generator_module, generator_function, output_filename)
_SKILL_REGISTRY = {
    "refactoring": (
        "skill_engineering.generators.refactoring_instruction_generator",
        "generate_refactoring_instruction",
        "refactoring_skill.md",
    ),
    "correction": (
        "skill_engineering.generators.refactoring_instruction_generator",
        "generate_correction_instruction",
        "correction_skill.md",
    ),
    "refactoring_baseline": (
        "skill_engineering.generators.refactoring_instruction_generator",
        "generate_refactoring_instruction_baseline",
        "refactoring_baseline_skill.md",
    ),
    "fixing_syntax": (
        "skill_engineering.generators.refactoring_instruction_generator",
        "generate_fixing_syntax_rules_violation_instruction",
        "fixing_syntax_skill.md",
    ),
    "misconfiguration_1": (
        "skill_engineering.generators.misconfiguration_handling_instruction_generator",
        "generate_misconfiguration_handling_instruction_1",
        "misconfiguration_1_skill.md",
    ),
    "misconfiguration_2": (
        "skill_engineering.generators.misconfiguration_handling_instruction_generator",
        "generate_misconfiguration_handling_instruction_2",
        "misconfiguration_2_skill.md",
    ),
    "unified": (
        "skill_engineering.generators.unified_instruction_generator",
        "generate_unified_instruction",
        "unified_skill.md",
    ),
}

# Argument mapping: skill_name -> how kwargs map to positional/keyword args of the generator
_ARG_MAPPINGS = {
    "refactoring": lambda kw: (kw["adl_name"], kw["new_requirement"]),
    "correction": lambda kw: (kw["adl"], kw["liveness_properties"]),
    "refactoring_baseline": lambda kw: (kw["adl_name"], kw["new_requirement"]),
    "fixing_syntax": lambda kw: (kw["adl"],),
    "misconfiguration_1": lambda kw: (kw["adl"],),
    "misconfiguration_2": lambda kw: (kw["adl"],),
    "unified": None,  # pass kwargs directly
}


def load_skill(skill_name, **kwargs):
    """
    Generate a skill prompt, save it to a .md file, read it back, and return it.

    Args:
        skill_name (str): Name of the skill (e.g., "refactoring", "correction", "unified")
        **kwargs: Arguments passed to the underlying generator function

    Returns:
        str: The generated skill prompt content
    """
    if skill_name not in _SKILL_REGISTRY:
        raise ValueError(f"Unknown skill: {skill_name}. Available: {list(_SKILL_REGISTRY.keys())}")

    module_path, func_name, md_filename = _SKILL_REGISTRY[skill_name]

    # Import the generator function
    import importlib
    module = importlib.import_module(module_path)
    generator_func = getattr(module, func_name)

    # Call the generator with appropriate arguments
    arg_mapper = _ARG_MAPPINGS[skill_name]
    if arg_mapper is None:
        # Pass kwargs directly (for unified which takes keyword args)
        generator_func(**kwargs)
    else:
        args = arg_mapper(kwargs)
        generator_func(*args)

    # Read back from the .md file (source of truth)
    md_path = os.path.join(SKILLS_DIR, md_filename)
    with open(md_path, "r") as f:
        return f.read()


def load_system_skill(skill_name):
    """
    Load a static system instruction skill from a .md file.

    Args:
        skill_name (str): Name of the system skill (e.g., "unified_system_instruction")

    Returns:
        str: The system instruction content
    """
    md_path = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    with open(md_path, "r") as f:
        return f.read()
