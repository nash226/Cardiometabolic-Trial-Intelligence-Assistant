-- Small accepted reviewer corpus for Docker demos.
-- The full project pipeline can still ingest and load a larger ClinicalTrials.gov corpus.

INSERT INTO trials (
    nct_id, source, source_url, brief_title, official_title, brief_summary,
    study_type, phases, allocation, intervention_model, masking, primary_purpose,
    enrollment_count, enrollment_type, overall_status, start_date_text,
    primary_completion_date_text, completion_date_text, study_first_posted_at_text,
    last_update_posted_at_text, is_2026_relevant, relevance_reasons,
    lead_sponsor_name, lead_sponsor_class, collaborator_names, sex,
    minimum_age_text, maximum_age_text, age_groups, healthy_volunteers,
    condition_labels, intervention_labels, drug_class_labels, keyword_labels,
    country_codes, has_us_sites, raw_has_results
) VALUES (
    'NCT06893016',
    'clinicaltrials_gov',
    'https://clinicaltrials.gov/study/NCT06893016',
    'Evaluation of RAY1225 in Adult Participants Who Have Obesity or Are Overweight',
    'A Multicenter, Randomized, Double-blind, Placebo-controlled Phase 3 Study Evaluating the Safety, Tolerability, and Efficacy of RAY1225 in Participants Who Have Obesity or Are Overweight',
    'The primary objective of this study is to demonstrate that RAY1225 is superior to placebo for percent change in body weight.',
    'INTERVENTIONAL',
    ARRAY['PHASE3'],
    'RANDOMIZED',
    'PARALLEL',
    'DOUBLE',
    'TREATMENT',
    640,
    'ESTIMATED',
    'RECRUITING',
    '2025-06-15',
    '2026-06-15',
    '2026-09-15',
    '2025-03-25',
    '2025-07-17',
    TRUE,
    ARRAY['active_or_recruiting_status', 'primary_completion_in_2026', 'completion_in_2026'],
    'Guangdong Raynovent Biotech Co., Ltd',
    'INDUSTRY',
    ARRAY[]::TEXT[],
    'ALL',
    '18 Years',
    NULL,
    ARRAY['ADULT', 'OLDER_ADULT'],
    FALSE,
    ARRAY['obesity'],
    ARRAY['RAY1225', 'Placebo'],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    ARRAY[]::TEXT[],
    FALSE,
    FALSE
)
ON CONFLICT (nct_id) DO UPDATE SET
    brief_title = EXCLUDED.brief_title,
    brief_summary = EXCLUDED.brief_summary,
    phases = EXCLUDED.phases,
    overall_status = EXCLUDED.overall_status,
    is_2026_relevant = EXCLUDED.is_2026_relevant,
    condition_labels = EXCLUDED.condition_labels,
    intervention_labels = EXCLUDED.intervention_labels,
    updated_at = NOW();

DELETE FROM trial_conditions WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_interventions WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_arms WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_outcomes WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_locations WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_eligibility WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');
DELETE FROM trial_validation WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT06893016');

INSERT INTO trial_conditions (trial_id, name, normalized_name, is_primary)
SELECT id, 'Obesity', 'obesity', TRUE FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_interventions (trial_id, intervention_type, name, normalized_name, description, arm_group_labels, drug_class)
SELECT id, 'DRUG', 'RAY1225', 'ray1225', 'RAY1225 will be administered subcutaneously.', ARRAY['RAY1225 High Dose', 'RAY1225 Medium Dose', 'RAY1225 Low Dose'], NULL FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'DRUG', 'Placebo', 'placebo', 'Placebo will be administered subcutaneously.', ARRAY['Placebo'], NULL FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_arms (trial_id, label, type, description, intervention_names)
SELECT id, 'RAY1225 High Dose', 'EXPERIMENTAL', 'Participants receive RAY1225 high dose subcutaneously for 52 weeks.', ARRAY['Drug: RAY1225'] FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'RAY1225 Medium Dose', 'EXPERIMENTAL', 'Participants receive RAY1225 medium dose subcutaneously for 52 weeks.', ARRAY['Drug: RAY1225'] FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'RAY1225 Low Dose', 'EXPERIMENTAL', 'Participants receive RAY1225 low dose subcutaneously for 52 weeks.', ARRAY['Drug: RAY1225'] FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'Placebo', 'PLACEBO_COMPARATOR', 'Participants receive placebo subcutaneously for 52 weeks.', ARRAY['Drug: Placebo'] FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_outcomes (trial_id, outcome_type, measure, description, time_frame)
SELECT id, 'primary', 'Percent change from baseline in body weight at Week 52', NULL, 'Baseline and Week 52' FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'primary', 'Number of participants who achieved at least 5 percent reduction in body weight from baseline at Week 52', NULL, 'Baseline and Week 52' FROM trials WHERE nct_id = 'NCT06893016'
UNION ALL
SELECT id, 'secondary', 'Change from baseline in waist circumference at Week 52', NULL, 'Baseline and Week 52' FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_locations (trial_id, facility_name, city, state, country, status)
SELECT id, NULL, NULL, NULL, NULL, 'RECRUITING' FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_eligibility (trial_id, criteria_text, sex, minimum_age_text, maximum_age_text, age_groups, healthy_volunteers)
SELECT id,
       $$Inclusion criteria include adults at least 18 years old with BMI at least 28 kg/m2, or BMI 24 to less than 28 kg/m2 with at least one weight-related comorbidity. Participants need a history of at least one unsuccessful attempt at weight loss by diet and exercise. Exclusion criteria include obesity caused by monogenic mutations, family or personal history of medullary thyroid carcinoma, severe psychiatric history, organ transplantation, plans to quit smoking during the study, or allergy to RAY1225 or GLP-1 related drugs.$$,
       'ALL', '18 Years', NULL, ARRAY['ADULT', 'OLDER_ADULT'], FALSE
FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trial_validation (trial_id, accepted, errors, rejection_reasons, warning_reasons)
SELECT id, TRUE, ARRAY[]::TEXT[], ARRAY[]::TEXT[], ARRAY[]::TEXT[] FROM trials WHERE nct_id = 'NCT06893016';

INSERT INTO trials (
    nct_id, source, source_url, brief_title, official_title, brief_summary,
    study_type, phases, allocation, intervention_model, masking, primary_purpose,
    enrollment_count, enrollment_type, overall_status, start_date_text,
    primary_completion_date_text, completion_date_text, study_first_posted_at_text,
    last_update_posted_at_text, is_2026_relevant, relevance_reasons,
    lead_sponsor_name, lead_sponsor_class, collaborator_names, sex,
    minimum_age_text, maximum_age_text, age_groups, healthy_volunteers,
    condition_labels, intervention_labels, drug_class_labels, keyword_labels,
    country_codes, has_us_sites, raw_has_results
) VALUES (
    'NCT07314684',
    'clinicaltrials_gov',
    'https://clinicaltrials.gov/study/NCT07314684',
    'GLP1-RAs Effects on Inflammatory and Endothelial Biomarkers in T2DM',
    'Impact of GLP1-RAs on Inflammation and Endothelial Biomarkers in Type 2 Diabetes Mellitus Patients: STABLE-GLP1 Trial',
    'The STABLE-GLP1 study evaluates semaglutide in addition to standard therapy in patients with type 2 diabetes, focusing on clinical prognosis, inflammatory biomarkers, and endothelial biomarkers.',
    'INTERVENTIONAL',
    ARRAY['PHASE4'],
    'RANDOMIZED',
    'PARALLEL',
    'NONE',
    'TREATMENT',
    80,
    'ESTIMATED',
    'RECRUITING',
    '2025-09-08',
    '2027-03-08',
    '2027-03-08',
    '2026-01-02',
    '2026-01-02',
    TRUE,
    ARRAY['active_or_recruiting_status'],
    'Federico II University',
    'OTHER',
    ARRAY[]::TEXT[],
    'ALL',
    '18 Years',
    '85 Years',
    ARRAY['ADULT', 'OLDER_ADULT'],
    FALSE,
    ARRAY['type_2_diabetes'],
    ARRAY['semaglutide', 'Standard Treatment (Guideline-Based)'],
    ARRAY['glp1_receptor_agonist'],
    ARRAY['Type 2 Diabetes Mellitus', 'Semaglutide', 'Inflammation', 'Endothelial function', 'Biomarkers', 'Coronary Plaque'],
    ARRAY[]::TEXT[],
    FALSE,
    FALSE
)
ON CONFLICT (nct_id) DO UPDATE SET
    brief_title = EXCLUDED.brief_title,
    brief_summary = EXCLUDED.brief_summary,
    phases = EXCLUDED.phases,
    overall_status = EXCLUDED.overall_status,
    is_2026_relevant = EXCLUDED.is_2026_relevant,
    condition_labels = EXCLUDED.condition_labels,
    intervention_labels = EXCLUDED.intervention_labels,
    drug_class_labels = EXCLUDED.drug_class_labels,
    updated_at = NOW();

