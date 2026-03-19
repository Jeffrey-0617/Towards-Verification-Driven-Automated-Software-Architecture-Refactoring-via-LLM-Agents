import re
import requests
from helpers.preprocessing import load_adl, preprocess_with_adl, identify_liveness_assert_with_adl

def verify_adl(adl_with_assertions):
    # Update with your API's endpoint
    url = "http://0.0.0.0:8080/api/adlapi/verify"  # Update with your API's endpoint
    data = {
        "model": "test",
        "code": adl_with_assertions
    }

    try:
        response = requests.post(url, json=data, timeout=30)  # 30 second timeout
        #print("Response Status Code:", response.status_code)
        #print("Response Data:", response.json())  # If the response is JSON
        VS = response.json()
    except Exception as e:
        print("Error occurred:", e)
        return "error"
    return VS

def extract_attach_statements(adl_text):
    """
    Extracts all 'attach' statements from the ADL text and returns them as a list.

    Args:
        adl_text (str): Full ADL text containing attach statements.

    Returns:
        List[str]: A list of attach statements as strings.
    """
    # Regex pattern to match all attach statements
    attach_pattern = r'attach\s+[\w\.]+\(\)\s*=\s*.*?;'

    # Find all attach statements (including multi-branch)
    attach_statements = re.findall(attach_pattern, adl_text, re.DOTALL)

    # Clean up and return the attach statements
    return [stmt.strip() for stmt in attach_statements]
def parse_paths(paths_text):
    """
    Parses the input paths text and returns a list of paths, where each path
    is a list of nodes.
    """
    paths = []
    lines = paths_text.strip().split("\n")
    for line in lines:
        # Extract the path using regex
        match = re.search(r'Path \d+:\s*(.+)', line)
        if match:
            path_str = match.group(1)
            nodes = [node.strip() for node in path_str.split("->")]
            paths.append(nodes)
    return paths

def extract_lhs(attach_statement):
    """
    Extracts the component port from an attach statement.
    For example, "attach PassengerUI.call() = callwire.requester(10);"
    returns "PassengerUI.call".
    """
    m = re.search(r'^attach\s+([\w\.]+)\(\)\s*=', attach_statement)
    if m:
        return m.group(1)
    return None

def select_attachments_for_paths(paths, attach_statements):
    """
    For each path, selects the relevant attach statements based on the nodes in the path.
    Avoids duplicates.
    """
    # Build a dictionary mapping component ports to attach statements
    attach_dict = {}
    for stmt in attach_statements:
        comp_port = extract_lhs(stmt)
        if comp_port:
            attach_dict[comp_port] = stmt

    # Iterate over each path and collect relevant attach statements
    all_selected_attachments = []

    for path_idx, path_nodes in enumerate(paths):
        selected_attachments = set()  # To avoid duplicates
        for node in path_nodes:
            if node in attach_dict:
                selected_attachments.add(attach_dict[node])
        all_selected_attachments.append((path_idx, list(selected_attachments)))

    return all_selected_attachments

def fix_last_brace_indentation(adl_code: str):
    lines = adl_code.split("\n")
    
    # Find the last non-empty line that contains only '}'
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            lines[i] = "}"
            break
    
    return "\n".join(lines)

def update_adl_with_new_attachments(original_adl, new_attachments, new_execute_line):
    cleaned_adl = re.sub(r'attach\s+[\w\.]+\(\)\s*=.*?;\s*', '', original_adl, flags=re.DOTALL)
    cleaned_adl = re.sub(r'execute\s+[^;\n]+;?', '', cleaned_adl, flags=re.DOTALL)
    cleaned_adl = re.sub(r'\n\s*\n', '\n', cleaned_adl).strip()

    system_block_pattern = r'(system\s+\w+\s*{)'
    match = re.search(system_block_pattern, cleaned_adl)
    if match:
        # Prepare the new attachments string
        new_attachments_str = "\n"+ new_attachments + "\n\t " + new_execute_line

        # Insert new attachments inside the system block
        updated_adl = re.sub(system_block_pattern, r'\1' + new_attachments_str, cleaned_adl)

        declare_pattern = r'(declare\s+\w+\s*=\s*\w+\s*;)'  # Matches all declare statements
        declares = list(re.finditer(declare_pattern, cleaned_adl, flags=re.MULTILINE))

        if declares:
            last_declare = declares[-1]
            # Insert new attachments after the last declare
            insertion_point = last_declare.end()
            updated_adl = cleaned_adl[:insertion_point] + new_attachments_str + cleaned_adl[insertion_point:]
    else:
        raise ValueError("System block not found in ADL.")
    
    # the last bracket will have influence on generated paths
    updated_adl = fix_last_brace_indentation(updated_adl)

    return updated_adl

