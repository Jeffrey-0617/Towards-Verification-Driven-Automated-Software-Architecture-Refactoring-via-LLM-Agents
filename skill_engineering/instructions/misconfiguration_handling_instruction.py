misconfiguration_handling_instruction_system_instruction = """
You are an expert for solving the misconfiguration in the architecture design model in Wright#. Your task is to modify the design model based on the misconfiguration rules and provided information. The Output only contains the script of refactored architecture design model.
"""

misconfiguration_handling_instruction_instruct_1 = """You are provided with misconfiguration rules including the misconfiguration rules and corresponding solutions. Please follow the following steps to fix the illegal attachment statements in the given Wright# scripts step by step.

1. Please undertstand the provided misconfiguration rules and coresponding solutions and behvaior flow of the solutions.
2. Please undertstand the provided connector definition and connector roles.
3. Based on these understandings, please refine the provided Wright# scripts to solve the misconfiguration. Please only output the refactored Wright# scripts.
"""

misconfiguration_rule_1 = """
#################################################
Multiple Attachment Rules (Constraint):
#################################################

1. Rule 1: Each input role of a connector instance can only be attached to one component port.
- Invalid Design:
declare connector = CSConnector;
attach ComponentA.portA() = connector.requester(14); // output role
attach ComponentB.portB() = connector.responder(); // input role
attach ComponentC.portC() = connector.responder(); // the same input role is attached to two different component ports: componentB.portB and componentC.portC

- Solution: Use separate connector instances with their output role connected via coupling.
declare connector1 = CSConnector;
declare connector2 = CSConnector;
attach ComponentA.portA() = connector1.requester(14) <*> connector2.requester(18);
attach ComponentB.portB() = connector1.responder();
attach ComponentC.portC() = connector2.responder();

- Behavior Flow of the correct version:
ComponentA.portA → connector1.requester(14) → connector1.responder → ComponentB.portB → connector2.requester(18) → connector2.responder → ComponentC.portC

2. Rule 2: One component port can only be attached to at most one input role.
- Invalid Design:
declare connector1 = CSConnector;
declare connector2 = CSConnector;
attach ComponentA.portA() = connector1.requester(14); //output role
attach ComponentB.portB() = connector2.requester(19); //output role
attach ComponentC.portC() = connector1.responder() <*> connector2.responder(); // violation of the rule, two input roles are attached to the same component port

- Solution1: combine these two connectors to have two seperate flows.
declare connector = CSConnector;
attach ComponentA.portA() = connector.requester(14);
attach ComponentB.portB() = connector.requester(19);
attach ComponentC.portC() = connector.responder();

- Behavior Flows of the correct version:
First flow: ComponentA.portA → connector.requester(14) → connector.responder → ComponentC.portC
Second flow: ComponentB.portB → connector.requester(19) → connector.responder → ComponentC.portC

- Solution2: make these components in one flow.
declare connector = CSConnector;
attach ComponentA.portA() = connector1.requester(14);
attach ComponentB.portB() = connector1.responder() <*> connector2.requester(19);
attach ComponentC.portC() = connector2.responder();

- Behavior Flows of the correct version:
ComponentA.portA → connector1.requester(14) → connector1.responder → ComponentB.portB → connector2.requester(19) → connecto2.responder → ComponentC.portC
"""

misconfiguration_handling_architecture_artifacts_1 = """
#################################################
Architecture artifacts:
#################################################

Connector information:\n{connector_information}
Provided Wright# scripts with misconfiguration analysis:\n{issues_string}

*** ONLY Output the final fixed Wright# scripts (new declaration + attachments) ***
"""

misconfiguration_handling_instruction_instruct_2 = """You are provided with misconfiguration rules and illegal attachment statements. Please follow fix the illegal attachment statements in the given Wright# scripts.
"""

misconfiguration_rule_2 = """
One port can only be attached to one input role.

"""

misconfiguration_handling_architecture_artifacts_2 = """
The following ports are illegally attached to multiple input roles, violating the constraint that each port can only be attached to one input role:\n{issues_string}
Constraint: Each port on the left-hand side can only be attached to one input role. To handle multiple input roles, you need to create additional ports.
Request: Please provide the refined attachment statements that resolve these violations by creating new ports as needed.

*** ONLY Output the final fixed Wright# scripts (only new attachments) ***
"""