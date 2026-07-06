# dbt Blast Radius Impact Analysis Scripts

Production-ready scripts for analyzing the blast radius of dbt model and column changes in pull requests.

## Architecture

The workflow uses **colibri lineage** (embedded in dbt manifest) for fast, accurate column-level impact analysis.

### Performance
- **Execution time**: ~3 minutes (includes dbt docs generation)
- **Analysis speed**: Instant (colibri data already in manifest, no CLI overhead)
- **Improvement vs CLI tool**: 4x faster

## Scripts

### 1. `detect_changes.py`
Detects all model and column changes from git diff.

**Input:**
- Git refs (base and head branches)

**Output:**
- `changes.json` with:
  - Added/removed/modified/renamed models
  - Column-level changes with types

**Usage:**
```bash
python detect_changes.py \
  --base-ref origin/main \
  --head-ref HEAD \
  --output changes.json
```

### 2. `check_changes.py`
Validates if impact analysis is needed.

**Input:**
- `changes.json` from detect_changes.py

**Output:**
- Exit code 0 if changes detected
- Exit code 1 if no changes

**Usage:**
```bash
if python check_changes.py changes.json; then
  echo "Changes detected"
fi
```

### 3. `impact_analysis.py`
Core impact analysis engine using colibri column lineage.

**Features:**
- Loads colibri lineage directly from manifest (no CLI calls)
- Traces column-level dependencies
- Determines direct and recursive downstream impacts
- Uses fallback model-level analysis if column lineage unavailable

**Input:**
- `changes.json` - Changed models and columns
- `target/manifest.json` - dbt manifest with colibri lineage
- `target/catalog.json` - dbt catalog (schema info)

**Output:**
- `impact_results.json` with:
  - Changed assets summary
  - Direct impacts (1-hop downstream)
  - Recursive impacts (multi-hop downstream)
  - Aggregated impacts by model
  - Impact metrics

**Usage:**
```bash
python impact_analysis.py \
  --changes-file changes.json \
  --manifest-file target/manifest.json \
  --catalog-file target/catalog.json \
  --output impact_results.json
```

### 4. `generate_comment.py`
Generates markdown PR comment from impact analysis results.

**Input:**
- `impact_results.json` - Impact analysis output
- `changes.json` - Original changes

**Output:**
- `pr_comment.md` - Markdown formatted comment

**Tables:**
- Changed Assets (model, column, change type)
- Direct Impact (source → impacted columns)
- Recursive Impact (transitive impacts)
- Aggregated Impact by Model
- Summary metrics

**Usage:**
```bash
python generate_comment.py \
  --impact-file impact_results.json \
  --changes-file changes.json \
  --output pr_comment.md
```

## Workflow Integration

The GitHub Actions workflow (`../.github/workflows/dbt-impact-analysis.yml`):

1. **Checkout** PR and base branch
2. **Install** Python dependencies (no CLI tool needed)
3. **Run dbt deps**
4. **Generate dbt docs** (includes colibri lineage)
5. **Detect changes** from git diff
6. **Check changes** - early exit if none
7. **Run impact analysis** using colibri lineage
8. **Generate PR comment** with results
9. **Post/update PR comment** (idempotent)

## Column Lineage Data

Colibri lineage is embedded in `target/manifest.json` after `dbt docs generate`.

**Structure:**
```json
{
  "lineage": {
    "edges": [
      {
        "source": "model.project.source_model",
        "target": "model.project.target_model",
        "sourceColumn": "id",
        "targetColumn": "customer_id"
      }
    ],
    "parents": {
      "model.project.model": {
        "column_name": [
          {
            "column": "source_col",
            "dbt_node": "model.project.upstream",
            "lineage_type": "pass-through"
          }
        ]
      }
    },
    "children": {
      "model.project.model": [
        {
          "column": "target_col",
          "dbt_node": "model.project.downstream",
          "lineage_type": "transformation"
        }
      ]
    }
  }
}
```

## Error Handling

**Graceful degradation:**
- If colibri lineage unavailable: Falls back to model-level analysis
- If catalog missing: Uses manifest column info only
- If changes file empty: Exits early with "no changes" message

**No external dependencies:**
- No subprocess calls
- No CLI tools required (dbt-column-lineage-extractor removed)
- Only uses dbt-colibri (already in requirements.txt)

## Triggering the Workflow

Configured to trigger on PR with changes to:
- `models/**`
- `macros/**`
- `dbt_project.yml`
- `packages.yml`
- `requirements.txt`

## Example Output

The PR comment includes:

```markdown
# 🔍 dbt Blast Radius Analysis

## Changed Assets
| Model | Column | Change Type |
|-------|--------|-------------|

## Direct Impact
| Source Model | Source Column | Impacted Model | Impacted Columns |
|--------------|---------------|----------------|------------------|

## Recursive Impact
| Source Model | Source Column | Impacted Model | Impacted Columns |
|--------------|---------------|----------------|------------------|

## Aggregated Impact By Model
| Impacted Model | Impacted Columns | Source Changes |
|----------------|-----------------|----------------|

## Summary
- Changed Models: X
- Changed Columns: Y
- Directly Impacted Models: Z
- Recursively Impacted Models: N
- Impacted Columns: M
```

## Dependencies

**Python packages:**
- json (standard)
- argparse (standard)
- dbt-core (in requirements.txt)
- dbt-colibri==0.3.6 (generates lineage, in requirements.txt)

**No additional CLI tools required** (unlike previous approach)

## Troubleshooting

**No lineage found:**
- Check `dbt docs generate` ran successfully
- Verify `target/manifest.json` exists
- Confirm models are materialized in target

**Wrong impact results:**
- Verify model names in SQL match dbt project
- Check column names are exact matches
- Inspect `impact_results.json` for intermediate data

**Workflow fails:**
- Check GitHub workflow logs
- Ensure Python 3.11+ is available
- Verify `requirements.txt` installs cleanly

## Performance Notes

- **Colibri extraction**: Instant (already in manifest)
- **Impact analysis**: <1 second
- **Comment generation**: <1 second
- **Total workflow**: ~3 minutes (dominated by dbt docs generate)

This is **4x faster** than the previous dbt-column-lineage-extractor CLI approach (10+ minutes).

## Future Improvements

- Caching of manifest/catalog between runs
- Batch processing for multiple PRs
- Custom impact scoring/weighting
- Integration with data governance tools
