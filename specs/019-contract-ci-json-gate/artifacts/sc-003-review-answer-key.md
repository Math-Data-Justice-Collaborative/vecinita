# SC-003 documentation review — answer key (maintainers)

**Not** for contributor-facing docs. Used to score the five-question checklist in `CONTRIBUTING.md`.

1. **No** — missing attestation fails the gate (`missing_file` / attestation scope).
2. **No** — Option A: merge proof is local attestation + manifest validation; hosted re-run of manifest commands is not required (**FR-010**).
3. Any two of the verbatim risk strings from **SC-005** / contributor docs (e.g. **no mandatory hosted re-run of manifest checks for merge**, **fork/untrusted machine attestation**, **environment drift**, **bad-faith or mistaken claims**).
4. Regenerate `.ci/ci-attestation.json` (e.g. `make ci-attestation`) so every manifest `id` is present and `passed`, then commit.
5. **Fail** — exceeds configured max age (**FR-006** / `staleness`).
