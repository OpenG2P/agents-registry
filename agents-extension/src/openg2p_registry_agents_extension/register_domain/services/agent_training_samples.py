"""Sample trainings for a demo install, built from the sample agents in the Agent register.

db-seed loads the sample agents (the country pack's ``samples/agents.json``) as
approved Agent records before this runs. Every sample agent gets a course in
the topic of their primary specialization; every second one also an online
course on digital tools; every third one a certification. One training is
corrected (its hours re-entered), so a correction shows. Dates are fixed and
every sample carries an idempotency key, so a reinstall records nothing twice.

The codes used are the AGENT_* lists' codes, which every country pack keeps
(a country changes the labels, not these codes).
"""

from datetime import date, datetime, timedelta
from typing import Optional

from openg2p_registry_core.schemas.activity import ActivityInput
from openg2p_registry_core.services import SampleStep

REGISTER = "AgentTraining"

# Primary specialization -> (topic, course title, hours)
COURSES = {
    "AGSPEC_CROP": ("AGTOP_CROP_PRODUCTION", "Improved crop production practices", 32),
    "AGSPEC_LIVESTOCK": ("AGTOP_LIVESTOCK", "Livestock feeding and management", 32),
    "AGSPEC_ANIMAL_HEALTH": ("AGTOP_ANIMAL_HEALTH", "Animal health and disease surveillance", 40),
    "AGSPEC_NATURAL_RESOURCES": ("AGTOP_NATURAL_RESOURCES", "Soil and water conservation", 24),
    "AGSPEC_IRRIGATION": ("AGTOP_IRRIGATION", "Small-scale irrigation scheduling", 24),
    "AGSPEC_HORTICULTURE": ("AGTOP_CROP_PRODUCTION", "Fruit and vegetable production", 24),
    "AGSPEC_COOPERATIVES": ("AGTOP_EXTENSION_METHODS", "Cooperative organisation and marketing", 16),
    "AGSPEC_AGRIBUSINESS": ("AGTOP_POST_HARVEST", "Post-harvest handling and market linkage", 16),
    "AGSPEC_HOME_ECONOMICS": ("AGTOP_NUTRITION", "Household nutrition and food safety", 16),
}
DEFAULT_COURSE = ("AGTOP_EXTENSION_METHODS", "Participatory extension methods", 24)

FIRST_COURSE_END = date(2025, 10, 24)
DIGITAL_COURSE_END = date(2026, 3, 13)
CERTIFIED_ON = date(2026, 4, 30)


def _at(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, 9, 0, 0)


def build_steps(agents: list[tuple[str, Optional[str], Optional[str]]]) -> list[SampleStep]:
    """Sample steps for ``agents``: (Agent ID, primary specialization, assigned area), ordered by Agent ID."""
    steps: list[SampleStep] = []
    corrected = False
    for seq, (agent_id, specialization, area) in enumerate(sorted(agents), start=1):
        topic, title, hours = COURSES.get(specialization or "", DEFAULT_COURSE)
        where = {"geo_lowest_level_value_id": area} if area else {}

        def add(kind: str, day: date, number: int, **payload) -> SampleStep:
            step = SampleStep(ActivityInput(
                register_mnemonic=REGISTER, activity_type=kind, occurred_at=_at(day),
                idempotency_key=f"sample:{agent_id}:{number}", payload={"agent_id": agent_id, **payload},
            ))
            steps.append(step)
            return step

        first = add("TRAINING_COMPLETED", FIRST_COURSE_END, 1, topic=topic, course_title=title,
                    course_code=f"{topic.removeprefix('AGTOP_')}-101", provider="Regional agricultural training centre",
                    start_date=(FIRST_COURSE_END - timedelta(days=4)).isoformat(),
                    end_date=FIRST_COURSE_END.isoformat(), hours=hours, delivery_mode="AGTDM_IN_PERSON",
                    result="AGTRS_PASSED", score=60 + (seq * 7) % 40, **where)
        if not corrected:
            first.correction = {"reason": "Sample: hours re-entered from the attendance sheet",
                                "payload": {"hours": hours + 8}}
            corrected = True
        if seq % 2 == 0:
            add("TRAINING_COMPLETED", DIGITAL_COURSE_END, 2, topic="AGTOP_DIGITAL_TOOLS",
                course_title="Digital tools for extension work", course_code="DIGITAL-201",
                provider="Online learning platform", start_date=(DIGITAL_COURSE_END - timedelta(days=11)).isoformat(),
                end_date=DIGITAL_COURSE_END.isoformat(), hours=8, delivery_mode="AGTDM_ONLINE",
                result="AGTRS_COMPLETED")
        if seq % 3 == 0:
            add("CERTIFICATION_AWARDED", CERTIFIED_ON, 3, certification="Certified extension practitioner",
                topic=topic, issuing_body="Agricultural training authority",
                certificate_number=f"CEP-{CERTIFIED_ON.year}-{seq:04d}",
                valid_until=CERTIFIED_ON.replace(year=CERTIFIED_ON.year + 3).isoformat())
    return steps
