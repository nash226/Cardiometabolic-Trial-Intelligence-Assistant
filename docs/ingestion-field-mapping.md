# Ingestion Field Mapping

This document is the first step of the ingestion pipeline. It answers one question:

`How does a ClinicalTrials.gov study record become a normalized trial record in our system?`

We are not writing the ETL yet. We are fixing the extraction plan first.

## Ground rules

Primary source:

- ClinicalTrials.gov API v2 study records

Current source notes from the official API docs:

- The modernized ClinicalTrials.gov ingest changed on August 26, 2025.
- Data refreshes daily Monday through Friday, generally by 9 a.m. ET.
- Some rich-text markup fields and location/geopoint handling changed in the modernized pipeline.

Implication for our ingestion design:

- Keep the full raw payload for auditability.
- Normalize only the fields we know we need for search, compare, and grounded QA.
- Treat markup and location fields as source data that may evolve slightly over time.

## Representative studies reviewed

We looked at representative public study pages to sanity-check the fields our MVP will need:

- Obesity: `NCT04881760`
- Obesity + type 2 diabetes: `NCT07282600`
- MASH: `NCT06318169`
- MASH + type 2 diabetes overlap: `NCT07303803`

These confirm that our target domain mixes:

- structured fields like phase, status, sponsor, dates, enrollment, and locations
- semi-structured fields like eligibility criteria and detailed descriptions
- condition naming variation such as `MASH`, `NAFLD`, `NASH`, `MASLD`, and `type 2 diabetes`

## Source record anatomy

ClinicalTrials.gov study records are organized into top-level sections. For MVP ingestion, the most important ones are:

- `protocolSection`
- `derivedSection`
- `resultsSection`

For our first pass, `protocolSection` is the core source of truth. `resultsSection` is useful later when we explicitly support result-aware questions.

## Modules we will extract first

These are the protocol modules that matter most for the MVP:

### `protocolSection.identificationModule`

Use for:

- `nct_id`
- `brief_title`
- `official_title`
- source URL construction

Why it matters:

- Every downstream join, compare, and citation depends on stable study identity.

### `protocolSection.statusModule`

Use for:

- `overall_status`
- `last_known_status`
- `start_date`
- `primary_completion_date`
- `completion_date`
- `study_first_posted_at`
- `results_first_posted_at`
- `last_update_posted_at`
- 2026 relevance logic

Why it matters:

- Status and timeline drive the core product questions.
- We should derive 2026 relevance from dates and statuses during normalization, not at query time only.

### `protocolSection.sponsorCollaboratorsModule`

Use for:

- `lead_sponsor_name`
- `lead_sponsor_class`
- `collaborator_names`

Why it matters:

- Users will ask for industry-sponsored trials and sponsor-specific comparisons.

### `protocolSection.conditionsModule`

Use for:

- condition rows
- normalized condition labels
- keyword labels

Why it matters:

- Source condition strings vary a lot. This module will feed both filtering and terminology normalization.

### `protocolSection.designModule`

Use for:

- `study_type`
- `phases`
- `allocation`
- `intervention_model`
- `masking`
- `primary_purpose`
- `enrollment_count`
- `enrollment_type`

Why it matters:

- This is the main structured design metadata for filtering and compare views.

### `protocolSection.armsInterventionsModule`

Use for:

- interventions
- intervention types
- arms/groups
- drug-class heuristics

Why it matters:

- Many of the most useful user questions center on intervention families, not just exact drug names.

### `protocolSection.outcomesModule`

Use for:

- primary outcomes
- secondary outcomes
- outcome descriptions
- time frames

Why it matters:

- This is critical for trial comparison and endpoint-focused questions.

### `protocolSection.eligibilityModule`

Use for:

- full eligibility criteria
- `sex`
- `minimum_age`
- `maximum_age`
- `std_ages`
- `healthy_volunteers`

Why it matters:

- Eligibility is one of the highest-value narrative sections for users.
- We should preserve both the raw criteria blob and parsed helper fields.

### `protocolSection.contactsLocationsModule`

Use for:

- site locations
- countries
- states
- facility names
- site statuses

Why it matters:

- Geography is a first-class filter and a common answer citation target.

## MVP normalized field mapping

This is the initial raw-to-normalized mapping for the first ETL pass.

