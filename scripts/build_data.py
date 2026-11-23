"""Build data/races.json and data/candidates.csv for the 2026 performance-vs-PVI dashboard.

Inputs (data/raw/):
  results-data.js                 2026 results, from github.com/Tom-Neverwinter/election-tracker
                                  (NBC News results, AP vote data; unofficial until certified)
  history.js                      same repo; pre-election snapshot used for incumbents (and Missouri PVI)
  cook_pvi_2026_wikipedia.csv     2026 Cook PVI (districts + states) as listed on Wikipedia's
                                  "Cook Partisan Voting Index" article; (c) The Cook Political Report
  pres2024_by_cd_2024lines.csv    2024 presidential results by district (2024 lines),
                                  from github.com/jaytimm/PresElectionResults (The Downballot / Drew Savicki et al.)

Run:  python3 scripts/build_data.py
"""
import csv, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

ABBR = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT",
"Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
"Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI",
"Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH",
"New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
"Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN",
"Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}

# States whose November 2026 House map differs from the 2024 map. 2024 district margins are
# omitted for these (old lines). Missouri is NOT here: its new map was blocked and the 2022 map was used.
REDRAWN = {"AL","CA","FL","LA","NC","OH","TN","TX","UT"}


# States where more than one candidate from a party can appear on the November ballot
# (Louisiana's all-candidate ballot, Alaska's top-four ranked-choice general).
SPLIT_BALLOT = {"LA", "AK"}


def load_js(name):
    s = open(os.path.join(RAW, name), encoding="utf-8").read()
    return json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])


def pvi_num(p):
    """'D+5' -> 5, 'R+3' -> -3, 'EVEN' -> 0 (positive = Democratic)."""
    p = (p or "").strip().upper()
    if p == "EVEN":
        return 0.0
    m = re.match(r"([DR])\+(\d+(?:\.\d+)?)$", p)
    if not m:
        return None
    return float(m.group(2)) * (1 if m.group(1) == "D" else -1)


def pct(s):
    return float(s.replace("%", "").strip())


def num(s):
    return float(s.replace(",", ""))


def side_of(party):
    p = (party or "").lower()
    if p.startswith("dem"):
        return "D"
    if p.startswith("rep"):
        return "R"
    return "I"


def norm(name):
    parts = re.sub(r"[^a-z ]", "", (name or "").lower()).split()
    while parts and parts[-1] in ("jr", "sr", "ii", "iii", "iv"):
        parts.pop()
    return parts


def same_person(a, b):
    a, b = norm(a), norm(b)
    return bool(a and b and a[-1] == b[-1] and (a[0][:3] == b[0][:3] or a[0][0] == b[0][0]))


