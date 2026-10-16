"""Small TF-IDF retriever (free, no model download). Swap in embeddings later."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class Retriever:
    def __init__(self, texts: list[str], meta: list | None = None):
        self.texts = texts
        self.meta = meta if meta is not None else list(range(len(texts)))
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                                   stop_words="english")
        self.matrix = self.vec.fit_transform(texts)

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = self.vec.transform([query])
        scores = linear_kernel(q, self.matrix).ravel()
        order = scores.argsort()[::-1][:k]
        return [{"score": round(float(scores[i]), 4), "text": self.texts[i],
                 "meta": self.meta[i]} for i in order if scores[i] > 0]
