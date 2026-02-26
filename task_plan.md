# Task Plan: on_the_way v0.2.0 Implementation

## Goal
Deliver a runnable `v0.2.0` iOS UI/UX release based on `v0.1.0` baseline, focused on Home redesign, MUJI-style design tokens, and 8-theme navigation interactions without backend/data changes.

## Current Phase
Completed

## Phases

### Phase 1: Requirements & Discovery
- [x] Read `docs/product/product_v0.2.0.md`
- [x] Read related docs (`docs/frame/frame_v1.0.md`, `docs/api/api_v0.1.0.md`, `docs/run/交付物启动与验收说明_v0.1.0.md`)
- [x] Inspect current React Native iOS app structure and entry flow
- [x] Capture constraints and potential conflicts into findings
- **Status:** complete

### Phase 2: UI/UX Architecture & Implementation
- [x] Create MUJI design tokens (`colors/typography/spacing/radius/shadow/motion`)
- [x] Add theme definitions (8 topics + copy + icon mapping)
- [x] Implement `HomeScreen` with:
  - top brand section + date
  - horizontal 8-topic nav bar
  - 2x4 card grid
  - footer statement
- [x] Implement unified "coming soon" interaction feedback (no API calls)
- [x] Switch `App.tsx` first screen to Home and preserve v0.1.0 pages as debug-only entry
- [x] Ensure a11y/touch target and 375/430 width adaptation
- **Status:** complete

### Phase 3: Regression & Documentation
- [x] Update iOS/readme docs for v0.2.0 home behavior and debug access
- [x] Update product doc if implementation-confirmed deltas exist
- [x] Run feasible checks (Jest/lint) and report limitations
- [x] Final delivery summary against v0.2.0 acceptance checklist
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Keep all server/data layers untouched | Product v0.2.0 explicitly limits scope to iOS UI/UX. |
| Keep v0.1.0 ingest/query pages as hidden debug entry | Product requires retaining access for integration while not exposing in home/main nav. |
| Implement topic icons as built-in monochrome vector-like RN components | Avoids introducing new dependency while delivering consistent non-placeholder icon assets in this version. |
| Mark v0.2.0 docs as accepted/completed after user acceptance confirmation | Keeps delivery documentation consistent with actual project lifecycle state. |

## Open Questions for User Confirmation
| Question | Current Assumption |
|----------|--------------------|
| Do you have a fixed external icon pack to use for the 8 topics? | No fixed pack. Implement coded icons first and replace later if assets are provided. |

## Final Closure
- v0.2.0 acceptance completed by user on 2026-02-26.
- Final wrap-up executed:
  - dead code scan and minor redundancy cleanup
  - docs status alignment to accepted/completed
  - generated runtime artifacts cleanup

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `apps/ios/src/screens/PocScreen.tsx` not found while probing old entry | Confirmed current app uses `ManualInputScreen` + `DailySummaryScreen`; plan updated accordingly. |
| `npm test` failed due AsyncStorage native module in Jest | Added official AsyncStorage Jest mock in `apps/ios/__tests__/App.test.tsx`. |
| `npx tsc --noEmit` flagged route narrowing and `jest` global typing | Removed impossible branch comparison and imported `jest` from `@jest/globals`. |
