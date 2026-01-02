from collections import defaultdict, deque

class TemporalMatriculeValidator:
    def __init__(self, window=5, min_votes=2):
        self.window = window
        self.min_votes = min_votes
        self.buffer = deque(maxlen=window)

    def update(self, best):
        """
        best: dict ou None (sortie OCR par frame)
        """
        self.buffer.append(best)

    def get_stable(self):
        votes = defaultdict(float)

        for b in self.buffer:
            if b is None:
                continue
            votes[b["text"]] += b.get("score", 1.0)

        if not votes:
            return None

        text, score = max(votes.items(), key=lambda x: x[1])

        if score >= self.min_votes:
            return {"text": text, "score": round(score, 2)}

        return None
