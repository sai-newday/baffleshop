# baffleshop (dbt mesh consumer)

This dbt project consumes a public model from `../jaffleshop`.

## Quick start

```bash
cd /Users/n45413/dev/baffleshop
source .venv/bin/activate
export DBT_PROFILES_DIR=/Users/n45413/dev/baffleshop/.dbt
dbt deps
dbt seed
dbt run
dbt test
dbt docs generate
```

