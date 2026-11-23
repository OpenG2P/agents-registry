"""The Agent register: its seeded metadata, a record round-tripping through its tables, its checks."""

from datetime import date, datetime

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_registry_core.errors import G2PRegistryException
from openg2p_registry_agents_extension.register_domain.models import (
    G2PRegisterAgent,
    G2PRegisterAgentQualification,
    G2PRegisterAgentSpecialization,
)
from openg2p_registry_agents_extension.register_domain.services import (
    G2PRegisterDomainServiceAgent,
    G2PRegisterDomainServiceAgentQualification,
    G2PRegisterDomainServiceAgentSpecialization,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

AGENT = "a6e00000-0000-4000-8000-0000000a0001"
SPECIALIZATION = "a6e00000-0000-4000-8000-0000000a0002"
QUALIFICATION = "a6e00000-0000-4000-8000-0000000a0003"
TRAINING = "a6e00000-0000-4000-8000-0000000a0010"
MODELS = {AGENT: G2PRegisterAgent, SPECIALIZATION: G2PRegisterAgentSpecialization,
          QUALIFICATION: G2PRegisterAgentQualification}


def _widgets(node):
    if isinstance(node, dict):
        if "widget-id" in node or "column-key" in node:
            yield node
        for value in node.values():
            yield from _widgets(value)
    elif isinstance(node, list):
        for item in node:
            yield from _widgets(item)


async def test_registers_are_seeded(database):
    async with database.connect() as conn:
        rows = {r.register_mnemonic: r for r in (await conn.execute(text(
            "SELECT register_id, register_mnemonic, register_purpose, master_register_id, "
            "functional_id_generation_required, dedup_is_enabled, requires_registrant_authentication "
            "FROM g2p_register_definitions"))).all()}
    assert rows["Agent"].register_purpose == "REGISTER" and rows["Agent"].functional_id_generation_required
    assert rows["Agent"].dedup_is_enabled and not rows["Agent"].requires_registrant_authentication
    for mnemonic in ("AgentSpecialization", "AgentQualification"):
        assert rows[mnemonic].register_purpose == "TABLE" and rows[mnemonic].master_register_id == AGENT
    assert rows["AgentTraining"].register_purpose == "ACTIVITY"


async def test_every_widget_writes_a_real_column(database):
    async with database.connect() as conn:
        sections = (await conn.execute(text(
            "SELECT section_id, section_register_id, is_list, section_ui_schema FROM g2p_register_sections "
            "WHERE register_id = :r"), {"r": AGENT})).all()
        tab_sections = set((await conn.execute(text(
            "SELECT ts.section_id FROM g2p_register_ui_tab_sections ts JOIN g2p_register_ui_tabs t "
            "ON t.tab_id = ts.tab_id WHERE t.register_id = :r"), {"r": AGENT})).scalars())
        intake_sections = set((await conn.execute(text(
            "SELECT ts.section_id FROM g2p_intake_form_ui_tab_sections ts JOIN g2p_intake_form_ui_tabs t "
            "ON t.tab_id = ts.tab_id JOIN g2p_intake_form_definitions f ON f.form_id = t.form_id "
            "WHERE f.register_id = :r"), {"r": AGENT})).scalars())
        attributes = set((await conn.execute(text("SELECT attribute_id FROM g2p_attributes"))).scalars())

    by_id = {s.section_id: s for s in sections}
    assert tab_sections == set(by_id)  # every section is shown, and every tab section exists
    assert intake_sections <= set(by_id) and "agent_header_section" not in intake_sections

    bound = {}
    for section in sections:
        columns = set(MODELS[section.section_register_id].__table__.columns.keys())
        for widget in _widgets(section.section_ui_schema):
            source = widget.get("widget-data-source") or {}
            if source.get("service") == "attributes":
                assert source["params"]["attribute_id"] in attributes, (section.section_id, widget)
            if "column-key" in widget:  # a list section's column: a field of the row's register
                assert section.is_list and widget["column-key"] in columns, widget
                bound[(section.section_register_id, widget["column-key"])] = widget
                continue
            paths = widget.get("widget-data-path")
            if widget.get("widget") in ("header-section", "table"):
                continue
            for path in paths.values() if isinstance(paths, dict) else [paths]:
                register_id, field = path.split(".", 1)
                assert register_id == section.section_register_id, path
                if field.startswith("documents."):
                    continue
                assert field in columns, path
                bound[(register_id, field)] = widget

    agent_fields = {field for register, field in bound if register == AGENT}
    assert {"functional_record_id", "first_name", "last_name", "gender", "birth_date", "foundational_id",
            "mobile_number", "position", "employer_type", "geo_lowest_level_value_id", "service_point_name",
            "assigned_since", "service_status", "service_status_date"} <= agent_fields
    assert bound[(AGENT, "geo_lowest_level_value_id")]["widget"] == "geo-hierarchy"
    # Staff never type the Agent ID: it is generated, and shown read-only.
    assert bound[(AGENT, "functional_record_id")]["widget-readonly"]
    assert {(SPECIALIZATION, "specialization"), (QUALIFICATION, "qualification_level")} <= set(bound)


async def test_change_requests_and_intake_go_to_awe(database):
    async with database.connect() as conn:
        policies = dict((await conn.execute(text(
            "SELECT policy_scope, policy_key FROM g2p_registry_awe_policy_configurations "
            "WHERE register_id = :r"), {"r": AGENT})).all())
    assert policies == {"REGISTER": "registry.change_request.agent", "INTAKE_FORM": "registry.intake_form.agent"}


async def test_agent_round_trips_with_its_rows(database):
    sessions = async_sessionmaker(database, expire_on_commit=False)
    stamp = dict(created_by="test", created_at=datetime(2026, 11, 23), last_approved_at=datetime(2026, 11, 23),
                 last_approved_by="test")
    async with sessions() as session:
        agent = G2PRegisterAgent(
            functional_record_id="99000001", first_name="Abeba", middle_name="Kebede", last_name="Tola",
            gender="FEMALE", birth_date=date(1990, 3, 4), foundational_id="712345678901",
            mobile_number="+251911000001", position="AGPOS_FIELD_AGENT", employer_type="AGEMPR_GOVERNMENT",
            employment_type="AGEMP_PERMANENT", date_of_hire=date(2014, 9, 11),
            geo_lowest_level_value_id="ET040611", service_point_name="Sheno FTC",
            service_point_type="AGSP_TRAINING_CENTRE", assigned_since=date(2014, 9, 11),
            assignment_reason="AGRSN_FIRST_POSTING", service_status="AGST_ACTIVE", **stamp)
        session.add(agent)
        await session.flush()
        session.add(G2PRegisterAgentSpecialization(link_internal_record_id=agent.internal_record_id,
                                                   specialization="AGSPEC_CROP", is_primary=True, **stamp))
        session.add(G2PRegisterAgentQualification(link_internal_record_id=agent.internal_record_id,
                                                  qualification_level="AGQUAL_DIPLOMA", year_completed=2013,
                                                  **stamp))
        await session.commit()
    try:
        async with sessions() as session:
            stored = (await session.execute(select(G2PRegisterAgent).where(
                G2PRegisterAgent.functional_record_id == "99000001"))).scalar_one()
            assert stored.record_name == "Abeba Kebede Tola"
            assert "712345678901" in stored.search_text and "Sheno FTC" in stored.search_text
            rows = (await session.execute(select(G2PRegisterAgentSpecialization).where(
                G2PRegisterAgentSpecialization.link_internal_record_id == stored.internal_record_id))).scalars().all()
            assert [(r.specialization, r.is_primary) for r in rows] == [("AGSPEC_CROP", True)]
        async with database.connect() as conn:
            view = (await conn.execute(text(
                "SELECT agent_name, area_code, primary_specialization, qualification_count, training_count "
                "FROM agents_rpt_agent WHERE agent_id = '99000001'"))).one()
            assert tuple(view) == ("Abeba Kebede Tola", "ET040611", "AGSPEC_CROP", 1, 0)
            # The credential view (VC issuance): identity and role claims, keyed on the record.
            card = (await conn.execute(text(
                'SELECT internal_record_id, foundational_id, "functionalRecordId", "fullName", "dateOfBirth", '
                '"position", "servicePoint" FROM agent_vc_view WHERE "functionalRecordId" = \'99000001\''))).one()
            assert card.internal_record_id == stored.internal_record_id and card.foundational_id == "712345678901"
            assert (card.fullName, card.dateOfBirth, card.position, card.servicePoint) == (
                "Abeba Kebede Tola", "1990-03-04", "AGPOS_FIELD_AGENT", "Sheno FTC")
            # An agent out of service gets no card.
            await conn.execute(text("UPDATE g2p_register_agents SET service_status = 'AGST_RETIRED' "
                                    "WHERE functional_record_id = '99000001'"))
            assert (await conn.execute(text(
                'SELECT count(*) FROM agent_vc_view WHERE "functionalRecordId" = \'99000001\''))).scalar() == 0
    finally:
        async with database.begin() as conn:
            for table in ("g2p_register_agent_specializations", "g2p_register_agent_qualifications"):
                await conn.execute(text(f"DELETE FROM {table} WHERE created_by = 'test'"))
            await conn.execute(text("DELETE FROM g2p_register_agents WHERE functional_record_id = '99000001'"))


async def _refused(service, records):
    with pytest.raises(G2PRegistryException) as info:
        await service.validate_domain_attributes(records)
    return info.value.message


async def test_agent_checks():
    service = G2PRegisterDomainServiceAgent()
    good = {"birth_date": "1990-01-01", "date_of_hire": "2014-09-11", "assigned_since": "2016-09-11",
            "service_status": "AGST_ACTIVE", "email": "a.b@example.org", "mobile_number": "+251 911 000 001"}
    await service.validate_domain_attributes([good])
    assert "after birth_date" in await _refused(service, [{**good, "date_of_hire": "1989-01-01"}])
    assert "assigned_since" in await _refused(service, [{**good, "assigned_since": "2010-01-01"}])
    assert "service_status_date is required" in await _refused(service, [{**good, "service_status": "AGST_RETIRED"}])
    await service.validate_domain_attributes([{**good, "service_status": "AGST_RETIRED",
                                               "service_status_date": "2026-01-31"}])
    assert "email" in await _refused(service, [{**good, "email": "not-an-email"}])
    assert "mobile_number" in await _refused(service, [{**good, "mobile_number": "call me"}])


async def test_section_checks():
    specializations = G2PRegisterDomainServiceAgentSpecialization()
    await specializations.validate_domain_attributes([
        {"specialization": "AGSPEC_CROP", "is_primary": True}, {"specialization": "AGSPEC_LIVESTOCK"}])
    assert "only once" in await _refused(specializations, [
        {"specialization": "AGSPEC_CROP"}, {"specialization": "AGSPEC_CROP"}])
    assert "primary" in await _refused(specializations, [
        {"specialization": "AGSPEC_CROP", "is_primary": True},
        {"specialization": "AGSPEC_LIVESTOCK", "is_primary": True}])
    qualifications = G2PRegisterDomainServiceAgentQualification()
    await qualifications.validate_domain_attributes([{"qualification_level": "AGQUAL_DIPLOMA", "year_completed": 2013}])
    assert "past year" in await _refused(qualifications, [{"year_completed": date.today().year + 1}])


async def test_reseed_keeps_registrant_authentication(database):
    """VC issuance's bootstrap turns on requires_registrant_authentication; an upgrade's re-seed keeps it."""
    from pathlib import Path

    seed = (Path(__file__).resolve().parents[2] / "agents-extension/src/openg2p_registry_agents_extension"
            / "meta_data/register-metadata/10_register_definitions.sql").read_text()
    async with database.begin() as conn:
        await conn.execute(text("UPDATE g2p_register_definitions SET requires_registrant_authentication = TRUE "
                                "WHERE register_id = :r"), {"r": AGENT})
        raw = (await conn.get_raw_connection()).driver_connection
        await raw.execute(seed)
        kept = (await conn.execute(text("SELECT requires_registrant_authentication FROM g2p_register_definitions "
                                        "WHERE register_id = :r"), {"r": AGENT})).scalar()
        await conn.execute(text("UPDATE g2p_register_definitions SET requires_registrant_authentication = FALSE "
                                "WHERE register_id = :r"), {"r": AGENT})
    assert kept is True
