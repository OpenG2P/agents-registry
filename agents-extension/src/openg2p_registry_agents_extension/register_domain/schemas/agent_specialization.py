from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PRegisterHistorySchema


class G2PSchemaAgentSpecialization:
    specialization: Optional[str] = None
    is_primary: Optional[bool] = None
    since: Optional[date] = None


class G2PRegisterSchemaAgentSpecialization(G2PRegisterBaseSchema, G2PSchemaAgentSpecialization):
    """An agent's specialization (a row of the Specializations section)."""


class G2PRegisterHistorySchemaAgentSpecialization(G2PRegisterHistorySchema):
    """Specialization history."""


class G2PIntakeFormSchemaAgentSpecialization(G2PIntakeFormSchemaBase, G2PRegisterBaseSchema,
                                             G2PSchemaAgentSpecialization):
    """A specialization row on the agent intake form."""
