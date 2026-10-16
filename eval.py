"""Evals for StayShield.

  python -m projects.stayshield.eval          # bundled mini-set (labeled by hand)
  python -m projects.stayshield.eval --hf     # + robustness run on a free HF dataset
"""
import json
import os
import sys

from common import evalkit
from common.hf import load_rows, pick
from common.retrieval import Retriever
from projects.stayshield import service

HERE = os.path.dirname(__file__)


def run_bundled() -> dict:
    claims = json.load(open(os.path.join(HERE, "claims_sample.json")))
    clauses = service.default_policy()
    retr = Retriever([f'{c["title"]}. {c["text"]}' for c in clauses], [c["id"] for c in clauses])
    n = type_ok = clause_ok = hit3 = miss_tp = miss_fn = miss_fp = excl_ok = excl_n = 0
    for c in claims:
        out = service.draft_claim(c)
        for item, exp in zip(out["items"], c["expected"]):
            n += 1
            type_ok += item["damage_type"] == exp["type"]
            clause_ok += bool(item["clause"]) and item["clause"]["id"] == exp["clause"]
            query = f'{item["item"]}. {c["description"]}'
            hit3 += exp["clause"] in [h["meta"] for h in retr.search(query, 3)]
            excl_n += 1
            excl_ok += (item["status"] == "possible_exclusion_review") == (exp["clause"].startswith("3."))
        got, want = set(out["missing_evidence"]), set(c["expected_missing"])
        miss_tp += len(got & want); miss_fn += len(want - got); miss_fp += len(got - want)
    m = {"items": n,
         "damage_type_accuracy": round(type_ok / n, 3),
         "clause_assignment_accuracy": round(clause_ok / n, 3),
         "retrieval_hit_at_3_only": round(hit3 / n, 3),
         "exclusion_flag_accuracy": round(excl_ok / excl_n, 3),
         "missing_evidence_recall": round(miss_tp / max(1, miss_tp + miss_fn), 3),
         "missing_evidence_precision": round(miss_tp / max(1, miss_tp + miss_fp), 3)}
    return evalkit.save("stayshield", "bundled_minset", m)


def run_hf(n: int = 200) -> dict | None:
    rows = load_rows("infinite-dataset-hub/TextClaimsDataset", "train", n)
    if not rows:
        return None
    texts = [str(pick(r, ("text", "claim", "description", "Text")) or "") for r in rows]
    texts = [t for t in texts if t.strip()]
    types, handled = {}, 0
    for i, t in enumerate(texts):
        out = service.draft_claim({"claim_id": f"HF{i}", "description": t, "photos": 1,
                                   "items": [{"item": "reported damage", "amount": 0}]})
        typ = out["items"][0]["damage_type"] or "unclassified"
        types[typ] = types.get(typ, 0) + 1
        handled += out["items"][0]["clause"] is not None
    m = {"rows": len(texts), "rows_with_a_clause_suggested": round(handled / max(1, len(texts)), 3),
         "damage_type_distribution": types,
         "note": "Unlabeled data: this is a robustness/coverage check, not an accuracy score."}
    return evalkit.save("stayshield", "hf_textclaims", m)


if __name__ == "__main__":
    print(json.dumps(run_bundled(), indent=2))
    if "--hf" in sys.argv:
        print(json.dumps(run_hf() or {"error": "HF load failed, see log"}, indent=2))
