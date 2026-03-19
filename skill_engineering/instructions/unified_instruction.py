unified_instruction_system_instruction = """
You are an expert for refactoring, repairing, and fixing misconfiguration of the architecture design model in Wright#.

CRITICAL FORMATTING REQUIREMENTS:
- Do NOT add excessive whitespace or extra indentation
- Follow the EXACT indentation pattern of the original ADL
- Match the original spacing style exactly - no extra alignment or padding
"""

unified_instruction_instruct = """
You are provided with instructions to refactor, repair, and fix misconfiguration of the provided Software architecture in Wright# Specification.

Refactoring:
Please strictly follow the steps step by step to refactor the provided Software architecture in Wright# Specification to accomodate the new requirement.
Step 1: Undertstand everything provided in the Wright# Documentation.
Step 2: Analyze the provided Software architecture in Wright# Specification.
Step 3: Refactor the Software architecture in Wright# Specification to accomodate the new requirement.
Step 4: Systematic Constraint Verification and Violation Fix
For each component in the specification, systematically verify:
- Port names are unique within the component and across all components
- List port name: [X], event names in process: [Y, Z, ...]
- Port names differ from ALL event names in their process expressions
Step 5: Output the refactored Software architecture in Wright# Specification.

Repairing:
Please strictly follow the steps step by step to identify and fix ALL violations using minimal changes.
IMPORTANT: Follow this systematic approach:
1. FIRST: List every declared connector instance and its connector type and required roles
2. SECOND: For each connector instance, verify if ALL roles are attached
3. THIRD: Verify role names match the connector definitions exactly
4. FOURTH: List every component and its ports
5. FIFTH: Verify port names are unique within the component and across all components.
6. SIXTH: Only after completing steps 1-5, make minimal fixes
7. SEVENTH: Double-check the new specification doesn't create new violations
######################################################
Wright# Syntax and Semantics Rules to Check:
#######################################################
1. Incomplete connector attachments of the declared connnector instances are not allowed. Every declared connector instance must have ALL its roles attached.
2. Connector Instance Role Inconsistency is not allowed: Role names in attach statements must match connector definitions exactly.
3. Unique port names are required: Port names must be unique within the component and across all components.
OUTPUT FORMAT:
Only output the fixed specification.


Fixing Misconfiguration 1:
Please follow the following steps to fix the illegal attachment statements in the given Wright# scripts step by step.
1. Please undertstand the provided misconfiguration rules and coresponding solutions and behvaior flow of the solutions.
2. Please undertstand the provided connector definition and connector roles.
3. Based on these understandings, please refine the provided Wright# scripts to solve the misconfiguration. Please only output the refactored Wright# scripts.
#################################################
Misconfiguration 1: Multiple Attachment Rules (Constraint):
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

Fixing Misconfiguration 2:
Please follow fix the illegal attachment statements in the given Wright# scripts.
#################################################
Misconfiguration 2: One port can only be attached to one input role.
#################################################
"""

