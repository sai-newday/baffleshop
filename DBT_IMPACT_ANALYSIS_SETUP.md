# dbt Blast Radius Impact Analysis - Setup Guide

## What Was Created

A complete GitHub Actions workflow for analyzing the blast radius of dbt model and column changes in pull requests.

### Files Created

```
.github/workflows/
└── dbt-impact-analysis.yml          # Main workflow definition

.github/scripts/
├── detect_changes.py                 # Detects model/column changes from git diff
├── check_changes.py                  # Validates if changes exist
├── impact_analysis.py                # Analyzes lineage dependencies
├── generate_comment.py               # Generates markdown PR comment
└── README.md                         # Technical documentation
```

## Quick Start

### 1. Verify Prerequisites

Your repository already has:
- ✅ dbt project configured (`dbt_project.yml`)
- ✅ dbt dependencies (`requirements.txt` with dbt-core, dbt-duckdb)
- ✅ GitHub repository with PR workflow support

### 2. Commit Files to Repository

```bash
cd /Users/n45413/dev/baffleshop
git add .github/workflows/dbt-impact-analysis.yml
git add .github/scripts/
git commit -m "feat: add dbt blast radius impact analysis workflow"
git push origin main
```

### 3. Test the Workflow

Create a test PR that modifies a dbt model:

```bash
# Create test branch
git checkout -b test/impact-analysis

# Modify a model (e.g., add a column to models/staging/stg_customers.sql)
# Commit and push
git add models/
git commit -m "test: add new column to stg_customers"
git push origin test/impact-analysis

# Create pull request on GitHub
# The workflow will automatically run and post a comment
```

## How It Works

### When Triggered
The workflow runs automatically when a PR modifies:
- `models/**` - Any dbt model files
- `macros/**` - Any dbt macros
- `dbt_project.yml` - Project configuration
- `packages.yml` - dbt packages
- `requirements.txt` - Python dependencies

### What It Does

1. **Detects Changes**: Compares PR branch with base branch to identify:
   - New models
   - Removed models
   - Modified models
   - Added/removed columns

2. **Generates dbt Artifacts**:
   - Runs `dbt deps`
   - Runs `dbt docs generate`
   - Creates `target/manifest.json` and `target/catalog.json`

3. **Analyzes Lineage**: Uses dbt manifest to determine:
   - Direct downstream dependencies (1st order)
   - Recursive downstream dependencies (all transitive)
   - Affected columns in downstream models

4. **Posts PR Comment**: Generates markdown summary with:
   - Changed assets table
   - Direct impact analysis
   - Recursive impact analysis
   - Aggregated impact by model
   - Summary statistics

## Example Workflow Run

### Scenario: Modify fct_orders model

**PR Changes:**
- Added column `order_priority` to `fct_orders`
- Modified data type of `created_at`

**Workflow Output:**

```markdown
# 🔍 dbt Blast Radius Analysis

## Changed Assets
| Model | Column | Change Type |
| `fct_orders` | `order_priority` | added |
| `fct_orders` | `created_at` | modified |

## Direct Impact
| Source Model | Impacted Model | Impacted Columns |
| `fct_orders` | `mart_customer_metrics` | total_orders, avg_priority |
| `fct_orders` | `dashboard_orders` | orders |

## Summary
- Changed Models: 1
- Changed Columns: 2
- Directly Impacted Models: 2
- Recursively Impacted Models: 1
```

## Customization

### Adjust Trigger Paths

Edit `.github/workflows/dbt-impact-analysis.yml` to trigger on different paths:

```yaml
on:
  pull_request:
    paths:
      - 'models/**'           # All models
      - 'dbt_project.yml'     # Project config
      - 'custom_path/**'      # Add custom paths
```

### Change Analysis Depth

The workflow analyzes:
- **Direct**: 1st-order dependencies
- **Recursive**: All transitive dependencies

To limit analysis, modify `.github/scripts/impact_analysis.py`:

```python
# Modify get_downstream_nodes() function
# Current: recursive (all downstream)
# Option: return only direct (remove recursion)
```

### Update Comment Template

Modify `.github/scripts/generate_comment.py` to customize:
- Comment sections
- Table formatting
- Summary metrics

## Troubleshooting

### Workflow Not Triggering
- Verify files modified match trigger paths
- Check branch protection rules don't block checks
- Ensure `.github/workflows/dbt-impact-analysis.yml` is on main branch

### "dbt artifacts not found" Error
- Check dbt project structure matches `dbt_project.yml`
- Verify models are valid SQL
- Run `dbt parse` locally to identify issues

```bash
cd /Users/n45413/dev/baffleshop
dbt parse
```

### Impact Analysis Shows No Results
- This is expected if changes don't have downstream dependencies
- Verify models are referenced correctly in downstream files
- Check `target/manifest.json` for model dependencies

```bash
# View model dependencies locally
dbt docs generate
dbt compile
```

### Python Scripts Fail
- Verify Python 3.11 is available
- Check all dependencies installed:
  ```bash
  pip install -r requirements.txt
  pip install dbt-column-lineage-extractor pyyaml
  ```

## Next Steps

### 1. Enable on All PRs
The workflow is now ready. It will automatically run on PRs modifying dbt models.

### 2. Add to CI/CD Pipeline
Integrate with existing deployment workflows:
```yaml
# In deploy.yml or similar
- name: Check impact analysis
  run: |
    # Add additional checks based on impact results
```

### 3. Enhance Column-Level Lineage
For more accurate column-level tracking:
- Install `dbt-column-lineage-extractor`
- Modify `impact_analysis.py` to use column-level lineage
- Update SQL parsing logic in `detect_changes.py`

### 4. Add Metrics Collection
Track impact analysis over time:
- Store results in database
- Generate trends/reports
- Alert on large blast radius

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review script output in workflow run
3. Verify dbt project configuration
4. Check `.github/scripts/README.md` for technical details

---

**Created by**: dbt Blast Radius Impact Analysis Agent  
**Date**: 2026-07-06  
**Repository**: sai-newday/baffleshop
