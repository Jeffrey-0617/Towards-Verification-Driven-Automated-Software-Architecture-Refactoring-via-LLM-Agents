
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

component ArchlightNoticeView {
  port query_notice() = notice_queried -> query_notice();
}

component ArchlightNoticeADT {
  port report_to_archlight() = issue_reported -> report_to_archlight();
  port handle_notice_query() = query_handled -> handle_notice_query();
}

component Schematron {
  port validate_archlight() = validated -> validate_archlight();
  port register_tool() = tool_registered -> register_tool();
  port apply_schm_prefs() = schm_prefs_applied -> apply_schm_prefs();
}

component SchematronPrefs {
  port configure_schematron() = config_sent -> configure_schematron();
}

component ArchlightIssueView {
  port query_issues() = issues_fetched -> query_issues();
}

component ArchlightIssueADT {
  port send_to_archlight() = issue_sent -> send_to_archlight();
  port handle_issue_query() = issue_handled -> handle_issue_query();
}

component ArchipelagoTypesPrefs {
  port configure_types() = types_configured -> configure_types();
}

component XArchADT {
  port access_xarch_utils() = xarch_util_call -> access_xarch_utils();
  port load_xarch_resources() = xarch_res_load -> load_xarch_resources();
}

component EclipseContentStore {
  port store_content() = content_stored -> store_content();
}

component GraphLayoutPrefs {
  port set_layout_prefs() = layout_configured -> set_layout_prefs();
}

component ArchlightToolAggregator {
  port aggregate_to_archlight() = aggregated -> aggregate_to_archlight();
  port recv_tool_registration() = registration_recv -> recv_tool_registration();
}

component Archipelago {
  port use_archstudio_utils() = arch_util_used -> use_archstudio_utils();
  port use_arch_resources() = arch_res_used -> use_arch_resources();
  port use_aim() = aim_used -> use_aim();
  port use_meta() = meta_used -> use_meta();
  port recv_archipelago_prefs() = arch_prefs_recv -> recv_archipelago_prefs();
  port recv_types_prefs() = types_prefs_recv -> recv_types_prefs();
}

component ChangeSetsViewer {
  port view_changesets() = sets_viewed -> view_changesets();
}

component CopyPasteManager {
  port manage_clipboard() = clipboard_managed -> manage_clipboard();
}

component GraphLayout {
  port layout_to_utils() = layout_util_call -> layout_to_utils();
  port recv_layout_prefs() = layout_prefs_recv -> recv_layout_prefs();
}

component SelectorDriver {
  port drive_archlight() = archlight_driven -> drive_archlight();
  port drive_selector() = selector_driven -> drive_selector();
}

component Archlight {
  port invoke_type_wrangler() = wrangler_invoked -> invoke_type_wrangler();
  port invoke_test_adt() = test_invoked -> invoke_test_adt();
  port call_al_util_service() = al_util_called -> call_al_util_service();
  port fetch_al_resources() = al_resources_fetched -> fetch_al_resources();
  port handle_notice_report() = notice_handled -> handle_notice_report();
  port handle_schematron() = schematron_handled -> handle_schematron();
  port handle_issue_report() = issue_report_handled -> handle_issue_report();
  port handle_aggregation() = aggregation_handled -> handle_aggregation();
  port handle_selector_driver() = driver_handled -> handle_selector_driver();
}

component TypeWrangler {
  port wrangle_utils() = types_wrangled -> wrangle_utils();
  port recv_archlight_wrangle() = archlight_wrangle_recv -> recv_archlight_wrangle();
}

component GuardTracker {
  port track_guards() = guards_tracked -> track_guards();
}

component AIMLauncher {
  port launch_aim() = aim_launched -> launch_aim();
}

component ArchEdit {
  port edit_via_utils() = edit_dispatched -> edit_via_utils();
}

component RelatedElements {
  port find_related() = elements_found -> find_related();
}

component VersionPruner {
  port prune_version() = version_pruned -> prune_version();
}

component ArchlightTestADT {
  port run_test() = test_executed -> run_test();
}

component Launcher {
  port launch_editor() = editor_launched -> launch_editor();
  port launch_utils() = utils_launched -> launch_utils();
}

component BooleanNotation {
  port notate_boolean() = boolean_notated -> notate_boolean();
}

component SharedEditorInfrastructure {
  port delegate_editor_mgr() = editor_delegated -> delegate_editor_mgr();
  port shared_util_call() = shared_util_called -> shared_util_call();
  port recv_launcher_call() = launcher_call_recv -> recv_launcher_call();
}

component RationaleView {
  port view_meta() = meta_viewed -> view_meta();
  port view_rv_utils() = rv_util_called -> view_rv_utils();
}

component PreferencesADT {
  port access_prefs_utils() = prefs_accessed -> access_prefs_utils();
}

component TracelinkView {
  port trace_links() = links_traced -> trace_links();
}

component ChangeSetIdRelationships {
  port relate_xarch_cs() = xarch_related -> relate_xarch_cs();
  port relate_id_cs_utils() = id_cs_utils_related -> relate_id_cs_utils();
}

component XArchDetach {
  port detach_xarch() = xarch_detached -> detach_xarch();
}

component ChangeSetStatusRelationships {
  port status_xarch_cs() = status_xarch_sent -> status_xarch_cs();
  port status_sr_cs_utils() = status_sr_utils_sent -> status_sr_cs_utils();
}

