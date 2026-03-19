
You are provided with a Wright# documentation including the syntax and semantics of Wright# ADL. Please strictly follow the steps step by step to refactor the provided Software architecture in Wright# Specification to accomodate the new requirement.

Step 1: Undertstand everything provided inthe Wright# Documentation.
Step 2: Analyze the provided Software architecture in Wright# Specification.
Step 3: Refactor the Software architecture in Wright# Specification to accomodate the new requirement.
Step 4: Systematic Constraint Verification and Violation Fix
For each component in the specification, systematically verify:
- Port names are unique within the component and across all components
- List port name: [X], event names in process: [Y, Z, ...]
- Port names differ from ALL event names in their process expressions

Step 5: Output the refactored Software architecture in Wright# Specification.



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



#################################################
Refactoring Task with the following information:
#################################################

Current ADL:
connector CSConnector {
  role requester(j) = process -> req!j -> res?j -> Skip;
  role responder() = req?j -> invoke -> process -> res!j -> responder();
}
connector ROConnector {
  role querier(j) = request -> uid!j -> res?j -> process -> Skip;
  role readstore() = uid?j -> process -> res!j -> readstore();
}
connector IOConnector {
  role extsupplier(j) = process -> token!j -> extsupplier(j);
  role blockstorage() = token?j -> process -> stored -> blockstorage();
}
connector QRConnector {
  role querier(j) = process -> stmt!j -> res?j -> Skip;
  role readstore() = stmt?j -> process -> res!j -> readstore();
}
connector ESConnector {
  role eventpublisher(j) = process -> pevt!j -> sevt?j -> bevt!j -> broadcast -> Skip;
  role eventsubscriber() = bevt?j -> process -> eventsubscriber();
  role eventstore() = pevt?j -> process -> sevt!j -> persist -> eventstore();
}
connector CRConnector {
  role readstore() = stmt?j -> process -> persist -> readstore();
  role commander(j) = process -> stmt!j -> cmmd!j -> Skip;
  role commandstore() = cmmd?j -> process -> persist -> commandstore();
}
connector PSConnector {
  role publisher(j) = process -> pub!j -> Skip;
  role subscriber() = pub?j -> process -> subscriber();
}
connector WRConnector {
  role writer(j) = process -> req!j -> res?j -> Skip;
  role writestorage() = req?j -> invoke -> process -> res!j -> writestorage();
}
connector REConnector {
  role reader(j) = process -> req!j -> res?j -> Skip;
  role readstorage() = req?j -> invoke -> process -> res!j -> readstorage();
}
component ShopFrontend {
  port login() = submit -> login();
  port browse() = read -> browse();
  port order() = purchased -> order();
  port shop() = itemadded -> shop();
  port stream() = watching -> stream();
  port syncproduct() = synced -> syncproduct();
  port sharepost() = sharing -> sharepost();
}
component CatalogueService {
  port list() = query -> list();
  port inventory() = inventoried -> inventory();
  port stockcheck() = stockverified -> stockcheck();
}
component UserService {
  port auth() = checked -> auth();
  port streamauth() = streamchecked -> streamauth();
}
component OrdersService {
  port postorder() = check -> postorder();
  port get() = ack -> get();
  port flashorder() = flashcheck -> flashorder();
  port streamget() = streamack -> streamget();
}
component OrdersDB {
  port writereader() = orderwritten -> writereader();
  port queryorder() = orderreaded -> queryorder();
}
component CartsService {
  port manage() = saveitem -> manage();
  port livecart() = livesaved -> livecart();
}
component Payment {
  port pay() = paid -> pay();
  port flashpay() = flashpaid -> flashpay();
}
component ShippingService {
  port postshipping() = posted -> postshipping();
}
component ShippingWorker {
  port listqueue() = queueread -> listqueue();
}
component QueueDB {
  port writequeue() = queuewritten -> writequeue();
  port readqueue() = queueread -> readqueue();
}
component ShopBackend {
  port listorder() = renderlist -> listorder();
  port analytics() = analyzed -> analytics();
}
component LiveStreamService {
  port broadcast() = streamed -> broadcast();
  port liveauth() = streamverified -> liveauth();
}
component StreamingServer {
  port streamin() = received -> streamin();
  port streamout() = delivered -> streamout();
  port chatpub() = chatbroadcast -> chatpub();
}
component ChatService {
  port chat() = messaged -> chat();
}
component LiveCartIntegration {
  port addtocart() = cartfeatured -> addtocart();
}
component FlashSaleEngine {
  port applyprice() = priceapplied -> applyprice();
  port flashprice() = flashpriced -> flashprice();
}
component SocialMediaAPI {
  port socialpost() = socialmessaged -> socialpost();
  port socialshare() = sharemessaged -> socialshare();
}
system eshop {

  declare userwire = CSConnector;
  declare catelequewire = CSConnector;
  declare orderquerywire = CSConnector;
  declare cartwire = CSConnector;
  declare shippingwire = CSConnector;
  declare queuereadwire = REConnector;
  declare shippinglogwire = WRConnector;
  declare orderlogwire = WRConnector;
  declare orderreadwire = REConnector;
  declare orderwire = PSConnector;
  declare paywire = WRConnector;
  declare streambroadcastwire = CSConnector;
  declare streamviewwire = CSConnector;
  declare chatwire = PSConnector;
  declare livecatalogwire = CSConnector;
  declare liveauthwire = CSConnector;
  declare livecartwire = CSConnector;
  declare flashcartwire = CSConnector;
  declare flashpaywire = WRConnector;
  declare socialwire = PSConnector;
  declare analyticswire = REConnector;
  declare inventorywire = CSConnector;
  declare ordersocialwire = PSConnector;

  attach ShopBackend.listorder() = orderquerywire.requester(1);
  attach OrdersService.get() = orderquerywire.responder() <*> orderreadwire.reader(2);
  attach OrdersService.postorder() = orderwire.subscriber() <*> orderlogwire.writer(3) <*> paywire.writer(98) <*> shippingwire.requester(28) <*> ordersocialwire.publisher(99);
  attach OrdersDB.queryorder() = orderreadwire.readstorage();
  attach OrdersDB.writereader() = orderlogwire.writestorage();
  attach Payment.pay() = paywire.writestorage();
  attach UserService.auth() = userwire.responder();
  attach ShopFrontend.browse() = catelequewire.requester(48);
  attach ShopFrontend.login() = userwire.requester(93);
  attach ShopFrontend.order() = orderwire.publisher(62);
  attach ShopFrontend.shop() = cartwire.requester(31);
  attach CartsService.manage() = cartwire.responder();
  attach CatalogueService.list() = catelequewire.responder();
  attach ShippingService.postshipping() = shippingwire.responder() <*> shippinglogwire.writer(65);
  attach ShippingWorker.listqueue() = queuereadwire.reader(13);
  attach QueueDB.readqueue() = queuereadwire.readstorage();
  attach QueueDB.writequeue() = shippinglogwire.writestorage();
  attach LiveStreamService.broadcast() = streambroadcastwire.requester(71);
  attach StreamingServer.streamin() = streambroadcastwire.responder() <*> chatwire.publisher(72);
  attach ChatService.chat() = chatwire.subscriber();
  attach ShopFrontend.stream() = streamviewwire.requester(73);
  attach StreamingServer.streamout() = streamviewwire.responder();
  attach ShopFrontend.syncproduct() = livecatalogwire.requester(74);
  attach CatalogueService.inventory() = livecatalogwire.responder();
  attach LiveStreamService.liveauth() = liveauthwire.requester(75);
  attach UserService.streamauth() = liveauthwire.responder();
  attach LiveCartIntegration.addtocart() = livecartwire.requester(76);
  attach FlashSaleEngine.applyprice() = livecartwire.responder() <*> flashcartwire.requester(77) <*> flashpaywire.writer(78);
  attach CartsService.livecart() = flashcartwire.responder();
  attach Payment.flashpay() = flashpaywire.writestorage();
  attach ShopFrontend.sharepost() = socialwire.publisher(79);
  attach SocialMediaAPI.socialshare() = socialwire.subscriber();
  attach SocialMediaAPI.socialpost() = ordersocialwire.subscriber();
  attach ShopBackend.analytics() = analyticswire.reader(80);
  attach OrdersService.streamget() = analyticswire.readstorage();
  attach OrdersService.flashorder() = inventorywire.requester(81);
  attach CatalogueService.stockcheck() = inventorywire.responder();

  execute ShopBackend.listorder() || ShopBackend.analytics() || OrdersService.get() || OrdersService.postorder() || OrdersService.flashorder() || OrdersDB.queryorder() || OrdersDB.writereader() || Payment.pay() || Payment.flashpay() || UserService.auth() || UserService.streamauth() || ShopFrontend.order() || ShopFrontend.login() || ShopFrontend.browse() || ShopFrontend.shop() || ShopFrontend.stream() || ShopFrontend.syncproduct() || ShopFrontend.sharepost() || CartsService.manage() || CartsService.livecart() || CatalogueService.list() || CatalogueService.inventory() || CatalogueService.stockcheck() || ShippingService.postshipping() || ShippingWorker.listqueue() || QueueDB.readqueue() || QueueDB.writequeue() || LiveStreamService.broadcast() || LiveStreamService.liveauth() || StreamingServer.streamin() || StreamingServer.streamout() || StreamingServer.chatpub() || ChatService.chat() || LiveCartIntegration.addtocart() || FlashSaleEngine.applyprice() || FlashSaleEngine.flashprice() || SocialMediaAPI.socialpost() || SocialMediaAPI.socialshare() || OrdersService.streamget();
}

