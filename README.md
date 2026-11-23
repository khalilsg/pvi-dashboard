# 2026 candidates vs. Cook PVI

A single-page dashboard comparing every 2026 Senate, governor and House candidate's margin with
(a) the margin their state or district's **Cook PVI** implies and (b) the **2024 presidential** margin.
Filter by body, party, state, incumbency, result and race-call status, and download the filtered rows as CSV.

`index.html` is fully self-contained (data baked in), so it works on GitHub Pages or opened locally.

## Layout

```
index.html                       built page (don't edit by hand)
src/template.html                page source; data is injected at /*__DATA__*/
scripts/build_data.py            raw sources -> data/races.json + data/candidates.csv
src/version.js                   version shown in the footer
scripts/build_site.py            data/races.json + template + version -> index.html
scripts/update.sh                pull the latest results, then run both builds
data/raw/                        source snapshots (see Sources)
data/overrides/certified_results.csv   hand-entered certified totals (take priority)
data/overrides/highlights.csv          hand-picked candidates for the "Curated" highlight
.github/workflows/update.yml     daily refresh + rebuild on override edits
```

## Updating results

- **Automatic:** the GitHub Action runs daily (and from the Actions tab via "Run workflow"),
  pulls the latest tracker snapshot, rebuilds and commits if anything changed.
- **By hand:** `./scripts/update.sh`, then commit and push.
- **Certified results:** add rows to `data/overrides/certified_results.csv`
  (`race,candidate,party,votes,source`, one row per candidate, e.g. `PA-07,Bob Brooks,Democratic,201234,PA DOS 2026-11-30`).
  All rows for a race replace that race's numbers and mark it "Certified". Pushing an edit triggers a rebuild.
- **Curated highlights:** add rows to `data/overrides/highlights.csv` (`race,candidate,note`, e.g.
  `PA-07,Bob Brooks,Flipped a Trump district`). They become the chart's "Curated" highlight set, and the note
  shows in the hover card. The option stays hidden while the file has no rows. Pushing an edit triggers a rebuild.

## Versioning

The footer shows the version from `src/version.js`. Bump it on every push that changes the site,
run `python3 scripts/build_site.py`, and commit both. The automatic data refresh does not bump it.

- same-day follow-up push → third number (1.2 → 1.2.1)
- first push of the day, minor change → second number (1.2 → 1.3)
- new pages or major features → first number (1.x → 2.0)
- docs-only and CI-only changes don't bump

`.githooks/pre-push` blocks a push that leaves the version untouched. Enable it once per clone with
`git config core.hooksPath .githooks`; bypass with `git push --no-verify`.

## Method

- **Margin** = candidate share − main opponent share (% of all votes), from the candidate's point of view.
- **PVI-implied margin** = 2 × PVI in the candidate's party's direction (D+5 → D +10 / R −10). It assumes a
  neutral national environment, so in a wave year compare candidates with each other, not with zero.
- **vs. 2024** = candidate margin − their party's 2024 presidential margin in the same state/district.
- Where a party had no nominee and an independent was the main opponent (≥ 30% of the vote, e.g. NE Senate),
  the independent stands in for that side. Same-party and effectively uncontested races get no comparison.
- District 2024 margins are omitted for the nine states that used new maps in 2026
  (AL, CA, FL, LA, NC, OH, TN, TX, UT). Missouri's new map was blocked, so its 2022 lines (and matching PVI) are used.

## Sources and credit

- **Cook PVI** © The Cook Political Report with Amy Walter — 2026 Cook PVI for states and districts, as listed on
  Wikipedia's [Cook Partisan Voting Index](https://en.wikipedia.org/wiki/Cook_Partisan_Voting_Index) article.
  See [cookpolitical.com/cook-pvi](https://www.cookpolitical.com/cook-pvi). Please keep this credit if you reuse the data.
- **2026 results and incumbents:** [Tom-Neverwinter/election-tracker](https://github.com/Tom-Neverwinter/election-tracker)
  (NBC News results with Associated Press vote data). Unofficial until certified.
- **2024 presidential results by district:** [jaytimm/PresElectionResults](https://github.com/jaytimm/PresElectionResults)
  (state election offices; Drew Savicki / The Downballot).
