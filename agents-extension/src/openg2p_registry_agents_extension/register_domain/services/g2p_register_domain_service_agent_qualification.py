import logging
from datetime import date

from openg2p_registry_core.services import G2PRegisterDomainService

from ._validation import as_int, invalid, joined

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceAgentQualification(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            year = as_int(record, "year_completed")
            if year is not None and not 1950 <= year <= date.today().year:
                invalid("year_completed must be a past year")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        return joined(payload, ["qualification_level", "field_of_study", "institution"], extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        return joined(payload, ["qualification_level", "field_of_study"], extra)
