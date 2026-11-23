"""An agent's qualifications: a list section, one row per qualification, under the agent."""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceAgentQualification


class G2PAgentQualification:
    qualification_level: Mapped[str] = mapped_column(String, nullable=True, index=True)  # AGENT_QUALIFICATION_LEVEL
    field_of_study: Mapped[str] = mapped_column(String, nullable=True)  # AGENT_FIELD_OF_STUDY
    institution: Mapped[str] = mapped_column(String, nullable=True)
    year_completed: Mapped[int] = mapped_column(Integer, nullable=True)


class G2PRegisterAgentQualification(G2PRegister, G2PAgentQualification):
    __tablename__ = "g2p_register_agent_qualifications"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAgentQualification().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAgentQualification().construct_record_name(self.to_dict())


class G2PRegisterHistoryAgentQualification(G2PRegisterHistory, G2PAgentQualification):
    __tablename__ = "g2p_register_history_agent_qualifications"


class G2PIntakeFormAgentQualification(G2PIntakeForm, G2PRegister, G2PAgentQualification):
    __tablename__ = "g2p_intake_form_agent_qualifications"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAgentQualification().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAgentQualification().construct_record_name(self.to_dict())
