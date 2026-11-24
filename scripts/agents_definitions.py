"""The Agents Registry's configuration, in one readable place.

`scripts/build_seed_sql.py` turns this into the seed SQL under
agents-extension/.../meta_data/. Edit here, regenerate, commit both.

The registry is a generic reference registry of the agents who serve farmers
(extension agents, development agents, animal health workers). It assumes no
country: every coded field names a Master Data list (the AGENT_* lists of the
country pack's agriculture domain, openg2p-data packs/<country>/domains/
agriculture), and the assigned area is a geography unit at whatever level the
country's geography has. A country customises the lists and, if it must, the
forms below.

Two registers make the Agent record:
  * Agent (entity register): identity, person, contact, employment, the current
    assignment and the service status, kept through change requests approved in
    AWE (the version history is the audit trail of transfers and status changes);
  * its list sections, each a register of rows under the agent:
    AgentSpecialization and AgentQualification.
One activity register:
  * AgentTraining: trainings completed and certifications awarded, against the
    agent (the activity's subject is the Agent record).

Labels are plain English, shown as written (a label with no translation is
displayed as is).
"""

# ------------------------------------------------------------------ register IDs

AGENT = "a6e00000-0000-4000-8000-0000000a0001"
SPECIALIZATION = "a6e00000-0000-4000-8000-0000000a0002"
QUALIFICATION = "a6e00000-0000-4000-8000-0000000a0003"
TRAINING = "a6e00000-0000-4000-8000-0000000a0010"
INTAKE_FORM = "a6e00000-0000-4000-8000-0000000a0011"

REGISTERS = [
    # register_id, mnemonic, subject, description, master, rank, purpose, generates ID, dedup
    {"register_id": AGENT, "register_mnemonic": "Agent", "register_subject": "Agents",
     "register_description": "Agents who serve farmers: identity, employment, assignment and status",
     "master_register_id": None, "register_rank": 1, "register_purpose": "REGISTER",
     "functional_id_generation_required": True, "dedup_is_enabled": True, "dedup_threshold_score": 70},
    {"register_id": SPECIALIZATION, "register_mnemonic": "AgentSpecialization",
     "register_subject": "Specializations", "register_description": "An agent's specializations",
     "master_register_id": AGENT, "register_rank": 10, "register_purpose": "TABLE",
     "functional_id_generation_required": False, "dedup_is_enabled": False, "dedup_threshold_score": 0},
    {"register_id": QUALIFICATION, "register_mnemonic": "AgentQualification",
     "register_subject": "Qualifications", "register_description": "An agent's qualifications",
     "master_register_id": AGENT, "register_rank": 20, "register_purpose": "TABLE",
     "functional_id_generation_required": False, "dedup_is_enabled": False, "dedup_threshold_score": 0},
    {"register_id": TRAINING, "register_mnemonic": "AgentTraining", "register_subject": "Trainings",
     "register_description": "Trainings completed and certifications awarded, by agent",
     "master_register_id": None, "register_rank": 30, "register_purpose": "ACTIVITY",
     "functional_id_generation_required": False, "dedup_is_enabled": False, "dedup_threshold_score": 0},
]

# ----------------------------------------------------------- widget helpers

def _api_list(list_code: str) -> dict:
    """A Master Data list, read live by the dropdown."""
    return {"type": "api", "method": "POST", "params": {"attribute_id": list_code}, "service": "attributes",
            "endpoint": "values", "labelKey": "value_display", "valueKey": "value_id"}


_YES_NO = {"type": "static", "options": [{"label": "Yes", "value": True}, {"label": "No", "value": False}]}


def _widget(kind: str, register: str, field: str, label: str, required=False, readonly=False, **extra) -> dict:
    return {"widget": kind, "widget-id": field, "widget-type": "input", "widget-label": label,
            "widget-readonly": readonly, "widget-required": required,
            "widget-data-path": f"{register}.{field}", **extra}


def text(field, label, required=False, readonly=False, **extra):
    return _widget("text", AGENT, field, label, required, readonly, **extra)


