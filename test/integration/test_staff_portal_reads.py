"""The platform's own services read the Agent register the way the staff portal does:
its tabs and sections, and an agent's records tab by tab (the list sections included)."""

from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_registry_agents_extension.register_domain.models import (
    G2PRegisterAgent,
    G2PRegisterAgentQualification,
    G2PRegisterAgentSpecialization,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

AGENT = "a6e00000-0000-4000-8000-0000000a0001"
SPECIALIZATION = "a6e00000-0000-4000-8000-0000000a0002"
QUALIFICATION = "a6e00000-0000-4000-8000-0000000a0003"


@pytest_asyncio.fixture(loop_scope="session")
async def agent_record(database):
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="test")
    # The read path also touches platform tables the other tests do not need
    # (completion scores, change requests, ...): create every declared table.
    import openg2p_registry_core.models  # noqa: F401
    from openg2p_fastapi_common.models import BaseORMModel

    async with database.begin() as conn:
        await conn.run_sync(lambda sync: BaseORMModel.metadata.create_all(sync, checkfirst=True))
    from openg2p_registry_core.services.g2p_document_service import G2PDocumentService

    if G2PDocumentService.get_component() is None:
        G2PDocumentService()  # resolves record images; there are none here
    stamp = dict(created_by="portal-test", created_at=datetime(2026, 11, 23), last_approved_at=datetime(2026, 11, 23),
                 last_approved_by="portal-test")
    sessions = async_sessionmaker(database, expire_on_commit=False)
    async with sessions() as session:
        agent = G2PRegisterAgent(functional_record_id="99000200", first_name="Bontu", last_name="Gemechu",
                                 gender="FEMALE", birth_date=date(1993, 5, 1), position="AGPOS_FIELD_AGENT",
                                 geo_lowest_level_value_id="ET040611", service_status="AGST_ACTIVE", **stamp)
        session.add(agent)
        await session.flush()
        session.add_all([
            G2PRegisterAgentSpecialization(link_internal_record_id=agent.internal_record_id,
                                           specialization="AGSPEC_CROP", is_primary=True, **stamp),
            G2PRegisterAgentSpecialization(link_internal_record_id=agent.internal_record_id,
                                           specialization="AGSPEC_IRRIGATION", is_primary=False, **stamp),
            G2PRegisterAgentQualification(link_internal_record_id=agent.internal_record_id,
                                          qualification_level="AGQUAL_TVET_LEVEL_4", year_completed=2014, **stamp),
        ])
        await session.commit()
    yield agent.internal_record_id
    async with database.begin() as conn:
        for table in ("g2p_register_agent_specializations", "g2p_register_agent_qualifications",
                      "g2p_register_agents"):
            await conn.execute(text(f"DELETE FROM {table} WHERE created_by = 'portal-test'"))


async def test_tabs_and_sections(agent_record):
    from openg2p_registry_core.services import G2PRegisterMetadataService

    service = G2PRegisterMetadataService.get_component() or G2PRegisterMetadataService()
    tabs, total, _ = await service.get_all_tabs(AGENT)
    assert [t.tab_id for t in tabs] == ["agent_profile_tab", "agent_employment_tab", "agent_qualifications_tab",
                                        "agent_documents_tab"]
    sections = await service.get_tab_sections("agent_qualifications_tab", 1, 50)
    assert [s.section_id for s in sections] == ["agent_specializations_section", "agent_qualifications_section"]


async def test_an_agents_records_by_tab(agent_record):
    from openg2p_registry_core.services import G2PRegisterHierarchicalService

    service = G2PRegisterHierarchicalService.get_component() or G2PRegisterHierarchicalService()
    tab = await service.get_tab_records(AGENT, agent_record, "agent_qualifications_tab")
    by_register = {}
    for group in tab:
        data = group.model_dump() if hasattr(group, "model_dump") else dict(group)
        by_register[data.get("section_register_id")] = data
    assert set(by_register) == {SPECIALIZATION, QUALIFICATION}
    rows = by_register[SPECIALIZATION].get("records") or []
    assert sorted(r.get("specialization") for r in rows) == ["AGSPEC_CROP", "AGSPEC_IRRIGATION"]

    profile = await service.get_tab_records(AGENT, agent_record, "agent_profile_tab")
    record = profile[0].model_dump() if hasattr(profile[0], "model_dump") else dict(profile[0])
    flat = str(record)
    assert "Bontu" in flat and "99000200" in flat
