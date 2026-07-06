# dbt Blast Radius Impact Analysis Workflow

This GitHub Actions workflow automatically analyzes the blast radius of dbt model and column changes in pull requests.

## Overview

The workflow detects changes to dbt models and their columns, then uses the dbt manifest and catalog to determine:

- **Direct Impact**: Models that directly depend on changed models (1st order dependencies)
- **Recursive Impact**: All downstream dependencies (transitive closures)
- **Column-level Impact**: Which columns in downstream models are affected

## How It Works

### Trigger
The workflow runs automatically when a pull request modifies files in:
- `models/` directory
- `macros/` directory
- `dbt_project.yml`
- `packages.yml`
- `requirements.txt`

### Execution Steps

1. **Checkout Code**: Fetches PR branch and base branch for diff comparison
2. **Setup Python**: Installs Python 3.11 and dependencies
3. **Install Dependencies**: Installs dbt and required packages from `requirements.txt`
4. **Generate dbt Artifacts**: 
   - Runs `dbt deps` to install dbt packages
   - Runs `dbt docs generate` to create manifest and catalog
   - Verifies `target/manifest.json` and `target/catalog.json` exist
5. **Detect Changes**: Analyzes git diff to identify:
   - Added, removed, modified models
   - Added, removed columns
6. **Run Impact Analysis**: Uses dbt manifest to trace downstream dependencies
7. **Generate PR Comment**: Creates markdown summary of blast radius
8. **Post Comment**: Posts or updates comment on the PR

## Output

The workflow generates a detailed markdown comment on the PR containing:

### Changed Assets
Table of all modified models and columns with change type (added/removed/modified)

### Direct Impact (1st Order)
Models that directly depend on the changed models

### Recursive Impact
All downstream models affected transitively

### Aggregated Impact by Model
For each impacted model:
- Which columns are affected
- Source of the change (which changed model caused it)

### Summary Statistics
- Total changed models/columns
- Total directly/recursively impacted models
- Total impacted columns

## Configuration

### dbt Profile
Ensure your `profiles.yml` or dbt configuration is set up to work in CI/CD environments.
The workflow uses the profile specified in `dbt_project.yml`.

### dbt Packages
If using dbt packages, ensure `packages.yml` exists in the root directory.

### Python Dependencies
Update `requirements.txt` with required packages:
```txt
dbt-core==1.10.22
dbt-duckdb==1.10.0
dbt-colibri==0.3.6
```

## Troubleshooting

### Workflow doesn't trigger
- Verify files match the trigger paths in `dbt-impact-analysis.yml`
- Check that `.github/workflows/dbt-impact-analysis.yml` is committed to the repo

### "artifact not found" error
- Ensure `dbt deps` succeeds
- Verify `dbt docs generate` completes without errors
- Check dbt project configuration in `dbt_project.yml`

### No changes detected
- This is expected if PR only modifies non-model files
- The workflow will not post a PR comment

### Incorrect impact analysis
- Impact analysis relies on dbt manifest dependencies
- Ensure all model references in your SQL are properly resolved by dbt
- Use `dbt compile` to check for issues

## Scripts

Located in `.github/scripts/`:

- **detect_changes.py**: Compares git diff to identify model and column changes
- **check_changes.py**: Validates that changes were detected
- **impact_analysis.py**: Uses dbt manifest to trace downstream dependencies
- **generate_comment.py**: Formats results as markdown PR comment

## Example PR Comment

```markdown
# 🔍 dbt Blast Radius Analysis

## Changed Assets
| Model | Column | Change Type |
|---------|---------|---------|
| `fct_orders` | — | `modified` |
| `fct_orders` | `order_date` | `added` |

## Direct Impact (1st Order Dependencies)
| Source Model | Source Column | Impacted Model | Impacted Columns |
|---|---|---|---|
| `fct_orders` | — | `mart_customer_metrics` | `total_orders`, `order_count` |

## Recursive Impact
| Source Model | Source Column | Impacted Model | Impacted Columns |
|---|---|---|---|
| `fct_orders` | — | `dashboard_orders` | `orders` |

## Summary
- Changed Models: 1
- Changed Columns: 1
- Directly Impacted Models: 1
- Recursively Impacted Models: 1
- Impacted Columns: 3
```

## Limitations

- Column-level lineage detection uses basic SQL pattern matching (can be improved with dbt-column-lineage-extractor)
- Macro dependencies are not currently analyzed
- Tests and analyses are not included in impact scope
