import logging
from datetime import date

from openg2p_registry_core.services import G2PRegisterDomainService

from ._validation import EMAIL, PHONE, as_date, invalid, joined

_logger = logging.getLogger("g2p-register-domain-service")

# The one service status that needs no date: a country's list may add others.
ACTIVE = "AGST_ACTIVE"


class G2PRegisterDomainServiceAgent(G2PRegisterDomainService):
    """Checks that hold in every country: dates in order, contact details well formed."""

    async def validate_domain_attributes(self, records: list[dict]):
        today = date.today()
        for record in records:
            birth = as_date(record, "birth_date")
            hired = as_date(record, "date_of_hire")
            assigned = as_date(record, "assigned_since")
            status_date = as_date(record, "service_status_date")
            if birth and birth >= today:
                invalid("birth_date must be in the past")
            if birth and hired and hired <= birth:
                invalid("date_of_hire must be after birth_date")
            if hired and hired > today:
                invalid("date_of_hire must not be in the future")
            if hired and assigned and assigned < hired:
                invalid("assigned_since must not be before date_of_hire")
            if hired and status_date and status_date < hired:
                invalid("service_status_date must not be before date_of_hire")
            status = record.get("service_status")
            if status and status != ACTIVE and not status_date:
                invalid("service_status_date is required when the status is not active")
            email = str(record.get("email") or "").strip()
            if email and not EMAIL.match(email):
                invalid("email is not an email address")
            for key in ("mobile_number", "alternate_phone"):
                phone = str(record.get(key) or "").strip()
                if phone and not PHONE.match(phone):
                    invalid(f"{key} is not a phone number")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        # The Agent ID (functional_record_id) is added by G2PRegister.
        return joined(payload, ["first_name", "middle_name", "last_name", "foundational_id", "employee_number",
                                "mobile_number", "email", "position", "service_point_name",
                                "geo_lowest_level_value_id"], extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        return joined(payload, ["first_name", "middle_name", "last_name"], extra)
