from typing import List

class MemoryExtractor:
    def extract_from_message(self, message: str) -> List[str]:
        # naive extractor: split sentences > 80 chars
        parts = [s.strip() for s in message.split('.') if s.strip()]
        return [p for p in parts if len(p) > 30]

    def score(self, text: str) -> float:
        # naive scoring
        return min(1.0, len(text) / 500.0)
