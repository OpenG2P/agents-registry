-- Agents Registry — source view for verifiable credential issuance (an agent's ID card).
--
-- The Registry Platform owns the issuance machinery but no view: the claim
-- fields differ per registry, so each manifestation supplies its own.
--
-- Contract expected by the Agent Portal API (RegistryLookupService):
--   internal_record_id  REQUIRED — the key issuance is done on. The national ID
--                       typed at the counter only *locates* the record.
--   foundational_id     REQUIRED — the national ID, matched when the agent is
--                       looked up, and what the ID system's authenticated
--                       subject is checked against by the registry core.
--   record_status       optional — lets the API say *why* a record cannot be issued to.
--   record_name         optional — shown to confirm the right person.
--   everything else     becomes a credential claim.
--
-- Claims: who the agent is (Agent ID, name, date of birth, gender) and what they
-- are (position, service point, assigned area) — what a farmer or an official
-- checks on an agent's card. Nothing about employment terms, qualifications or
-- trainings: a printed credential is a bearer document, and a column added here
-- goes on paper and into the QR.
--
-- Only agents in service: an active record whose service status is active (a
-- retired, suspended or separated agent gets no card).
--
-- Applied by the db-seed Job with the rest of meta_data/, after the model migration.

CREATE OR REPLACE VIEW agent_vc_view AS
SELECT
    a.internal_record_id                                   AS "internal_record_id",
    a.foundational_id                                      AS "foundational_id",
    a.record_status                                        AS "record_status",
    a.record_name                                          AS "record_name",

    -- Claims. Quoted aliases: they must match the ${...} variables in the
    -- credential template exactly, and Postgres lowercases unquoted names.
    a.functional_record_id                                 AS "functionalRecordId",
    NULLIF(CONCAT_WS(' ',
        NULLIF(a.first_name, ''),
        NULLIF(a.middle_name, ''),
        NULLIF(a.last_name, '')
    ), '')                                                 AS "fullName",
    TO_CHAR(a.birth_date, 'YYYY-MM-DD')                    AS "dateOfBirth",
    a.gender                                               AS "gender",
    a.position                                             AS "position",
    a.service_point_name                                   AS "servicePoint",
    -- The assigned area's name: the last (lowest) unit of its hierarchy.
    a.geo_code_hierarchy_json -> 'hierarchy' -> -1 ->> 'level_value_mnemonic' AS "assignedArea"
FROM g2p_register_agents a
WHERE a.record_status = 'ACTIVE'
  AND a.foundational_id IS NOT NULL
  AND COALESCE(a.service_status, 'AGST_ACTIVE') = 'AGST_ACTIVE';

COMMENT ON VIEW agent_vc_view IS
  'Identity and role claims for agent verifiable credentials. Keyed on internal_record_id; looked up by foundational_id. Agents in service only — see the file header before adding columns.';