component ExplicitADT {
  port explicit_utils_call() = explicit_called -> explicit_utils_call();
}

component ChangeSetIdView {
  port view_cs_id() = cs_id_viewed -> view_cs_id();
}

component ChangeSetStatusView {
  port view_cs_status() = cs_status_viewed -> view_cs_status();
}

component Selector {
  port select_eval() = eval_selected -> select_eval();
  port recv_driver_input() = driver_input_recv -> recv_driver_input();
}

component EditorPrefs {
  port set_editor_prefs() = editor_prefs_set -> set_editor_prefs();
}

component EditorManager {
  port manage_files() = files_managed -> manage_files();
  port manager_util_call() = mgr_util_called -> manager_util_call();
  port recv_shared_editor() = shared_editor_recv -> recv_shared_editor();
  port recv_editor_prefs() = editor_prefs_recv -> recv_editor_prefs();
}

component FileManager {
  port file_util_call() = file_util_called -> file_util_call();
  port handle_file_ops() = file_ops_handled -> handle_file_ops();
}

component Meta {
  port meta_aim_call() = meta_aim_called -> meta_aim_call();
  port meta_util_call() = meta_util_called -> meta_util_call();
  port recv_archipelago_meta() = arch_meta_recv -> recv_archipelago_meta();
  port recv_rationale_meta() = rationale_meta_recv -> recv_rationale_meta();
}

component AIMEclipse {
  port eclipse_aim_call() = eclipse_aim_called -> eclipse_aim_call();
}

component ChangeSetView {
  port manage_cs_view() = cs_view_managed -> manage_cs_view();
}

component ChangeSetSync {
  port sync_changesets() = cs_synced -> sync_changesets();
}

component ChangeSetRelationshipManager {
  port manage_cs_rels() = cs_rels_managed -> manage_cs_rels();
}

component ChangeSetADT {
  port access_cs_adt() = cs_adt_accessed -> access_cs_adt();
}

component XArchChangeSet {
  port xarch_cs_utils_call() = xarch_cs_util -> xarch_cs_utils_call();
  port xarch_cs_archstudio_call() = xarch_cs_arch -> xarch_cs_archstudio_call();
  port recv_id_relationships() = id_rels_recv -> recv_id_relationships();
  port recv_detach() = detach_recv -> recv_detach();
  port recv_status_relationships() = status_rels_recv -> recv_status_relationships();
}

component BooleanEval {
  port evaluate_pruner() = pruner_evaluated -> evaluate_pruner();
  port recv_selector_eval() = selector_eval_recv -> recv_selector_eval();
}

component ArchlightPrefs {
  port set_archlight_prefs() = al_prefs_set -> set_archlight_prefs();
}

component ArchipelagoPrefs {
  port config_archipelago() = arch_configured -> config_archipelago();
  port config_archprefs_utils() = archprefs_utils_configured -> config_archprefs_utils();
}

component FileTracker {
  port track_files() = files_tracked -> track_files();
}

component AIM {
  port aim_util_call() = aim_util_called -> aim_util_call();
  port aim_res_call() = aim_res_called -> aim_res_call();
  port recv_aim_launcher() = launcher_aim_recv -> recv_aim_launcher();
  port recv_archipelago_aim() = arch_aim_recv -> recv_archipelago_aim();
  port recv_meta_aim() = meta_aim_recv -> recv_meta_aim();
  port recv_eclipse_aim() = eclipse_aim_recv -> recv_eclipse_aim();
}

component Pruner {
  port handle_version_prune() = version_prune_handled -> handle_version_prune();
  port handle_eval_prune() = eval_prune_handled -> handle_eval_prune();
}

component BasePreferences {
  port base_prefs_call() = base_prefs_called -> base_prefs_call();
}

component ArchStudioUtils {
  port provide_resources() = resources_provided -> provide_resources();
  port serve_archlight() = al_served -> serve_archlight();
  port serve_type_wrangler() = tw_served -> serve_type_wrangler();
  port serve_guard_tracker() = gt_served -> serve_guard_tracker();
  port serve_archipelago() = ar_served -> serve_archipelago();
  port serve_arch_edit() = ae_served -> serve_arch_edit();
  port serve_launcher() = la_served -> serve_launcher();
  port serve_shared_editor() = se_served -> serve_shared_editor();
  port serve_editor_manager() = em_served -> serve_editor_manager();
  port serve_file_manager() = fm_served -> serve_file_manager();
  port serve_boolean_notation() = bn_served -> serve_boolean_notation();
  port serve_rationale_view() = rv_served -> serve_rationale_view();
  port serve_preferences_adt() = pa_served -> serve_preferences_adt();
  port serve_meta() = mt_served -> serve_meta();
  port serve_aim() = ai_served -> serve_aim();
  port serve_base_prefs() = bp_served -> serve_base_prefs();
  port serve_archlight_prefs() = alp_served -> serve_archlight_prefs();
  port serve_archipelago_prefs() = arp_served -> serve_archipelago_prefs();
  port serve_file_tracker() = ft_served -> serve_file_tracker();
  port serve_xarch_changeset() = xcs_served -> serve_xarch_changeset();
  port serve_changeset_utils() = csu_served -> serve_changeset_utils();
  port serve_related_elements() = re_served -> serve_related_elements();
  port serve_graph_layout() = gl_served -> serve_graph_layout();
  port serve_copy_paste() = cp_served -> serve_copy_paste();
  port serve_eclipse_content() = ec_served -> serve_eclipse_content();
  port serve_xarch_adt() = xa_served -> serve_xarch_adt();
  port serve_explicit_adt() = ea_served -> serve_explicit_adt();
  port serve_tracelink_view() = tv_served -> serve_tracelink_view();
}

