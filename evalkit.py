import json
import os
import re
import time

RESULTS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evals", "results")


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def f1(pred: str, gold: str) -> float:
    p, g = tokens(pred), tokens(gold)
    if not p or not g:
        return 0.0
    overlap = sum(min(p.count(t), g.count(t)) for t in set(p))
    if overlap == 0:
        return 0.0
    prec, rec = overlap / len(p), overlap / len(g)
    return 2 * prec * rec / (prec + rec)


def save(project: str, source: str, metrics: dict) -> dict:
    os.makedirs(RESULTS, exist_ok=True)
    out = {"project": project, "data_source": source,
           "ran_at": time.strftime("%Y-%m-%d %H:%M:%S"), "metrics": metrics}
    with open(os.path.join(RESULTS, f"{project}_{source}.json"), "w") as f:
        json.dump(out, f, indent=2)
    return out
