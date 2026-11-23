from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PGeoHistorySchema,
    G2PGeoSchema,
    G2PIntakeFormSchemaBase,
    G2PPersonHistorySchema,
    G2PPersonSchema,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)


class G2PSchemaAgent:
    employee_number: Optional[str] = None
    languages_spoken: Optional[str] = None
    mobile_number: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    employer_type: Optional[str] = None
    employer_name: Optional[str] = None
    employment_type: Optional[str] = None
    date_of_hire: Optional[date] = None
    service_point_name: Optional[str] = None
    service_point_type: Optional[str] = None
    assigned_since: Optional[date] = None
    assignment_reason: Optional[str] = None
    service_status: Optional[str] = None
    service_status_date: Optional[date] = None
    service_status_reason: Optional[str] = None


class G2PRegisterSchemaAgent(G2PRegisterBaseSchema, G2PPersonSchema, G2PGeoSchema, G2PSchemaAgent):
    """The Agent register: person and location (the assigned area) fields, plus the agent's own."""


class G2PRegisterHistorySchemaAgent(G2PRegisterHistorySchema, G2PPersonHistorySchema, G2PGeoHistorySchema):
    """Agent history."""


class G2PIntakeFormSchemaAgent(G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PPersonSchema, G2PGeoSchema,
                               G2PSchemaAgent):
    """The intake form that registers a new agent."""
