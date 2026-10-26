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