New requirement:
assert eshop |= [] (ShopFrontend.stream.watching -> <> CatalogueService.inventory.inventoried);

Current system execution paths:
Path 1: ShopBackend.listorder -> OrdersService.get -> OrdersDB.queryorder
Path 2: ShopFrontend.order -> OrdersService.postorder -> OrdersDB.writereader -> Payment.pay -> ShippingService.postshipping -> QueueDB.writequeue -> SocialMediaAPI.socialpost
Path 3: ShopFrontend.login -> UserService.auth
Path 4: ShopFrontend.browse -> CatalogueService.list
Path 5: ShopFrontend.shop -> CartsService.manage
Path 6: ShippingWorker.listqueue -> QueueDB.readqueue
Path 7: LiveStreamService.broadcast -> StreamingServer.streamin -> ChatService.chat
Path 8: ShopFrontend.stream -> StreamingServer.streamout
Path 9: ShopFrontend.syncproduct -> CatalogueService.inventory
Path 10: LiveStreamService.liveauth -> UserService.streamauth
Path 11: LiveCartIntegration.addtocart -> FlashSaleEngine.applyprice -> CartsService.livecart -> Payment.flashpay
Path 12: ShopFrontend.sharepost -> SocialMediaAPI.socialshare
Path 13: ShopBackend.analytics -> OrdersService.streamget
Path 14: OrdersService.flashorder -> CatalogueService.stockcheck
