import re
from collections import defaultdict
from helpers.preprocessing import extract_connector_order
from helpers.postprocessing import extract_declarations, find_rest_role_attachments

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

def split_into_two_roles(connector_roles):
    input_roles = set()
    output_roles = set()
    for i in range(len(connector_roles)):
        input_roles.add(connector_roles[i][1])
        output_roles.add(connector_roles[i][2])
        if connector_roles[i][3] != None:
            output_roles.add(connector_roles[i][3])
    return input_roles, output_roles

def get_misconfiguration_information1(adl): 
    """Detects connectors with the same output role attached to multiple ports."""
  
    connector_role_map = defaultdict(list)
    attachments = extract_attach_statements(adl)
    connector_roles = extract_connector_order(adl)

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
    illegal_pattern = []
    for (connector, role), ports in connector_role_map.items():
        if len(ports) > 1:
            issues.append({
                "connector": connector,
                "role": role,
                "ports": ports
            })

    if issues:
        issue_list = []
        for i, issue in enumerate(issues, start=1):
            issue_string = f"Issue {i}: the input role {issue['role']} of the connector {issue['connector']} ({issue['connector']}.{issue['role']}) is attached to multiple ports: {issue['ports']}"
            
            # Build the illegal pattern string
            issue_string += "\nThe illegal attachment statements are:"
            for attach_statement in list(set(attachments)):
                if issue['connector'] in attach_statement:
                    issue_string += f"\n{attach_statement.strip()}"
                    illegal_pattern.append(attach_statement.strip())
            
            issue_list.append(issue_string)
        return issue_list, illegal_pattern
    else:
        # "No misconfiguration detected"
        return [], []

def get_misconfiguration_information2(adl_text):
    connector_roles = extract_connector_order(adl_text)
    output_roles, input_roles = split_into_two_roles(connector_roles)
    attachments = extract_attach_statements(adl_text)
    # Regex pattern to extract port and roles
    attachment_pattern = re.compile(r'attach\s+([\w.]+)\(\)\s*=\s*(.*?);')

    # Store port and attached input roles and their corresponding attachments
    port_input_roles = defaultdict(list)
    port_attachments = defaultdict(set)  # Using set to avoid duplicate attachments

    # Process attachments
    for attachment in attachments:
        match = attachment_pattern.search(attachment)
        if match:
            port = match.group(1)  # Extract port name
            roles = match.group(2).split('<*>')  # Handle multiple roles
            for role in roles:
                role = role.strip()
                role_name = role.split('(')[0].split('.')[-1]  # Extract role name
                if role_name in input_roles:
                    port_input_roles[port].append(role)  # Store full role reference
                    port_attachments[port].add(attachment)  # Store unique attachment

    # Identify ports with multiple input roles and their attachments using a for loop
    violations = {}
    for port, roles in port_input_roles.items():
        if len(roles) > 1:
            violations[port] = {
                'input_roles': roles,
                'attachments': list(port_attachments[port])
            }

    if violations:
        issue_list = []
        illegal_pattern = []
        for i, (port, info) in enumerate(violations.items(), start=1):
            issue_string = (
                f"Issue {i}: the port {port} is attached to multiple input roles: {info['input_roles']}"
            )
            issue_string += "\nThe illegal attachment statement is:"
            for attachment in info['attachments']:
                issue_string += f"\n{attachment}"
                illegal_pattern.append(attachment)
            # for attachment in info['attachments']:
            #     # get the connector.roles from right side of the = in the attachment
            #     connector_roles = re.findall(r'([\w]+)\.([\w]+)', attachment.split('=')[1].strip())
            #     # get connector names from connector_roles
            #     connector_names = [connector_role[0] for connector_role in connector_roles]
            #     print("connector_names:", connector_names)
            #     # go through the whole attachments and find the attachments that have the same connector names
            #     for attachment in attachments:
            #         if any(connector_name in attachment for connector_name in connector_names):
            #             issue_string += f"\n{attachment}"
            #             illegal_pattern.append(attachment)
            issue_list.append(issue_string)
        return issue_list, illegal_pattern
    else:
        # "No misconfiguration detected"
        return [],[]
    
    

