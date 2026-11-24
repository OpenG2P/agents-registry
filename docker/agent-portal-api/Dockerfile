# Agents Registry — agent-portal-api image (VC issuance at the counter).
#
# Thin layer over the registry-platform base image: installs the agents
# extension and selects it with REGISTRY_EXTENSION_MODULE. The platform's image
# carries only the reference extension and would create the register tables in
# that shape, breaking db-seed — hence a variant image, as the Farmer Registry has.
#
# Keep RP_VERSION in lockstep with the openg2p-registry dependency in
# helm/openg2p-agents-registry/Chart.yaml (scripts/bump-rp-version.sh).
#
# Build context = repo root.
ARG RP_VERSION=0.0.0-develop.847
FROM openg2p/openg2p-registry-agent-portal-api:${RP_VERSION}

ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_agents_extension

COPY agents-extension/ /app/agents-extension/
RUN pip install --no-cache-dir /app/agents-extension
