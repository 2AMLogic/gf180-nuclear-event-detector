# Work Log

Chronological record of merged PRs and closed issues, maintained by the Guide role.

## Archives

_None yet._

### 2026-11-19

- **PR #14**: ci(smoke): bound ngspice-build and ciel steps with step timeouts and curl limits
- **Issue #13** (closed): smoke.yml: ngspice-build and ciel steps still have no step-level timeout (same unbounded-step class as #11)
- **PR #12**: ci: bound the smoke apt step so a mirror stall fails fast
- **Issue #11** (closed): ci flake: smoke job cancelled by the 30-minute timeout in `Install build prerequisites` (apt update stalls 29m43s)
- **PR #10**: ci: validate smoke pin values before $GITHUB_ENV write; guard smoke.sh cd
- **Issue #9** (closed): Harden sim/smoke.sh and smoke.yml against two mechanical failure modes (shellcheck SC2164, GITHUB_ENV value injection)
- **PR #7**: feat(sim): bootstrap the verification harness — smoke bench, pins, one-command gate, CI
- **Issue #2** (closed): Bootstrap the verification harness
- **Issue #8** (closed): CLAUDE.md still says the repo is private pending a classification ruling
- **PR #5**: docs: describe the block as a general-purpose science instrument
