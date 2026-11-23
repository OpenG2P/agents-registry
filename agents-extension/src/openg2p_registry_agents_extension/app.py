# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.context import dbengine
from openg2p_registry_core.app import Initializer as CoreInitializer
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from .register_domain.factory import G2PIdGeneratorFactory, G2PRegisterDomainFactory
from .register_domain.models import (
    G2PIntakeFormAgent,
    G2PIntakeFormAgentQualification,
    G2PIntakeFormAgentSpecialization,
    G2PRegisterAgent,
    G2PRegisterAgentQualification,
    G2PRegisterAgentSpecialization,
    G2PRegisterHistoryAgent,
    G2PRegisterHistoryAgentQualification,
    G2PRegisterHistoryAgentSpecialization,
)
from .register_domain.services import (
    G2PActivityDomainServiceAgentTraining,
    G2PRegisterDomainServiceAgent,
    G2PRegisterDomainServiceAgentQualification,
    G2PRegisterDomainServiceAgentSpecialization,
)

_logger = logging.getLogger(_config.logging_default_logger_name)

# The record registers' tables: the Agent register and its two list sections,
# each with its history and intake-form table. The platform's core migration
# creates the AgentTraining activity and projection tables itself.
RECORD_MODELS = (
    G2PRegisterAgent, G2PRegisterHistoryAgent, G2PIntakeFormAgent,
    G2PRegisterAgentSpecialization, G2PRegisterHistoryAgentSpecialization, G2PIntakeFormAgentSpecialization,
    G2PRegisterAgentQualification, G2PRegisterHistoryAgentQualification, G2PIntakeFormAgentQualification,
)


async def add_missing_columns(model) -> list[str]:
    """Add the model's columns that its existing table lacks; return their names.

    create_migrate() only creates a table that is not there yet, so a column
    added to a model later never reaches an install whose table already exists.
    This brings such a table up to the model, as the Farmer Registry does.
    Columns are added nullable unless they carry a server default, so existing
    rows stay valid. Nothing is ever dropped.
    """
    table = model.__table__
    dialect = postgresql.dialect()
    async with dbengine.get().begin() as conn:
        existing = set((await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = :name"), {"name": table.name})).scalars())
        if not existing:
            return []  # no table yet: create_migrate creates it whole
        added = []
        for column in table.columns:
            if column.name in existing:
                continue
            ddl = (f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS "{column.name}" '
                   + column.type.compile(dialect=dialect))
            default = column.server_default
            if default is not None:
                ddl += f" DEFAULT {getattr(default.arg, 'text', default.arg)}"
                if not column.nullable:
                    ddl += " NOT NULL"
            await conn.execute(text(ddl))
            added.append(column.name)
    if added:
        _logger.info("Added columns to %s: %s", table.name, added)
    return added


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        CoreInitializer().initialize()

        G2PRegisterDomainFactory()
        G2PIdGeneratorFactory()
        G2PRegisterDomainServiceAgent()
        G2PRegisterDomainServiceAgentSpecialization()
        G2PRegisterDomainServiceAgentQualification()
        G2PActivityDomainServiceAgentTraining()

    def migrate_database(self, args):
        async def migrate():
            _logger.info("Migrating extensions database")
            for model in RECORD_MODELS:
                await add_missing_columns(model)
                await model.create_migrate()

        asyncio.run(migrate())