def get_divided_adls(adl_text):
    paths = preprocess_with_adl(adl_text)
    attach_statements = extract_attach_statements(adl_text)
    selected_attachments = select_attachments_for_paths(paths, attach_statements)

    adl_variants = []

    for path_idx, attaches in selected_attachments:
        attachment_string = "\t " + "\n\t ".join(attaches)
        lhs_list = [extract_lhs(stmt) for stmt in attaches]
        lhs_list = [f"{lhs}()" for lhs in lhs_list]
        execute_line = "execute " + " || ".join(lhs_list) + ";"

        # Compose the ADL version for this path
        new_adl = update_adl_with_new_attachments(adl_text, attachment_string, execute_line)
        assertions = identify_liveness_assert_with_adl(new_adl)
        full_adl = new_adl + "\n" + "\n".join(assertions)

        adl_variants.append(full_adl)

    return adl_variants  # List of full ADLs per path



def get_verification_results_with_adl(adl_text):
    divided_adls = get_divided_adls(adl_text)
    final_result = "valid"
    #print("-" * 50)
    for adl_variant in divided_adls:
        VS = verify_adl(adl_variant)
        if isinstance(VS, dict):
            print(VS.get('Message', 'Unknown error'))
            print(adl_variant)
            print("-" * 50)
            final_result = "invalid"
        else:
            for vs in VS:
                if vs['result'] == "invalid":
                    print(vs['fullResultString'])
                    print(adl_variant)
                    print("-" * 50)
                    final_result = "invalid"
    return final_result


def extract_assertion_components(assertion):
    """
    Extracts start and end components from an assertion.
    Example: "assert rideshare |= [] (PassengerUI.call.callride -> <> DriverUI.notify.notified);"
    Returns: ("PassengerUI.call", "DriverUI.notify")
    """
    # Pattern to match the assertion format: (start.action -> <> end.action)
    pattern = r'assert\s+\w+\s+\|=\s+\[\]\s+\(([^.]+\.[^.]+)\.[^.]+\s+->\s+<>\s+([^.]+\.[^.]+)\.[^)]+\)'
    match = re.search(pattern, assertion)
    if match:
        start_component = match.group(1)
        end_component = match.group(2)
        return (start_component, end_component)
    return None

def get_tailored_assertions_for_path(path_nodes, assertions):
    """
    Gets the tailored assertions for a specific path based on the path nodes.
    An assertion matches a path if both its start and end components exist in the path,
    and the start component appears before the end component in the path.
    If multiple assertions match the same path, only the one with the longest gap
    (covering the most components) is retained.
    """
    if not path_nodes or len(path_nodes) < 2:
        return []
    
    valid_assertions = []
    
    for assertion in assertions:
        components = extract_assertion_components(assertion)
        if components:
            start_comp, end_comp = components
            
            # Find the indices of start and end components in the path
            start_index = -1
            end_index = -1
            
            for i, node in enumerate(path_nodes):
                if node == start_comp:
                    start_index = i
                elif node == end_comp:
                    end_index = i
            
            # Check if both components exist in path and start comes before end
            if start_index != -1 and end_index != -1 and start_index < end_index:
                gap_size = end_index - start_index + 1  # Number of components covered
                valid_assertions.append((assertion, gap_size, start_index, end_index))
    
    # If no valid assertions found, return empty list
    if not valid_assertions:
        return []
    
    # Find the maximum gap size
    max_gap = max(valid_assertions, key=lambda x: x[1])[1]
    
    # Keep only assertions with the maximum gap size
    longest_gap_assertions = [assertion for assertion, gap_size, _, _ in valid_assertions if gap_size == max_gap]
    
    return longest_gap_assertions

def get_divided_adls_with_GraphRAG_properties(adl_text, assertions):
    paths = preprocess_with_adl(adl_text)
    attach_statements = extract_attach_statements(adl_text)
    selected_attachments = select_attachments_for_paths(paths, attach_statements)

    adl_variants = []

    for path_idx, attaches in selected_attachments:
        attachment_string = "\t " + "\n\t ".join(attaches)
        lhs_list = [extract_lhs(stmt) for stmt in attaches]
        lhs_list = [f"{lhs}()" for lhs in lhs_list]
        execute_line = "execute " + " || ".join(lhs_list) + ";"

        # Compose the ADL version for this path
        new_adl = update_adl_with_new_attachments(adl_text, attachment_string, execute_line)
        
        # Get tailored assertions for this path
        path_nodes = paths[path_idx] if path_idx < len(paths) else []
        tailored_assertions = get_tailored_assertions_for_path(path_nodes, assertions)
        
        full_adl = new_adl + "\n" + "\n".join(tailored_assertions)
        adl_variants.append(full_adl)

    return adl_variants  # List of full ADLs per path



def get_verification_results_with_adl_with_GraphRAG_properties(adl_text, assertions):
    divided_adls = get_divided_adls_with_GraphRAG_properties(adl_text, assertions)
    final_result = "valid"
    #print("-" * 50)
    for adl_variant in divided_adls:
        VS = verify_adl(adl_variant)
        if isinstance(VS, dict):
            print(VS.get('Message', 'Unknown error'))
            print(adl_variant)
            print("-" * 50)
            final_result = "invalid"
        else:
            for vs in VS:
                if vs['result'] == "invalid":
                    print(vs['fullResultString'])
                    print(adl_variant)
                    print("-" * 50)
                    final_result = "invalid"
    return final_result