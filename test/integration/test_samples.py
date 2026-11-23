"""Sample data: the ETH pack's sample agents through the db-seed loader, then their sample trainings."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

from openg2p_registry_core.errors import G2PRegistryException

pytestmark = pytest.mark.asyncio(loop_scope="session")

REPO = Path(__file__).resolve().parents[2]
LOADER = REPO / "docker/db-seed/load_sample_data.py"


def _mds_client(levels, units):
    """The platform's seed MDS client (registry-platform docker/db-seed/mds_client.py) over the catalogue stand-in."""
    import httpx
    from openg2p_registry_core.testing.master_data_stub import BASE_URL, TOKEN_URL, stub_from_tables

    seed_dir = Path(os.environ.get("RP_DB_SEED_DIR", REPO.parent / "registry-platform/docker/db-seed"))
    if str(seed_dir) not in sys.path:
        sys.path.insert(0, str(seed_dir))
    mds_client = pytest.importorskip("mds_client", reason="registry-platform's docker/db-seed/mds_client.py "
                                                          "not found (set RP_DB_SEED_DIR)")
    stub = stub_from_tables(levels=levels, level_values=units)

    def send(method, url, headers, body):
        response = stub._handle(httpx.Request(method, url, headers=headers, content=body or b""))
        return response.status_code, response.content

    return mds_client.MdsClient(BASE_URL, token_url=TOKEN_URL, client_id="registry-staff-portal",
                                client_secret="secret", transport=send)


def _loader():
    pytest.importorskip("psycopg2", reason="the db-seed loader needs psycopg2 (pip install psycopg2-binary)")
    spec = importlib.util.spec_from_file_location("agents_load_sample_data", LOADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _geography(conn):
    levels = [dict(r._mapping) for r in (await conn.execute(text(
        "SELECT level_id, level_mnemonic, parent_level_id FROM g2p_geo_levels"))).all()]
    units = [dict(r._mapping) for r in (await conn.execute(text(
        "SELECT level_value_id, level_id, level_value_mnemonic, parent_level_value_id FROM g2p_geo_level_values"
    ))).all()]
    return levels, units


async def test_sample_agents_then_their_trainings(service, clean, database, monkeypatch):
    from openg2p_registry_core.services import G2PActivitySampleService

    from conftest import DB_URL

    loader = _loader()
    async with database.connect() as conn:
        levels, units = await _geography(conn)
    mds = _mds_client(levels, units)
    monkeypatch.setattr(loader, "master_data", lambda: mds)
    data = os.environ.get("OPENG2P_DATA_DIR") or str(REPO.parent / "openg2p-data")
    monkeypatch.setattr(loader, "DATA_DIR", Path(data))
    url = DB_URL.replace("postgresql+asyncpg://", "postgresql://")
    from sqlalchemy.engine import make_url

    parsed = make_url(url)
    for key, value in {"PGHOST": parsed.host, "PGPORT": str(parsed.port or 5432), "PGDATABASE": parsed.database,
                       "PGUSER": parsed.username, "PGPASSWORD": parsed.password or ""}.items():
        monkeypatch.setenv(key, value)

    samples = G2PActivitySampleService()
    try:
        # No sample agents yet: an error naming the missing source, not a silent "nothing loaded".
        with pytest.raises(G2PRegistryException, match="No sample agents"):
            await samples.load("AgentTraining")

        loader.main()
        loader.main()  # idempotent
        async with database.connect() as conn:
            agents = (await conn.execute(text(
                "SELECT functional_record_id, record_name, geo_code_hierarchy_json FROM g2p_register_agents "
                "WHERE created_by = 'seeder' ORDER BY 1"))).all()
            rows = dict((await conn.execute(text(
                "SELECT 'specializations', count(*) FROM g2p_register_agent_specializations "
                "UNION ALL SELECT 'qualifications', count(*) FROM g2p_register_agent_qualifications"))).all())
        assert len(agents) == 24 and agents[0].functional_record_id == "01010101"
        assert agents[0].record_name == "Gebremedhin Hailu Tesfay"
        hierarchy = [level["level_value_mnemonic"] for level in agents[0].geo_code_hierarchy_json["hierarchy"]]
        assert hierarchy == ["Ethiopia", "Tigray", "North Western", "Tahtay Adiyabo"]
        assert rows["specializations"] >= 24 and rows["qualifications"] >= 24

        loaded = await samples.load("AgentTraining")
        assert loaded > 30
        assert await samples.load("AgentTraining") == 0  # idempotent
        async with database.connect() as conn:
            summary = (await conn.execute(text(
                "SELECT count(*), sum(training_count), count(*) FILTER (WHERE is_certified) "
                "FROM g2p_activity_projection_agent_training"))).one()
            superseded = (await conn.execute(text(
                "SELECT count(*) FROM g2p_activity_agent_training WHERE status = 'SUPERSEDED'"))).scalar()
            by_area = (await conn.execute(text(
                "SELECT sum(agents) FROM agents_rpt_agents_by_area"))).scalar()
        # Every sample agent (whatever their service status) has trainings; every third is certified.
        assert summary[0] == 24 and summary[1] >= 24 and summary[2] == 8
        assert superseded == 1
        assert by_area == 24
    finally:
        async with database.begin() as conn:
            for table in ("g2p_register_agent_specializations", "g2p_register_agent_qualifications",
                          "g2p_register_agents"):
                await conn.execute(text(f"DELETE FROM {table} WHERE created_by = 'seeder'"))
