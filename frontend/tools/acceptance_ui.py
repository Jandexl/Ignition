#!/usr/bin/env python3
"""Browser acceptance test for 1gnition (handoff section 9 + the acceptance demo).

    python3 -m http.server 8765            # from the site folder, in another terminal
    python3 tools/acceptance_ui.py [--base http://localhost:8765] [--chrome /usr/bin/google-chrome]

Needs: pip install playwright (uses an installed Chrome via --chrome). Prints PASS/FAIL per check
and exits 1 on any failure.
"""
import argparse
import asyncio
import re
import sys

from playwright.async_api import async_playwright

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


async def text(pg, sel):
    return re.sub(r"\s+", " ", await pg.inner_text(sel))


async def main(base, chrome):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        pg.set_default_timeout(6000)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        U = lambda h="": f"{base}/index.html{('#' + h) if h else ''}"

        # --- acceptance demo: open 1gnition, Compare Runs, I-1 vs II-5
        await pg.goto(U("compare")); await pg.wait_for_timeout(1200)
        t = await text(pg, "#cmpOlson")
        check("Compare: default pair is I-1 vs II-5", "I-1 → II-5" in t and await pg.get_attribute("#cmpOlson [data-case='0']", "aria-pressed") == "true")
        check("Compare: both flame lengths 4 cm", "4 → 4 cm" in t)
        check("Compare: rates 0.18 and 0.21 cm/s", "0.18 cm/s" in t and "0.21 cm/s" in t)
        check("Compare: +0.03 cm/s and +16.67% of I-1", "+0.03 cm/s" in t and "+16.67%" in t and "Change from I-1" in t)
        check("Compare: width, length, O2 and flight listed as changed", all(k in t for k in ["Sample width", "Sample length", "Oxygen", "Flight"]))
        check("Compare: conflicts column present", "Conflicting" in t)
        check("Compare: warning says causal effect not isolated", "causal effect not isolated" in t)
        await pg.click("#cmpOlson [data-case='1']"); await pg.wait_for_timeout(300)
        t = await text(pg, "#cmpOlson")
        check("Compare: III-1 vs II-6 shows +13.04% and 5 cm lengths", "+13.04%" in t and "5 → 5 cm" in t)
        check("Compare: II-6/III airflow conflict flagged", "PSI-99" in t or "PSI-100" in t)
        await pg.click("#cmpOlson [data-case='2']"); await pg.wait_for_timeout(300)
        t = await text(pg, "#cmpOlson")
        check("Compare: I-1 vs IV-SIBAL shows +100% and 4 vs 8.5 cm", "+100%" in t and "4 → 8.5 cm" in t)
        check("Compare: I-1 vs IV credits no single cause", "can't be credited to duct height alone" in t)
        await pg.click("#cmpOlson [data-metric='rate']"); await pg.wait_for_timeout(200)
        t = await text(pg, "#cmpOlson .sci-metrics")
        check("Compare: rate toggle hides the length panel", "Flame-spread rate, cm/s" in t and "Flame length, cm" not in t)
        await pg.click("#cmpOlson [data-metric='length']"); await pg.wait_for_timeout(200)
        t = await text(pg, "#cmpOlson .sci-metrics")
        check("Compare: length toggle hides the rate panel", "Flame length, cm" in t and "Flame-spread rate, cm/s" not in t)
        check("Compare: Urban grid labelled steady flame size", "Steady flame size" in await text(pg, "#gridCard"))
        await pg.click("#cmpOlson [data-metric='both']")

        # --- Scale Transfer Lab: NASA prediction disabled
        await pg.goto(U("transfer")); await pg.wait_for_timeout(900)
        await pg.click("[data-step='predict']"); await pg.wait_for_timeout(300)
        t = await text(pg, "#predCard")
        check("Transfer: VALIDATION_NOT_SUPPORTED shown", "VALIDATION_NOT_SUPPORTED" in t)
        check("Transfer: predicted rate is 'none', not 0", "Predicted rate none" in t)
        # synthetic mode
        await pg.click("[data-step='synthetic']"); await pg.wait_for_timeout(300)
        t = await text(pg, "#pane-synthetic")
        check("Synthetic: banner says NOT NASA DATA", "SYNTHETIC VERIFICATION — NOT NASA DATA" in t and "NOT PHYSICAL VALIDATION" in t)
        for i, (name, want, zero) in enumerate([("positive", "+0.0800", "no"), ("zero", "+0.0000", "yes"), ("negative", "−0.0800", "no"), ("height sessions", "+0.0800", "no")]):
            await pg.click(f"[data-syn='{i}']"); await pg.wait_for_timeout(250)
            t = await text(pg, "#synCard")
            check(f"Synthetic {name}: programmed {want}, interval contains 0 = {zero}", f"Programmed Δ {want} cm/s" in t and f"Interval contains 0 {zero}" in t, t[:200])
        t = await text(pg, "#pane-synthetic")
        check("Synthetic: 4 invalid designs refused with null", t.count("ANALYSIS_NOT_SUPPORTED") == 4 and "Interaction: null" in t)
        check("Synthetic: benchmark labelled not NASA accuracy", "NOT NASA ACCURACY" in t)
        # proposed test
        await pg.click("[data-step='design']"); await pg.wait_for_timeout(300)
        t = await text(pg, "#pane-design")
        check("Design: missing narrow/shallow cell shown", "No matching historical Saffire configuration" in t and "5 cm wide in a 30.5 cm" in t)
        check("Design: historical cells flagged confounded", t.lower().count("confounded analog") == 3)
        check("Design: hypothesis UNTESTED, interaction none", "UNTESTED" in t and "Interaction estimate none" in t)
        check("Design: log-linear model marked not fitted", "not fitted" in t)

        # --- Research gaps
        await pg.goto(U("gaps")); await pg.wait_for_timeout(900)
        t = await text(pg, "#gapTypes")
        check("Gaps: six gap types", all(k in t for k in ["Missing experiment configuration", "Missing run identity", "Missing atmosphere", "Source conflicts", "Insufficient independent replication", "Out-of-domain scenario"]))
        check("Gaps: 2x2 design with missing analog", "No matching historical Saffire configuration" in t)
        check("Gaps: map labelled as the team's indexed dataset", "team's indexed dataset" in await text(pg, "#mapCard"))

        # --- click a source
        await pg.goto(U("transfer")); await pg.wait_for_timeout(900)
        await pg.click("[data-step='compare']"); await pg.wait_for_timeout(200)
        await pg.click("#sciMetric .pv >> nth=0"); await pg.wait_for_timeout(300)
        href = await pg.get_attribute("#pop a", "href")
        check("Source: popover links to Olson 2023 manuscript", href and "discovery.ucl.ac.uk" in href, str(href))
        await pg.keyboard.press("Escape")
        await pg.click(".term >> nth=0"); await pg.wait_for_timeout(200)
        check("Glossary: a term opens its definition", "Term" in await text(pg, "#pop"))
        await pg.keyboard.press("Escape")

        # --- Data view
        await pg.goto(U("data")); await pg.wait_for_timeout(900)
        counts = await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#dataTabs [data-tab]')].map(b=>[b.dataset.tab,+b.querySelector('.c').textContent]))")
        check("Data: tabs Table 1 = 8, Figure 10 = 23, PSI-99 = 2, synthetic = 4",
              counts.get("table1") == 8 and counts.get("figure10") == 23 and counts.get("psi99") == 2 and counts.get("synthetic") == 4, str(counts))
        await pg.click("[data-tab='synthetic']"); await pg.wait_for_timeout(200)
        check("Data: synthetic tab labelled not NASA", "NOT NASA DATA" in await text(pg, "#dataCls"))

        # --- scenario controls change downstream output
        await pg.goto(U("evidence")); await pg.wait_for_timeout(900)
        before = await text(pg, "#invList")
        await pg.click('#presetSeg [data-preset="iss"]'); await pg.wait_for_timeout(600)
        after = await text(pg, "#invList")
        check("Scenario: switching habitat changes the evidence ranking", before != after)
        await pg.select_option("#fDir", "opposed"); await pg.wait_for_timeout(400)
        await pg.goto(U("gaps")); await pg.wait_for_timeout(600)
        check("Scenario: flow direction feeds applicability", "flow direction" in (await text(pg, ".gt-dom")).lower())

        # --- whole-site text hygiene
        bad = []
        for h in ["overview", "evidence", "compare", "transfer", "gaps", "data"]:
            await pg.goto(U(h)); await pg.wait_for_timeout(700)
            body = await pg.evaluate("document.body.innerText")
            for w in ["NaN", "undefined", "IGNIS", "[object Object]"]:
                if re.search(r"\b" + re.escape(w) + r"\b", body):
                    bad.append(f"{h}:{w}")
        check("No NaN/undefined/IGNIS/[object Object] in any view", not bad, ", ".join(bad))

        # --- phones
        m = await b.new_page(viewport={"width": 390, "height": 844})
        wide = []
        for h in ["overview", "evidence", "compare", "transfer", "gaps", "data"]:
            await m.goto(U(h)); await m.wait_for_timeout(700)
            w = await m.evaluate("document.documentElement.scrollWidth")
            if w > 390:
                wide.append(f"{h}={w}")
        check("Phone 390 px: no horizontal overflow", not wide, ", ".join(wide))

        # --- science JSON unavailable: no crash, explicit message
        f = await b.new_page(viewport={"width": 1440, "height": 900})
        ferrs = []
        f.on("pageerror", lambda e: ferrs.append(str(e)))
        await f.route("**/data/scientific_comparisons.json", lambda r: r.fulfill(status=404, body="missing"))
        await f.goto(U("transfer")); await f.wait_for_timeout(1500)
        body = await f.evaluate("document.body.innerText")
        check("Missing science JSON: site still loads without page errors", not ferrs, "; ".join(ferrs))
        check("Missing science JSON: the gap is stated, nothing invented", "unavailable" in body.lower() or "fallback" in body.lower() or "Table 1" in body)

        check("No console or page errors during the run", not errs, "; ".join(errs[:3]))
        await b.close()
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\n{len(RESULTS) - n_fail} of {len(RESULTS)} UI acceptance checks passed")
    return n_fail


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8765")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    a = ap.parse_args()
    sys.exit(1 if asyncio.run(main(a.base, a.chrome)) else 0)