def select(field, label, list_code, required=False):
    return _widget("select", AGENT, field, label, required, **{"widget-data-source": _api_list(list_code)})


def date(field, label, required=False, past_only=True):
    fmt = {"dateFormat": "DD/MM/YYYY", **({"dateConstraint": "past-only"} if past_only else {})}
    extra = {"widget-data-format": fmt}
    if past_only:
        extra["widget-data-options"] = {"maxDate": "today", "minDate": "1900-01-01"}
    return _widget("date", AGENT, field, label, required, **extra)


def coordinate(field, label, bound):
    return _widget("number", AGENT, field, label, **{
        "widget-data-format": {"textAlign": "left", "numericType": "decimal", "decimalPlaces": 6,
                               "decimalSeparator": ".", "thousandSeparator": ",", "allowSigned": True},
        "widget-data-validation": {"max": bound, "min": -bound}})


def geo(widget_id, label, required=False):
    return {"widget": "geo-hierarchy", "widget-id": widget_id, "widget-type": "input", "widget-label": label,
            "widget-required": required,
            "widget-data-path": {"value": f"{AGENT}.geo_lowest_level_value_id",
                                 "hierarchy": f"{AGENT}.geo_code_hierarchy_json"},
            "widget-geo-layout": {"columnSpan": 1},
            "widget-data-source": {"type": "api", "method": "POST", "service": "master-data",
                                   "levelsEndpoint": "get-all-g2p-geo-levels", "valuesEndpoint": "geo-level-values"}}


def document(key, label, required=False):
    return {"widget": "file", "widget-id": key, "widget-type": "input", "widget-label": label,
            "widget-required": required, "widget-data-path": f"{AGENT}.documents.{key}",
            "widget-data-options": {"accept": ".pdf,.jpg,.jpeg,.png", "maxSize": 5242880}}


def column(kind, field, label, list_code=None, required=False, **extra):
    col = {"widget": kind, "column-key": field, "widget-type": "input", "widget-label": label,
           "widget-readonly": False, "widget-required": required, "widget-data-path": field, **extra}
    if kind == "select":
        col["widget-data-source"] = _api_list(list_code) if list_code else _YES_NO
    return col


def panel(panel_id, widgets, title=None, **extra):
    p = {"widgets": widgets, "panel-id": panel_id, "panel-orientation": "vertical", **extra}
    if title:
        p["panel-title"] = title
    return p


def section_schema(section_key, title, panels, **extra):
    schema = {"panels": [{"panels": panels, "panel-id": f"{section_key}_main", "panel-orientation": "horizontal"}],
              "section-id": section_key, "section-title": title}
    # "section-editable": true makes every widget of the section editable in the
    # staff portal, overriding a widget's "widget-readonly": true. A section with a
    # read-only widget (the generated Agent ID) leaves it out, so each widget's own
    # setting holds. Not false: the staff API refuses change requests for a section
    # marked "section-editable": false.
    if not any(w.get("widget-readonly") for p in panels for w in p.get("widgets", [])):
        schema["section-editable"] = True
    schema.update(extra)
    return schema


def table_schema(section_key, title, register, columns, add_label):
    return {"panels": [{"panels": [{
        "widgets": [{"widget": "table", "widget-id": f"{section_key}_table", "widget-type": "table",
                     "widget-label": title, "widget-readonly": False,
                     "widget-data-path": f"{register}.records", "widget-data-columns": columns,
                     "widget-data-add-label": add_label,
                     "widget-data-operations": {"add": True, "edit": True, "remove": True}}],
        "panel-id": f"{section_key}_panel", "panel-column-span": 3, "panel-orientation": "vertical"}],
        "panel-id": f"{section_key}_main", "panel-orientation": "horizontal"}],
        "section-id": section_key, "section-title": title, "section-editable": True}


