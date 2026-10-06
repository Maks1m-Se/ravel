# Decisions

## Agreed

- Clinical and biomedical scenarios come first, with baseline/change from
  baseline in a fictional longitudinal study as the first demonstration.
  First-release boundaries and deferred features remain in [the plan](plan.md).
- Keep the general generation engine separate from clinical rules and thin
  interface adapters. The clinical module initially shares the repository and
  distribution; a public plugin loader/API is deferred.
- Local Codex implements changes; the ChatGPT Project handles planning and
  review. The maintainer accepts changes and release decisions. Work one
  reviewable task at a time.
- [progress.json](progress.json) is the authoritative progress record;
  [plan.md](plan.md) defines scope and acceptance criteria. The planned dashboard
  will be generated from progress.json. Issues support discussion, defects, and
  linked tasks without a duplicate status board.

## Unresolved

- Product name and license (MIT is proposed, subject to dependency review).
- Supported Python minor version, locked dependencies, and UI framework.
- Exact platform environments, including macOS version on Apple silicon.
- Installer/signing choices and benchmark reference hardware/frozen workload.
- Detailed recipe schema, selected clinical mapping standard versions, and
  declared handling of ties, missing dose, units, and invalid cases.

Resolve these through the planned specifications and M0 experiments; proposals
are not adopted choices or implementation evidence.
