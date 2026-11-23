"""AgentTraining: trainings and certifications against an agent of the Agent register."""

from datetime import date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_registry_core.errors import G2PRegistryException
from openg2p_registry_core.schemas.activity import ActivityInput
from openg2p_registry_agents_extension.register_domain.models import G2PRegisterAgent

pytestmark = pytest.mark.asyncio(loop_scope="session")

REG = "AgentTraining"
AGENT_ID = "99000100"


@pytest_asyncio.fixture(loop_scope="session")
async def agent(database):
    sessions = async_sessionmaker(database, expire_on_commit=False)
    async with sessions() as session:
        session.add(G2PRegisterAgent(
            functional_record_id=AGENT_ID, first_name="Hana", last_name="Desta", gender="FEMALE",
            geo_lowest_level_value_id="ET010101", position="AGPOS_FIELD_AGENT", service_status="AGST_ACTIVE",
            created_by="test", created_at=datetime(2026, 11, 23), last_approved_at=datetime(2026, 11, 23),
            last_approved_by="test"))
        await session.commit()
    yield AGENT_ID
    async with database.begin() as conn:
        await conn.execute(text("DELETE FROM g2p_register_agents WHERE functional_record_id = :id"), {"id": AGENT_ID})


def training(days_ago, agent_id=AGENT_ID, kind="TRAINING_COMPLETED", **payload):
    return ActivityInput(register_mnemonic=REG, activity_type=kind,
                         occurred_at=datetime.utcnow().replace(microsecond=0) - timedelta(days=days_ago),
                         payload={"agent_id": agent_id, **payload})


COURSE = {"topic": "AGTOP_SOIL_FERTILITY", "course_title": "Integrated soil fertility management",
          "course_code": "SOIL-101", "provider": "Regional training centre", "delivery_mode": "AGTDM_IN_PERSON",
          "result": "AGTRS_PASSED", "score": 82}


async def _code(awaitable):
    with pytest.raises(G2PRegistryException) as info:
        await awaitable
    return info.value.code


async def test_trainings_summarise_on_the_agent(service, clean, agent, database):
    end = date.today() - timedelta(days=30)
    first, _ = await service.append(training(30, **COURSE, start_date=(end - timedelta(days=4)).isoformat(),
                                             end_date=end.isoformat(), hours=32,
                                             geo_lowest_level_value_id="ET010101"), "trainer-1", "STAFF_PORTAL")
    # The agent is the subject: the platform links the Agent record, so the training shows on its profile.
    assert first.subject_type == "LOCAL_RECORD" and first.subject_id == AGENT_ID
    async with database.connect() as conn:
        record = (await conn.execute(text("SELECT internal_record_id FROM g2p_register_agents "
                                          "WHERE functional_record_id = :id"), {"id": AGENT_ID})).scalar()
    assert first.subject_internal_record_id == record and first.subject_register_mnemonic == "Agent"
    assert first.payload["course_days"] == 5 and not first.rule_warnings
    assert first.display["topic"] == "Soil fertility"

    await service.append(training(10, topic="AGTOP_DIGITAL_TOOLS", course_title="Digital tools for extension",
                                  hours=8, delivery_mode="AGTDM_ONLINE", result="AGTRS_COMPLETED"),
                         "lms", "PARTNER")
    valid_until = (date.today() + timedelta(days=3 * 365)).isoformat()
    await service.append(training(5, kind="CERTIFICATION_AWARDED", certification="Certified extension practitioner",
                                  issuing_body="Training authority", certificate_number="CEP-2026-0001",
                                  valid_until=valid_until), "trainer-1", "STAFF_PORTAL")

    async with database.connect() as conn:
        row = (await conn.execute(text(
            "SELECT * FROM g2p_activity_projection_agent_training WHERE agent_id = :id"), {"id": AGENT_ID})
        ).mappings().one()
        participants = (await conn.execute(text(
            "SELECT DISTINCT role, ref_id FROM g2p_activity_participants"))).all()
        view = (await conn.execute(text(
            "SELECT training_count, certification_count FROM agents_rpt_agent WHERE agent_id = :id"),
            {"id": AGENT_ID})).one()
    assert row["context_key"] == AGENT_ID and row["activity_count"] == 3
    assert row["training_count"] == 2 and float(row["training_hours"]) == 40
    assert row["last_training_topic"] == "AGTOP_DIGITAL_TOOLS"
    assert row["is_certified"] and row["latest_certification"] == "Certified extension practitioner"
    assert row["latest_certification_valid_until"].isoformat() == valid_until
    assert participants == [("agent", AGENT_ID)]
    assert tuple(view) == (2, 1)


async def test_a_training_needs_a_registered_agent(service, clean, agent):
    assert await _code(service.append(training(3, agent_id="99999999", **COURSE), "lms", "PARTNER")) == "ACT-ERR-005"


async def test_coded_fields_are_checked(service, clean, agent):
    # The delivery mode and result are strict; a topic a learning platform sends that the list lacks only warns.
    assert await _code(service.append(training(3, **{**COURSE, "delivery_mode": "BY_PIGEON"}), "lms", "PARTNER")
                       ) == "ACT-ERR-005"
    unknown_topic, _ = await service.append(training(3, **{**COURSE, "topic": "LMS_TOPIC_42"}), "lms", "PARTNER")
    assert unknown_topic.reference_checks and unknown_topic.status == "ACTIVE"


async def test_course_dates_and_hours(service, clean, agent):
    end = date.today() - timedelta(days=2)
    assert await _code(service.append(training(2, **COURSE, start_date=end.isoformat(),
                                               end_date=(end - timedelta(days=3)).isoformat()), "t", "STAFF_PORTAL")
                       ) == "ACT-ERR-004"
    long_days, _ = await service.append(training(2, **COURSE, start_date=end.isoformat(), end_date=end.isoformat(),
                                                 hours=20), "t", "STAFF_PORTAL")
    assert any("more than 12 hours a day" in w for w in long_days.rule_warnings)
    no_score = {k: v for k, v in COURSE.items() if k != "score"}
    failed, _ = await service.append(training(1, **{**no_score, "result": "AGTRS_FAILED"}), "t", "STAFF_PORTAL")
    assert "no score was recorded" in " ".join(failed.rule_warnings)


async def test_a_correction_replaces_the_training(service, clean, agent, database):
    first, _ = await service.append(training(20, **COURSE, hours=24), "t", "STAFF_PORTAL")
    fixed = await service.supersede(REG, first.activity_id, "hours re-entered", "t", "STAFF_PORTAL",
                                    payload={**first.payload, "hours": 30})
    assert fixed.payload["hours"] == 30
    async with database.connect() as conn:
        row = (await conn.execute(text(
            "SELECT training_count, training_hours FROM g2p_activity_projection_agent_training "
            "WHERE agent_id = :id"), {"id": AGENT_ID})).one()
    assert row.training_count == 1 and float(row.training_hours) == 30
