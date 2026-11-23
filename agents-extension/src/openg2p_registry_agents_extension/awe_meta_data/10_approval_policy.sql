-- Agent approval policies, seeded into the shared AWE database (db-seed, when
-- global.aweEnabled). Bound to the Agent register by
-- meta_data/awe-integration/g2p_registry_awe_policy_configurations.sql.
-- Untargeted DO NOTHING: approval_policy also carries uq_policy_key_version, and
-- the AWE database is shared, so another release of this registry may already
-- hold these keys.
INSERT INTO "public"."approval_policy" (
    "id",
    "policy_key",
    "version",
    "name",
    "description",
    "status",
    "artifact_type",
    "created_by",
    "forbid_self_approval",
    "forbid_repeat_approvers",
    "created_at",
    "updated_at"
) VALUES
    ('a6e00000-0000-4000-8000-0000000a0041', 'registry.change_request.agent', 1, 'Policy for Agent Change Request', NULL, 'active', 'registry.change_request', 'seed', 'FALSE', 'FALSE', NOW(), NOW()),
    ('a6e00000-0000-4000-8000-0000000a0042', 'registry.intake_form.agent', 1, 'Policy for Agent Intake Form', NULL, 'active', 'registry.intake_form', 'seed', 'FALSE', 'FALSE', NOW(), NOW())
ON CONFLICT DO NOTHING;
