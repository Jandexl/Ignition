#!/usr/bin/env python3
"""Runs the science team's 8 final UI QA cases (research/closeout_kit/data/final_ui_qa_cases.json)
against a running copy of the site, saves a screenshot per case and a JSON + text log.

    (cd frontend && python3 -m http.server 8765 &)
    python3 frontend/tools/final_ui_qa.py --base http://localhost:8765 --out qa/
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent


def norm(s):
    return re.sub(r"\s+", " ", s)


async def run(base, out, chrome):
    out.mkdir(parents=True, exist_ok=True)
    cases = json.loads((HERE.parents[1] / "research" / "closeout_kit" / "data" / "final_ui_qa_cases.json").read_text())["cases"]
    titles = {c["id"]: c["title"] for c in cases}
    results = []

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        pg.set_default_timeout(6000)
        errs, failed_req = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("response", lambda r: failed_req.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        U = lambda h="": f"{base}/index.html{('#' + h) if h else ''}"

        def rec(cid, checks, shot):
            ok = all(v for _, v in checks)
            results.append(dict(id=cid, title=titles[cid], passed=ok, checks=[dict(check=k, passed=bool(v)) for k, v in checks], screenshot=shot))
            print(("PASS " if ok else "FAIL ") + f"{cid} {titles[cid]}")
            for k, v in checks:
                if not v:
                    print("     failed:", k)

        # QA01
        await pg.goto(U("compare")); await pg.wait_for_timeout(1200)
        await pg.click("#cmpOlson [data-case='0']"); await pg.click("#cmpOlson [data-metric='length']"); await pg.wait_for_timeout(250)
        L = norm(await pg.inner_text("#cmpOlson .sci-metrics"))
        await pg.click("#cmpOlson [data-metric='rate']"); await pg.wait_for_timeout(250)
        R = norm(await pg.inner_text("#cmpOlson .sci-metrics")); T = norm(await pg.inner_text("#cmpOlson"))
        await pg.locator("#cmpOlson").screenshot(path=str(out / "QA01.png"))
        rec("QA01", [("flame length 4 vs 4 cm", "4 → 4 cm" in L), ("spread 0.18 vs 0.21 cm/s", "0.18 cm/s" in R and "0.21 cm/s" in R),
                     ("+0.03 cm/s, +16.67%", "+0.03 cm/s" in R and "+16.67%" in R), ("confounding warning", "causal effect not isolated" in T),
                     ("Olson source shown", "Olson et al. (2023)" in T or "Table 1, PDF p9" in T)], "QA01.png")
        # QA02
        await pg.click("#cmpOlson [data-case='1']"); await pg.click("#cmpOlson [data-metric='both']"); await pg.wait_for_timeout(300)
        T = norm(await pg.inner_text("#cmpOlson"))
        await pg.locator("#cmpOlson").screenshot(path=str(out / "QA02.png"))
        rec("QA02", [("flame length 5 vs 5 cm", "5 → 5 cm" in T), ("spread 0.23 vs 0.26", "0.23 cm/s" in T and "0.26 cm/s" in T),
                     ("+0.03, +13.04%", "+0.03 cm/s" in T and "+13.04%" in T), ("PSI-100 airflow conflict visible", "PSI-100" in T and "30 cm/s" in T)], "QA02.png")
        # QA03
        await pg.click("#cmpOlson [data-case='2']"); await pg.wait_for_timeout(300)
        T = norm(await pg.inner_text("#cmpOlson"))
        await pg.locator("#cmpOlson").screenshot(path=str(out / "QA03.png"))
        rec("QA03", [("0.18 vs 0.36 cm/s, +100%", "0.18 cm/s" in T and "0.36 cm/s" in T and "+100%" in T),
                     ("duct 51 vs 30.5 cm", "51 cm · 30.5 cm" in T), ("oxygen 21.7 vs 23.1", "21.7 vol % · 23.1 vol %" in T),
                     ("no claim duct alone caused it", "can't be credited to duct height alone" in T and "causal effect not isolated" in T)], "QA03.png")
        # QA04
        for view, sel, shot in [("gaps", "#gapFactCard", "QA04_gaps.png"), ("transfer", "#factCard", "QA04_transfer.png")]:
            await pg.goto(U(view)); await pg.wait_for_timeout(900)
            if view == "transfer":
                await pg.click("[data-step='design']"); await pg.wait_for_timeout(300)
            await pg.locator(sel).screenshot(path=str(out / shot))
        T = norm(await pg.inner_text("#pane-design"))
        rec("QA04", [("narrow 5 cm x shallow 30.5 cm missing", "5 cm wide in a 30.5 cm" in T and "No matching historical Saffire configuration" in T),
                     ("existing cells are historical analogs", T.lower().count("confounded analog") == 3 and "not a completed factorial experiment" in T),
                     ("interaction estimate null", "Interaction estimate none" in T and "95% interval none" in T)], "QA04_transfer.png")
        # QA05
        await pg.goto(U("compare")); await pg.wait_for_timeout(900)
        await pg.click("#cmpOlson [data-case='1']"); await pg.wait_for_timeout(300)
        C = norm(await pg.inner_text("#cmpCond .cond-col.cfl"))
        loaded = await pg.evaluate("!!(IGNIS_DATA.source_conflicts && IGNIS_DATA.source_conflicts.conflicts.length === 2)")
        js = await (await pg.request.get(f"{base}/js/app.js")).text()
        await pg.locator("#cmpCond .cond-col.cfl").screenshot(path=str(out / "QA05.png"))
        rec("QA05", [("Olson 25 cm/s shown", "25 cm/s for III-1" in C), ("PSI-100 candidate S1 30 cm/s shown", "30 cm/s for S1" in C),
                     ("both claims separate, unresolved", "UNRESOLVED" in C.upper()), ("source_conflicts.json loaded", loaded),
                     ("no hard-coded value in app.js", "30 cm/s for Saffire" not in js and "KNOWN_CONFLICTS" not in js)], "QA05.png")
        # QA06
        await pg.click("#cmpOlson [data-case='2']"); await pg.wait_for_timeout(300)
        C = norm(await pg.inner_text("#cmpCond .cond-col.cfl"))
        await pg.locator("#cmpCond .cond-col.cfl").screenshot(path=str(out / "QA06.png"))
        await pg.goto(U("data")); await pg.wait_for_timeout(700); await pg.click("[data-tab='conflicts']"); await pg.wait_for_timeout(300)
        Dt = norm(await pg.inner_text("#dataTable"))
        await pg.screenshot(path=str(out / "QA06_data_tab.png"))
        rec("QA06", [("probable, not confirmed", "PROBABLE, NOT CONFIRMED" in C.upper()), ("table 0.36 and digitized ~0.368 shown separately", "0.36 cm/s (table)" in C and "≈0.368 cm/s (digitized)" in C),
                     ("not counted as a separate run", "Not counted as a separate run" in C), ("conflict listed on Data page", "probable_not_confirmed" in Dt)], "QA06.png")
        # QA07
        await pg.goto(U("transfer")); await pg.wait_for_timeout(900)
        await pg.click("[data-step='predict']"); await pg.wait_for_timeout(300)
        P = norm(await pg.inner_text("#predCard"))
        await pg.locator("#predCard").screenshot(path=str(out / "QA07_prediction.png"))
        await pg.click("[data-step='synthetic']"); await pg.wait_for_timeout(300)
        Sy = norm(await pg.inner_text("#pane-synthetic"))
        await pg.locator("#pane-synthetic").screenshot(path=str(out / "QA07_synthetic.png"))
        pred_null = await pg.evaluate("IGNIS_DATA.scientific_comparisons.prediction_status === 'VALIDATION_NOT_SUPPORTED' && IGNIS_DATA.scientific_comparisons.prediction_cm_s === null")
        rec("QA07", [("VALIDATION_NOT_SUPPORTED shown", "VALIDATION_NOT_SUPPORTED" in P), ("predicted rate none", "Predicted rate none" in P), ("data prediction_cm_s null", pred_null),
                     ("synthetic labelled not NASA", "SYNTHETIC VERIFICATION — NOT NASA DATA" in Sy and "NOT NASA ACCURACY" in Sy)], "QA07_prediction.png")
        # QA08
        await pg.goto(U()); await pg.wait_for_timeout(1800)
        H = norm(await pg.inner_text(".hx-copy h1"))
        await pg.screenshot(path=str(out / "QA08_hero.png"))
        await pg.click("#askBtn"); await pg.wait_for_timeout(2500)   # lets the panel learn whether the AI backend is on
        A = norm(await pg.inner_text("#drawer"))
        await pg.screenshot(path=str(out / "QA08_ask.png"))
        await pg.keyboard.press("Escape")
        views_ok = []
        for v in ["overview", "evidence", "compare", "transfer", "gaps", "data"]:
            await pg.goto(U(v)); await pg.reload(); await pg.wait_for_timeout(900)
            views_ok.append(await pg.evaluate(f"!document.getElementById('v-{v}').hidden && getComputedStyle(document.getElementById('v-{v}')).display !== 'none'"))
        origin = await pg.evaluate("IGNIS_DATA.origin")
        rec("QA08", [("hero ZERO GUESSING. / ZERO HIDDEN UNCERTAINTY. / 1gnition", H.startswith("ZERO GUESSING. ZERO HIDDEN UNCERTAINTY. 1gnition") or H.replace("\n", " ").startswith("ZERO GUESSING.ZERO HIDDEN UNCERTAINTY.1gnition") or ("ZERO GUESSING." in H and "ZERO HIDDEN UNCERTAINTY." in H and H.strip().endswith("1gnition"))),
                     ("Ask discloses what it is: AI-generated (Gemini, check sources) or offline rule-based",
                      ("AI · GOOGLE GEMINI" in A.upper() and "AI-generated answers" in A and "check the cited sources" in A)
                      or ("offline rule-based evidence helper, not a generative AI assistant" in A)),
                     ("all views load after refresh/deep link", all(views_ok)), ("data from static JSON, not an API", origin == "the project data files"),
                     ("no failed requests", not failed_req), ("no console or page errors", not errs)], "QA08_hero.png")
        await b.close()

    n = sum(r["passed"] for r in results)
    log = dict(base=base, passed=n, total=len(results), results=results, failed_requests=failed_req, errors=errs)
    (out / "final_ui_qa_results.json").write_text(json.dumps(log, indent=2))
    print(f"\n{n} of {len(results)} final UI QA cases passed")
    return n == len(results)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8765")
    ap.add_argument("--out", default="qa")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    a = ap.parse_args()
    sys.exit(0 if asyncio.run(run(a.base.rstrip("/"), Path(a.out), a.chrome)) else 1)
