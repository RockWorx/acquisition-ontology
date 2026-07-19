"""DISCOVERY + scheduled poll -- auto-find acquisition-relevant bills and detect status changes.

Congress.gov has no free-text search (the q= param is silently ignored), so discovery combines:
  1. a WATCHLIST of known defense-acquisition-reform bills (pending items the poll tracks), and
  2. enumeration of recent enacted PUBLIC LAWS (/law/{congress}/pub), filtered by acquisition/defense
     title keywords -- this is how a NEW acquisition-relevant law gets picked up automatically.

The scheduled poll re-checks each discovered bill's maturity and reports what CHANGED since the last run
(new bills, or a bill that advanced a rung). Reuses the federal-poller pattern (cache-diff, single pass);
wire to Task Scheduler the same way the other pollers are (register_scheduled_tasks.ps1).

    python -m horizon.discover                       # discover + report changes vs last run
"""
import json
import os
import sys
import urllib.request

from .poll import derive_maturity

BASE = "https://api.congress.gov/v3"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RockWorx-SKEDS-horizon/1.0"
_ACQ_KEYWORDS = ("national defense authorization", "defense appropriations", "acquisition", "procurement")
# Bounded "recent" window: enumerate the N most-recent enacted public laws (NOT the full Congress).
# A scheduled poll runs often, so recent laws suffice; raise to widen the discovery window (Red Team F8).
LAW_SCAN_LIMIT = 50

# Known defense-acquisition-reform bills the horizon layer tracks (the pending watchlist).
WATCHLIST = [
    {"congress": 119, "type": "hr", "number": 3838, "label": "H.R. 3838 -- SPEED Act / House FY26 NDAA"},
    {"congress": 119, "type": "s", "number": 1071, "label": "S. 1071 -- FY26 NDAA (PL 119-60)"},
    {"congress": 119, "type": "hr", "number": 8800, "label": "H.R. 8800 -- House FY27 NDAA"},
    {"congress": 119, "type": "s", "number": 4784, "label": "S. 4784 -- Senate FY27 NDAA"},
]

HERE = os.path.dirname(__file__)
STATE_CACHE = os.path.join(HERE, "demo", "poll_state.json")


def _get(path, key, **params):
    params["api_key"] = key
    params.setdefault("format", "json")
    q = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{BASE}{path}?{q}", headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def discover(congress=119, watchlist=None, key=None):
    """Return acquisition-relevant bill specs = the watchlist + title-filtered recent public laws."""
    key = key or os.environ.get("DATAGOV_API_KEY")
    wl = WATCHLIST if watchlist is None else watchlist          # [] means "enumeration only"
    bills = {(b["type"], b["number"]): dict(b, discovered_via="watchlist") for b in wl}
    for law in _get(f"/law/{congress}/pub", key, limit=LAW_SCAN_LIMIT).get("bills", []):
        title = (law.get("title") or "").lower()
        if any(kw in title for kw in _ACQ_KEYWORDS):
            k = (law.get("type", "").lower(), int(law.get("number", 0)))
            if k[1] and k not in bills:
                bills[k] = {"congress": congress, "type": k[0], "number": k[1],
                            "label": (law.get("title") or "")[:80], "discovered_via": "public-law enumeration"}
    return list(bills.values())


def _poll_maturity(b, key):
    bill = _get(f"/bill/{b['congress']}/{b['type']}/{b['number']}", key).get("bill", {})
    actions = _get(f"/bill/{b['congress']}/{b['type']}/{b['number']}/actions", key, limit=250).get("actions", [])
    return derive_maturity(bill, actions)


def scheduled_poll(state_cache=STATE_CACHE, key=None):
    """Discover acquisition bills, poll each maturity, and return (discovered, changes) where changes are
    the new bills / rung-advances since the last run. Persists the new state."""
    key = key or os.environ.get("DATAGOV_API_KEY")
    discovered = discover(key=key)
    prev = json.load(open(state_cache, encoding="utf-8")) if os.path.exists(state_cache) else {}
    now, changes = {}, []
    for b in discovered:
        bid = f"{b['type']}{b['number']}_{b['congress']}"
        maturity = _poll_maturity(b, key)
        now[bid] = maturity
        if bid not in prev:
            changes.append({"bill": b["label"], "event": "NEW", "to": maturity, "via": b["discovered_via"]})
        elif prev[bid] != maturity:
            changes.append({"bill": b["label"], "event": "ADVANCED", "from": prev[bid], "to": maturity})
    with open(state_cache, "w", encoding="utf-8") as fh:
        json.dump(now, fh, indent=2)
    return discovered, changes


def main(argv=None):
    discovered, changes = scheduled_poll()
    print("=" * 84)
    print("SKEDS horizon -- scheduled acquisition-bill discovery + change poll")
    print("=" * 84)
    print(f"\nDISCOVERED {len(discovered)} acquisition-relevant bills:")
    for b in discovered:
        print(f"  [{b['discovered_via']:>24}]  {b['label']}")
    print(f"\nCHANGES since last run: {len(changes)}")
    for c in changes:
        if c["event"] == "NEW":
            print(f"  + NEW      {c['bill']}  (maturity={c['to']}, via {c['via']})")
        else:
            print(f"  ^ ADVANCED {c['bill']}  ({c['from']} -> {c['to']})")
    if not changes:
        print("  (none -- all tracked bills at their previously-seen maturity)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
