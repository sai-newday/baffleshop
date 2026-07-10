# baffleshop

baffleshop is a downstream dbt consumer repo.
It depends on public models from `../jaffleshop` and uses the shared dbt-colibri PR workflow for blast-radius comments.

## What it does

- Consumes upstream public dbt models
- Builds downstream marts and tests them
- Generates dbt docs
- Reuses the shared PR impact workflow

## Key features

- Mesh-style dependency on `jaffleshop`
- Standard dbt project layout
- Shared reusable workflow integration

## Example commands

```bash
dbt deps
dbt seed
dbt run
dbt test
dbt docs generate
```

Expected output:

```text
Finished running seeds/models/tests
Catalog written to target/catalog.json
Manifest written to target/manifest.json
```

## Unified Artifact Pipeline

This repo is part of a unified dbt artifact pipeline shared across three repos (jaffleshop, baffleshop, daffleshop).

### How it works

1. **Deployment Pipeline** (`.github/workflows/deploy.yml`)
   - Triggered on merge to `main`
   - Runs: `dbt deps` → `dbt run` → `dbt test` → `dbt docs generate`
   - Publishes artifacts (manifest.json, catalog.json) to the `dbt-colibri` artifacts-sync branch
   - These artifacts are then merged into a unified master catalog

2. **Master Artifact Merge** (in dbt-colibri)
   - After all three repos publish their artifacts, dbt-colibri's deploy workflow:
     - Fetches artifacts from all three projects
     - Runs `colibri merge-artifacts` to create a unified manifest and catalog
     - Stores merged artifacts at `combined-lineage/dist/_merged_artifacts/`
   - The master artifacts enable cross-project blast-radius analysis

3. **Cross-Project Blast Radius** (shared PR workflow)
   - When a PR is opened, the shared workflow in dbt-colibri:
     - Checks out the merged master catalog
     - Analyzes changed models against ALL three projects' models
     - Posts a PR comment showing downstream impact across the entire mesh
   - This gives complete visibility into cross-project dependencies

### Artifact Locations

- **Individual artifacts**: Published to `dbt-colibri/artifacts/{repo_name}/`
- **Master artifacts**: Stored at `dbt-colibri/combined-lineage/dist/_merged_artifacts/`
- **Reference**: artifacts-sync branch in dbt-colibri

## PR blast-radius workflow

Workflow file:

`.github/workflows/dbt-model-change-comment.yml`

It uses the shared workflow from dbt-colibri to analyze changed SQL files against the master catalog and post a PR comment showing cross-project impact.