simplified_wrighthash_documentation = """
######################################################
Wright# Documentation:
Comprehensive Syntax and Semantics Guide
#######################################################

1. Overview
Wright# is an Architecture Description Language (ADL) for modeling software architecture using the Component & Connector paradigm with formal behavioral modeling via CSP# and automated verification using PAT.

2. Core Language Elements
2.1 Connector Definitions
2.1.1 Connector Syntax:
connector <ConnectorName> {
    role <OutputRoleName>(<param>) = <ProcessExpression>;
    role <InputRoleName>() = <ProcessExpression>;
    ...
}

2.1.2 Connector Semantics:
- Defines reusable interaction patterns between components
- Data exchange occurs through channels that connect roles:
    - Output channels (ch!j): Send data from one role to another
    - Input channels (ch?j): Receive data from another role
- Output Role: Initiates interaction with parameter j, sends data j via output channels
- Input Role: Receives data via input channels
- Each role represents a participant in the communication using CSP-style processes
- The "process" event in a role's sequence determines when the attached component port executes
- CRITICAL RULE: Component ports execute in the chronological order that their roles encounter the process event during connector execution, regardless of whether the role is output or input
- Output/Input role designation determines who initiates the interaction, but process event placement determines when each attached port executes
- To determine execution order: trace through the connector's communication sequence and execute attached ports exactly when their role hits the process event

2.1.3 Example of a clinet server connector (CSConnector):
connector CSConnector {
    role requester(j) = process -> req!j -> res?j -> Skip;
    role responder() = req?j -> invoke -> process -> res!j -> responder();
}
- requester is the output role, and responder is the input role.
- requester hits process first →  requester's attached component port executes
- requester sends req!j
- responder receives req?j, triggers invoke
- responder hits process → responder's attached component port executes
- responder sends res!j, requester receives res?j

2.1.4 Connector Constraints:
- Each connector can have multiple input roles but only one output role.
- If a connector is used, each role must be attached to a component port.

2.2 Component Definitions
2.2.1 Component Syntax:
component <ComponentName> {
    port <PortName>() = <ProcessExpression>;
    ...
}

2.2.2 Component Semantics:
- Models computation units with interaction ports, which serves as the interaction interface for the component.
- Ports are associated with connector roles via attachments
- Ports execute when their attached connector role encounters the process event during connector execution

2.2.3 Example of a component:
component PassengerUI {
	 port call() = callride->call();
}
call is the name of the port, and callride is the event in its process expression. Port name must be unique, and it also must be different from the event name in its process expression.

2.2.4 Component Constraints:
- port name must be unique, and it also must be different from any event name in its process expression.

3. System Configuration
3.1 System Syntax:
system <SystemName> {
    declare <ConnectorInstanceName> = <ConnectorType>;
    attach <Component.Port()> = <ConnectorInstanceName.Role(param?)>;
    execute <ProcessComposition>;
}

3.2 System Semantics:
- Instantiates connectors and binds components to roles
- `execute` combines all processes using CSP operators (`||` for parallel)

3.3 Example of a ridecalling system:

connector CSConnector {
    role requester(j) = process -> req!j -> res?j -> Skip;
    role responder() = req?j -> invoke -> process -> res!j -> responder();
}
connector ESConnector {
	 role eventpublisher(j) = process -> pevt!j -> sevt?j -> bevt!j -> broadcast -> Skip;
	 role eventsubscriber() = bevt?j -> process -> eventsubscriber();
	 role eventstore() = pevt?j -> process -> sevt!j -> persist -> eventstore();
}
connector WRConnector {
	 role writer(j) = process -> req!j -> res?j -> Skip;
	 role writestorage() = req?j -> invoke -> process -> res!j -> writestorage();
}
component PassengerUI {
	 port call() = callride->call();
	 port pay() = issuepay->pay();
	 port plogin() = login->plogin();
}
component TripMgmt {
	 port accept() = acknowledged->accept();
}
component DriverUI {
	 port notify() = notified->notify();
}
component AssignLog {
	 port logassign() = logged->logassign();
}
component AdminUI {
	 port record() = info_recorded->record();
}
system ridecalling {
    declare callwire = CSConnector;
    declare assign = ESConnector;
    declare adminwire = WRConnector;
    attach PassengerUI.call() = callwire.requester(10);
	attach TripMgmt.accept() = callwire.responder() <*> assignwire.eventpublisher(94) <*> adminwire.writer(41);
	attach DriverUI.notify() = assignwire.eventsubscriber();
    attach AssignLog.logassign() = assignwire.eventstore()
    attach AdminUI.record() = adminwire.writestorage();
    execute PassengerUI.call() || TripMgmt.accept() || DriverUI.notify() || AssignLog.logassign();
}

- Analysis the connectors and attachmentsto understand the execution flow:
    - CSConnector: requester is the output role, and responder is the input role. Then we look at the "process" position of each role's sequence to determine the flow of associated ports. The complete flow is: PassengerUI.call() -> callwire.requester(10) -> callwire.responder() -> TripMgmt.accept()
    - ESConnector: by finding the process and matching the channels, the eventpublisher is the output role, eventstore is the first input role, and eventsubscriber is the second input role, so the execution flow is from somewhere -> assignwire.eventpublisher(94) -> assignwire.eventstore() -> AssignLog.logassign() -> assignwire.eventsubscriber() -> DriverUI.notify()
    - WRConnector: writer is the output role, writestorage is the input role. The "process" comes first in the output role, and comes second in the input role by following the channel matching rules, so the execution flow is from somewhere -> adminwire.writer(41) -> adminwire.writestorage() -> AdminUI.record()
    - However, <*> is the coupling operator is applied to state the order of the execution of the ports and roles. So after all ports attached to the connector callwire is executed, the next connector assignwire can be triggered, and the associated ports can be executed. Same for the connector assignwire. After all ports associated to assignwire are executed, the next connector adminwire can be triggered. Thus, the final execution flow of ports and roles in the ridecalling system is: PassengerUI.call() -> callwire.requester(10) -> callwire.responder() -> TripMgmt.accept() -> assignwire.eventpublisher(94) -> assignwire.eventstore() -> AssignLog.logassign() -> assignwire.eventsubscriber() -> DriverUI.notify() -> adminwire.writer(41) -> adminwire.writestorage() -> AdminUI.record()


4. Relevant Process Expressions
| Syntax | Description |
|--------|-------------|
| `e → P` | Event followed by process P |
| `ch!p → P` | Send data p over channel ch |
| `ch?p → P` | Receive data p from channel ch |
| `P || Q` | Parallel composition |
| `P <*> Q` | Coupling (sequential composition) |
| `Stop` | Deadlock process |
| `Skip` | Successful termination |


5. Examples of invalid attachments and their correct versions
5.1 Multiple Attachment Constraint
5.1.1 Rule: Each input role of a connector instance can only be attached to one component port.
- Invalid Design:
declare connector = CSConnector;
attach ComponentA.portA() = connector.requester(14); // output role
attach ComponentB.portB() = connector.responder(); // input role
attach ComponentC.portC() = connector.responder(); // the same input role is attached to two different component ports: componentB.portB and componentC.portC

- Solution: Use separate connector instances with coupling
declare connector1 = CSConnector;
declare connector2 = CSConnector;
attach ComponentA.portA() = connector1.requester(14) <*> connector2.requester(18);
attach ComponentB.portB() = connector1.responder();
attach ComponentC.portC() = connector2.responder();

- Behavior Flow of the correct version:
ComponentA.portA → connector1.requester(14) → connector1.responder → ComponentB.portB → connector2.requester(18) → connector2.responder → ComponentC.portC

5.1.2 Rule: One component port can only be attached to at most one input role.
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

Unified_artifact = """
#################################################
Refactoring Task with the following information:
#################################################

Current ADL:\n{original_adl}\n
New requirement:\n{new_requirement}\n
Current system execution paths:\n{formatted_paths}
Error ADL:\n{adl}\n

Misconfiguration 1:
connector information:\n{connector_information}
Provided Wright# scripts with misconfiguration analysis:\n{issues_string1}

*** ONLY Output the final fixed Wright# scripts (new declaration + attachments) ***

Misconfiguration 2:
The following ports are illegally attached to multiple input roles, violating the constraint that each port can only be attached to one input role:\n{issues_string2}
Constraint: Each port on the left-hand side can only be attached to one input role. To handle multiple input roles, you need to create additional ports.
Request: Please provide the refined attachment statements that resolve these violations by creating new ports as needed.
*** ONLY Output the final fixed Wright# scripts (only new attachments) ***

"""