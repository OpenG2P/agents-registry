# Agents Registry — DB-seed image.
#
# The base image's entrypoint runs every *.sql under /seed/meta_data (sorted).
# The Agents Registry seed is:
#   activity-metadata/        AgentTraining activity types (JSON Schemas, rules) and indicators
#   awe-integration/          Agent change requests / intake form -> AWE policy keys
#   register-metadata/        the registers (Agent, its list sections, AgentTraining) and
#                             the Agent register's sections, tabs, search and intake form
#   registry-configurations/  the staff portal's name, theme and languages
#   reporting-views/          agents_rpt_* views
#   awe_meta_data/            Agent approval policies + this release's callback secret
#                             (run against the shared AWE database)
# No code lists: the registry reads them live from Master Data (the country
# pack's agriculture domain, AGENT_* lists, loaded by the master-data chart).
#
# Sample data (LOAD_SAMPLE_DATA=true) is the country pack's samples/agents.json
# in openg2p-data, inserted by load_sample_data.py as approved Agent records.
# The base image carries openg2p-data from when it was built; it is fetched
# again here so the sample agents are those of this build. Sample trainings are
# created through the APIs by the platform's sample task.
#
# Build context = repo root.
ARG RP_VERSION=0.0.0-develop.845
FROM openg2p/openg2p-registry-db-seed:${RP_VERSION}

ARG OPENG2P_DATA_REPO=https://github.com/openg2p/openg2p-data.git
ARG OPENG2P_DATA_BRANCH=develop
RUN rm -rf /openg2p-data && mkdir -p /openg2p-data && cd /openg2p-data \
    && git init -q \
    && git remote add origin ${OPENG2P_DATA_REPO} \
    && git fetch -q --depth 1 origin ${OPENG2P_DATA_BRANCH} \
    && git checkout -q FETCH_HEAD \
    && rm -rf /openg2p-data/.git

RUN rm -rf /seed/meta_data/* /seed/awe_meta_data/* /seed/templates/* /seed/seed-data/*

COPY agents-extension/src/openg2p_registry_agents_extension/meta_data/     /seed/meta_data/
COPY agents-extension/src/openg2p_registry_agents_extension/awe_meta_data/ /seed/awe_meta_data/

# The registry's own sample loader: the entrypoint keeps the hook, the variant
# supplies the loader (as the Farmer and Crop Sown Registries do).
COPY docker/db-seed/load_sample_data.py /seed/load_sample_data.py
RUN chmod +x /seed/load_sample_data.py
