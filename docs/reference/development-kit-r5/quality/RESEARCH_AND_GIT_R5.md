# Technology research / Git evidence (2026-10-10)

## Verified external Git boundaries

**Engram:** v3.7.0 (2026-10-03), release/tag and commits `fd579e40995f` / `714637b0f69b` / `0fba1c6abc7f`: recursive CLI help, safe unknown args, dry-run, Windows repair paths. Reuse UX **principle**, not Engram runtime internals. https://github.com/greatgc-flow/Engram/releases/tag/v3.7.0

**PeerHub:** v0.12.6 (2026-10-09), release/commits `811a16d7ec47` / `25bd02f1c4fb` / `16424647a588`: opt-in native resume, measured context efficiency, fallback safety; newer `ccdee96c527b` is an English-docs change on main (not a separate release). Native resume must be discovered by version and tested per provider; no generic guarantee. https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.6

**No unseen Git history claim:** No canonical repository was given for this *development-kit ZIP*, so true provenance can only be measured from preserved parent ZIP bytes, not from commits. The public histories above are for external dependencies, not the design kit. Source review was of newest releases/recent commits and README, **not every historical commit**.

## Practice adoption decision (prune by value)

| Source | Decision | Why / What NOT to do |
|---|---|---|
| GitHub Spec Kit SDD (current docs 2026-09-28) | **Adopt as method**: specify→plan→tasks→implement→converge | Don't depend on external CLI or copy its entire workflow into core. https://github.com/github/spec-kit/blob/main/docs/index.md |
| OpenAI Harness Engineering (2026-02) | **Adopt**: independently enforced constraints and fast observable feedback | Don't assume AI-generated checks are independent. https://openai.com/index/harness-engineering/ |
| DORA AI Development Report (2025) | **Adopt**: AI amplifies existing delivery quality; measure actual outcomes | Don't use generated code/test count as success KPI. https://research.google/pubs/dora-2025-state-of-ai-assisted-software-development-report/ |
| PeerHub native resume measured in v0.12.6 | **Optional**: use only with compatibility/cost evidence and guarded fallback | Don't put context logic or provider session IDs into SSOT Core. https://github.com/greatgc-flow/peerhub/releases/tag/v0.12.6 |
| pytest/hypothesis/jsonschema/ExifTool/FFmpeg/BagIt | **Conditional** stable external components | No custom reimplementation until a concrete test fails and a stable component is unfit. See `standards/12_EXTERNAL_MODULES.md`. |

## 5 Whys distilled

1. Why user struggles? Many docs and commands obscure a first action.
2. Why many? Independent teams create overlapping guides, status and inventories.
3. Why overlap persists? Derived views lack one canonical owner and automatic consistency gate.
4. Why loop breaks? Closure rewarded for 'test passed', not observed user impact.
5. Root causes: **multiple authoritative narratives + missing evidence-bound close + insufficient small lookup tools**.

**Resolution:** one canonical source per concern, generated views, 4 main commands, notes within 3-state feedback process, real candidate-bound verification. Further features require demonstrable net improvement to a named scenario.