DELETE FROM trial_conditions WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_interventions WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_arms WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_outcomes WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_locations WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_eligibility WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');
DELETE FROM trial_validation WHERE trial_id = (SELECT id FROM trials WHERE nct_id = 'NCT07314684');

INSERT INTO trial_conditions (trial_id, name, normalized_name, is_primary)
SELECT id, 'T2DM (Type 2 Diabetes Mellitus)', 'type_2_diabetes', TRUE FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_interventions (trial_id, intervention_type, name, normalized_name, description, arm_group_labels, drug_class)
SELECT id, 'DRUG', 'semaglutide', 'semaglutide', 'The starting dose is 0.25 mg semaglutide once weekly, escalating to 0.5 mg and potentially 1 mg once weekly.', ARRAY['Semaglutide in addition to standard therapy'], 'glp1_receptor_agonist' FROM trials WHERE nct_id = 'NCT07314684'
UNION ALL
SELECT id, 'DRUG', 'Standard Treatment (Guideline-Based)', 'standard treatment (guideline-based)', 'Patients receive standard therapy for type 2 diabetes according to clinical practice.', ARRAY['Semaglutide in addition to standard therapy', 'Standard therapy alone'], NULL FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_arms (trial_id, label, type, description, intervention_names)
SELECT id, 'Semaglutide in addition to standard therapy', 'EXPERIMENTAL', NULL, ARRAY['Drug: semaglutide', 'Drug: Standard Treatment (Guideline-Based)'] FROM trials WHERE nct_id = 'NCT07314684'
UNION ALL
SELECT id, 'Standard therapy alone', 'EXPERIMENTAL', NULL, ARRAY['Drug: Standard Treatment (Guideline-Based)'] FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_outcomes (trial_id, outcome_type, measure, description, time_frame)
SELECT id, 'primary', 'Effects of semaglutide plus standard therapy on inflammatory biomarkers compared with standard therapy alone', 'Inflammatory biomarkers include CRP, interleukins, colony-stimulating factors, tumor necrosis factors, interferons, transforming growth factors, and adiponectin.', 'From enrollment to the end of treatment at 52 weeks' FROM trials WHERE nct_id = 'NCT07314684'
UNION ALL
SELECT id, 'primary', 'Effects of semaglutide plus standard therapy on biomarkers of endothelial dysfunction compared with standard therapy alone', 'Biomarkers include endothelin-1, ICAM-1, VCAM-1, E-selectin, and P-selectin.', 'From enrollment to the end of treatment at 52 weeks' FROM trials WHERE nct_id = 'NCT07314684'
UNION ALL
SELECT id, 'secondary', 'Retrospective evaluation of fat attenuation index at CTA', 'FAI is evaluated retrospectively from CTA using dedicated software.', 'At baseline retrospectively' FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_locations (trial_id, facility_name, city, state, country, status)
SELECT id, NULL, NULL, NULL, NULL, 'RECRUITING' FROM trials WHERE nct_id = 'NCT07314684'
UNION ALL
SELECT id, NULL, NULL, NULL, NULL, 'RECRUITING' FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_eligibility (trial_id, criteria_text, sex, minimum_age_text, maximum_age_text, age_groups, healthy_volunteers)
SELECT id,
       $$Inclusion criteria include adults at least 18 years old with type 2 diabetes, no ASCVD or severe target-organ damage, stable clinical conditions, stable antidiabetic treatment, and left ventricular ejection fraction at least 50 percent. Exclusion criteria include age over 85 years, previous semaglutide or GLP1-RA treatment, epicardial coronary artery stenosis at least 50 percent, significant renal impairment, ASCVD history, type 1 diabetes mellitus, liver disease, recent inflammatory or infectious disease, recent cancer history, or substance abuse.$$,
       'ALL', '18 Years', '85 Years', ARRAY['ADULT', 'OLDER_ADULT'], FALSE
FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_validation (trial_id, accepted, errors, rejection_reasons, warning_reasons)
SELECT id, TRUE, ARRAY[]::TEXT[], ARRAY[]::TEXT[], ARRAY[]::TEXT[] FROM trials WHERE nct_id = 'NCT07314684';

