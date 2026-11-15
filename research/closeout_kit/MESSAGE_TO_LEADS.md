# Message to Frontend + Backend Leads — final decision

**Science is finished for submission.** The Scientific Lead's dated decision and methodology already verify eight Olson Table 1 records, the three Saffire comparisons, the physics interpretation and the proposed factorial study. Please correct the handoff status: only **final website wording/source-claim QA** is unverified, not the underlying scientific research. We do **not** need to redo science or run new microgravity experiments to ship.

**Required P0 changes:**

1. Change the hero to exactly:

   **ZERO GUESSING.**

   **ZERO HIDDEN UNCERTAINTY.**

   **1gnition**

   Smaller tagline: *Know What the Evidence Supports.*

   Keep factual disclaimers in the methodology: inference has assumptions, missing evidence and possible errors. Those two lines are branding, not proof of literally zero uncertainty.

2. Move the hard-coded PSI-100 30 vs 25 cm/s airflow claims and the probable IV-SIBAL ↔ IV-1 source crosswalk into **data files**. I attached a ready-to-ingest `data/source_conflicts.json`. Display both original claims, citations and unknown resolution; mark the IV mapping probable, never confirmed or double-counted.

3. The API does **not** have to be publicly hosted if the complete UI works from canonical generated static JSON. If any UI feature still requires a runtime API, deploy that endpoint and verify the live health/data paths before shipping. Please share the actual public URLs and test results; having a local start command alone does not count as public deployment.

4. "Ask 1gnition" can stay a rule-based helper. Clearly state so. Do not delay submission to add generative AI, and do not market the helper as a trained AI chatbot.

5. Preserve published NASA numbers and `prediction_status: VALIDATION_NOT_SUPPORTED`, `prediction_cm_s: null`. Keep synthetic ML tests and preliminary PMMA benchmarks explicitly separate from measured Saffire evidence. Never show unsupported predictive numeric results as NASA-validated.

6. Run the 8 specific browser QA cases in `data/final_ui_qa_cases.json`, record pass/fail + screenshot where appropriate, and have the Scientific Lead/QA quickly check **only new scientific text and conflict rendering**. This is implementation QA, not redoing the science. Fix failures before launch.

7. Deploy the latest actual website (not the archived site), check the full scenario → compare → evidence → scale transfer → research gaps journey, and record a **6–7 second screen capture** for the 30-second presentation video. Send the URL, release commit, latest test log and any known limits.

**Definition of done:** (a) no unsupported scientific predictions; (b) comparisons and conflicts traceable to sources; (c) all 8 UI QA cases passed; (d) no dead API/data dependencies; (e) working public URL; (f) actual demo footage; (g) final brand copy. 

The attached kit gives you the science-status record, authoritative numeric JSON, source conflict data, branding JSON, eight QA cases and an automatic consistency checker. Please integrate it into your **latest** codebase rather than restarting the project.
