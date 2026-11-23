# Schemas for the record (entity) registers. The AgentTraining activity register
# has none: activity payloads are validated by each activity type's JSON Schema
# (meta_data/activity-metadata/10_g2p_activity_types.sql).
from .agent import G2PIntakeFormSchemaAgent, G2PRegisterHistorySchemaAgent, G2PRegisterSchemaAgent
from .agent_qualification import (
    G2PIntakeFormSchemaAgentQualification,
    G2PRegisterHistorySchemaAgentQualification,
    G2PRegisterSchemaAgentQualification,
)
from .agent_specialization import (
    G2PIntakeFormSchemaAgentSpecialization,
    G2PRegisterHistorySchemaAgentSpecialization,
    G2PRegisterSchemaAgentSpecialization,
)

__all__ = [
    "G2PIntakeFormSchemaAgent",
    "G2PIntakeFormSchemaAgentQualification",
    "G2PIntakeFormSchemaAgentSpecialization",
    "G2PRegisterHistorySchemaAgent",
    "G2PRegisterHistorySchemaAgentQualification",
    "G2PRegisterHistorySchemaAgentSpecialization",
    "G2PRegisterSchemaAgent",
    "G2PRegisterSchemaAgentQualification",
    "G2PRegisterSchemaAgentSpecialization",
]
