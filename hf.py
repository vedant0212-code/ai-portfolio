"""Load a few rows of a free Hugging Face dataset, with a local cache.

Streams only `n` rows (no full download). Returns None if the `datasets`
package is missing, the machine is offline, or the dataset can't be read, so
callers can fall back to the bundled mini-sets.
Note: some older datasets use loading scripts, which `datasets>=4` no longer
runs. If a load fails for that reason, use `pip install "datasets<4"`.
"""
import json
import os

CACHE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache")


def load_rows(name: str, split: str, n: int, config: str | None = None):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{name.replace('/', '__')}.{split}.{n}.jsonl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    try:
        from datasets import load_dataset
        ds = load_dataset(name, config, split=split, streaming=True)
        rows = []
        for row in ds:
            # drop non-JSON values such as images
            rows.append({k: v for k, v in row.items()
                         if isinstance(v, (str, int, float, bool, list, dict, type(None)))})
            if len(rows) >= n:
                break
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        return rows
    except Exception as exc:
        print(f"[hf] could not load {name}: {exc}")
        return None


def pick(row: dict, candidates: tuple[str, ...]):
    """First present key from `candidates` (case-insensitive)."""
    lower = {k.lower(): k for k in row}
    for c in candidates:
        if c.lower() in lower:
            return row[lower[c.lower()]]
    return None
