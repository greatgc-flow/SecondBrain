# Gate 1b response (design owner, 2026-11-09) — DESIGN r8 -> r9

Scope: cx's `tests/fixtures/EXPECTED.md` (36 fixtures + 19 synthetic reports, real markitdown-gc 0.3.5) raised
three contradictions. Resolutions below; DESIGN edits are marked **[1b]**; details in EXPECTED.md "Gate 1b resolution".

1. **CP949 plain text (AT-08 vs §3 row 12).** Text allow-list split: plain-text set `.txt .csv .log .json .xml` is
   converted (charset honored) and **skips triage** (`triage` null, row 11 text-only/ready); markup set `.md .html .htm`
   is still triaged (0.3.5 -> `media_not_inspected`, row 12 unknown). §2 `triage` rule, §3 step 1/3, row 11, AT-05,
   AT-08 updated. `unknown/*` fixtures and AT-11 unchanged. No fixture moved.
2. **"No socket use" (AT-12) vs urllib3 import probe.** §6 defines "no network" as no external connect and no DNS
   (`connect`, `connect_ex`, `create_connection`, `getaddrinfo`, `gethostbyname*`); socket construction and loopback
   bind allowed. §9 guard = patch those calls (in-process and in converter children via `sitecustomize.py` on
   `PYTHONPATH`). AT-12/AT-37 reworded; AT-37 also asserts that importing `markitdown` does not trip the guard.
3. **Oversize peer output vs 50 KB fixture cap.** `peer-output/oversize.md` dropped from §9; §9 states the cap and
   runtime generation. AT-21 adds: 1 MiB accepted, 1 MiB + 1 or invalid UTF-8 -> exit 2 `invalid_request`, no writes
   (§5 Record now names the code). AT-28 oversize LLM body also generated at runtime.
4. **AT-18 p10.** `two-pages.pdf` has one candidate; AT-18 asserts one unit `u0001` (source `p2`, page 2 rendered) and
   checks numeric ordering (`p10, p2, p1`, `pages_total` 10) on a synthetic report.
5. **Consistency.** All §9 fixtures present and correctly placed; every EXPECTED.md row matches §3 r9. AT-06 now cites
   `reports/sample-ocr-report-png.json` (same JSON value as the renewal sample, re-serialized). The `renamed-audio.pdf`
   pin (null/failed, `FileConversionException`) is adopted in AT-12.
6. **Open (not design changes).** No-audio-extras (AT-37) and the six-job matrix are certified by CI, not locally.

Files changed: `docs/renewal/DESIGN.md`, `tests/fixtures/EXPECTED.md`, this file. Reviewers (cx, ag, argon): please
APPROVE/REJECT gate 1b on these four decisions.