HEADER_SCHEMA = {"panels": [{"panels": [{"widgets": [{
    "widget": "header-section", "widget-id": "registry-header", "widget-type": "group",
    "widget-data-path": {key: f"{AGENT}.{field}" for key, field in {
        "name": "record_name", "image": "record_image_document_id", "status": "record_status",
        "imageUrl": "record_image_url", "createdAt": "created_at", "createdBy": "created_by",
        "functionalId": "functional_record_id", "statusReason": "record_status_reason",
        "lastApprovedAt": "last_approved_at", "lastApprovedBy": "last_approved_by"}.items()},
    "widget-data-format": {"imageSize": 120, "nameColor": "#ED7C22",
                           "statusColors": {"active": "#16A34A", "archived": "#6B7280", "inactive": "#D97706"}},
    "widget-field-config": {"status": {"data-source": {"type": "static", "options": [
        {"label": "ACTIVE", "value": "ACTIVE"}, {"label": "INACTIVE", "value": "INACTIVE"},
        {"label": "ARCHIVED", "value": "ARCHIVED"}]}}}}],
    "panel-id": "agent_header_inside_panel", "panel-orientation": "vertical"}],
    "panel-id": "agent_header_outside_panel", "panel-orientation": "horizontal"}],
    "section-id": "agent_header", "section-title": "Agent", "section-editable": True}

# ------------------------------------------------------------------ sections
# section_id, mnemonic, the register its data is in, list or not, description, UI schema.

