-- Agents Registry reporting views, for Superset / G2P Insights and SQL users.
--
-- Plain views, always up to date: they read the Agent register, its list
-- sections and the AgentTraining activity register (its per-agent projection is
-- kept current by the platform in the same transaction as every activity).
--
-- Geography is generic: an agent's assigned area is a Master Data unit at any
-- level, stored with its ancestry (geo_code_hierarchy_json, top level first).
-- Levels are exposed by position, area_level_1 being the top (the country), each
-- with its code, name and the level's name (e.g. region, zone, woreda), so the
-- views work for any country's geography.
--
-- Re-run on every install/upgrade by db-seed (CREATE OR REPLACE). Hand-written,
-- not generated. Add new columns at the end: CREATE OR REPLACE VIEW only allows that.

-- One row per agent.
CREATE OR REPLACE VIEW agents_rpt_agent AS
SELECT
    a.internal_record_id,
    a.functional_record_id                                                    AS agent_id,
    a.record_name                                                             AS agent_name,
    a.record_status,
    a.gender,
    a.birth_date,
    date_part('year', age(a.birth_date))::int                                 AS age_years,
    a.position,
    a.employer_type,
    a.employer_name,
    a.employment_type,
    a.date_of_hire,
    date_part('year', age(a.date_of_hire))::int                               AS years_of_service,
    a.service_status,
    a.service_status_date,
    a.service_point_name,
    a.service_point_type,
    a.assigned_since,
    a.assignment_reason,
    a.geo_lowest_level_value_id                                               AS area_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> -1 ->> 'level_value_mnemonic' AS area_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> -1 ->> 'level_mnemonic'       AS area_level,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 0 ->> 'level_value_id'        AS area_level_1_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 0 ->> 'level_value_mnemonic'  AS area_level_1_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 1 ->> 'level_value_id'        AS area_level_2_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 1 ->> 'level_value_mnemonic'  AS area_level_2_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 1 ->> 'level_mnemonic'        AS area_level_2_type,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 2 ->> 'level_value_id'        AS area_level_3_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 2 ->> 'level_value_mnemonic'  AS area_level_3_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 2 ->> 'level_mnemonic'        AS area_level_3_type,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 3 ->> 'level_value_id'        AS area_level_4_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 3 ->> 'level_value_mnemonic'  AS area_level_4_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 3 ->> 'level_mnemonic'        AS area_level_4_type,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 4 ->> 'level_value_id'        AS area_level_5_code,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 4 ->> 'level_value_mnemonic'  AS area_level_5_name,
    a.geo_code_hierarchy_json -> 'hierarchy' -> 4 ->> 'level_mnemonic'        AS area_level_5_type,
    (SELECT s.specialization FROM g2p_register_agent_specializations s
      WHERE s.link_internal_record_id = a.internal_record_id AND s.is_primary IS TRUE
        AND s.record_status = 'ACTIVE' LIMIT 1)                               AS primary_specialization,
    (SELECT count(*) FROM g2p_register_agent_specializations s
      WHERE s.link_internal_record_id = a.internal_record_id AND s.record_status = 'ACTIVE')::int
                                                                              AS specialization_count,
    (SELECT count(*) FROM g2p_register_agent_qualifications q
      WHERE q.link_internal_record_id = a.internal_record_id AND q.record_status = 'ACTIVE')::int
                                                                              AS qualification_count,
    coalesce(t.training_count, 0)                                             AS training_count,
    coalesce(t.training_hours, 0)                                             AS training_hours,
    t.last_training_on,
    t.last_training_topic,
    coalesce(t.certification_count, 0)                                        AS certification_count,
    t.latest_certification,
    t.latest_certification_valid_until
FROM g2p_register_agents a
LEFT JOIN g2p_activity_projection_agent_training t ON t.agent_id = a.functional_record_id;

-- Agents per assigned area, position and status.
CREATE OR REPLACE VIEW agents_rpt_agents_by_area AS
SELECT
    area_code, area_name, area_level,
    area_level_2_code, area_level_2_name,
    position, service_status,
    count(*)                                                  AS agents,
    count(*) FILTER (WHERE gender = 'FEMALE')                 AS female_agents,
    count(*) FILTER (WHERE training_count > 0)                AS trained_agents,
    count(*) FILTER (WHERE certification_count > 0)           AS certified_agents
FROM agents_rpt_agent
WHERE record_status = 'ACTIVE'
GROUP BY area_code, area_name, area_level, area_level_2_code, area_level_2_name, position, service_status;

-- One row per current training or certification, with the agent's area.
CREATE OR REPLACE VIEW agents_rpt_training AS
SELECT
    t.activity_id,
    t.activity_type,
    t.occurred_at::date                                       AS occurred_on,
    t.agent_id,
    a.agent_name,
    a.position,
    a.area_code,
    a.area_name,
    a.area_level_2_code,
    a.area_level_2_name,
    t.topic,
    t.payload ->> 'course_title'                              AS course_title,
    t.course_code,
    t.payload ->> 'provider'                                  AS provider,
    t.payload ->> 'delivery_mode'                             AS delivery_mode,
    t.hours,
    t.result,
    t.payload ->> 'certification'                             AS certification,
    t.certificate_number,
    t.valid_until,
    t.verification_status
FROM g2p_activity_agent_training t
LEFT JOIN agents_rpt_agent a ON a.agent_id = t.agent_id
WHERE t.status = 'ACTIVE';
