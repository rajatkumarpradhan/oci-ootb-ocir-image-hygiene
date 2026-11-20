# oci-ootb-ocir-image-hygiene

**Category: built-in OCI services project (OOTB).** The custom portfolio project in this pair
is `oci-dynamic-group-audit`.

## Which built-in OCI services this wires

- **OCI Container Registry (OCIR)** (`oci_artifacts_container_repository`): the built-in
  private/public container image registry. A repository can be private or **public**
  (anonymously pullable), and images are addressed by tags that clients choose - nothing in
  the service forces tag discipline.

## Custom code vs native config

- **Native config**: `terraform/` declares one private repository with an immutable
  `latest`-style tag avoided by convention, plus the repo set up the way a real pipeline
  would reference it. **Template only - NOT plan/apply validated** (no live tenancy).
- **Custom code**: `ocir_checker/` audits an offline JSON export of repositories and image
  tags against four hygiene gaps the service accepts silently.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| OCIR001 | HIGH | A **public** repository contains an image tagged like a production artifact (`prod`, `release`, `stable`) - production-looking artifacts that are anonymously pullable. Review flag: confirm this exposure is intentional. |
| OCIR002 | MEDIUM | An image is tagged only `latest` with no version/digest tag recorded - deploys that reference it are not reproducible from this export. |
| OCIR003 | MEDIUM | A repository contains zero images - an empty repo (stale scaffolding or a broken push pipeline, as far as the export records). |
| OCIR004 | LOW | The image currently tagged `latest` is over 180 days old - the floating tag points at a stale artifact as recorded in the export. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m ocir_checker.cli samples/ocir_messy.json --as-of 2026-11-20   # exits 2, all 4 rules fire
python -m ocir_checker.cli samples/ocir_clean.json --as-of 2026-11-20   # exits 0
python -m unittest discover -s tests -v                                 # 18 tests, stdlib only
```

`--as-of` fixes the reference date so tag-age math is reproducible; omit it for today (UTC).

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCIR API.
- Findings describe what the export records. OCIR001 is a review flag on a naming heuristic
  (`prod`/`release`/`stable` tags), not proof that an exposure is unintended.
- The 180-day stale-latest window (OCIR004) is a default, not OCI policy.
- Vulnerability scanning of images is a different service (not covered here).
- Terraform template is illustrative and has **not** been plan/apply validated.

## Project status

Built as a daily OOTB project. 18 unit tests, green locally and in CI. Free tier only; no
live cloud calls, no spend.
