# Eval set

Sample crop-damage photos for testing the damage assessor. Images are
gitignored — re-download via `scripts/fetch_eval_set.py` (added in a later task)
or curl from Wikimedia Commons directly.

A known-good first sample:

```bash
curl -sSLo data/eval/sample_drought_corn.jpg \
  "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Cornfield_in_2007_drought%2C_eastern_West_Tennessee.jpg/960px-Cornfield_in_2007_drought%2C_eastern_West_Tennessee.jpg"

uv run python scripts/test_damage.py data/eval/sample_drought_corn.jpg
```

Expected output: `crop_type: maize`, `damage_cause: drought`, severity ~85–95.
