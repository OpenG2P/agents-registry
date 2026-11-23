"""AgentTraining domain rules: the per-agent context, the projection (the agent's
training summary) and sample trainings.

Declarations (context fields, subject, UI hints, search fields) and the
plausibility rules are configuration: meta_data/activity-config/AgentTraining.json.
"""

import logging
from decimal import Decimal
from typing import Any

from openg2p_fastapi_common.context import dbengine
from openg2p_registry_core.errors import G2PRegistryErrorCodes, G2PRegistryException
from openg2p_registry_core.services import G2PActivityDomainService, SampleStep
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from . import agent_training_samples

_logger = logging.getLogger("agent-training-domain-service")


def _date(value):
    if value in (None, ""):
        return None
    from datetime import date

    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class G2PActivityDomainServiceAgentTraining(G2PActivityDomainService):

    # --------------------------------------------------------------- context

    def build_context(self, activity_type, subject_type, subject_id, payload):
        agent_id = str(payload.get("agent_id") or "").strip()
        if not agent_id:
            return None
        return {
            "context_key": agent_id,
            "context_type": "AGENT",
            "subject_type": subject_type or self.subject_type or "AGENT_ID",
            "subject_id": subject_id or agent_id,
            "attributes": {"agent_id": agent_id},
        }

    # ------------------------------------------------- derived values, checks

    def enrich_payload(self, activity_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """A course's length in days, from its start and end dates."""
        if activity_type == "TRAINING_COMPLETED":
            start, end = _date(payload.get("start_date")), _date(payload.get("end_date"))
            if start and end and end >= start:
                payload = {**payload, "course_days": (end - start).days + 1}
        return payload

    def validate(self, activity_type: str, payload: dict[str, Any], context_activities: list) -> list[str]:
        """The configured rules, then date checks the rule language cannot express."""
        warnings = list(super().validate(activity_type, payload, context_activities) or [])
        if activity_type == "TRAINING_COMPLETED":
            start, end = _date(payload.get("start_date")), _date(payload.get("end_date"))
            if start and end and end < start:
                raise G2PRegistryException(
                    code=G2PRegistryErrorCodes.ACTIVITY_PAYLOAD_INVALID.value[1],
                    message=f"The course ends ({end}) before it starts ({start})",
                )
            days, hours = payload.get("course_days"), payload.get("hours")
            if days and hours is not None and float(hours) > 12 * int(days):
                warnings.append(f"{hours} hours in {days} days is more than 12 hours a day")
        return warnings

    # ------------------------------------------------------------ projection

    def project(self, context, activities: list) -> dict[str, Any]:
        row: dict[str, Any] = {
            "agent_id": (context.attributes or {}).get("agent_id") or context.subject_id,
            "training_count": 0,
            "training_hours": Decimal("0"),
            "certification_count": 0,
            "is_certified": False,
        }
        for activity in activities:  # oldest first; later activities win
            payload = activity.payload or {}
            day = activity.occurred_at.date() if activity.occurred_at else None
            if activity.activity_type == "TRAINING_COMPLETED":
                row["training_count"] += 1
                row["training_hours"] += Decimal(str(payload.get("hours") or 0))
                if day and (row.get("last_training_on") is None or day >= row["last_training_on"]):
                    row["last_training_on"] = day
                    row["last_training_topic"] = payload.get("topic")
                    row["last_training_title"] = payload.get("course_title")
            elif activity.activity_type == "CERTIFICATION_AWARDED":
                row["certification_count"] += 1
                row["is_certified"] = True
                if day and (row.get("latest_certification_on") is None or day >= row["latest_certification_on"]):
                    row["latest_certification_on"] = day
                    row["latest_certification"] = payload.get("certification")
                    row["latest_certification_valid_until"] = _date(payload.get("valid_until"))
        return row

    # ---------------------------------------------------------- sample data

    async def sample_activities(self, register) -> list[SampleStep]:
        """Sample trainings for the sample agents db-seed loaded (see ``agent_training_samples``).

        Asked for only when sample trainings are switched on, so no sample
        agents is an error, not "nothing to load": the install-time samples Job
        then fails with the reason.
        """
        try:
            async with async_sessionmaker(dbengine.get())() as session:
                rows = (await session.execute(text(
                    "SELECT a.functional_record_id, s.specialization, a.geo_lowest_level_value_id "
                    "FROM g2p_register_agents a "
                    "LEFT JOIN g2p_register_agent_specializations s "
                    "  ON s.link_internal_record_id = a.internal_record_id AND s.is_primary IS TRUE "
                    "WHERE a.created_by = 'seeder' AND a.record_status = 'ACTIVE' "
                    "AND a.functional_record_id IS NOT NULL ORDER BY a.functional_record_id"
                ))).all()
        except Exception as error:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.UNEXPECTED_ERROR.value[1],
                message=f"Could not read the Agent register: {type(error).__name__}",
            ) from error
        agents = {}
        for agent_id, specialization, area in rows:
            agents.setdefault(agent_id, (agent_id, specialization, area))
        if not agents:
            raise G2PRegistryException(
                code=G2PRegistryErrorCodes.INVALID_REQUEST.value[1],
                message="No sample agents in the Agent register: turn on Load Sample Data (registry.dbSeed.loadSampleData)",
            )
        return agent_training_samples.build_steps(list(agents.values()))
