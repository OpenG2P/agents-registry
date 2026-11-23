"""The AgentTraining activity register and its current state per agent.

One context per agent (the context key is the Agent ID); the agent is the
activity's subject, a record of this registry's Agent register. Each training
completed and each certification awarded is an append-only activity in that
context. The columns below are promoted from the payload so they can be
filtered, indexed and used by indicators; everything else stays in the JSONB
``payload``, validated by the activity type's JSON Schema.
"""

from datetime import date

from openg2p_registry_core.models import G2PActivity, G2PActivityProjection, G2PGeo
from sqlalchemy import Boolean, Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class G2PActivityAgentTraining(G2PActivity, G2PGeo):
    __tablename__ = "g2p_activity_agent_training"
    __table_args__ = {"extend_existing": True}

    agent_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String, nullable=True, index=True)  # AGENT_TRAINING_TOPIC
    course_code: Mapped[str] = mapped_column(String, nullable=True, index=True)
    hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    result: Mapped[str] = mapped_column(String, nullable=True)  # AGENT_TRAINING_RESULT
    certificate_number: Mapped[str] = mapped_column(String, nullable=True, index=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=True)

    def get_search_text_fields(self) -> list[str]:
        return [self.agent_id or "", self.topic or "", self.course_code or "", self.certificate_number or ""]


class G2PActivityProjectionAgentTraining(G2PActivityProjection):
    """An agent's trainings, summarised: counts, hours, the last training and the latest certification."""

    __tablename__ = "g2p_activity_projection_agent_training"
    __table_args__ = {"extend_existing": True}

    agent_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    training_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    training_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    last_training_on: Mapped[date] = mapped_column(Date, nullable=True)
    last_training_topic: Mapped[str] = mapped_column(String, nullable=True, index=True)
    last_training_title: Mapped[str] = mapped_column(String, nullable=True)
    certification_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latest_certification: Mapped[str] = mapped_column(String, nullable=True)
    latest_certification_on: Mapped[date] = mapped_column(Date, nullable=True)
    latest_certification_valid_until: Mapped[date] = mapped_column(Date, nullable=True)
