# canary-guards

External safety-property guards for [Canary](../..) (Canary issue #63).

In-repo CI can be weakened by the same PR it is supposed to catch. This
repo exists so guard and guarded code can never change in one PR: the
worker has no GitHub identity at all, and this repo takes writes from
the owner only.

## What is checked (against the PR tree)

- **G1 — guard presence:** `.github/workflows/ci.yml` invokes this repo's
  `guard.yml`, pinned to a full 40-char SHA (no floating tags/branches).
- **G2 — prod gate wired:** `scripts/container_run.sh` invokes
  `scripts/prod_gate.sh` before any `docker build`.
- **G3 — no baked credentials:** Dockerfiles never explicitly `COPY`
  credential files, and `.dockerignore` excludes `.env`/`*.key`
  (the `COPY .` layer relies on it).
- **Behavioral prod gate:** the *target tree's own* `prod_gate.sh` is
  executed against hostile fixture repos (stale/ahead main, detached
  HEAD, missing remote, unknown profile). A weakened gate fails here
  even if the PR also guts Canary's in-repo `test_prod_gate.py`.

## Negative test

`test_guard_catches_weakening.py` builds evil fixture trees (gutted
gate, guardless CI, credential `COPY`) and asserts the suite fails on
them. It runs in this repo's selftest and on every guarded PR.

## Wiring (Canary side)

```yaml
guard:
  if: github.event_name == 'pull_request'
  uses: mikkokotila/canary-guards/.github/workflows/guard.yml@<SHA>
  with:
    repo: mikkokotila/Canary
    ref: ${{ github.event.pull_request.head.sha }}
```

The pin is a full commit SHA of this repo. To bump it: review the guard
diff here, then open a Canary PR updating the pin (G1 fails the build
otherwise). For the guard to have teeth, the `guard` check must be a
required check on main (owner-side branch protection, with #62's
reviewer ruleset).

## Running locally

```sh
PR_TREE=/path/to/Canary python -m pytest guard/tests -q
```
