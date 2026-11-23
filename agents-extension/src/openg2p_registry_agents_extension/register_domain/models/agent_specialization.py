"""An agent's specializations: a list section, one row per specialization, under the agent."""

from datetime import date

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceAgentSpecialization


class G2PAgentSpecialization:
    specialization: Mapped[str] = mapped_column(String, nullable=True, index=True)  # AGENT_SPECIALIZATION
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=True)
    since: Mapped[date] = mapped_column(Date, nullable=True)


class G2PRegisterAgentSpecialization(G2PRegister, G2PAgentSpecialization):
    __tablename__ = "g2p_register_agent_specializations"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAgentSpecialization().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAgentSpecialization().construct_record_name(self.to_dict())


class G2PRegisterHistoryAgentSpecialization(G2PRegisterHistory, G2PAgentSpecialization):
    __tablename__ = "g2p_register_history_agent_specializations"


class G2PIntakeFormAgentSpecialization(G2PIntakeForm, G2PRegister, G2PAgentSpecialization):
    __tablename__ = "g2p_intake_form_agent_specializations"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAgentSpecialization().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAgentSpecialization().construct_record_name(self.to_dict())
