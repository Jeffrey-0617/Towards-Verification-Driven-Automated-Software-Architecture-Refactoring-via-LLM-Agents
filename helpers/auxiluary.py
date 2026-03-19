import re
from helpers.preprocessing import extract_connector_order

def extract_adl(llm_response):
    """
    Extract ADL code from LLM response.
    
    Args:
        llm_response (str): The response from the LLM containing ADL code
        
    Returns:
        str: The extracted ADL code, or None if not found
    """
    if not llm_response:
        return None
    
    # Remove any markdown code block markers
    adl_text = llm_response.strip()
    
    # Try to extract from markdown code blocks
    code_block_pattern = r'```(?:adl)?\s*\n(.*?)\n```'
    code_matches = re.findall(code_block_pattern, adl_text, re.DOTALL)
    if code_matches:
        adl_text = code_matches[0].strip()
    
    # If no code block found, try to find ADL content directly
    # Look for system, component, or connector declarations
    adl_patterns = [
        r'(connector\s+\w+\s*\{.*?\})',  # Connector block
        r'(component\s+\w+\s*\{.*?\})',  # Component block
        r'(system\s+\w+\s*\{.*?\})',  # System block
    ]
    
    extracted_parts = []
    for pattern in adl_patterns:
        matches = re.findall(pattern, adl_text, re.DOTALL)
        extracted_parts.extend(matches)
    
    if extracted_parts:
        # Combine all extracted parts
        adl_text = '\n'.join(extracted_parts)
    
    # Clean up the extracted text
    adl_text = re.sub(r'^\s*//.*$', '', adl_text, flags=re.MULTILINE)  # Remove single-line comments
    adl_text = re.sub(r'/\*.*?\*/', '', adl_text, re.DOTALL)  # Remove multi-line comments
    adl_text = re.sub(r'^\s*$', '', adl_text, flags=re.MULTILINE)  # Remove empty lines
    adl_text = adl_text.strip()
    
    # Validate that we have actual ADL content
    if not adl_text or not any(keyword in adl_text.lower() for keyword in ['system', 'component', 'connector']):
        return None
    
    return adl_text

def extract_declare_attach_statements(response_text):
    """
    Extract only declare and attach statements from post-processing response.
    
    Args:
        response_text (str): The response from the post-processing agent
        
    Returns:
        list: List of declare and attach statements
    """
    if not response_text:
        return []
    
    # Clean up the response text
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    code_block_pattern = r'```(?:adl)?\s*\n(.*?)\n```'
    code_matches = re.findall(code_block_pattern, text, re.DOTALL)
    if code_matches:
        text = code_matches[0].strip()
    
    # Extract declare statements
    declare_pattern = r'declare\s+\w+\s*=\s*\w+\s*;'
    declare_statements = re.findall(declare_pattern, text, re.MULTILINE)
    
    # Extract attach statements
    attach_pattern = r'attach\s+[\w\.]+\(\)\s*=\s*[^;]+;'
    attach_statements = re.findall(attach_pattern, text, re.MULTILINE)
    
    # Combine and return
    all_statements = declare_statements + attach_statements
    
    # Clean up each statement (remove extra whitespace)
    cleaned_statements = []
    for statement in all_statements:
        cleaned = re.sub(r'\s+', ' ', statement.strip())
        cleaned_statements.append(cleaned)
    
    return cleaned_statements

def split_into_two_roles(connector_roles):
    input_roles = set()
    output_roles = set()
    for i in range(len(connector_roles)):
        input_roles.add(connector_roles[i][1])
        output_roles.add(connector_roles[i][2])
        if connector_roles[i][3] != None:
            output_roles.add(connector_roles[i][3])
    return input_roles, output_roles

