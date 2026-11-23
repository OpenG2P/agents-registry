# openg2p-registry-agents-extension

The Agents Registry's domain, installed into the OpenG2P registry-platform images
and selected with `REGISTRY_EXTENSION_MODULE=openg2p_registry_agents_extension`.

| Register | Kind | Holds |
|---|---|---|
| `Agent` | Entity register | Agent ID (generated, 8 digits), person, national ID, contact, employment, current assignment (the record's location), service status |
| `AgentSpecialization`, `AgentQualification` | List sections of `Agent` | Rows under the agent |
| `AgentTraining` | Activity register | Trainings completed and certifications awarded, one context per agent, with a summary per agent |

| Path | What |
|---|---|
| `register_domain/models/` | The record registers' models (register, history, intake form) and the activity and projection models |
| `register_domain/services/` | Validation, record names and search text; the training context, projection and sample trainings |
| `register_domain/id_generator/` | Agent ID prefix (none) for the `agent` pool |
| `meta_data/` | Seed SQL, copied into the db-seed image and run at install. Register metadata, AWE bindings, activity types and indicators are **generated** by `scripts/build_seed_sql.py` from `scripts/agents_definitions.py`: edit it, regenerate, commit both |
| `meta_data/activity-config/AgentTraining.json` | The training register's context, subject, UI hints, search fields and plausibility rules |
| `meta_data/reporting-views/` | Reporting views over agents and trainings |
| `awe_meta_data/` | Approval policies for agent change requests and the intake form (run against the shared AWE database) |
