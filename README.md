# Towards Verification Driven Automated Software Architecture Refactoring via LLM Agents

A dual-agent solution for automated software architecture refactoring using Large Language Models (LLMs). The system employs collaborative agents to analyze, modify, and verify software architectures in response to new functional requirements.

## Project Structure

```
├── ADL/                        # Architecture specifications
├── agents/                     # LLM-based agents
├── GRAG_ADLSyntax/             # GraphRAG knowledge base for Wright# syntax
├── helpers/                    # Utility modules
├── skill_engineering/          # Skill system (instructions, generators, skills)
└── new_clustered_requirements.xlsx  # Input requirements dataset
```
## Prerequisites

### 1. PAT Verifier with Wright# Module API Service

Before running the full pipeline, you need to deploy the Process Analysis Toolkit (PAT) with the Wright# Module as an API service for verification purposes. Here is the [setup link](https://www.comp.nus.edu.sg/~pat/OnlineHelp/).

**Setup Instructions:**
1. Deploy the PAT Verifier with Wright# Module as a REST API service.
2. Ensure the service is accessible and running on your designated endpoint.
3. The service will be used for design verification.

### 2. LLM API Configuration

Configure your LLM API keys in the environment files:

#### Environment Configuration (`.env`)
Create a `.env` file in the project root with the following API keys:

```bash
# API Keys for Architecture Designer
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

Create a `GRAG_ADLSyntax/.env` file for GraphRAG configurations:

```bash
# API keys for the Evaluator
GRAPHRAG_API_KEY=your_openai_api_key
```


## Usage

### Running the Full Approach

The system provides a script for running the full pipeline with Claude-sonnnet-4.6 set as default:

```bash
python fullpipeline.py
```
### Model and Pipeline Configuration Options

#### Model Selection
The system supports multiple LLM models. Configure the model in the pipeline execution script.
```python
# Initialize agents
architecture_designer = ArchitectureDesigner()
architecture_designer.set_model("gpt-5.4")
# other options: various models provided by OpenAI, Gemini, and Claude
```
#### Skill Composition

The skill system (`skill_engineering/`) separates instruction based on the process. Each skill is composed in three layers:

1. **Instructions** (`instructions/`) — Static templates
2. **Generators** (`generators/`) — Functions that load runtime data, and each generator saves the fully composed result as a `.md` file in `skills/`.
3. **Skills** (`skills/`) — The generated skill files ready for agent to use.

```
Agent calls load_skill("refactoring", adl_name=..., new_requirement=...)
  → generator loads ADL, computes execution paths, formats template
  → saves to skill_engineering/skills/refactoring_skill.md
  → load_skill reads the .md file back
  → returns content to Agent
```

#### Feedback-Driven Repair Control
The dual-agent pipeline includes two specialized repair tasks that run after each evaluation. You can selectively disable them to customize the feedback-driven repair loop:

1. **Interaction deadlock and non-determinism repair** (`misconfiguration_handling`) — fixes connector misconfiguration issues such as illegal attachments that cause interaction deadlocks or non-deterministic behavior.
2. **General repair** (`fix_syntax`, `correct_validation`) — fixes syntax/semantic violations and corrects functionally incomplete properties.

```python
architecture_designer = ArchitectureDesigner()
architecture_designer.set_model("gpt-5.4")

# 1. Disable interaction deadlock and non-determinism repair only
architecture_designer.disable_function("misconfiguration_handling")

# 2. Disable general repair only
architecture_designer.disable_function("fix_syntax")
architecture_designer.disable_function("correct_validation")

# 3. Disable both to remove feedback-driven repair entirely
architecture_designer.disable_function("misconfiguration_handling")
architecture_designer.disable_function("fix_syntax")
architecture_designer.disable_function("correct_validation")
```

**Checking Configuration Status:**
```python
# View current configuration
architecture_designer.get_config_status()
```

## Input and Output
The approach takes software architecture design in Wright# specifications and new functional requirements in natural language as input.

The approach generates:
- **Refactored design**: Refactored designs with verification results
- **Agent usage statistics**: Detailed agent usage information, such as agent name, agent detailed task, task execution time.
- **Verification properties**: Produced verification properties.

## Overall

This repository is for a dual-agent collaborative framework for software architecture refactoring based on functional requirements:

1. **ArchitectureDesigner**: Handles all refactoring tasks including initial modification, interaction deadlock and non-determinism repair, and general repair.
2. **EvaluatorAgent**: Handles the verification process.

The pipeline uses an iterative feedback-driven repair loop to ensure high-quality refactoring results with continuous verification and improvement.
