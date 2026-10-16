"""StayShield AI: draft a damage-claim file with policy citations.

The system never decides coverage or payment. Every output is a draft with
status `needs_human_review`; an assessor approves, edits or rejects it.
"""
import os
import re

from common import llm
from common.retrieval import Retriever

HERE = os.path.dirname(__file__)
DISCLAIMER = ("Draft only. A human assessor decides coverage and payment; "
              "clause matches are suggestions, not decisions.")

TYPE_RULES = {
    "gradual": ["mold", "mould", "condensation", "gradual", "slow", "over time", "seepage", "damp"],
    "preexisting": ["pre-existing", "preexisting", "already", "prior damage", "previous inspection", "noted before", "noted in"],
    "wear_tear": ["wear", "worn", "faded", "ageing", "aging", "years of", "ordinary use", "normal use"],
    "water": ["leak", "pipe", "flood", "water", "burst", "overflow", "tap", "sink", "drip"],
    "fire_smoke": ["fire", "smoke", "burn", "scorch", "cigarette", "soot", "singed"],
    "theft": ["missing", "stolen", "theft", "disappeared", "not in the room", "taken"],
    "vandalism": ["graffiti", "vandal", "smashed", "spray", "unknown persons", "broken into", "forced entry", "break-in"],
    "guest_damage": ["spilled", "stain", "broke", "broken", "snapped", "kicked", "cracked", "ripped", "torn", "splintered", "jumping"],
}
EXCLUSIONS = {"gradual", "preexisting", "wear_tear"}
TYPE_TO_CLAUSE = {"water": "2.1", "fire_smoke": "2.2", "guest_damage": "2.3", "theft": "2.4",
                  "vandalism": "2.5", "wear_tear": "3.1", "gradual": "3.2", "preexisting": "3.3"}
EVIDENCE_BY_TYPE = {"water": "plumber or maintenance report",
                    "fire_smoke": "incident or fire service report",
                    "theft": "police report"}
HIGH_VALUE = float(os.getenv("STAYSHIELD_HIGH_VALUE", "50000"))  # currency-agnostic


def parse_policy(text: str) -> list[dict]:
    clauses, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^(\d+\.\d+)\s+(.+)$", line.strip())
        if m:
            cur = {"id": m.group(1), "title": m.group(2), "text": ""}
            clauses.append(cur)
        elif cur and line.strip():
            cur["text"] += (" " if cur["text"] else "") + line.strip()
    return clauses


_DEFAULT = None


def default_policy() -> list[dict]:
    global _DEFAULT
    if _DEFAULT is None:
        with open(os.path.join(HERE, "sample_policy.txt"), encoding="utf-8") as f:
            _DEFAULT = parse_policy(f.read())
    return _DEFAULT


def classify(text: str) -> str | None:
    t = text.lower()
    best, best_n = None, 0
    for typ, words in TYPE_RULES.items():  # dict order = tie-break (exclusions first)
        n = sum(1 for w in words if w in t)
        if n > best_n:
            best, best_n = typ, n
    return best


def draft_claim(claim: dict, policy_text: str | None = None) -> dict:
    clauses = parse_policy(policy_text) if policy_text else default_policy()
    by_id = {c["id"]: c for c in clauses}
    retriever = Retriever([f'{c["title"]}. {c["text"]}' for c in clauses], [c["id"] for c in clauses])
    desc = claim.get("description", "")
    docs = [d.lower() for d in claim.get("documents", [])]
    items_out, missing, flags = [], set(), []

    if not claim.get("photos"):
        missing.add("dated photographs")

    for it in claim.get("items", []):
        text = f'{it.get("item", "")}. {desc}'
        typ = classify(text)
        hits = retriever.search(text, k=3)
        cid = TYPE_TO_CLAUSE.get(typ) if typ in TYPE_TO_CLAUSE and TYPE_TO_CLAUSE[typ] in by_id \
            else (hits[0]["meta"] if hits else None)
        clause = by_id.get(cid)
        if clause is None:
            status = "no_clause_found"
        elif typ in EXCLUSIONS:
            status = "possible_exclusion_review"
        else:
            status = "appears_to_match_clause"
        need = EVIDENCE_BY_TYPE.get(typ)
        if need and not any(need.split()[0] in d for d in docs):
            missing.add(need)
        if it.get("amount", 0) >= HIGH_VALUE:
            flags.append(f'High-value item: {it.get("item")} ({it["amount"]})')
        items_out.append({
            "item": it.get("item"), "amount": it.get("amount"), "damage_type": typ,
            "clause": {"id": clause["id"], "title": clause["title"]} if clause else None,
            "status": status,
            "retrieved_clauses": [{"id": h["meta"], "score": h["score"]} for h in hits],
        })

    out = {"claim_id": claim.get("claim_id"), "items": items_out,
           "missing_evidence": sorted(missing), "flags": flags,
           "status": "needs_human_review", "disclaimer": DISCLAIMER}
    summary = llm.complete(
        "Write a 3-sentence neutral summary of this draft claim file for an assessor. "
        "Do not decide coverage. Use only these facts:\n" + str(out),
        system="You assist insurance assessors. Never decide coverage or payment.")
    if summary:
        out["summary"] = summary
    return out