SECTIONS = [
    {"section_id": "agent_header_section", "section_mnemonic": "agent_header", "section_register_id": AGENT,
     "is_list": False, "section_description": "Name, Agent ID and record status",
     "section_ui_schema": HEADER_SCHEMA},
    {"section_id": "agent_personal_section", "section_mnemonic": "agent_personal", "section_register_id": AGENT,
     "is_list": False, "section_description": "Agent ID, name, gender, date of birth, national ID and languages",
     "section_ui_schema": section_schema("agent_personal", "Personal details", [
         panel("agent_identity_panel", [
             text("functional_record_id", "Agent ID", readonly=True),
             text("foundational_id", "National ID"),
             text("languages_spoken", "Languages spoken"),
         ]),
         panel("agent_name_panel", [
             text("first_name", "First name", required=True),
             text("middle_name", "Middle name"),
             text("last_name", "Last name", required=True),
         ]),
         panel("agent_person_panel", [
             select("gender", "Gender", "GENDER", required=True),
             date("birth_date", "Date of birth", required=True),
         ]),
     ])},
    {"section_id": "agent_contact_section", "section_mnemonic": "agent_contact", "section_register_id": AGENT,
     "is_list": False, "section_description": "Mobile number, alternate phone and email",
     "section_ui_schema": section_schema("agent_contact", "Contact", [
         panel("agent_phone_panel", [
             text("mobile_number", "Mobile number", required=True,
                  **{"widget-data-validation": {"pattern": "^\\+?[0-9 ]{7,20}$",
                                                "patternMessage": "Enter a phone number, e.g. +251911000000"}}),
             text("alternate_phone", "Alternate phone"),
         ]),
         panel("agent_email_panel", [
             text("email", "Email", **{"widget-data-validation": {
                 "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", "patternMessage": "Enter an email address"}}),
         ]),
     ])},
    {"section_id": "agent_employment_section", "section_mnemonic": "agent_employment", "section_register_id": AGENT,
     "is_list": False,
     "section_description": "Employee number, position, employer, employment type and date of hire",
     "section_ui_schema": section_schema("agent_employment", "Employment", [
         panel("agent_position_panel", [
             text("employee_number", "Employee number"),
             select("position", "Position", "AGENT_POSITION", required=True),
         ]),
         panel("agent_employer_panel", [
             select("employer_type", "Employer type", "AGENT_EMPLOYER_TYPE", required=True),
             text("employer_name", "Employer"),
         ]),
         panel("agent_contract_panel", [
             select("employment_type", "Employment type", "AGENT_EMPLOYMENT_TYPE"),
             date("date_of_hire", "Date of hire"),
         ]),
     ])},
    {"section_id": "agent_assignment_section", "section_mnemonic": "agent_assignment", "section_register_id": AGENT,
     "is_list": False,
     "section_description": "Current assignment: area, service point, since when and why",
     "section_ui_schema": section_schema("agent_assignment", "Current assignment", [
         panel("agent_area_panel", [geo("agent_assigned_area", "Assigned area", required=True)],
               **{"panel-column-span": 1}),
         panel("agent_service_point_panel", [
             text("service_point_name", "Service point"),
             select("service_point_type", "Service point type", "AGENT_SERVICE_POINT_TYPE"),
             date("assigned_since", "Assigned since"),
             select("assignment_reason", "Assignment reason", "AGENT_ASSIGNMENT_REASON"),
         ], **{"panel-column-span": 1}),
         panel("agent_coordinates_panel", [
             coordinate("latitude", "Latitude", 90),
             coordinate("longitude", "Longitude", 180),
         ], **{"panel-column-span": 1}),
     ])},
    {"section_id": "agent_status_section", "section_mnemonic": "agent_status", "section_register_id": AGENT,
     "is_list": False, "section_description": "Service status: active, on leave, suspended, retired, separated",
     "section_ui_schema": section_schema("agent_status", "Service status", [
         panel("agent_status_panel", [
             select("service_status", "Status", "AGENT_SERVICE_STATUS", required=True),
             date("service_status_date", "Status date"),
         ]),
         panel("agent_status_reason_panel", [text("service_status_reason", "Reason")]),
     ])},
    {"section_id": "agent_specializations_section", "section_mnemonic": "agent_specializations",
     "section_register_id": SPECIALIZATION, "is_list": True,
     "section_description": "The agent's specializations, one marked primary",
     "section_ui_schema": table_schema("agent_specializations", "Specializations", SPECIALIZATION, [
         column("select", "specialization", "Specialization", "AGENT_SPECIALIZATION", required=True),
         column("select", "is_primary", "Primary"),
         column("date", "since", "Since", **{"widget-data-format": {"dateFormat": "DD/MM/YYYY",
                                                                     "dateConstraint": "past-only"}}),
     ], "Add specialization")},
    {"section_id": "agent_qualifications_section", "section_mnemonic": "agent_qualifications",
     "section_register_id": QUALIFICATION, "is_list": True,
     "section_description": "The agent's qualifications: level, field of study, institution, year",
     "section_ui_schema": table_schema("agent_qualifications", "Qualifications", QUALIFICATION, [
         column("select", "qualification_level", "Level", "AGENT_QUALIFICATION_LEVEL", required=True),
         column("select", "field_of_study", "Field of study", "AGENT_FIELD_OF_STUDY"),
         column("text", "institution", "Institution"),
         column("number", "year_completed", "Year completed",
                **{"widget-data-format": {"allowSigned": False, "numericType": "integer"},
                   "widget-data-validation": {"min": 1950, "max": 2100}}),
     ], "Add qualification")},
    {"section_id": "agent_documents_section", "section_mnemonic": "agent_documents", "section_register_id": AGENT,
     "is_list": False, "section_description": "Appointment letter and national ID document",
     "section_ui_schema": section_schema("agent_documents", "Documents", [
         panel("agent_documents_panel", [
             document("appointment_letter", "Appointment letter"),
             document("national_id_document", "National ID document"),
         ]),
     ], **{"section-column-span": 3})},
]

# Register tabs, in order: (tab_id, label, order, [section_id ...]).
TABS = [
    ("agent_profile_tab", "Profile", 0,
     ["agent_header_section", "agent_personal_section", "agent_contact_section"]),
    ("agent_employment_tab", "Employment and assignment", 10,
     ["agent_employment_section", "agent_assignment_section", "agent_status_section"]),
    ("agent_qualifications_tab", "Specializations and qualifications", 20,
     ["agent_specializations_section", "agent_qualifications_section"]),
    ("agent_documents_tab", "Documents", 30, ["agent_documents_section"]),
]

