from __future__ import annotations

from ..db.connection import get_connection
from ..schemas.trial_detail import (
    TrialArm,
    TrialChunkPreview,
    TrialCondition,
    TrialDetail,
    TrialEligibility,
    TrialIntervention,
    TrialLocation,
    TrialOutcome,
    TrialValidation,
)


def get_trial_detail(nct_id: str) -> TrialDetail | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, nct_id, source, source_url, brief_title, official_title, brief_summary,
                    detailed_description, study_type, phases, allocation, intervention_model,
                    masking, primary_purpose, enrollment_count, enrollment_type, overall_status,
                    last_known_status, start_date_text, primary_completion_date_text,
                    completion_date_text, study_first_posted_at_text, results_first_posted_at_text,
                    last_update_posted_at_text, is_2026_relevant, relevance_reasons,
                    lead_sponsor_name, lead_sponsor_class, collaborator_names, sex,
                    minimum_age_text, maximum_age_text, age_groups, healthy_volunteers,
                    condition_labels, intervention_labels, drug_class_labels, keyword_labels,
                    country_codes, has_us_sites, raw_has_results
                FROM trials
                WHERE nct_id = %s
                """,
                (nct_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            (
                trial_id,
                fetched_nct_id,
                source,
                source_url,
                brief_title,
                official_title,
                brief_summary,
                detailed_description,
                study_type,
                phases,
                allocation,
                intervention_model,
                masking,
                primary_purpose,
                enrollment_count,
                enrollment_type,
                overall_status,
                last_known_status,
                start_date_text,
                primary_completion_date_text,
                completion_date_text,
                study_first_posted_at_text,
                results_first_posted_at_text,
                last_update_posted_at_text,
                is_2026_relevant,
                relevance_reasons,
                lead_sponsor_name,
                lead_sponsor_class,
                collaborator_names,
                sex,
                minimum_age_text,
                maximum_age_text,
                age_groups,
                healthy_volunteers,
                condition_labels,
                intervention_labels,
                drug_class_labels,
                keyword_labels,
                country_codes,
                has_us_sites,
                raw_has_results,
            ) = row

            cur.execute(
                """
                SELECT name, normalized_name, is_primary
                FROM trial_conditions
                WHERE trial_id = %s
                ORDER BY name ASC
                """,
                (trial_id,),
            )
            conditions = [
                TrialCondition(name=name, normalized_name=normalized_name, is_primary=is_primary)
                for name, normalized_name, is_primary in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT intervention_type, name, normalized_name, description, arm_group_labels, drug_class
                FROM trial_interventions
                WHERE trial_id = %s
                ORDER BY name ASC
                """,
                (trial_id,),
            )
            interventions = [
                TrialIntervention(
                    intervention_type=intervention_type,
                    name=name,
                    normalized_name=normalized_name,
                    description=description,
                    arm_group_labels=arm_group_labels or [],
                    drug_class=drug_class,
                )
                for intervention_type, name, normalized_name, description, arm_group_labels, drug_class in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT label, type, description, intervention_names
                FROM trial_arms
                WHERE trial_id = %s
                ORDER BY label ASC NULLS LAST
                """,
                (trial_id,),
            )
            arms = [
                TrialArm(
                    label=label,
                    type=arm_type,
                    description=description,
                    intervention_names=intervention_names or [],
                )
                for label, arm_type, description, intervention_names in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT outcome_type, measure, description, time_frame
                FROM trial_outcomes
                WHERE trial_id = %s
                ORDER BY outcome_type ASC NULLS LAST, measure ASC NULLS LAST
                """,
                (trial_id,),
            )
            outcomes = [
                TrialOutcome(
                    outcome_type=outcome_type,
                    measure=measure,
                    description=description,
                    time_frame=time_frame,
                )
                for outcome_type, measure, description, time_frame in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT facility_name, city, state, country, status
                FROM trial_locations
                WHERE trial_id = %s
                ORDER BY country ASC NULLS LAST, state ASC NULLS LAST, city ASC NULLS LAST
                """,
                (trial_id,),
            )
            locations = [
                TrialLocation(
                    facility_name=facility_name,
                    city=city,
                    state=state,
                    country=country,
                    status=status,
                )
                for facility_name, city, state, country, status in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT criteria_text, sex, minimum_age_text, maximum_age_text, age_groups, healthy_volunteers
                FROM trial_eligibility
                WHERE trial_id = %s
                """,
                (trial_id,),
            )
            eligibility_row = cur.fetchone()
            eligibility = None
            if eligibility_row is not None:
                (
                    criteria_text,
                    eligibility_sex,
                    eligibility_min_age,
                    eligibility_max_age,
                    eligibility_age_groups,
                    eligibility_healthy_volunteers,
                ) = eligibility_row
                eligibility = TrialEligibility(
                    criteria_text=criteria_text,
                    sex=eligibility_sex,
                    minimum_age_text=eligibility_min_age,
                    maximum_age_text=eligibility_max_age,
                    age_groups=eligibility_age_groups or [],
                    healthy_volunteers=eligibility_healthy_volunteers,
                )

            cur.execute(
                """
                SELECT accepted, errors, rejection_reasons, warning_reasons
                FROM trial_validation
                WHERE trial_id = %s
                """,
                (trial_id,),
            )
            validation_row = cur.fetchone()
            validation = None
            if validation_row is not None:
                accepted, errors, rejection_reasons, warning_reasons = validation_row
                validation = TrialValidation(
                    accepted=accepted,
                    errors=errors or [],
                    rejection_reasons=rejection_reasons or [],
                    warning_reasons=warning_reasons or [],
                )

            cur.execute(
                """
                SELECT chunk_id, chunk_type, title, content, source_field_paths
                FROM trial_chunks
                WHERE trial_id = %s
                ORDER BY chunk_type ASC, chunk_id ASC
                """,
                (trial_id,),
            )
            chunks = [
                TrialChunkPreview(
                    chunk_id=chunk_id,
                    chunk_type=chunk_type,
                    title=title,
                    snippet=(content or "")[:180].replace("\n", " ").strip(),
                    source_field_paths=source_field_paths or [],
                )
                for chunk_id, chunk_type, title, content, source_field_paths in cur.fetchall()
            ]

    return TrialDetail(
        nct_id=fetched_nct_id,
        source=source,
        source_url=source_url,
        brief_title=brief_title,
        official_title=official_title,
        brief_summary=brief_summary,
        detailed_description=detailed_description,
        study_type=study_type,
        phases=phases or [],
        allocation=allocation,
        intervention_model=intervention_model,
        masking=masking,
        primary_purpose=primary_purpose,
        enrollment_count=enrollment_count,
        enrollment_type=enrollment_type,
        overall_status=overall_status,
        last_known_status=last_known_status,
        start_date_text=start_date_text,
        primary_completion_date_text=primary_completion_date_text,
        completion_date_text=completion_date_text,
        study_first_posted_at_text=study_first_posted_at_text,
        results_first_posted_at_text=results_first_posted_at_text,
        last_update_posted_at_text=last_update_posted_at_text,
        is_2026_relevant=is_2026_relevant,
        relevance_reasons=relevance_reasons or [],
        lead_sponsor_name=lead_sponsor_name,
        lead_sponsor_class=lead_sponsor_class,
        collaborator_names=collaborator_names or [],
        sex=sex,
        minimum_age_text=minimum_age_text,
        maximum_age_text=maximum_age_text,
        age_groups=age_groups or [],
        healthy_volunteers=healthy_volunteers,
        condition_labels=condition_labels or [],
        intervention_labels=intervention_labels or [],
        drug_class_labels=drug_class_labels or [],
        keyword_labels=keyword_labels or [],
        country_codes=country_codes or [],
        has_us_sites=has_us_sites,
        raw_has_results=raw_has_results,
        conditions=conditions,
        interventions=interventions,
        arms=arms,
        outcomes=outcomes,
        locations=locations,
        eligibility=eligibility,
        validation=validation,
        chunks=chunks,
    )
