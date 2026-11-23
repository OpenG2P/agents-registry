# Agents Registry — Celery image (worker and beat, chosen by CELERY_APP).
#
# The worker runs the activity outbox, projection reconciliation, partition
# maintenance and the sample trainings; beat schedules them.
#
# Build context = repo root.
ARG RP_VERSION=0.0.0-develop.843
FROM openg2p/openg2p-registry-celery:${RP_VERSION}

ENV REGISTRY_EXTENSION_MODULE=openg2p_registry_agents_extension

COPY agents-extension/ /app/agents-extension/
RUN pip install --no-cache-dir /app/agents-extension