component Resources {
  port provide_archlight_res() = al_res_provided -> provide_archlight_res();
  port provide_archipelago_res() = ar_res_provided -> provide_archipelago_res();
  port provide_aim_res() = ai_res_provided -> provide_aim_res();
  port provide_archstudio_res() = asu_res_provided -> provide_archstudio_res();
  port provide_changeset_res() = csu_res_provided -> provide_changeset_res();
  port provide_xarch_res() = xa_res_provided -> provide_xarch_res();
}

component ChangeSetUtils {
  port cs_util_arch_call() = cs_arch_called -> cs_util_arch_call();
  port cs_util_res_call() = cs_res_called -> cs_util_res_call();
  port serve_changesets_viewer() = csv_served -> serve_changesets_viewer();
  port serve_id_relationships() = idr_served -> serve_id_relationships();
  port serve_status_relationships() = str_served -> serve_status_relationships();
  port serve_id_view() = idv_served -> serve_id_view();
  port serve_status_view() = stv_served -> serve_status_view();
  port serve_cs_view() = csview_served -> serve_cs_view();
  port serve_cs_sync() = sync_served -> serve_cs_sync();
  port serve_cs_rel_mgr() = relmgr_served -> serve_cs_rel_mgr();
  port serve_cs_adt() = csadt_served -> serve_cs_adt();
  port serve_xarch_cs() = xarchcs_served -> serve_xarch_cs();
}

