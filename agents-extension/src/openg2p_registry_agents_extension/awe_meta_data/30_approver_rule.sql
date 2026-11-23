-- Approvers are the platform chart's demo staff users (keycloak-init creates
-- alex.carter and nina.patel for every registry release).
INSERT INTO "public"."approver_rule" (
    "id",
    "stage_id",
    "rule_type",
    "rule_value",
    "kind",
    "required",
    "created_at",
    "updated_at"
)
SELECT v."id", v."stage_id", v."rule_type", v."rule_value"::json, v."kind",
       v."required"::boolean, v."created_at"::timestamptz, v."updated_at"::timestamptz
FROM (VALUES
    ('a6e00000-0000-4000-8000-0000000a0061', 'a6e00000-0000-4000-8000-0000000a0051', 'user', '{"user_id": "alex.carter"}', 'approver', 'FALSE', NOW(), NOW()),
    ('a6e00000-0000-4000-8000-0000000a0062', 'a6e00000-0000-4000-8000-0000000a0052', 'user', '{"user_id": "nina.patel"}', 'approver', 'FALSE', NOW(), NOW()),
    ('a6e00000-0000-4000-8000-0000000a0063', 'a6e00000-0000-4000-8000-0000000a0053', 'user', '{"user_id": "alex.carter"}', 'approver', 'FALSE', NOW(), NOW()),
    ('a6e00000-0000-4000-8000-0000000a0064', 'a6e00000-0000-4000-8000-0000000a0054', 'user', '{"user_id": "nina.patel"}', 'approver', 'FALSE', NOW(), NOW())
) AS v("id","stage_id","rule_type","rule_value","kind","required","created_at","updated_at")
WHERE EXISTS (SELECT 1 FROM "public"."approval_stage" s WHERE s.id = v."stage_id")
ON CONFLICT DO NOTHING;