# Registering a new agent: the staff intake form, approved in AWE.
INTAKE = {
    "form_id": INTAKE_FORM, "form_mnemonic": "agent_intake_form",
    "form_description": "Registers a new agent. The Agent ID is generated on approval.",
    "tab_id": "agent_intake_tab",
    "sections": ["agent_personal_section", "agent_contact_section", "agent_employment_section",
                 "agent_assignment_section", "agent_status_section", "agent_specializations_section",
                 "agent_qualifications_section", "agent_documents_section"],
}

# Staff search results and filters on the Agent register; duplicate check.
SEARCH_RESULTS = [
    ("functional_record_id", "Agent ID"), ("record_name", "Name"), ("position", "Position"),
    ("geo_lowest_level_value_id", "Assigned area"), ("service_point_name", "Service point"),
    ("service_status", "Status"), ("mobile_number", "Mobile"),
]
FILTERS = [
    ("first_name", "First name", "text"), ("last_name", "Last name", "text"),
    ("functional_record_id", "Agent ID", "text"), ("foundational_id", "National ID", "text"),
    ("employee_number", "Employee number", "text"), ("position", "Position", "text"),
    ("service_status", "Status", "text"), ("geo_lowest_level_value_id", "Assigned area", "text"),
]
DEDUPLICATE = [
    {"field_name": "foundational_id", "match_type": "exact", "weight": 0.5},
    {"field_name": "first_name", "match_type": "fuzzy", "weight": 0.2},
    {"field_name": "last_name", "match_type": "fuzzy", "weight": 0.15},
    {"field_name": "birth_date", "match_type": "exact", "weight": 0.15},
]
SECTION_SEARCH_RESULTS = {
    SPECIALIZATION: [("specialization", "Specialization"), ("is_primary", "Primary"), ("since", "Since")],
    QUALIFICATION: [("qualification_level", "Level"), ("field_of_study", "Field of study"),
                    ("institution", "Institution"), ("year_completed", "Year")],
}

# Change requests and intake forms of the Agent register are approved in AWE
# under these policy keys (awe_meta_data/ seeds the policies).
AWE_POLICIES = [
    ("a6e00000-0000-4000-8000-0000000a0031", "REGISTER", "", "registry.change_request",
     "registry.change_request.agent"),
    ("a6e00000-0000-4000-8000-0000000a0032", "INTAKE_FORM", INTAKE_FORM, "registry.intake_form",
     "registry.intake_form.agent"),
]

# Every coded field of the record, by Master Data list (checked against the pack in CI).
RECORD_LISTS = {
    "gender": "GENDER", "position": "AGENT_POSITION", "employer_type": "AGENT_EMPLOYER_TYPE",
    "employment_type": "AGENT_EMPLOYMENT_TYPE", "service_point_type": "AGENT_SERVICE_POINT_TYPE",
    "assignment_reason": "AGENT_ASSIGNMENT_REASON", "service_status": "AGENT_SERVICE_STATUS",
    "specialization": "AGENT_SPECIALIZATION", "qualification_level": "AGENT_QUALIFICATION_LEVEL",
    "field_of_study": "AGENT_FIELD_OF_STUDY",
}

# ======================================================== AgentTraining activities

_DATE = {"type": "string", "format": "date"}
_CONTEXT = {
    "agent_id": {"type": "string", "title": "Agent ID", "minLength": 1, "maxLength": 64},
    "geo_lowest_level_value_id": {"type": "string", "title": "Where it took place"},
    "remarks": {"type": "string", "title": "Remarks", "maxLength": 2000},
}


def _schema(required: list[str], properties: dict) -> dict:
    return {"type": "object", "required": ["agent_id"] + required,
            "properties": {**_CONTEXT, **properties}, "additionalProperties": False}


