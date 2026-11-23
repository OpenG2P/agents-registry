from openg2p_fastapi_common.service import BaseService
from openg2p_registry_core.interfaces import G2PIdGeneratorInterface, IdAffix
from openg2p_registry_core.models.g2p_register import G2PRegister


class G2PIdGeneratorService(BaseService, G2PIdGeneratorInterface):
    """Prefixes for generated functional IDs. Only the Agent register mints IDs:
    pool ``agent`` in the ID generator (the register mnemonic in lowercase), eight
    digits and no prefix, so an Agent ID reads e.g. ``48207193``. The list
    sections and the AgentTraining activity register need none.

    A country that wants a prefix sets it here; the length is the chart's
    ``registry.idgenerator.idGenerator.appConfig.idTypes.agent.idLength``.
    """

    def generate_prefix_suffix(self, g2p_register: G2PRegister, register_mnemonic: str) -> IdAffix:
        mnemonic = (register_mnemonic or "").lower()

        if mnemonic == "agent":
            return IdAffix(prefix="", suffix="")

        return IdAffix(prefix="DEFAULT-", suffix="")
