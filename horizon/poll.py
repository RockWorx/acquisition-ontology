"""POLL stage -- fetch each legislative instrument's REAL status from the Congress.gov API and derive
its legislative-maturity rung straight from that status (never guessed).

Congress.gov: https://api.congress.gov/v3 ; DATAGOV_API_KEY ; a Mozilla User-Agent is required
(Cloudflare 403s the default urllib UA). Results are cached to JSON so the demo + tests run offline
and reproducibly; pass live=True to re-fetch.
"""
import json
import os
import urllib.error
import urllib.request

BASE = "https://api.congress.gov/v3"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RockWorx-SKEDS-horizon/1.0"

# The legislative-maturity ladder (also the controlled vocabulary in rwx-acq-horizon).
MATURITY_LADDER = ["proposed", "introduced", "reported", "passed-one-chamber", "in-conference", "enacted"]


def _get(path, key, **params):
    params["api_key"] = key
    params.setdefault("format", "json")
    q = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{BASE}{path}?{q}", headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def derive_maturity(bill, actions):
    """Map a Congress.gov bill record + its actions to a legislative-maturity rung. The status is
    taken from the source; this only classifies it onto the ladder."""
    if bill.get("laws"):
        return "enacted"
    texts = [a.get("text", "") for a in actions]
    joined = " || ".join(texts)
    if "Became Public Law" in joined:
        return "enacted"
    passed_house = any("Passed" in t and "House" in t for t in texts) or "On passage Passed" in joined
    passed_senate = any(("Passed Senate" in t) or ("Passed/agreed to in Senate" in t) for t in texts)
    if passed_house and passed_senate:
        return "in-conference"
    if passed_house or passed_senate:
        return "passed-one-chamber"
    if any(("Reported" in t) or ("Placed on" in t and "Calendar" in t) or ("committee report" in t.lower())
           for t in texts):
        return "reported"
    if any(("Introduced" in t) or ("Referred to" in t) for t in texts):
        return "introduced"
    return "proposed"


def poll(instruments, cache_path, live=False):
    """Return {instrument_id: {label, congress, type, number, maturity, latest_action, laws}}.
    live=True fetches from Congress.gov (and rewrites the cache); live=False reads the cache."""
    if not live and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            return json.load(fh)

    key = os.environ.get("DATAGOV_API_KEY") or os.environ.get("DATA_GOV_API_KEY")
    if not key:
        raise RuntimeError("live poll needs DATAGOV_API_KEY in the environment")

    out = {}
    for iid, spec in instruments.items():
        rec = {"label": spec["label"], "congress": spec.get("congress"),
               "type": spec.get("type"), "number": spec.get("number"), "cycle": spec.get("cycle")}
        if spec.get("maturity_override") or not spec.get("number"):
            rec["maturity"] = spec.get("maturity_override", "reported")
            rec["latest_action"] = spec.get("note", "(no floor vehicle; committee status)")
            rec["laws"] = None
        else:
            c, t, n = spec["congress"], spec["type"], spec["number"]
            bill = _get(f"/bill/{c}/{t}/{n}", key).get("bill", {})
            actions = _get(f"/bill/{c}/{t}/{n}/actions", key, limit=250).get("actions", [])
            rec["maturity"] = derive_maturity(bill, actions)
            la = bill.get("latestAction", {})
            rec["latest_action"] = f"{la.get('actionDate','')} - {la.get('text','')}"
            rec["laws"] = bill.get("laws")
        out[iid] = rec

    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return out
