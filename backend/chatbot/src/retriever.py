from rank_bm25 import BM25Okapi

def simple_tokenize(s: str):
    return s.lower().split()

class BM25Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.corpus_tokens = [simple_tokenize(c) for c in chunks]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def retrieve(self, query: str, k: int = 8):
        q_tokens = simple_tokenize(query)
        scores = self.bm25.get_scores(q_tokens)
        top_idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.chunks[i] for i in top_idxs]
