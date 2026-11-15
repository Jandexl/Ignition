# Canonical data contract

Every scientific field needs a documented review. No identifier or target enters the predictor.

| Field | Meaning | Units | Role | Missing allowed | Leakage rule |
|---|---|---|---|---|---|
| observation_id | Unique measurement record, not evidence of independence | — | identifier | never | NEVER a predictor |
| investigation_id | Verified investigation identity; BASS and BASS-II stay distinct | — | metadata | never | NEVER a predictor |
| campaign_id | Verified campaign identifier | — | group | never | NEVER a predictor |
| run_id | Verified experimental run within investigation and campaign | — | group | never | NEVER a predictor |
| dependency_group_id | Globally unique cluster covering repeats and all related runs | — | group | never | NEVER a predictor |
| material | Reviewed canonical fuel specification, not a loose alias | — | input | never | Use only pre-outcome measurements; fit transformations inside each training fold |
| flow_direction | Concurrent or opposed relative to spread | — | input | never | Use only pre-outcome measurements; fit transformations inside each training fold |
| gravity_regime | Reviewed gravity regime, such as microgravity | — | domain | never | NEVER a predictor |
| combustion_regime | Reviewed outcome/regime definition such as steady_solid_spread | — | domain | never | NEVER a predictor |
| flow_velocity_cm_s | Nonnegative imposed flow speed magnitude | cm/s | input | never | Use only pre-outcome measurements; fit transformations inside each training fold |
| oxygen_percent | Oxygen mole/volume percentage, not mass percentage | % | input | never | Use only pre-outcome measurements; fit transformations inside each training fold |
| pressure_kpa | Absolute total gas pressure | kPa | input | never | Use only pre-outcome measurements; fit transformations inside each training fold |
| sample_width_cm | Verified transverse specimen width | cm | candidate input | if not selected | Use only pre-outcome measurements; fit transformations inside each training fold |
| sample_length_cm | Verified specimen length along spread | cm | candidate input | if not selected | Use only pre-outcome measurements; fit transformations inside each training fold |
| sample_thickness_mm | Verified fuel thickness | mm | candidate input | if not selected | Use only pre-outcome measurements; fit transformations inside each training fold |
| duct_height_cm | Verified confinement height with consistent definition | cm | candidate input | if not selected | Use only pre-outcome measurements; fit transformations inside each training fold |
| flame_spread_rate_cm_s | Measured flame-front displacement per elapsed time in the specified regime | cm/s | target | never | NEVER a predictor |
| outcome_type | Must be flame_spread_rate | — | metadata | never | NEVER a predictor |
| outcome_unit | Must be cm/s after explicit conversion | — | metadata | never | NEVER a predictor |
| measurement_status | verified_numeric, reviewed_digitized, or synthetic | — | metadata | never | NEVER a predictor |
| verification_status | verified or synthetic; unreviewed blocks modeling | — | metadata | never | NEVER a predictor |
| grouping_status | verified or synthetic; human review of dependency structure | — | metadata | never | NEVER a predictor |
| geometry_status | verified or synthetic when geometry is selected | — | metadata | if unused | NEVER a predictor |
| geometry_definition_id | Shared reviewed dimension-definition document | — | metadata | if unused | NEVER a predictor |
| source_id | Foreign key to source manifest | — | provenance | never | NEVER a predictor |
| source_location | Table, figure, file or extraction location | — | provenance | never | NEVER a predictor |
| review_id | External scientific audit/review document reference | — | provenance | never | NEVER a predictor |
| data_origin | experimental or synthetic; mixing is forbidden | — | metadata | never | NEVER a predictor |
