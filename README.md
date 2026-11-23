# Agents Registry

An OpenG2P **reference registry** of the agents who serve farmers — extension
agents, development agents, animal health workers — built on the OpenG2P
registry platform. Generic fields and lists that a system integrator customises
for a country; Ethiopia's Development Agents are the first case.

* **Agent** (entity register): Agent ID (generated, eight digits), person and
  national ID, contact, employment, the **current assignment** (an area of the
  country's geography, at any level, and a service point) and the **service
  status**, with **Specializations** and **Qualifications** as list sections.
  Every change is a change request approved in AWE; the record's version
  history is the audit trail of transfers, promotions and status changes.
* **AgentTraining** (activity register): **trainings completed** and
  **certifications awarded**, append-only, against the agent (the activity's
  subject is the Agent record, so they show on its profile), with a summary per
  agent: trainings, hours, last training, latest certification.

It is not shared with partners: no Partner API search output, no data scopes,
consent enforcement off. The Partner API is deployed only to take data in (a
learning platform's trainings, an existing agent system's records).

Design: [Agents Registry](https://docs.openg2p.org/products/open-agri-stack/roadmap/agent-registry).

## What this repo owns

| Path | What |
|---|---|
| `agents-extension/` | The domain: models, domain services (checks, record names, the training context and summary, sample trainings), seed SQL, the training register's configuration |
| `scripts/agents_definitions.py` | The registers, sections, tabs, intake form, search, duplicate check, AWE bindings, activity types and indicators — the one place to edit. **Developer tool, never run in a deployment** |
| `scripts/build_seed_sql.py` | Generates the seed SQL in `agents-extension/.../meta_data/` from the definitions (`--check` in CI). Only that committed SQL ships |
| `docker/` | Thin images `FROM` the registry-platform images: staff-api, partner-api, celery, db-seed (with the sample loader) |
| `helm/openg2p-agents-registry/` | Values overlay over the `openg2p-registry` chart |
| `test/` | List checks against the country packs; integration tests on a real PostgreSQL |

The registry-platform version is pinned in `docker/*/Dockerfile` (`RP_VERSION`)
and `helm/.../Chart.yaml`, kept in lockstep by `scripts/bump-rp-version.sh`
(`-n` shows the newest published version).

## Lists come from Master Data

This registry keeps no code lists. Every coded field names a Master Data list,
the `AGENT_*` lists of the country pack's agriculture domain in
[openg2p-data](https://github.com/OpenG2P/openg2p-data) (`AGENT_POSITION`,
`AGENT_SPECIALIZATION`, `AGENT_SERVICE_STATUS`, …; gender is the core `GENDER`).
Every pack has the same codes; a country changes the labels and adds values.
Install Master Data with that domain before this registry:

```yaml
# openg2p-master-data values
geoSeed:
  countryPack: ETH
  domains: [agriculture]
```

## Sample data

Two switches, both off by default:

* `registry.dbSeed.loadSampleData`: db-seed loads the country pack's sample
  agents (`packs/<country>/samples/agents.json` in openg2p-data; the ETH pack has
  24 Development Agents in eleven woredas of eight regions) as approved Agent records;
* `REGISTRY_CELERY_WORKERS_ACTIVITY_LOAD_SAMPLE_DATA` (Rancher: "Load sample
  trainings"): the platform's sample task records their trainings and
  certifications through the activity APIs.

## Customising for a country

Change the `AGENT_*` lists in the country pack; set the ID length (and, in
`register_domain/id_generator`, a prefix) if the country wants another Agent ID;
change the forms in `scripts/agents_definitions.py` and regenerate. For
Ethiopia: a kebele level in the pack's geography, Farmer Training Centres as
service points, DA positions, and an ingestion mapping from the Ministry's
existing DA Registry.

## Tests

```bash
# List checks (no platform needed): every list and code is in each country pack
OPENG2P_DATA_DIR=../openg2p-data pytest test/test_code_lists_in_pack.py test/test_rp_pin_lockstep.py
python3 scripts/build_seed_sql.py --check

# Integration tests: registry-platform core + this extension installed, openg2p-data and
# registry-platform beside this repo, a disposable PostgreSQL
docker run -d --name agents-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:16
docker exec agents-pg psql -U postgres -c "create database agents_test"
pip install -e <registry-platform>/core/openg2p-registry-core -e agents-extension pytest pytest-asyncio psycopg2-binary
pytest test/integration
```
