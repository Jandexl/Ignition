"""Portable JSON schemas; prediction function also validates request shape."""
from .schema import CONDITIONS, GEOMETRY, CATEGORIES

REQUEST_SCHEMA = {
 '$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
 'additionalProperties': False,
 'required': list(CONDITIONS + CATEGORIES),
 'properties': {**{c: {'type': 'number', 'minimum': 0} for c in CONDITIONS + GEOMETRY},
                **{c: {'type': 'string', 'minLength': 1} for c in CATEGORIES},
                'geometry_status': {'enum': ['verified', 'synthetic', 'unreviewed']},
                'geometry_definition_id': {'type': 'string', 'minLength': 1}}}
REQUEST_SCHEMA['properties']['oxygen_percent']['maximum'] = 100
for c in GEOMETRY + ('pressure_kpa',):
    REQUEST_SCHEMA['properties'][c] = {'type': 'number', 'exclusiveMinimum': 0}
REQUEST_SCHEMA['properties']['flow_direction'] = {'enum': ['concurrent', 'opposed']}

RESPONSE_SCHEMA = {
 '$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object', 'additionalProperties': False,
 'properties': {
   'status': {'enum': ['SUPPORTED', 'LIMITED_EVIDENCE', 'UNSUPPORTED']},
   'predicted_flame_spread_rate_cm_s': {'type': ['number', 'null'], 'minimum': 0},
   'prediction_units': {'const': 'cm/s'}, 'model_version': {'type': 'string'},
   'model_type': {'enum': [None, 'mean', 'condition_ridge', 'geometry_ridge']},
   'inputs_used': {'type': 'object'}, 'validation_status': {'enum': ['VALIDATION_NOT_SUPPORTED', 'SYNTHETIC_DEMO_ONLY', 'REVIEWED_GROUPED_EVALUATION']},
   'model_performance': {'type': ['object', 'null']},
   **{k: {'type': 'array', 'items': {'type': 'string'}} for k in ['source_ids', 'evidence_limitations', 'out_of_domain_warnings', 'abstention_reasons']},
   'synthetic': {'type': 'boolean'}, 'intended_use': {'const': 'research_demonstration_only'}},
 'allOf': [
   {'if': {'properties': {'status': {'const': 'SUPPORTED'}}},
    'then': {'properties': {'predicted_flame_spread_rate_cm_s': {'type': 'number', 'minimum': 0},
                            'validation_status': {'enum': ['SYNTHETIC_DEMO_ONLY', 'REVIEWED_GROUPED_EVALUATION']},
                            'abstention_reasons': {'maxItems': 0}}},
    'else': {'properties': {'predicted_flame_spread_rate_cm_s': {'type': 'null'}, 'abstention_reasons': {'minItems': 1}}}},
   {'if': {'properties': {'validation_status': {'const': 'SYNTHETIC_DEMO_ONLY'}}},
    'then': {'properties': {'synthetic': {'const': True}}}}]}
RESPONSE_SCHEMA['required'] = list(RESPONSE_SCHEMA['properties'])
