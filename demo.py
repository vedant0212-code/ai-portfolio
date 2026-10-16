"""python -m projects.stayshield.demo  -> readable drafts for a few sample claims."""
import json
import os

from projects.stayshield import service

HERE = os.path.dirname(__file__)
PICK = ["S01", "S03", "S06"]


def main():
    claims = {c["claim_id"]: c for c in json.load(open(os.path.join(HERE, "claims_sample.json")))}
    for cid in PICK:
        c = claims[cid]
        out = service.draft_claim(c)
        print(f"=== Claim {cid}: {c['description']}")
        for it in out["items"]:
            cl = it["clause"]
            print(f"  item: {it['item']} ({it['amount']})")
            print(f"  type: {it['damage_type']}  ->  clause {cl['id']} {cl['title']}")
            print(f"  status: {it['status']}")
        print(f"  missing evidence: {', '.join(out['missing_evidence']) or 'none'}")
        print(f"  flags: {', '.join(out['flags']) or 'none'}")
        print(f"  review: {out['status']}")
        print()
    print("Every draft needs a human assessor. The AI never decides coverage or payment.")


if __name__ == "__main__":
    main()
