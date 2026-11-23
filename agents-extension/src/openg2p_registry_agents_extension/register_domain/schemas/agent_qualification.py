from typing import Optional

from openg2p_registry_core.schemas import G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PRegisterHistorySchema


class G2PSchemaAgentQualification:
    qualification_level: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    year_completed: Optional[int] = None


class G2PRegisterSchemaAgentQualification(G2PRegisterBaseSchema, G2PSchemaAgentQualification):
    """An agent's qualification (a row of the Qualifications section)."""


class G2PRegisterHistorySchemaAgentQualification(G2PRegisterHistorySchema):
    """Qualification history."""


class G2PIntakeFormSchemaAgentQualification(G2PIntakeFormSchemaBase, G2PRegisterBaseSchema,
                                            G2PSchemaAgentQualification):
    """A qualification row on the agent intake form."""