| Normalized field | Primary source path | Notes |
| --- | --- | --- |
| `nct_id` | `protocolSection.identificationModule.nctId` | Required unique key |
| `brief_title` | `protocolSection.identificationModule.briefTitle` | Required display field |
| `official_title` | `protocolSection.identificationModule.officialTitle` | Nullable |
| `brief_summary` | `protocolSection.descriptionModule.briefSummary` | Preserve as source text |
| `detailed_description` | `protocolSection.descriptionModule.detailedDescription` | Nullable narrative field |
| `study_type` | `protocolSection.designModule.studyType` | Must be `INTERVENTIONAL` for MVP |
| `phases` | `protocolSection.designModule.phases` | Array; filter to phases 2 to 4 |
| `allocation` | `protocolSection.designModule.designInfo.allocation` | Nullable |
| `intervention_model` | `protocolSection.designModule.designInfo.interventionModel` | Nullable |
| `masking` | `protocolSection.designModule.designInfo.maskingInfo.masking` or equivalent design field | Enum shape may require defensive parsing |
| `primary_purpose` | `protocolSection.designModule.designInfo.primaryPurpose` | Nullable |
| `enrollment_count` | `protocolSection.designModule.enrollmentInfo.count` | Nullable |
| `enrollment_type` | `protocolSection.designModule.enrollmentInfo.type` | Estimated vs actual |
| `overall_status` | `protocolSection.statusModule.overallStatus` | Core filter field |
| `last_known_status` | `protocolSection.statusModule.lastKnownStatus` | Useful when current status is stale or unknown |
| `start_date` | `protocolSection.statusModule.startDateStruct.date` | Partial dates may need normalization |
| `primary_completion_date` | `protocolSection.statusModule.primaryCompletionDateStruct.date` | Partial dates may need normalization |
| `completion_date` | `protocolSection.statusModule.completionDateStruct.date` | Partial dates may need normalization |
| `study_first_posted_at` | `protocolSection.statusModule.studyFirstPostDateStruct.date` | Useful for source freshness |
| `results_first_posted_at` | `protocolSection.statusModule.resultsFirstPostDateStruct.date` | Nullable |
| `last_update_posted_at` | `protocolSection.statusModule.lastUpdatePostDateStruct.date` | Freshness signal |
| `lead_sponsor_name` | `protocolSection.sponsorCollaboratorsModule.leadSponsor.name` | Nullable but usually present |
| `lead_sponsor_class` | `protocolSection.sponsorCollaboratorsModule.leadSponsor.class` | Industry, NIH, other |
| `collaborator_names` | `protocolSection.sponsorCollaboratorsModule.collaborators[].name` | Array |
| `sex` | `protocolSection.eligibilityModule.sex` | Enum |
| `minimum_age_text` | `protocolSection.eligibilityModule.minimumAge` | Keep original text |
| `maximum_age_text` | `protocolSection.eligibilityModule.maximumAge` | Keep original text |
| `age_groups` | `protocolSection.eligibilityModule.stdAges[]` | Derived by source, useful directly |
| `healthy_volunteers` | `protocolSection.eligibilityModule.healthyVolunteers` | Boolean |
| `criteria_text` | `protocolSection.eligibilityModule.eligibilityCriteria` | Preserve full text |

## Child-table extraction

These arrays should become child records during normalization.

### Conditions

Source:

- `protocolSection.conditionsModule.conditions[]`
- `protocolSection.conditionsModule.keywords[]`

Output:

- `trial_conditions`
- `condition_labels`
- `keyword_labels`

Normalization notes:

- Build a terminology layer that maps synonymous source labels into a stable internal taxonomy.
- Example mappings will likely include `type 2 diabetes`, `t2dm`, and `diabetes mellitus type 2`.
- MASH terminology should preserve the source string and also map into a broader normalized bucket.

### Interventions

Source:

- `protocolSection.armsInterventionsModule.interventions[]`

Output:

- `trial_interventions`
- `intervention_labels`
- `drug_class_labels`

Normalization notes:

- Keep exact intervention names.
- Add a lightweight derived `drug_class` when the mapping is clear enough for retrieval.
- Examples: `GLP-1 receptor agonist`, `dual GIP/GLP-1 agonist`, `FGF21 analog`.

### Arms

Source:

- `protocolSection.armsInterventionsModule.armGroups[]`

Output:

- `trial_arms`