system archstudio {

  declare alnv_to_alna = CSConnector;
  declare alna_to_al = CSConnector;
  declare schm_to_al = CSConnector;
  declare schm_to_alta = CSConnector;
  declare aliv_to_alia = CSConnector;
  declare alia_to_al = CSConnector;
  declare alta_to_al = CSConnector;
  declare sd_to_al = CSConnector;
  declare sd_to_sel = CSConnector;
  declare vp_to_prn = CSConnector;
  declare sel_to_be = CSConnector;
  declare be_to_prn = CSConnector;
  declare al_to_tw = CSConnector;
  declare al_to_altest = CSConnector;
  declare al_to_asu = CSConnector;
  declare al_to_res = CSConnector;
  declare tw_to_asu = CSConnector;
  declare gt_to_asu = CSConnector;
  declare aiml_to_aim = CSConnector;
  declare arch_to_asu = CSConnector;
  declare arch_to_res = CSConnector;
  declare arch_to_aim = CSConnector;
  declare arch_to_meta = CSConnector;
  declare ae_to_asu = CSConnector;
  declare lnch_to_sei = CSConnector;
  declare lnch_to_asu = CSConnector;
  declare sei_to_em = CSConnector;
  declare sei_to_asu = CSConnector;
  declare em_to_fm = CSConnector;
  declare em_to_asu = CSConnector;
  declare fm_to_asu = CSConnector;
  declare bn_to_asu = CSConnector;
  declare rv_to_meta = CSConnector;
  declare rv_to_asu = CSConnector;
  declare padt_to_asu = CSConnector;
  declare meta_to_aim = CSConnector;
  declare meta_to_asu = CSConnector;
  declare aime_to_aim = CSConnector;
  declare aim_to_asu = CSConnector;
  declare aim_to_res = CSConnector;
  declare bp_to_asu = CSConnector;
  declare asu_to_res = CSConnector;
  declare eprefs_to_em = CSConnector;
  declare alprefs_to_asu = CSConnector;
  declare archprefs_to_arch = CSConnector;
  declare archprefs_to_asu = CSConnector;
  declare ft_to_asu = CSConnector;
  declare csvw_to_csu = CSConnector;
  declare csir_to_xcs = CSConnector;
  declare csir_to_csu = CSConnector;
  declare xdet_to_xcs = CSConnector;
  declare cssr_to_xcs = CSConnector;
  declare cssr_to_csu = CSConnector;
  declare csiv_to_csu = CSConnector;
  declare cssv_to_csu = CSConnector;
  declare csv_to_csu = CSConnector;
  declare csyn_to_csu = CSConnector;
  declare csrm_to_csu = CSConnector;
  declare csadt_to_csu = CSConnector;
  declare xcs_to_csu = CSConnector;
  declare xcs_to_asu = CSConnector;
  declare csu_to_asu = CSConnector;
  declare csu_to_res = CSConnector;
  declare re_to_asu = CSConnector;
  declare gl_to_asu = CSConnector;
  declare cpm_to_asu = CSConnector;
  declare ecs_to_asu = CSConnector;
  declare xadt_to_asu = CSConnector;
  declare xadt_to_res = CSConnector;
  declare eadt_to_asu = CSConnector;
  declare tlv_to_asu = CSConnector;
  declare schprefs_to_schm = CSConnector;
  declare atprefs_to_arch = CSConnector;
  declare glprefs_to_gl = CSConnector;

  attach ArchlightNoticeView.query_notice() = alnv_to_alna.requester(1);
  attach ArchlightNoticeADT.report_to_archlight() = alna_to_al.requester(2);
  attach ArchlightNoticeADT.handle_notice_query() = alnv_to_alna.responder();
  attach Schematron.validate_archlight() = schm_to_al.requester(3);
  attach Schematron.register_tool() = schm_to_alta.requester(4);
  attach Schematron.apply_schm_prefs() = schprefs_to_schm.responder();
  attach SchematronPrefs.configure_schematron() = schprefs_to_schm.requester(72);
  attach ArchlightIssueView.query_issues() = aliv_to_alia.requester(5);
  attach ArchlightIssueADT.send_to_archlight() = alia_to_al.requester(6);
  attach ArchlightIssueADT.handle_issue_query() = aliv_to_alia.responder();
  attach ArchipelagoTypesPrefs.configure_types() = atprefs_to_arch.requester(73);
  attach XArchADT.access_xarch_utils() = xadt_to_asu.requester(68);
  attach XArchADT.load_xarch_resources() = xadt_to_res.requester(69);
  attach EclipseContentStore.store_content() = ecs_to_asu.requester(67);
  attach GraphLayoutPrefs.set_layout_prefs() = glprefs_to_gl.requester(74);
  attach ArchlightToolAggregator.aggregate_to_archlight() = alta_to_al.requester(7);
  attach ArchlightToolAggregator.recv_tool_registration() = schm_to_alta.responder();
  attach Archipelago.use_archstudio_utils() = arch_to_asu.requester(20);
  attach Archipelago.use_arch_resources() = arch_to_res.requester(21);
  attach Archipelago.use_aim() = arch_to_aim.requester(22);
  attach Archipelago.use_meta() = arch_to_meta.requester(23);
  attach Archipelago.recv_archipelago_prefs() = archprefs_to_arch.responder();
  attach Archipelago.recv_types_prefs() = atprefs_to_arch.responder();
  attach ChangeSetsViewer.view_changesets() = csvw_to_csu.requester(48);
  attach CopyPasteManager.manage_clipboard() = cpm_to_asu.requester(66);
  attach GraphLayout.layout_to_utils() = gl_to_asu.requester(65);
  attach GraphLayout.recv_layout_prefs() = glprefs_to_gl.responder();
  attach SelectorDriver.drive_archlight() = sd_to_al.requester(8);
  attach SelectorDriver.drive_selector() = sd_to_sel.requester(9);
  attach Archlight.invoke_type_wrangler() = al_to_tw.requester(13);
  attach Archlight.invoke_test_adt() = al_to_altest.requester(14);
  attach Archlight.call_al_util_service() = al_to_asu.requester(15);
  attach Archlight.fetch_al_resources() = al_to_res.requester(16);
  attach Archlight.handle_notice_report() = alna_to_al.responder();
  attach Archlight.handle_schematron() = schm_to_al.responder();
  attach Archlight.handle_issue_report() = alia_to_al.responder();
  attach Archlight.handle_aggregation() = alta_to_al.responder();
  attach Archlight.handle_selector_driver() = sd_to_al.responder();
  attach TypeWrangler.wrangle_utils() = tw_to_asu.requester(17);
  attach TypeWrangler.recv_archlight_wrangle() = al_to_tw.responder();
  attach GuardTracker.track_guards() = gt_to_asu.requester(18);
  attach AIMLauncher.launch_aim() = aiml_to_aim.requester(19);
  attach ArchEdit.edit_via_utils() = ae_to_asu.requester(24);
  attach RelatedElements.find_related() = re_to_asu.requester(64);
  attach VersionPruner.prune_version() = vp_to_prn.requester(10);
  attach ArchlightTestADT.run_test() = al_to_altest.responder();
  attach Launcher.launch_editor() = lnch_to_sei.requester(25);
  attach Launcher.launch_utils() = lnch_to_asu.requester(26);
  attach BooleanNotation.notate_boolean() = bn_to_asu.requester(32);
  attach SharedEditorInfrastructure.delegate_editor_mgr() = sei_to_em.requester(27);
  attach SharedEditorInfrastructure.shared_util_call() = sei_to_asu.requester(28);
  attach SharedEditorInfrastructure.recv_launcher_call() = lnch_to_sei.responder();
  attach RationaleView.view_meta() = rv_to_meta.requester(33);
  attach RationaleView.view_rv_utils() = rv_to_asu.requester(34);
  attach PreferencesADT.access_prefs_utils() = padt_to_asu.requester(35);
  attach TracelinkView.trace_links() = tlv_to_asu.requester(71);
  attach ChangeSetIdRelationships.relate_xarch_cs() = csir_to_xcs.requester(49);
  attach ChangeSetIdRelationships.relate_id_cs_utils() = csir_to_csu.requester(50);
  attach XArchDetach.detach_xarch() = xdet_to_xcs.requester(51);
  attach ChangeSetStatusRelationships.status_xarch_cs() = cssr_to_xcs.requester(52);
  attach ChangeSetStatusRelationships.status_sr_cs_utils() = cssr_to_csu.requester(53);
  attach ExplicitADT.explicit_utils_call() = eadt_to_asu.requester(70);
  attach ChangeSetIdView.view_cs_id() = csiv_to_csu.requester(54);
  attach ChangeSetStatusView.view_cs_status() = cssv_to_csu.requester(55);
  attach Selector.select_eval() = sel_to_be.requester(11);
  attach Selector.recv_driver_input() = sd_to_sel.responder();
  attach EditorPrefs.set_editor_prefs() = eprefs_to_em.requester(43);
  attach EditorManager.manage_files() = em_to_fm.requester(29);
  attach EditorManager.manager_util_call() = em_to_asu.requester(30);
  attach EditorManager.recv_shared_editor() = sei_to_em.responder();
  attach EditorManager.recv_editor_prefs() = eprefs_to_em.responder();
  attach FileManager.file_util_call() = fm_to_asu.requester(31);
  attach FileManager.handle_file_ops() = em_to_fm.responder();
  attach Meta.meta_aim_call() = meta_to_aim.requester(36);
  attach Meta.meta_util_call() = meta_to_asu.requester(37);
  attach Meta.recv_archipelago_meta() = arch_to_meta.responder();
  attach Meta.recv_rationale_meta() = rv_to_meta.responder();
  attach AIMEclipse.eclipse_aim_call() = aime_to_aim.requester(38);
  attach ChangeSetView.manage_cs_view() = csv_to_csu.requester(56);
  attach ChangeSetSync.sync_changesets() = csyn_to_csu.requester(57);
  attach ChangeSetRelationshipManager.manage_cs_rels() = csrm_to_csu.requester(58);
  attach ChangeSetADT.access_cs_adt() = csadt_to_csu.requester(59);
  attach XArchChangeSet.xarch_cs_utils_call() = xcs_to_csu.requester(60);
  attach XArchChangeSet.xarch_cs_archstudio_call() = xcs_to_asu.requester(61);
  attach XArchChangeSet.recv_id_relationships() = csir_to_xcs.responder();
  attach XArchChangeSet.recv_detach() = xdet_to_xcs.responder();
  attach XArchChangeSet.recv_status_relationships() = cssr_to_xcs.responder();
  attach BooleanEval.evaluate_pruner() = be_to_prn.requester(12);
  attach BooleanEval.recv_selector_eval() = sel_to_be.responder();
  attach ArchlightPrefs.set_archlight_prefs() = alprefs_to_asu.requester(44);
  attach ArchipelagoPrefs.config_archipelago() = archprefs_to_arch.requester(45);
  attach ArchipelagoPrefs.config_archprefs_utils() = archprefs_to_asu.requester(46);
  attach FileTracker.track_files() = ft_to_asu.requester(47);
  attach AIM.aim_util_call() = aim_to_asu.requester(39);
  attach AIM.aim_res_call() = aim_to_res.requester(40);
  attach AIM.recv_aim_launcher() = aiml_to_aim.responder();
  attach AIM.recv_archipelago_aim() = arch_to_aim.responder();
  attach AIM.recv_meta_aim() = meta_to_aim.responder();
  attach AIM.recv_eclipse_aim() = aime_to_aim.responder();
  attach Pruner.handle_version_prune() = vp_to_prn.responder();
  attach Pruner.handle_eval_prune() = be_to_prn.responder();
  attach BasePreferences.base_prefs_call() = bp_to_asu.requester(41);
  attach ArchStudioUtils.provide_resources() = asu_to_res.requester(42);
  attach ArchStudioUtils.serve_archlight() = al_to_asu.responder();
  attach ArchStudioUtils.serve_type_wrangler() = tw_to_asu.responder();
  attach ArchStudioUtils.serve_guard_tracker() = gt_to_asu.responder();
  attach ArchStudioUtils.serve_archipelago() = arch_to_asu.responder();
  attach ArchStudioUtils.serve_arch_edit() = ae_to_asu.responder();
  attach ArchStudioUtils.serve_launcher() = lnch_to_asu.responder();
  attach ArchStudioUtils.serve_shared_editor() = sei_to_asu.responder();
  attach ArchStudioUtils.serve_editor_manager() = em_to_asu.responder();
  attach ArchStudioUtils.serve_file_manager() = fm_to_asu.responder();
  attach ArchStudioUtils.serve_boolean_notation() = bn_to_asu.responder();
  attach ArchStudioUtils.serve_rationale_view() = rv_to_asu.responder();
  attach ArchStudioUtils.serve_preferences_adt() = padt_to_asu.responder();
  attach ArchStudioUtils.serve_meta() = meta_to_asu.responder();
  attach ArchStudioUtils.serve_aim() = aim_to_asu.responder();
  attach ArchStudioUtils.serve_base_prefs() = bp_to_asu.responder();
  attach ArchStudioUtils.serve_archlight_prefs() = alprefs_to_asu.responder();
  attach ArchStudioUtils.serve_archipelago_prefs() = archprefs_to_asu.responder();
  attach ArchStudioUtils.serve_file_tracker() = ft_to_asu.responder();
  attach ArchStudioUtils.serve_xarch_changeset() = xcs_to_asu.responder();
  attach ArchStudioUtils.serve_changeset_utils() = csu_to_asu.responder();
  attach ArchStudioUtils.serve_related_elements() = re_to_asu.responder();
  attach ArchStudioUtils.serve_graph_layout() = gl_to_asu.responder();
  attach ArchStudioUtils.serve_copy_paste() = cpm_to_asu.responder();
  attach ArchStudioUtils.serve_eclipse_content() = ecs_to_asu.responder();
  attach ArchStudioUtils.serve_xarch_adt() = xadt_to_asu.responder();
  attach ArchStudioUtils.serve_explicit_adt() = eadt_to_asu.responder();
  attach ArchStudioUtils.serve_tracelink_view() = tlv_to_asu.responder();
  attach Resources.provide_archlight_res() = al_to_res.responder();
  attach Resources.provide_archipelago_res() = arch_to_res.responder();
  attach Resources.provide_aim_res() = aim_to_res.responder();
  attach Resources.provide_archstudio_res() = asu_to_res.responder();
  attach Resources.provide_changeset_res() = csu_to_res.responder();
  attach Resources.provide_xarch_res() = xadt_to_res.responder();
  attach ChangeSetUtils.cs_util_arch_call() = csu_to_asu.requester(62);
  attach ChangeSetUtils.cs_util_res_call() = csu_to_res.requester(63);
  attach ChangeSetUtils.serve_changesets_viewer() = csvw_to_csu.responder();
  attach ChangeSetUtils.serve_id_relationships() = csir_to_csu.responder();
  attach ChangeSetUtils.serve_status_relationships() = cssr_to_csu.responder();
  attach ChangeSetUtils.serve_id_view() = csiv_to_csu.responder();
  attach ChangeSetUtils.serve_status_view() = cssv_to_csu.responder();
  attach ChangeSetUtils.serve_cs_view() = csv_to_csu.responder();
  attach ChangeSetUtils.serve_cs_sync() = csyn_to_csu.responder();
  attach ChangeSetUtils.serve_cs_rel_mgr() = csrm_to_csu.responder();
  attach ChangeSetUtils.serve_cs_adt() = csadt_to_csu.responder();
  attach ChangeSetUtils.serve_xarch_cs() = xcs_to_csu.responder();

  execute ArchlightNoticeView.query_notice() || ArchlightNoticeADT.report_to_archlight() || ArchlightNoticeADT.handle_notice_query() || Schematron.validate_archlight() || Schematron.register_tool() || Schematron.apply_schm_prefs() || SchematronPrefs.configure_schematron() || ArchlightIssueView.query_issues() || ArchlightIssueADT.send_to_archlight() || ArchlightIssueADT.handle_issue_query() || ArchipelagoTypesPrefs.configure_types() || XArchADT.access_xarch_utils() || XArchADT.load_xarch_resources() || EclipseContentStore.store_content() || GraphLayoutPrefs.set_layout_prefs() || ArchlightToolAggregator.aggregate_to_archlight() || ArchlightToolAggregator.recv_tool_registration() || Archipelago.use_archstudio_utils() || Archipelago.use_arch_resources() || Archipelago.use_aim() || Archipelago.use_meta() || Archipelago.recv_archipelago_prefs() || Archipelago.recv_types_prefs() || ChangeSetsViewer.view_changesets() || CopyPasteManager.manage_clipboard() || GraphLayout.layout_to_utils() || GraphLayout.recv_layout_prefs() || SelectorDriver.drive_archlight() || SelectorDriver.drive_selector() || Archlight.invoke_type_wrangler() || Archlight.invoke_test_adt() || Archlight.call_al_util_service() || Archlight.fetch_al_resources() || Archlight.handle_notice_report() || Archlight.handle_schematron() || Archlight.handle_issue_report() || Archlight.handle_aggregation() || Archlight.handle_selector_driver() || TypeWrangler.wrangle_utils() || TypeWrangler.recv_archlight_wrangle() || GuardTracker.track_guards() || AIMLauncher.launch_aim() || ArchEdit.edit_via_utils() || RelatedElements.find_related() || VersionPruner.prune_version() || ArchlightTestADT.run_test() || Launcher.launch_editor() || Launcher.launch_utils() || BooleanNotation.notate_boolean() || SharedEditorInfrastructure.delegate_editor_mgr() || SharedEditorInfrastructure.shared_util_call() || SharedEditorInfrastructure.recv_launcher_call() || RationaleView.view_meta() || RationaleView.view_rv_utils() || PreferencesADT.access_prefs_utils() || TracelinkView.trace_links() || ChangeSetIdRelationships.relate_xarch_cs() || ChangeSetIdRelationships.relate_id_cs_utils() || XArchDetach.detach_xarch() || ChangeSetStatusRelationships.status_xarch_cs() || ChangeSetStatusRelationships.status_sr_cs_utils() || ExplicitADT.explicit_utils_call() || ChangeSetIdView.view_cs_id() || ChangeSetStatusView.view_cs_status() || Selector.select_eval() || Selector.recv_driver_input() || EditorPrefs.set_editor_prefs() || EditorManager.manage_files() || EditorManager.manager_util_call() || EditorManager.recv_shared_editor() || EditorManager.recv_editor_prefs() || FileManager.file_util_call() || FileManager.handle_file_ops() || Meta.meta_aim_call() || Meta.meta_util_call() || Meta.recv_archipelago_meta() || Meta.recv_rationale_meta() || AIMEclipse.eclipse_aim_call() || ChangeSetView.manage_cs_view() || ChangeSetSync.sync_changesets() || ChangeSetRelationshipManager.manage_cs_rels() || ChangeSetADT.access_cs_adt() || XArchChangeSet.xarch_cs_utils_call() || XArchChangeSet.xarch_cs_archstudio_call() || XArchChangeSet.recv_id_relationships() || XArchChangeSet.recv_detach() || XArchChangeSet.recv_status_relationships() || BooleanEval.evaluate_pruner() || BooleanEval.recv_selector_eval() || ArchlightPrefs.set_archlight_prefs() || ArchipelagoPrefs.config_archipelago() || ArchipelagoPrefs.config_archprefs_utils() || FileTracker.track_files() || AIM.aim_util_call() || AIM.aim_res_call() || AIM.recv_aim_launcher() || AIM.recv_archipelago_aim() || AIM.recv_meta_aim() || AIM.recv_eclipse_aim() || Pruner.handle_version_prune() || Pruner.handle_eval_prune() || BasePreferences.base_prefs_call() || ArchStudioUtils.provide_resources() || ArchStudioUtils.serve_archlight() || ArchStudioUtils.serve_type_wrangler() || ArchStudioUtils.serve_guard_tracker() || ArchStudioUtils.serve_archipelago() || ArchStudioUtils.serve_arch_edit() || ArchStudioUtils.serve_launcher() || ArchStudioUtils.serve_shared_editor() || ArchStudioUtils.serve_editor_manager() || ArchStudioUtils.serve_file_manager() || ArchStudioUtils.serve_boolean_notation() || ArchStudioUtils.serve_rationale_view() || ArchStudioUtils.serve_preferences_adt() || ArchStudioUtils.serve_meta() || ArchStudioUtils.serve_aim() || ArchStudioUtils.serve_base_prefs() || ArchStudioUtils.serve_archlight_prefs() || ArchStudioUtils.serve_archipelago_prefs() || ArchStudioUtils.serve_file_tracker() || ArchStudioUtils.serve_xarch_changeset() || ArchStudioUtils.serve_changeset_utils() || ArchStudioUtils.serve_related_elements() || ArchStudioUtils.serve_graph_layout() || ArchStudioUtils.serve_copy_paste() || ArchStudioUtils.serve_eclipse_content() || ArchStudioUtils.serve_xarch_adt() || ArchStudioUtils.serve_explicit_adt() || ArchStudioUtils.serve_tracelink_view() || Resources.provide_archlight_res() || Resources.provide_archipelago_res() || Resources.provide_aim_res() || Resources.provide_archstudio_res() || Resources.provide_changeset_res() || Resources.provide_xarch_res() || ChangeSetUtils.cs_util_arch_call() || ChangeSetUtils.cs_util_res_call() || ChangeSetUtils.serve_changesets_viewer() || ChangeSetUtils.serve_id_relationships() || ChangeSetUtils.serve_status_relationships() || ChangeSetUtils.serve_id_view() || ChangeSetUtils.serve_status_view() || ChangeSetUtils.serve_cs_view() || ChangeSetUtils.serve_cs_sync() || ChangeSetUtils.serve_cs_rel_mgr() || ChangeSetUtils.serve_cs_adt() || ChangeSetUtils.serve_xarch_cs();
}


