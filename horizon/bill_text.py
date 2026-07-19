"""FULL-TEXT ingestion -- fetch a bill's REAL text from Congress.gov and extract its acquisition-title
sections as provision records the SHRED can consume. Promotes a bill from "tracked" (status only) to
candidates grounded in its actual statutory language.

The raw bill text (an NDAA runs ~2.5 MB) is cached under demo/.fulltext/ (gitignored, regenerated on
--live). The small EXTRACTED provision records are cached to demo/<id>_provisions.json (committed) so the
offline demo + tests reproduce without re-fetching megabytes.
"""
import json
import os
import re
import urllib.request

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RockWorx-SKEDS-horizon/1.0"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def fetch_bill_text(congress, btype, num, raw_dir):
    """Fetch the latest Formatted-Text version of a bill; cache the raw text under raw_dir."""
    os.makedirs(raw_dir, exist_ok=True)
    cache = os.path.join(raw_dir, f"{btype}{num}_{congress}.txt")
    if os.path.exists(cache):
        return open(cache, encoding="utf-8").read()
    key = os.environ.get("DATAGOV_API_KEY")
    meta = json.loads(_get(f"https://api.congress.gov/v3/bill/{congress}/{btype}/{num}/text?api_key={key}&format=json"))
    url = None
    for tv in meta.get("textVersions", []):
        for f in tv.get("formats", []):
            if f.get("type") in ("Formatted Text", "Text"):
                url = f["url"]; break
        if url:
            break
    if not url:
        raise RuntimeError("no Formatted Text version available")
    txt = re.sub(r"<[^>]+>", " ", _get(url))
    with open(cache, "w", encoding="utf-8") as fh:
        fh.write(txt)
    return txt


def extract_acquisition_sections(text, title_re=r"TITLE\s+VIII--ACQUISITION POLICY",
                                 sec_prefix="8", max_sections=None, max_chars=1500):
    """From the acquisition title, extract each SEC. <prefix>xx section as a provision record. Each
    section's text runs from its SEC heading to the NEXT SEC heading (a dynamic boundary -- Red Team F7:
    no fixed-length truncation that cuts a provision or bleeds into the next), capped at max_chars to keep
    the SHRED input bounded. Returns ordered, de-duplicated [{section, provision_text}]."""
    m = re.search(title_re, text, re.IGNORECASE)
    seg = text[m.start():] if m else text
    heads = list(re.finditer(r"SEC\.?\s*(" + sec_prefix + r"\d{2})\.?\s+[A-Z]", seg))
    seen, out = set(), []
    for i, mm in enumerate(heads):
        num = mm.group(1)
        if num in seen:
            continue
        seen.add(num)
        end = heads[i + 1].start() if i + 1 < len(heads) else mm.start() + max_chars
        chunk = " ".join(seg[mm.start():min(end, mm.start() + max_chars)].split())
        out.append({"section": f"sec. {num}", "provision_text": chunk})
        if max_sections and len(out) >= max_sections:
            break
    return out


def fulltext_provisions(instrument_id, congress, btype, num, demo_dir, live=False, max_sections=3):
    """Return provision records for a bill's acquisition-title sections. live=True fetches + extracts +
    caches the small records; else reads the cached records."""
    cache = os.path.join(demo_dir, f"{instrument_id}_provisions.json")
    if not live and os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    text = fetch_bill_text(congress, btype, num, os.path.join(demo_dir, ".fulltext"))
    secs = extract_acquisition_sections(text, max_sections=max_sections)
    src = f"{btype.upper()} {num} ({congress}th) Title VIII full text via Congress.gov (Reported in House)"
    provs = [{"id": f"{instrument_id}_{s['section'].replace('sec. ', 'sec')}",
              "instrument": instrument_id, "section": s["section"],
              "provision_text": s["provision_text"], "source": src, "enacted_in_fy26": False}
             for s in secs]
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(provs, fh, indent=2)
    return provs