INSERT INTO trial_chunks (chunk_id, trial_id, trial_nct_id, chunk_type, title, content, source_field_paths, token_count_estimate, content_tsv)
VALUES
(
    'NCT06893016-status',
    (SELECT id FROM trials WHERE nct_id = 'NCT06893016'),
    'NCT06893016',
    'status_identity',
    'Recruiting phase 3 obesity study',
    $$NCT06893016 is a recruiting phase 3 interventional obesity and overweight study sponsored by Guangdong Raynovent Biotech. The study is 2026 relevant because primary completion and completion dates fall in 2026.$$,
    ARRAY['trial.overall_status', 'trial.phases', 'trial.relevance_reasons'],
    41,
    to_tsvector('english', $$NCT06893016 is a recruiting phase 3 interventional obesity and overweight study sponsored by Guangdong Raynovent Biotech. The study is 2026 relevant because primary completion and completion dates fall in 2026.$$)
),
(
    'NCT06893016-outcomes',
    (SELECT id FROM trials WHERE nct_id = 'NCT06893016'),
    'NCT06893016',
    'outcomes',
    'Body weight endpoints',
    $$The primary endpoints include percent change from baseline in body weight at Week 52 and the number of participants achieving at least 5 percent body weight reduction at Week 52. A secondary endpoint tracks waist circumference change at Week 52.$$,
    ARRAY['outcomes.measure', 'outcomes.time_frame'],
    43,
    to_tsvector('english', $$The primary endpoints include percent change from baseline in body weight at Week 52 and the number of participants achieving at least 5 percent body weight reduction at Week 52. A secondary endpoint tracks waist circumference change at Week 52.$$)
),
(
    'NCT06893016-intervention',
    (SELECT id FROM trials WHERE nct_id = 'NCT06893016'),
    'NCT06893016',
    'conditions_interventions',
    'RAY1225 dose arms',
    $$The intervention arms compare high, medium, and low doses of subcutaneous RAY1225 against placebo over 52 weeks in adults with obesity or overweight and weight-related comorbidities.$$,
    ARRAY['interventions.name', 'arms.label', 'eligibility.criteria_text'],
    35,
    to_tsvector('english', $$The intervention arms compare high, medium, and low doses of subcutaneous RAY1225 against placebo over 52 weeks in adults with obesity or overweight and weight-related comorbidities.$$)
),
(
    'NCT07314684-summary',
    (SELECT id FROM trials WHERE nct_id = 'NCT07314684'),
    'NCT07314684',
    'summary_description',
    'Semaglutide biomarker study',
    $$The STABLE-GLP1 trial studies semaglutide in addition to standard therapy for type 2 diabetes. It evaluates inflammatory biomarkers, endothelial biomarkers, coronary plaque features, and cardiovascular outcomes over 52 weeks.$$,
    ARRAY['trial.brief_summary', 'trial.detailed_description'],
    34,
    to_tsvector('english', $$The STABLE-GLP1 trial studies semaglutide in addition to standard therapy for type 2 diabetes. It evaluates inflammatory biomarkers, endothelial biomarkers, coronary plaque features, and cardiovascular outcomes over 52 weeks.$$)
),
(
    'NCT07314684-intervention',
    (SELECT id FROM trials WHERE nct_id = 'NCT07314684'),
    'NCT07314684',
    'conditions_interventions',
    'GLP1 receptor agonist treatment',
    $$Semaglutide is a GLP1 receptor agonist. Participants receive semaglutide plus guideline-based standard therapy or standard therapy alone in a randomized phase 4 study.$$,
    ARRAY['interventions.name', 'interventions.drug_class', 'arms.intervention_names'],
    29,
    to_tsvector('english', $$Semaglutide is a GLP1 receptor agonist. Participants receive semaglutide plus guideline-based standard therapy or standard therapy alone in a randomized phase 4 study.$$)
),
(
    'NCT07314684-outcomes',
    (SELECT id FROM trials WHERE nct_id = 'NCT07314684'),
    'NCT07314684',
    'outcomes',
    'Inflammatory and endothelial endpoints',
    $$Primary endpoints evaluate semaglutide effects on inflammatory biomarkers such as CRP, interleukins, TNF-alpha, and adiponectin, plus endothelial dysfunction biomarkers such as endothelin-1, ICAM-1, VCAM-1, E-selectin, and P-selectin.$$,
    ARRAY['outcomes.measure', 'outcomes.description', 'outcomes.time_frame'],
    39,
    to_tsvector('english', $$Primary endpoints evaluate semaglutide effects on inflammatory biomarkers such as CRP, interleukins, TNF-alpha, and adiponectin, plus endothelial dysfunction biomarkers such as endothelin-1, ICAM-1, VCAM-1, E-selectin, and P-selectin.$$)
)
ON CONFLICT (chunk_id) DO UPDATE SET
    title = EXCLUDED.title,
    content = EXCLUDED.content,
    source_field_paths = EXCLUDED.source_field_paths,
    token_count_estimate = EXCLUDED.token_count_estimate,
    content_tsv = EXCLUDED.content_tsv;
