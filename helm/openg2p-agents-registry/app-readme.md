# OpenG2P Agents Registry

A reference registry of the agents who serve farmers — extension agents,
development agents, animal health workers — built on the OpenG2P registry
platform:

* **Agent** register: Agent ID (generated, eight digits), person and national ID,
  contact, employment, the current assignment (an area of the country's
  geography and a service point) and the service status, with specializations
  and qualifications. Every change is a change request approved in AWE; the
  version history keeps every transfer and status change.
* **AgentTraining** activity register: trainings completed and certifications
  awarded, against the agent, with a summary per agent.

Coded fields are Master Data lists (`AGENT_*`, the country pack's agriculture
domain): install Master Data with `geoSeed.domains: [agriculture]` first. The
registry is not shared with partners (consent enforcement is off).