New requirement:
Add a collaborative design review capability: introduce a ReviewSession component that allows multiple architects to asynchronously comment on specific architectural elements in XArchADT, a ReviewThread component that organizes discussions per element with status tracking (open, resolved, deferred) queried by Archipelago through GraphLayout for inline comment display, and a ReviewReport component that aggregates review outcomes and links to ArchlightIssueADT for issues discovered during review — ArchEdit must support adding review annotations, ChangeSetADT must associate reviews with pending changesets, Meta must store review decisions as architectural rationale through RationaleView, and EditorManager must notify reviewers when reviewed elements are modified through SharedEditorInfrastructure.

Current system execution paths:
Path 1: ArchlightNoticeView.query_notice -> ArchlightNoticeADT.handle_notice_query
Path 2: ArchlightNoticeADT.report_to_archlight -> Archlight.handle_notice_report
Path 3: Schematron.validate_archlight -> Archlight.handle_schematron
Path 4: Schematron.register_tool -> ArchlightToolAggregator.recv_tool_registration
Path 5: SchematronPrefs.configure_schematron -> Schematron.apply_schm_prefs
Path 6: ArchlightIssueView.query_issues -> ArchlightIssueADT.handle_issue_query
Path 7: ArchlightIssueADT.send_to_archlight -> Archlight.handle_issue_report
Path 8: ArchipelagoTypesPrefs.configure_types -> Archipelago.recv_types_prefs
Path 9: XArchADT.access_xarch_utils -> ArchStudioUtils.serve_xarch_adt
Path 10: XArchADT.load_xarch_resources -> Resources.provide_xarch_res
Path 11: EclipseContentStore.store_content -> ArchStudioUtils.serve_eclipse_content
Path 12: GraphLayoutPrefs.set_layout_prefs -> GraphLayout.recv_layout_prefs
Path 13: ArchlightToolAggregator.aggregate_to_archlight -> Archlight.handle_aggregation
Path 14: Archipelago.use_archstudio_utils -> ArchStudioUtils.serve_archipelago
Path 15: Archipelago.use_arch_resources -> Resources.provide_archipelago_res
Path 16: Archipelago.use_aim -> AIM.recv_archipelago_aim
Path 17: Archipelago.use_meta -> Meta.recv_archipelago_meta
Path 18: ArchipelagoPrefs.config_archipelago -> Archipelago.recv_archipelago_prefs
Path 19: ChangeSetsViewer.view_changesets -> ChangeSetUtils.serve_changesets_viewer
Path 20: CopyPasteManager.manage_clipboard -> ArchStudioUtils.serve_copy_paste
Path 21: GraphLayout.layout_to_utils -> ArchStudioUtils.serve_graph_layout
Path 22: SelectorDriver.drive_archlight -> Archlight.handle_selector_driver
Path 23: SelectorDriver.drive_selector -> Selector.recv_driver_input
Path 24: Archlight.invoke_type_wrangler -> TypeWrangler.recv_archlight_wrangle
Path 25: Archlight.invoke_test_adt -> ArchlightTestADT.run_test
Path 26: Archlight.call_al_util_service -> ArchStudioUtils.serve_archlight
Path 27: Archlight.fetch_al_resources -> Resources.provide_archlight_res
Path 28: TypeWrangler.wrangle_utils -> ArchStudioUtils.serve_type_wrangler
Path 29: GuardTracker.track_guards -> ArchStudioUtils.serve_guard_tracker
Path 30: AIMLauncher.launch_aim -> AIM.recv_aim_launcher
Path 31: ArchEdit.edit_via_utils -> ArchStudioUtils.serve_arch_edit
Path 32: RelatedElements.find_related -> ArchStudioUtils.serve_related_elements
Path 33: VersionPruner.prune_version -> Pruner.handle_version_prune
Path 34: Launcher.launch_editor -> SharedEditorInfrastructure.recv_launcher_call
Path 35: Launcher.launch_utils -> ArchStudioUtils.serve_launcher
Path 36: BooleanNotation.notate_boolean -> ArchStudioUtils.serve_boolean_notation
Path 37: SharedEditorInfrastructure.delegate_editor_mgr -> EditorManager.recv_shared_editor
Path 38: SharedEditorInfrastructure.shared_util_call -> ArchStudioUtils.serve_shared_editor
Path 39: RationaleView.view_meta -> Meta.recv_rationale_meta
Path 40: RationaleView.view_rv_utils -> ArchStudioUtils.serve_rationale_view
Path 41: PreferencesADT.access_prefs_utils -> ArchStudioUtils.serve_preferences_adt
Path 42: TracelinkView.trace_links -> ArchStudioUtils.serve_tracelink_view
Path 43: ChangeSetIdRelationships.relate_xarch_cs -> XArchChangeSet.recv_id_relationships
Path 44: ChangeSetIdRelationships.relate_id_cs_utils -> ChangeSetUtils.serve_id_relationships
Path 45: XArchDetach.detach_xarch -> XArchChangeSet.recv_detach
Path 46: ChangeSetStatusRelationships.status_xarch_cs -> XArchChangeSet.recv_status_relationships
Path 47: ChangeSetStatusRelationships.status_sr_cs_utils -> ChangeSetUtils.serve_status_relationships
Path 48: ExplicitADT.explicit_utils_call -> ArchStudioUtils.serve_explicit_adt
Path 49: ChangeSetIdView.view_cs_id -> ChangeSetUtils.serve_id_view
Path 50: ChangeSetStatusView.view_cs_status -> ChangeSetUtils.serve_status_view
Path 51: Selector.select_eval -> BooleanEval.recv_selector_eval
Path 52: EditorPrefs.set_editor_prefs -> EditorManager.recv_editor_prefs
Path 53: EditorManager.manage_files -> FileManager.handle_file_ops
Path 54: EditorManager.manager_util_call -> ArchStudioUtils.serve_editor_manager
Path 55: FileManager.file_util_call -> ArchStudioUtils.serve_file_manager
Path 56: Meta.meta_aim_call -> AIM.recv_meta_aim
Path 57: Meta.meta_util_call -> ArchStudioUtils.serve_meta
Path 58: AIMEclipse.eclipse_aim_call -> AIM.recv_eclipse_aim
Path 59: ChangeSetView.manage_cs_view -> ChangeSetUtils.serve_cs_view
Path 60: ChangeSetSync.sync_changesets -> ChangeSetUtils.serve_cs_sync
Path 61: ChangeSetRelationshipManager.manage_cs_rels -> ChangeSetUtils.serve_cs_rel_mgr
Path 62: ChangeSetADT.access_cs_adt -> ChangeSetUtils.serve_cs_adt
Path 63: XArchChangeSet.xarch_cs_utils_call -> ChangeSetUtils.serve_xarch_cs
Path 64: XArchChangeSet.xarch_cs_archstudio_call -> ArchStudioUtils.serve_xarch_changeset
Path 65: BooleanEval.evaluate_pruner -> Pruner.handle_eval_prune
Path 66: ArchlightPrefs.set_archlight_prefs -> ArchStudioUtils.serve_archlight_prefs
Path 67: ArchipelagoPrefs.config_archprefs_utils -> ArchStudioUtils.serve_archipelago_prefs
Path 68: FileTracker.track_files -> ArchStudioUtils.serve_file_tracker
Path 69: AIM.aim_util_call -> ArchStudioUtils.serve_aim
Path 70: AIM.aim_res_call -> Resources.provide_aim_res
Path 71: BasePreferences.base_prefs_call -> ArchStudioUtils.serve_base_prefs
Path 72: ArchStudioUtils.provide_resources -> Resources.provide_archstudio_res
Path 73: ChangeSetUtils.cs_util_arch_call -> ArchStudioUtils.serve_changeset_utils
Path 74: ChangeSetUtils.cs_util_res_call -> Resources.provide_changeset_res
