"""The meaning-based retriever.

Default: TF-IDF over word n-grams and character n-grams (fast, tiny, runs on the free
Streamlit Cloud tier). Set USE_DENSE_EMBEDDINGS=true and install sentence-transformers
to switch to BAAI/bge-m3 dense embeddings, which also understand Hindi directly.
"""
from __future__ import annotations

import logging

import numpy as np

log = logging.getLogger(__name__)


class TfidfRetriever:
    name = "TF-IDF (word + char n-grams)"

    def __init__(self, texts: list[str]):
        from scipy.sparse import hstack
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._hstack = hstack
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english", min_df=1)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)
        self.m = self._norm(hstack([self.word.fit_transform(texts), 0.6 * self.char.fit_transform(texts)]).tocsr())

    @staticmethod
    def _norm(m):
        from sklearn.preprocessing import normalize

        return normalize(m)

    def scores(self, query: str) -> np.ndarray:
        q = self._norm(self._hstack([self.word.transform([query]), 0.6 * self.char.transform([query])]).tocsr())
        return (self.m @ q.T).toarray().ravel()


class DenseRetriever:
    def __init__(self, texts: list[str], model_name: str):
        from sentence_transformers import SentenceTransformer

        self.name = f"Dense embeddings ({model_name})"
        self.model = SentenceTransformer(model_name)
        self.m = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)

    def scores(self, query: str) -> np.ndarray:
        q = self.model.encode([query], normalize_embeddings=True)[0]
        return self.m @ q


def build(texts: list[str], use_dense: bool, model_name: str):
    if use_dense:
        try:
            return DenseRetriever(texts, model_name)
        except Exception as e:  # missing package / no network / low memory
            log.warning("Dense embeddings unavailable (%s); falling back to TF-IDF", e)
    return TfidfRetriever(texts)
