# Search Terms

Master list and team assignments for the screening video corpus.

## Target

- **100 lung** + **100 colon** search terms (200 total)
- **Top 10 videos** per query → up to 2,000 query–video matches before dedup
- **6 team members** collect in parallel by cancer type

| Domain | Members |
|--------|---------|
| Lung | haikuan, tanay, xinhui |
| Colon | yiran, yule, suzie |

Current master file: **50 terms** (20 lung, 30 colon). See `config/collection_targets.json`.

## Files

| File | Description |
|------|-------------|
| `search_terms.csv` | Master list — add new terms here |
| `poc-handoff.csv` | 10-term POC subset (already handed off) |
| `search_terms.template.csv` | Blank row template for new contributors |
| `COLLECTION_PLAN.md` | Quota math, commands, merge steps |
| `assignments/collection_assignments.csv` | Final **200-term** split by domain + member |
| `assignments/collection_assignments_pilot50.csv` | Current **50-term** split by domain + member |
| `batches/` | Generated per-member CSVs (gitignored) |

## Adding terms

1. Copy a row from `search_terms.template.csv`
2. Set `cancer_domain` to `lung` or `colon`
3. Add to `search_terms.csv` and set `contributor` to your name
4. Keep lung terms together, then colon terms (script filters by `cancer_domain`)
5. Regenerate batches after edits:

```bash
# Current 50 terms (use now)
python3 scripts/assign_collection_batches.py \
  --assignments search_terms/assignments/collection_assignments_pilot50.csv

# Final 200 terms (use when master file is complete)
python3 scripts/assign_collection_batches.py
```

## Per-member collection

```bash
python3 collect_youtube_data.py \
  --input search_terms/batches/tanay.csv \
  --top-n 10 \
  --run-id batch-tanay-lung-pilot
```

Update `status=done` in the assignments CSV when finished.