def detect_output_role_issues(attachments, connector_roles):
    attached_ports = []
    attached_IR = []
    attached_OR = []
    matching_attachment_COR = []
    matching_attachment_CIR = []
    COR = None
    CT = None
    
    """Detects connectors with the same output role attached to multiple ports."""
    from collections import defaultdict

    connector_role_map = defaultdict(list)

    # get the output_roles from connector_roles
    input_roles, output_roles = split_into_two_roles(connector_roles)

    # Parse attachments to collect output roles per connector
    for line in attachments:
        match = re.match(r'attach\s+([\w.]+)\(\)\s*=\s*(.+);', line)
        if match:
            port = match.group(1)
            roles = re.findall(r'([\w]+)\.([\w]+)', match.group(2))
            for connector, role in roles:
                if role in output_roles:
                    connector_role_map[(connector, role)].append(port)
                    
                    
    # Find connectors with multiple ports using the same output role
    issues = []
    for (connector, role), ports in connector_role_map.items():
        if len(ports) > 1:
            issues.append({
                "connector": connector,
                "role": role,
                "ports": ports
            })
    # find corresponding input role
    CORs = []
    CIRs = []
    CTs = []
    if issues:
        for issue in issues:
            for i in range(len(connector_roles)):
                if issue['role'] == connector_roles[i][2] or issue['role'] == connector_roles[i][3]:
                    input_rolename = connector_roles[i][1]
                    connector_type = connector_roles[i][0]
            CORs.append(f"{issue['connector']}.{issue['role']}")
            CIRs.append(f"{issue['connector']}.{input_rolename}")
            CTs.append(f"{connector_type}")
    else:
        return issues, matching_attachment_CIR, matching_attachment_COR
        
    # find the attachement lines containing the target role
    for (CIR, COR) in zip(CIRs, CORs):
        for idx, line in enumerate(attachments, start=1):
            if CIR in line:
                matching_attachment_CIR.append(line)
            if COR in line:
                matching_attachment_COR.append(line)
    
    #from attachment COR and CIR, detete all the component.port pairs and connector.inputrole pairs and outputrole pairs
    # Parse attachments to collect output roles per connector
    for line in (matching_attachment_CIR + matching_attachment_COR):
        match = re.match(r'attach\s+([\w.]+)\(\)\s*=\s*(.+);', line)
        if match:
            attached_ports.append(match.group(1)) 
            roles = re.findall(r'([\w]+)\.([\w]+)(?:\((\d+)\))?', match.group(2))
            for connector, role, param in roles:
                role_with_params = f"{connector}.{role}({param})" if param else f"{connector}.{role}()"  # Append (23) if present
                if role in input_roles:  # Check role without ()
                    attached_IR.append(role_with_params)  # Append with (23) if exists
                if role in output_roles:  # Check role without ()
                    attached_OR.append(role_with_params)  # Append with (23) if exists
    attached_ports = list(set(attached_ports))
    attached_IR = list(set(attached_IR))
    attached_OR = list(set(attached_OR))
        
    return issues, matching_attachment_CIR, matching_attachment_COR

def extract_attach_statements(adl_text):
    """
    Extract all 'attach' statements from the ADL text into a list.
    
    Args:
        adl_text (str): The ADL source code as a string.
    
    Returns:
        list: A list of attach statements.
    """
    # Regular expression pattern to match attach statements
    pattern = r'attach\s+.*?;'
    
    # Find all matches using regex
    attach_statements = re.findall(pattern, adl_text)
    
    return attach_statements

def extract_assert_statements(text: str):
    """
    Extracts all 'assert' statements from a given block of text.

    Args:
        text (str): Input string containing possible assert statements.

    Returns:
        List[str]: A list of extracted assert statements.
    """
    # # Match lines that start with 'assert' and continue until the end of the line
    # pattern = r'assert\s.+?;'
    # matches = re.findall(pattern, text)
    # return matches

    # Match lines that start with 'assert' and continue until the end of the line
    pattern = r'^\s*assert\s.*$'
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    return matches

def parse_assert_components(assert_stmt: str):
    """
    Extracts the source and target component.port from an assert statement.
    Example: 'PassengerUI.call.callride -> <> TripMgmt.accept.acknowledged'
    returns 'PassengerUI.call', 'TripMgmt.accept'
    """
    match = re.search(r'assert\s+\w+\s*\|=\s*\[\]\s*\((.*?)\s*->\s*<>?\s*(.*?)\)', assert_stmt)
    if match:
        src_parts = match.group(1).strip().split('.')[0:2]
        tgt_parts = match.group(2).strip().split('.')[0:2]
        return '.'.join(src_parts), '.'.join(tgt_parts)
    return None, None

def match_asserts_to_paths(asserts, paths):
    """
    Matches each assert to a path index if both source and target appear in the same path.
    Returns a list of (assert, path_index or 'not existing') tuples.
    """
    results = []
    for stmt in asserts:
        src, tgt = parse_assert_components(stmt)
        found = False
        for i, path in enumerate(paths):
            if src in path and tgt in path:
                # Check order only if both exist
                if path.index(src) < path.index(tgt):
                    results.append((stmt, i))
                    found = True
                    break
        if not found:
            results.append((stmt, "not existing"))
    return results