def main():
    results = load_js("results-data.js")
    hist = load_js("history.js")
    snap = hist["2026-11-03"]  # last pre-election snapshot

    # --- PVI ---
    pvi_state, pvi_cd = {}, {}
    for r in csv.DictReader(open(os.path.join(RAW, "cook_pvi_2026_wikipedia.csv"))):
        if r["state"] == "STATE":
            pvi_state[ABBR[r["district"]]] = r["pvi"]
        else:
            d = 0 if r["district"] == "AL" else int(r["district"])
            pvi_cd[(ABBR[r["state"]], d)] = r["pvi"]
    pvi_src = {}
    # Missouri used its 2022 map; Wikipedia lists the blocked map's PVI. Use the tracker's Missouri values.
    for x in snap["house"]["races"]:
        st = ABBR[x["state"]]
        n = x["label"].split("-")[1]
        d = 0 if n in ("AL", "0") else int(n)
        if st == "MO":
            pvi_cd[(st, d)] = x["pvi"]
            pvi_src[(st, d)] = "Cook PVI (2022 map) via election-tracker"

    # --- 2024 presidential margins (Harris minus Trump, % of total vote) ---
    m24_cd, st_tot = {}, {}
    for r in csv.DictReader(open(os.path.join(RAW, "pres2024_by_cd_2024lines.csv"), encoding="utf-8")):
        st, n = r["CD"].split("-")
        d = 0 if n == "AL" else int(n)
        if not r["Total"].strip():  # NY-21 is blank in the source file
            continue
        m24_cd[(st, d)] = round(pct(r["Harris %"]) - pct(r["Trump %"]), 1)
        t = st_tot.setdefault(st, [0, 0, 0])
        t[0] += num(r["Harris"]); t[1] += num(r["Trump"]); t[2] += num(r["Total"])
    m24_state = {st: round(100 * (h - tr) / tot, 1) for st, (h, tr, tot) in st_tot.items()}

    # --- incumbents ---
    inc = {}
    for body, key in (("senate", "S"), ("governor", "G")):
        for x in snap[body]["races"]:
            special = "special" in x["label"].lower()
            st = ABBR[x["state"].replace(" (special)", "")]
            inc[(key, st, 0, special)] = (x.get("incumbent", ""), x.get("incParty", ""), x.get("note", ""))
    for x in snap["house"]["races"]:
        st = ABBR[x["state"]]
        n = x["label"].split("-")[1]
        d = 0 if n in ("AL", "0") else int(n)
        inc[("H", st, d, False)] = (x.get("incumbent", ""), x.get("incParty", ""), x.get("note", ""))

    # --- certified-result overrides (data/overrides/certified_results.csv) ---
    # columns: race,candidate,party,votes,source   e.g.  PA-07,Bob Brooks,Democratic,201234,PA DOS certified 2026-11-30
    # Rows for a race replace that race's candidate list entirely and mark it called + certified.
    overrides = {}
    opath = os.path.join(ROOT, "data", "overrides", "certified_results.csv")
    if os.path.exists(opath):
        for o in csv.DictReader(l for l in open(opath, encoding="utf-8") if not l.lstrip().startswith("#")):
            if o.get("race") and o.get("votes"):
                overrides.setdefault(o["race"].strip(), []).append(o)

    races, cands_out = [], []
    for r in results["races"]:
        off = r["office"]
        if off not in ("S", "G", "H"):
            continue
        st = ABBR[r["state"]]
        d = int(r["district"] or 0) if off == "H" else 0
        special = r["id"].split("~")[0].endswith("P") and off == "S"
        body = {"S": "Senate", "G": "Governor", "H": "House"}[off]
        label = (f"{st}-{d:02d}" if d else f"{st}-AL") if off == "H" else (f"{st} Senate" + (" (special)" if special else "") if off == "S" else f"{st} Governor")

        certified_src = None
        if label in overrides:
            rows = overrides[label]
            r = dict(r, cands=[{"name": o["candidate"].strip(), "party": o.get("party", "").strip(),
                                "votes": int(float(o["votes"].replace(",", "")))} for o in rows],
                     called=True, pctIn=100, votes=None)
            top = max(r["cands"], key=lambda c: c["votes"])
            r["winner"], r["winnerParty"] = top["name"], top["party"]
            certified_src = "; ".join(sorted({o.get("source", "").strip() for o in rows if o.get("source")})) or "certified"

        if off == "H":
            pvi = pvi_cd.get((st, d))
            m24 = None if st in REDRAWN else m24_cd.get((st, d))
        else:
            pvi = pvi_state.get(st)
            m24 = m24_state.get(st)
        pv = pvi_num(pvi)

        cs = sorted(r["cands"], key=lambda c: -(c.get("votes") or 0))
        # The tracker lists only each race's top two candidates but reports the full vote count,
        # so shares and margins use the full count, not the listed candidates' sum.
        listed = sum(c.get("votes") or 0 for c in cs)
        total = max(listed, r.get("votes") or 0) or None
        unlisted = round(100 * (1 - listed / total), 1) if total else 0
        topD = next((c for c in cs if side_of(c["party"]) == "D"), None)
        topR = next((c for c in cs if side_of(c["party"]) == "R"), None)
        note = ""
        # Main opposition stands in for a missing party (e.g. an independent backed in place of a Democrat).
        if topR and not topD:
            topD = next((c for c in cs if side_of(c["party"]) == "I"), None)
            if topD:
                note = f"No Democrat; {topD['name']} ({topD['party']}) treated as the D-side candidate"
        if topD and not topR:
            alt = next((c for c in cs if side_of(c["party"]) == "I"), None)
            if alt:
                topR = alt
                note = f"No Republican; {alt['name']} ({alt['party']}) treated as the R-side candidate"
        # A stand-in opponent only counts if they were a real contender (>= 30% of the vote).
        if note.startswith("No ") and total:
            sub = topD if note.startswith("No Democrat") else topR
            if sub and sub["votes"] / total < 0.30:
                note = f"No major-party opponent ({sub['name']}, {sub['party']}, under 30%); no D-vs-R comparison"
                if note and sub is topD: topD = None
                else: topR = None
        # Where several candidates of one party can share the ballot, a large unlisted vote means the
        # top Democrat vs. top Republican margin is not the party-vs-party margin.
        split = False
        if topD and topR and st in SPLIT_BALLOT and unlisted >= 10:
            note = (f"{unlisted:.0f}% of the vote went to candidates the source doesn't list, and this state "
                    "lets several candidates from one party share the ballot; no D-vs-R comparison")
            split = True
        contested = bool(topD and topR and total) and not split
        if not contested:
            note = note or ("Same-party or uncontested race; no D-vs-R comparison" if cs else "No results")

        margin_d = round(100 * (topD["votes"] - topR["votes"]) / total, 1) if contested else None
        vs_pvi_d = round(margin_d - 2 * pv, 1) if (contested and pv is not None) else None
        vs_24_d = round(margin_d - m24, 1) if (contested and m24 is not None) else None

        incname, incparty, incnote = inc.get((off, st, d, special), ("", "", ""))
        inc_ran = any(same_person(c["name"], incname) for c in cs) if incname and incname != "Open/new seat" else False
        winner_side = side_of(r.get("winnerParty"))

        race = dict(id=r["id"], body=body, state=st, district=d, label=label, pvi=pvi, pvi_num=pv,
                    pres24_margin=m24, redrawn=(off == "H" and st in REDRAWN), called=bool(r.get("called")),
                    pct_in=r.get("pctIn"), total_votes=total, winner=r.get("winner"), winner_party=winner_side,
                    incumbent=incname, incumbent_party=incparty, incumbent_ran=inc_ran, open_seat=not inc_ran,
                    pvi_source=pvi_src.get((st, d), "Cook PVI 2026 via Wikipedia"),
                    margin_d=margin_d, d_vs_pvi=vs_pvi_d, d_vs_2024=vs_24_d, note=note,
                    certified=certified_src, cands=[])
        for c in cs:
            sd = "D" if (topD is not None and c is topD) else "R" if (topR is not None and c is topR) else None
            sign = 1 if sd == "D" else -1 if sd == "R" else None
            share = round(100 * c["votes"] / total, 1) if total else None
            row = dict(name=c["name"], party=c["party"], side=sd, votes=c.get("votes"), share=share,
                       won=(c["name"] == r.get("winner")), incumbent=same_person(c["name"], incname),
                       margin=round(sign * margin_d, 1) if (sign and margin_d is not None) else None,
                       vs_pvi=round(sign * vs_pvi_d, 1) if (sign and vs_pvi_d is not None) else None,
                       vs_2024=round(sign * vs_24_d, 1) if (sign and vs_24_d is not None) else None)
            race["cands"].append(row)
            cands_out.append({"race": label, "body": body, "state": st, "district": d, "pvi": pvi,
                              "pres24_margin_d": m24, "called": race["called"], **{k: v for k, v in row.items()}})
        races.append(race)

    # --- curated highlights (data/overrides/highlights.csv) ---
    # columns: race,candidate,note   e.g.  PA-07,Bob Brooks,Flipped a Trump district
    hpath = os.path.join(ROOT, "data", "overrides", "highlights.csv")
    picked = 0
    if os.path.exists(hpath):
        by_label = {r["label"]: r for r in races}
        for h in csv.DictReader(l for l in open(hpath, encoding="utf-8") if not l.lstrip().startswith("#")):
            label, who = (h.get("race") or "").strip(), (h.get("candidate") or "").strip()
            if not label or not who:
                continue
            match = [c for c in by_label.get(label, {}).get("cands", []) if c["side"] and same_person(c["name"], who)]
            if len(match) != 1:
                print(f"WARNING: highlights.csv row not matched: {label}, {who}")
                continue
            match[0]["pick"] = (h.get("note") or "").strip() or True
            picked += 1

    out = dict(updated_results=results["updated"], races=races)
    json.dump(out, open(os.path.join(ROOT, "data", "races.json"), "w"), separators=(",", ":"))
    with open(os.path.join(ROOT, "data", "candidates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cands_out[0].keys()))
        w.writeheader(); w.writerows(cands_out)
    print(f"{len(races)} races, {len(cands_out)} candidate rows; {picked} curated; results as of {results['updated']}")


if __name__ == "__main__":
    main()
