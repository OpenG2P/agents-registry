#!/usr/bin/env python3
"""Load the Agents Registry's sample agents (db-seed, LOAD_SAMPLE_DATA=true).

The sample agents are country data, kept with the country pack in openg2p-data
(``packs/<country>/samples/agents.json``; the db-seed image carries openg2p-data
at /openg2p-data). The pack is the one whose sample agents' areas Master Data
knows: the country Master Data was installed with. Master Data does not load
this file; it serves only the geography it refers to.

Each sample agent becomes an approved Agent record, inserted straight into
g2p_register_agents with its specialization and qualification rows, as if it
had been registered and approved — the way the Farmer Registry and the Crop
Sown Registry load their samples. The Agent IDs are the samples' own (eight
digits, the generator's shape), so a reinstall produces the same data.
Idempotent: ON CONFLICT DO NOTHING on the record ids, which are derived from
the Agent ID.

geo_code_hierarchy_json is the area's ancestry read from Master Data through its
API (the platform's /seed/mds_client.py and the MDS_* env the chart passes), in
the shape registry-core's G2PGeoHierarchyService produces. If Master Data is
unreachable the area id is still stored and the hierarchy left empty.

Sample trainings are not loaded here: they go through the activity APIs (the
platform's sample task), not straight into tables.
"""

import json
import os
import sys
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

SEEDER = "seeder"
CREATED_AT = "2026-11-23 00:00:00"
NAMESPACE = uuid.UUID("a6e00000-0000-4000-8000-0000000a5eed")
DATA_DIR = Path(os.environ.get("OPENG2P_DATA_DIR", "/openg2p-data"))

AGENT_FIELDS = [
    "employee_number", "languages_spoken", "mobile_number", "email", "position", "employer_type",
    "employer_name", "employment_type", "date_of_hire", "service_point_name", "service_point_type",
    "assigned_since", "assignment_reason", "service_status", "service_status_date", "service_status_reason",
]


def log(message: str) -> None:
    print(f"[load-sample-data] {message}", flush=True)


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"[load-sample-data] Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def master_data():
    """The platform's Master Data API client, or None (logged) when unavailable."""
    try:
        from mds_client import MdsClient  # /seed/mds_client.py, from the RP db-seed base image
    except ImportError:
        log("mds_client.py is not in this image — agents are stored without a geo hierarchy.")
        return None
    client = MdsClient.from_env()
    if client is None:
        log("MDS_API_URL not set — agents are stored without a geo hierarchy.")
    return client


def hierarchy(client, unit_id: str):
    """The unit's ancestry, top level first, or None when Master Data does not know it."""
    if client is None or not unit_id:
        return None
    from mds_client import MdsError

    try:
        return client.geo_hierarchy_json(unit_id)
    except MdsError as exc:
        log(f"could not read area {unit_id} from Master Data ({exc}).")
        return None


def sample_files() -> list[Path]:
    return sorted(DATA_DIR.glob("packs/*/samples/agents.json"))


def choose_samples(client) -> tuple[Path, list[dict]] | tuple[None, list]:
    """The pack whose sample agents sit on areas Master Data knows; the only one when Master Data is not set."""
    files = sample_files()
    if not files:
        return None, []
    candidates = [(path, json.loads(path.read_text())) for path in files]
    if client is None:
        return candidates[0] if len(candidates) == 1 else (None, [])
    for path, agents in candidates:
        if agents and hierarchy(client, agents[0].get("geo_pcode")):
            return path, agents
    return None, []


def record_id(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, ":".join(parts)))


def search_text(agent: dict) -> str:
    parts = [agent["agent_id"], agent.get("given_name"), agent.get("fathers_name"), agent.get("grandfathers_name"),
             agent.get("national_id"), agent.get("employee_number"), agent.get("phone"), agent.get("email"),
             agent.get("position"), agent.get("service_point_name"), agent.get("geo_pcode")]
    return " ".join(str(p) for p in parts if p)


def insert(cur, table: str, row: dict) -> int:
    columns = list(row)
    cur.execute(
        f'INSERT INTO "public"."{table}" (' + ", ".join(f'"{c}"' for c in columns) + ") VALUES ("
        + ", ".join(["%s"] * len(columns)) + ") ON CONFLICT DO NOTHING",
        [row[c] for c in columns],
    )
    return cur.rowcount


def audit(name: str) -> dict:
    return {"record_name": name, "created_by": SEEDER, "created_at": CREATED_AT, "last_approved_at": CREATED_AT,
            "last_approved_by": SEEDER, "record_status": "ACTIVE"}


def main() -> None:
    mds = master_data()
    path, agents = choose_samples(mds)
    if not agents:
        found = ", ".join(str(p.relative_to(DATA_DIR)) for p in sample_files()) or "none"
        log(f"No sample agents for this country (sample files: {found}) — nothing to load.")
        return
    log(f"Loading {len(agents)} sample agents from {path.relative_to(DATA_DIR)}")

    conn = psycopg2.connect(
        host=env("PGHOST"), port=os.environ.get("PGPORT", "5432"), dbname=env("PGDATABASE"),
        user=env("PGUSER"), password=env("PGPASSWORD"),
    )
    counts = {"agents": 0, "specializations": 0, "qualifications": 0}
    try:
        with conn, conn.cursor() as cur:
            for agent in agents:
                agent_id = agent["agent_id"]
                parent = record_id("agent", agent_id)
                tree = hierarchy(mds, agent.get("geo_pcode"))
                counts["agents"] += insert(cur, "g2p_register_agents", {
                    "internal_record_id": parent, "functional_record_id": agent_id,
                    **audit(agent.get("full_name") or agent_id), "search_text": search_text(agent),
                    "first_name": agent.get("given_name"), "middle_name": agent.get("fathers_name"),
                    "last_name": agent.get("grandfathers_name"), "gender": agent.get("gender"),
                    "birth_date": agent.get("birth_date"), "foundational_id": agent.get("national_id"),
                    "mobile_number": agent.get("phone"),
                    "geo_lowest_level_value_id": agent.get("geo_pcode"),
                    "geo_code_hierarchy_json": Json(tree) if tree else None,
                    **{field: agent.get(field) for field in AGENT_FIELDS if field != "mobile_number"},
                })
                for row in agent.get("specializations") or []:
                    counts["specializations"] += insert(cur, "g2p_register_agent_specializations", {
                        "internal_record_id": record_id("specialization", agent_id, row["specialization"]),
                        "link_internal_record_id": parent, **audit(row["specialization"]),
                        "specialization": row["specialization"], "is_primary": bool(row.get("is_primary")),
                        "since": row.get("since"),
                    })
                for index, row in enumerate(agent.get("qualifications") or [], start=1):
                    counts["qualifications"] += insert(cur, "g2p_register_agent_qualifications", {
                        "internal_record_id": record_id("qualification", agent_id, str(index)),
                        "link_internal_record_id": parent, **audit(row["level"]),
                        "qualification_level": row["level"], "field_of_study": row.get("field_of_study"),
                        "institution": row.get("institution"), "year_completed": row.get("year_completed"),
                    })
        for table, inserted in counts.items():
            log(f"  -> {table}: {inserted} inserted")
        log("Done.")
    except Exception as exc:
        print(f"[load-sample-data] FAILED: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