_REFERENCES = {
    # The agent: a record of this registry's Agent register, by Agent ID, and the
    # activity's subject (the trainings show on the agent's profile).
    "agent_id": {"kind": "LOCAL_RECORD", "register": "Agent", "match": "functional_record_id",
                 "mode": "STRICT", "subject": True},
    # A topic code an external system (a learning platform) sends that the list
    # lacks is accepted with a warning.
    "topic": {"kind": "ATTRIBUTE", "attribute": "AGENT_TRAINING_TOPIC", "mode": "LENIENT"},
    "geo_lowest_level_value_id": {"kind": "GEO", "mode": "LENIENT", "location": True},
}

ACTIVITY_TYPES = [
    {
        "activity_type": "TRAINING_COMPLETED",
        "display_name": "Training completed",
        "description": "The agent completed a training course. Occurred at: the date it ended.",
        "display_order": 10,
        "payload_schema": _schema(["topic", "course_title"], {
            "topic": {"type": "string", "title": "Topic"},
            "course_title": {"type": "string", "title": "Course", "minLength": 2, "maxLength": 300},
            "course_code": {"type": "string", "title": "Course code", "maxLength": 100},
            "provider": {"type": "string", "title": "Provider", "maxLength": 300},
            "start_date": {**_DATE, "title": "Start date"},
            "end_date": {**_DATE, "title": "End date"},
            # Derived from start_date and end_date (the domain service's enrich_payload).
            "course_days": {"type": "integer", "title": "Course days", "minimum": 1},
            "hours": {"type": "number", "title": "Hours", "minimum": 0, "maximum": 5000},
            "delivery_mode": {"type": "string", "title": "Delivery mode"},
            "result": {"type": "string", "title": "Result"},
            "score": {"type": "number", "title": "Score (%)", "minimum": 0, "maximum": 100},
        }),
        "is_repeatable": True,
        "allow_future_dated": False,
        "reference_rules": {**_REFERENCES,
                            "delivery_mode": {"kind": "ATTRIBUTE", "attribute": "AGENT_TRAINING_DELIVERY_MODE",
                                              "mode": "STRICT"},
                            "result": {"kind": "ATTRIBUTE", "attribute": "AGENT_TRAINING_RESULT", "mode": "STRICT"}},
    },
    {
        "activity_type": "CERTIFICATION_AWARDED",
        "display_name": "Certification awarded",
        "description": "The agent was awarded a certification. Occurred at: the date it was issued.",
        "display_order": 20,
        "payload_schema": _schema(["certification"], {
            "certification": {"type": "string", "title": "Certification", "minLength": 2, "maxLength": 300},
            "topic": {"type": "string", "title": "Topic"},
            "issuing_body": {"type": "string", "title": "Issuing body", "maxLength": 300},
            "certificate_number": {"type": "string", "title": "Certificate number", "maxLength": 100},
            "valid_until": {**_DATE, "title": "Valid until"},
        }),
        "is_repeatable": True,
        "allow_future_dated": False,
        "reference_rules": _REFERENCES,
    },
]

INDICATORS = [
    ("AGENTS_TRAINED", "Agents trained", "agents",
     {"measure": {"fn": "count", "field": "context_id"}, "group_by": []}, 10),
    ("TRAINING_HOURS", "Training hours", "hours",
     {"measure": {"fn": "sum", "field": "training_hours"}, "group_by": []}, 20),
    ("AGENTS_TRAINED_BY_LAST_TOPIC", "Agents by topic of their last training", "agents",
     {"measure": {"fn": "count", "field": "context_id"}, "group_by": ["last_training_topic"]}, 30),
    ("AGENTS_CERTIFIED", "Agents with a certification", "agents",
     {"measure": {"fn": "count", "field": "context_id"}, "group_by": [],
      "filters": {"is_certified": True}}, 40),
]

PARTICIPANT_ROLES = {"agent": {"field": "agent_id", "primary": True}}

# Every coded field of the activities, by Master Data list.
ACTIVITY_LISTS = {"topic": "AGENT_TRAINING_TOPIC", "delivery_mode": "AGENT_TRAINING_DELIVERY_MODE",
                  "result": "AGENT_TRAINING_RESULT"}
