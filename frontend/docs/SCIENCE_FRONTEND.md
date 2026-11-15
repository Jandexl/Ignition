# Published comparisons and factorial readiness

After installation with the existing README instructions, run from the project root:

    python -m ignis_ml.science
    python -m unittest discover -s tests -v

The first command rebuilds outputs/scientific_comparisons.json from data/revision. Copy that JSON to the frontend's static data directory. For example:

    const response = await fetch('/data/scientific_comparisons.json');
    if (!response.ok) throw new Error('Scientific comparison data unavailable');
    const evidence = await response.json();
    const cases = evidence.comparison_cases;

Render one card per case. Each measurements array is ordered [baseline, comparison]. Label airflow in cm/s and oxygen in volume percent. Display difference_cm_s, percent_change relative to baseline, both length endpoints, source_locations, confounding_warning and the per-variable comparability rows. Use separate axes or a toggle for length and rate. Historical changes use rounded table inputs. The two width comparisons preserve reported lengths within each pair. Show short plateau and atmosphere/flight differences for I–IV.

Use table1_records as the eight-row published table. alternative_source_claims contains audit cross-references only. Preserve candidate and unresolved links and the units in each source. Missing BASS pyrolysis lengths are JSON null. For the factorial grid, read factorial_readiness.cells and historical_ids. A blank cell means no matching historical observation. Display the directional hypothesis as untested and the supplied reason with the grid. Keep the numerical NASA prediction disabled. The legacy synthetic predictor is accessed separately. The revised scientific source notes are in data/revision/Scientific_Methodology.md and Scientific_Lead_Decision.md.

## Future experiment analysis

Call ignis_ml.factorial.analyze_burns with a pandas DataFrame containing block_id, globally unique burn_id and specimen_id, width_cm, full_duct_height_cm, spread_cm_s, Boolean included, and exclusion_reason. Record excluded ignitions or censored endpoints explicitly. Keep one prespecified rate per included fresh specimen. controls_verified=True is a caller declaration based on actual protocol review. Review measured flow, atmosphere, common fit window and controls against the supplied methodology. Frames and analyst annotations belong within a burn.

For design='randomized_complete_blocks', each independent block contains every width/height combination. The estimator averages within each block and cell, subtracts deep from shallow for each width, then subtracts the narrow response from the wide response. The 95% t interval uses independent block contrasts. For design='randomized_height_sessions', block_id identifies an independent session randomized to one height with both widths randomized within session. Compute wide minus narrow per session, then shallow minus deep across sessions. The Welch interval uses between-session variance at each height. The implementation uses a pilot floor of three complete blocks or three sessions per height. Actual confirmatory sample size depends on pilot variance and the prespecified meaningful interaction.

Cell summaries report pooled burn counts, means and sample standard deviations. Contrasts weight blocks/sessions equally. Intervals assume representative independent blocks/sessions and reasonably regular contrast distributions; small pilots give fragile estimates. These intervals describe between-unit variability. Refit trajectories under the prespecified calibration, annotation and time-window sensitivity scenarios and rerun on each resulting burn table to assess measurement sensitivity. Historical source rows lack randomized experimental units and cannot be passed as a controlled experiment. Missing cells, failed inclusion requirements and unsupported designs return null estimates.
