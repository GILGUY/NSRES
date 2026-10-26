# Build environment ledger

Machine-specific facts, breakages, and their real fixes. Read this before diagnosing any
toolchain failure. Every entry carries a claim marker and notes what was ruled out.

## E-1 Session toolchain (2026-10-25)

| Tool | Version |
| --- | --- |
| Python | 3.13.17 (`/usr/local/bin/python3`) |
| uv | 0.11.32 |
| hatchling (build backend, pinned in `pyproject.toml`) | 1.32.4 |
| ruff | 0.17.2 |
| mypy | 2.4.0 |
| pytest | 9.1.1 |
| jsonschema | 4.26.0 |
| git | 2.43.0 |

**Verified by:** `uv --version`, `python3 --version`, and `uv lock` / `uv sync --frozen`
output at WP-000.

## E-2 `UV_NATIVE_TLS` deprecation warning

Every `uv` command prints "The `UV_NATIVE_TLS` environment variable is deprecated ... Use
`UV_SYSTEM_CERTS` instead." The session's network proxy sets `UV_NATIVE_TLS`. The warning is
harmless: `uv lock`, `uv sync`, and `uv build` (which fetches hatchling into an isolated
environment) all succeeded with it set. **Verified by:** WP-000 gate run, stages 6 and 8 exit
0. Ruled out: there is no need to unset it. **Inferred — unverified:** unsetting it could
break TLS through the proxy, because it makes uv use the system certificate store where the
proxy's CA bundle lives; cheapest test: run `env -u UV_NATIVE_TLS uv build --out-dir /tmp/x`
and see whether hatchling still downloads.

## E-3 `uv build --out-dir` writes a `.gitignore` into the output directory

The file contains `*` and is not a build artifact. `scripts/repro.py` counts only `.whl` and
`.tar.gz` files. **Verified by:** the first WP-000 gate run failed stage 8 listing
`.gitignore` among the artifacts; after filtering, stage 8 passed.

## E-4 hatchling always puts `.gitignore` in the sdist

Even with `only-include` set, the sdist contains `nsres-<version>/.gitignore`.
`scripts/verify_package.py` expects it. **Verified by:** the first WP-000 gate run failed
stage 7 with "sdist: unexpected file nsres-0.1.0.dev0/.gitignore".

## E-5 GitHub access

The `gh` CLI token in this environment is invalid, so repositories cannot be created from the
session; Patrick creates them. Clone and push go through the session's git proxy, which caps a
repository at two concurrent smart-HTTP operations. **Verified by:** `gh` failure earlier in
the session; the add-repository result's stated limits. Before pushing from the shallow clone,
`git fetch origin main` so the push sends a thin pack (a stale shallow push can be rejected
with HTTP 413).

## E-6 `UV_NATIVE_TLS` is deprecated in uv 0.11.32

Every uv command prints "The `UV_NATIVE_TLS` environment variable is deprecated ... Use
`UV_SYSTEM_CERTS` instead." The warning is harmless. During WP-010 and WP-020 the session ran
uv with `UV_SYSTEM_CERTS=1` and `UV_NATIVE_TLS` unset. **Verified by:** with that setting,
`uv sync --frozen` and the full gate (including the isolated `uv build` and the e2e `uv pip
install` of the wheel) passed 9/9, with no warning. This does not settle E-2's inferred claim
about unsetting `UV_NATIVE_TLS` *without* setting `UV_SYSTEM_CERTS`; that claim stays
unverified. **Inferred — unverified:** the build may have used uv's cache rather than the
network; cheapest test: `uv cache clean` then rerun the gate with the same setting.

## E-7 The GitHub repository moved to `GILGUY/NSRES`

Pushing to `https://github.com/GILGUY/nsres` printed "This repository moved. Please use the
new location: https://github.com/GILGUY/NSRES.git". The push still succeeded. The remote was
set with `git remote set-url origin https://github.com/GILGUY/NSRES.git`. **Verified by:**
`git push` output at the WP-010 commit, then `git fetch origin` against the new URL succeeded
and `git status -sb` showed `main...origin/main` in sync.

### E-7 amendment (WP-030)

**Correction to E-7.** E-7 says the remote "was set with `git remote set-url origin
https://github.com/GILGUY/NSRES.git`". That command did run and took effect at the time, but
the setting did not persist: at WP-030, `git remote -v` showed `https://github.com/GILGUY/nsres`
again. **Inferred — unverified:** the session's repository registration rewrites the remote
when the working directory is re-attached; cheapest test: set the URL, end the turn, and read
`git remote -v` in the next one. Either URL pushes successfully (verified at the WP-010 and
WP-020 pushes), so the "repository moved" notice is harmless and the remote is left as the
session sets it. The cursor's line naming `GILGUY/NSRES.git` as the remote is withdrawn by the
WP-030 cursor.
