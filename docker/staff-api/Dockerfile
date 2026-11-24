# Agents Registry — staff-api image.
#
# Thin layer over the registry-platform base image: installs the agents
# extension and selects it with REGISTRY_EXTENSION_MODULE. ENV defaults and the
# migrate + gunicorn CMD come from the base image. The extension's migration
# creates the Agent register tables; the platform's creates the AgentTraining
# activity tables (partitioned, append-only).
#
# Keep RP_VERSION in lockstep with the openg2p-registry dependency in
# helm/openg2p-agents-registry/Chart.yaml (scripts/bump-rp-version.sh).
#
# Build context = repo root.
ARG RP_VERSION=0.0.0-develop.847
FROM openg2p/openg2p-registry-staff-api:${RP_VERSION}

ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_agents_extension

COPY agents-extension/ /app/agents-extension/
RUN pip install --no-cache-dir /app/agents-extension
