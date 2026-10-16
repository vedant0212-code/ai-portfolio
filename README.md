# StayShield AI

**Domain:** Insurance

Drafts a property-damage claim file with policy-clause citations, exclusion flags and a missing-evidence list. It never decides coverage or payment.

![Architecture](docs/architecture.png)

Flow video: `docs/stayshield_demo.mp4`

## Flow

1. Claim in
2. Classify damage type
3. Retrieve policy clauses (TF-IDF)
4. Draft with citations
5. Flag missing evidence and high-value items
6. Human assessor decides

Every response is a draft with a review `status`. A person makes the decision.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload                         # docs at http://localhost:8000/docs
```

Try it: `POST /stayshield/draft` with a body like

```json
{"claim":{"description":"Pipe burst flooded the corridor","photos":3,"items":[{"item":"corridor flooring","amount":65000}]}}
```

## Test and evaluate

```bash
python -m unittest discover -s tests -v
python -m projects.stayshield.eval            # bundled mini-set, offline, seconds
python -m projects.stayshield.eval --hf       # free Hugging Face dataset (needs: pip install "datasets<4")
```

Results are saved to `evals/results/`. Free dataset: infinite-dataset-hub/TextClaimsDataset (unlabeled, so it is a robustness check; accuracy comes from the bundled hand-labeled set).

## LLM is optional

Default is deterministic logic (no keys, no GPU). To add an LLM for summaries or rewriting, copy `.env.example` to `.env` and set `LLM_BACKEND` to `ollama`, `gemini` or `groq`. Model names change, so they are env variables; check each provider's current free-tier limits.

## Honest limits

- The bundled mini-set is a small hand-made smoke test. Rule-based parts can score near 1.0 on it because the rules and examples came from the same author. Use the `--hf` numbers for real evaluation.
- The Hugging Face loader reads columns by common names. If a run prints a key list, edit the key tuples at the top of `projects/stayshield/eval.py`.
- Baselines are classical (TF-IDF, rules, regex). Swapping in embeddings or an LLM and comparing on the same eval is the natural next step.
- Not medical, legal, financial or insurance advice.

## Structure

```
api/main.py                 FastAPI service
common/                     LLM adapter, TF-IDF retriever, HF loader, eval helpers
projects/stayshield/    service.py, eval.py, sample data
tests/                      unit tests
docs/                       architecture and flow video
```
