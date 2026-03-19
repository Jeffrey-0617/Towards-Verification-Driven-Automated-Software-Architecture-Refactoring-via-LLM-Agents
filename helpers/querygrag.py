# ----------------------
# GRAG execution
# ----------------------
import tiktoken
from graphrag.cli.query import run_local_search
from pathlib import Path
from helpers.auxiluary import extract_assert_statements, match_asserts_to_paths
from helpers.preprocessing import preprocess_with_adl, get_all_verification_properties
from helpers.divide_adl import get_verification_results_with_adl, get_verification_results_with_adl_with_GraphRAG_properties

# Embedding model token limit (text-embedding-3-small)
_EMBEDDING_MAX_TOKENS = 8000


def _truncate_to_token_limit(text: str, max_tokens: int = _EMBEDDING_MAX_TOKENS) -> str:
    """Truncate text to fit within the embedding model's token limit."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    if len(tokens) > max_tokens:
        text = enc.decode(tokens[:max_tokens])
    return text


def get_validation_assert(original_paths: str, current_paths: str, ADL: str, new_requirement: str, original_asserts: str):
    # Point GraphRAG to the project config directory (GRAG_ADLSyntax/)
    repo_root = Path(__file__).resolve().parents[1]
    grag_dir = repo_root / "GRAG_ADLSyntax"

    # Query for GraphRAG entity embedding/matching — everything except the full ADL
    query = f"""Original System Execution Paths:
{original_paths}

Original liveness properties:
{original_asserts}

Updated System Execution Paths:
{current_paths}

New Functional Requirement:
{new_requirement}"""
    query = _truncate_to_token_limit(query)

    # Full detailed context passed via response_type so it reaches the LLM system prompt
    detailed_context = f"""multiple paragraphs

---Task Context---

You are an expert in formal verification and Wright# ADL.
Based on the given input, your task is to output the liveness properties for validation in the form of assert statements by following the steps below:
(1) verify the updated system behavior against the new requirements (by firstly strictly and rigorously consider if the new requirements can be achieved by the updated system behavior, if so generate the properties for the new requirements. If partially achieved (like some processes could contribute to better achieve the new requirements but not appeared) or even not achieved, generate the properties that you think it is necessary to achieve the new requirements even such elements are not present in the provided updated specification)
(2) identify the original system behavior should be preserved and not affected by the new requirements (by firstly identify the original system behavior should be preserved and should not be affected by the new requirements, then identify the properties for these behaviors from the provided original liveness properties)
The liveness properties should be in the form: assert systemname |= [] (initial_componentname.portname.eventname -> <> target_componentname.portname.eventname)

You are provided with:
1. Original System Execution Paths:
{original_paths}

2. Original liveness properties:
{original_asserts}

3. Updated System Execution Paths:
{current_paths}

4. Updated Wright# ADL Specification:
{ADL}

5. New Functional Requirement:
{new_requirement}

Output full validation properties, nothing else"""

    response, context = run_local_search(
        query=query,
        root_dir=grag_dir,
        community_level=2,
        response_type=detailed_context,
        streaming=False,
        data_dir=grag_dir / "output",
        config_filepath=grag_dir / "settings.yaml",
    )
    return response

def validation_verification(original_adl, adl, new_requirement):
    # Validation
    # Generate the Paths
      

    original_paths = ""
    paths = preprocess_with_adl(original_adl)
    for idx, path in enumerate(paths, 1):
        original_paths += f"Path {idx}: {' -> '.join(path)}\n"

    original_asserts = get_all_verification_properties(original_adl)

    # Validation
    current_paths = ""
    paths = preprocess_with_adl(adl)
    for idx, path in enumerate(paths, 1):
        current_paths += f"Path {idx}: {' -> '.join(path)}\n"
        
    # generate the assert statements for validation
    response = get_validation_assert(original_paths, current_paths, adl, new_requirement, original_asserts)
    asserts = extract_assert_statements(response)
    results = match_asserts_to_paths(asserts, paths)

    # Extracting existing properties from results
    existing_properties = []
    for stmt, result in results:
        if result != "not existing":
            existing_properties.append(stmt)

    verification_result = get_verification_results_with_adl_with_GraphRAG_properties(adl, existing_properties) 
    
    # Extract non-existing properties from results
    non_existing_properties = []
    for stmt, result in results:
        if result == "not existing":
            non_existing_properties.append(stmt)
    
    print("---------------------------------Results:-------------------------------\n", results)
    
    # assertions failed to be genrated, no pass 
    if asserts == []:
        exec_result =  f"Both Validation and Verification:invalid\n{adl}"
    
    # check the results
    for stmt, result in results:
        # if the existing properties are not valid, both failed
        if verification_result != "valid":
            exec_result = f"Both Validation and Verification:{verification_result}\n{adl}"
            break;
        else:
            #if pass check the functions not achieved
            if result == "not existing":
                exec_result = f"Validation: Failed; Verification:{verification_result}\n{adl}"
                break;
            else:
                exec_result = f"Both Validation and Verification:{verification_result}\n{adl}"

    return exec_result, non_existing_properties, asserts