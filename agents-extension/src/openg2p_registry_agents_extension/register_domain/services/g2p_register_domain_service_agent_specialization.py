import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from ._validation import as_date, invalid, joined

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceAgentSpecialization(G2PRegisterDomainService):
    async def validate_domain_attributes(self, records: list[dict]):
        seen: set[str] = set()
        primaries = 0
        for record in records:
            value = str(record.get("specialization") or "").strip()
            if not value:
                continue
            if value in seen:
                invalid("Each specialization may appear only once")
            seen.add(value)
            if record.get("is_primary") in (True, "true", "TRUE", "True"):
                primaries += 1
            as_date(record, "since")
        if primaries > 1:
            invalid("Only one specialization may be primary")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        return joined(payload, ["specialization"], extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        return joined(payload, ["specialization"], extra)