Normalization notes:

- Arms are useful for compare views and richer trial summaries.

### Outcomes

Source:

- `protocolSection.outcomesModule.primaryOutcomes[]`
- `protocolSection.outcomesModule.secondaryOutcomes[]`
- `protocolSection.outcomesModule.otherOutcomes[]`

Output:

- `trial_outcomes`

Normalization notes:

- Preserve the source measure text verbatim.
- Outcome summarization should happen later, not inside normalization.

### Locations

Source:

- `protocolSection.contactsLocationsModule.locations[]`

Output:

- `trial_locations`
- `country_codes`
- `has_us_sites`

Normalization notes:

- Store country and state exactly as provided.
- Derive helper fields for fast geographic filtering.

## What we should derive during normalization

These are not direct source fields, but they belong in the ETL because they stabilize retrieval and filtering.

### `is_2026_relevant`

Set to true if any of the following indicate 2026 relevance:

- recruiting or active status overlapping 2026
- primary completion in 2026
- study completion in 2026
- results first posted in 2026

### `relevance_reasons`

Array of explanation labels such as:

- `recruiting_in_2026`
- `active_in_2026`
- `primary_completion_in_2026`
- `completion_in_2026`
- `results_posted_in_2026`

### `source_url`

Construct as:

- `https://clinicaltrials.gov/study/{nct_id}`

### `has_us_sites`

True if any normalized location country is `United States`.

### `drug_class_labels`

Derived from interventions using a small local mapping file. This should be explicit and reviewable, not hidden in prompt logic.

## Parsing decisions

These are important design decisions for the normalizer.

### Preserve text before summarizing it

We should store:

- full eligibility criteria
- full brief summary
- full detailed description
- full outcome measure text

Reason:

- Retrieval and citation need the exact source text.
- Summaries belong in presentation or synthesis layers, not ingestion.

### Keep partial dates as text if needed

ClinicalTrials.gov uses partial dates in some fields.

Plan:

- store the original date string when present
- parse to a normalized date only when the source precision allows it
- avoid inventing a day value unless we make that derivation explicit

### Separate source fidelity from normalized helpers

Example:

- keep raw condition string: `Metabolic Dysfunction-Associated Steatotic Liver Disease (MASH) / Nonalcoholic Steatohepatitis (NASH) With Fibrosis`
- also derive normalized label: `mash`

This lets us retrieve precisely without losing broad filterability.

## What we are explicitly not doing in v1

- parsing inclusion and exclusion criteria into perfect structured rule objects
- ingesting full posted results tables
- building a sponsor knowledge graph
- using the LLM during ingestion
- inferring drug class when the intervention name is too ambiguous

## First implementation sequence

This should be the build order for the ingestion pipeline.

1. Fetch a small batch of raw records and save them unchanged
2. Define Pydantic models for the subset of fields we actually consume
3. Write a normalizer that maps one raw study record into one normalized trial record plus child tables
4. Add validation for required fields and rejected-study reasons
5. Add terminology normalization for conditions and drug classes
6. Add field-aware chunk generation

## Questions we should answer before coding the normalizer

1. Do we want to ingest by broad search query first, or by a condition-specific seed list?
2. Should `NAFLD`, `NASH`, `MASLD`, and `MASH` all enter the MVP corpus, or only records with explicit metabolic overlap?
3. Do we want to treat phase `NA` interventional device or behavioral trials as out of scope even if they match the disease area?

My recommendation:

- start broad enough to capture obesity, type 2 diabetes, and MASH terminology variants
- enforce `INTERVENTIONAL`
- keep only phase 2 to 4 in the first corpus
- reject ambiguous out-of-scope studies during normalization with a logged reason

## Official references

- ClinicalTrials.gov API: [data-api/api](https://clinicaltrials.gov/data-api/api)
- Study data structure: [data-api/about-api/study-data-structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure)
- Search areas: [data-api/about-api/search-areas](https://clinicaltrials.gov/data-api/about-api/search-areas)

Representative study pages:

- [NCT04881760](https://clinicaltrials.gov/study/NCT04881760)
- [NCT07282600](https://clinicaltrials.gov/study/NCT07282600)
- [NCT06318169](https://clinicaltrials.gov/study/NCT06318169)
- [NCT07303803](https://clinicaltrials.gov/study/NCT07303803)
