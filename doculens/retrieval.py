"""Small, transparent BM25 baseline. Scores are not confidence percentages."""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence

from doculens.models import Chunk, SearchHit

TRANSLATION = str.maketrans("يك۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "یک01234567890123456789")
STOPWORDS = frozenset(
    "a an the is are was were be been being to of and or for from in on at "
    "with by as it this that these those i you we they he she my your our "
    "what which who when where why how do does did can could would should "
    "please tell me about according document documents "
    "از به با در و یا که این آن را برای است هست بود من تو ما شما آنها "
    "چه چگونه چطور چند آیا یک می شود هستند شده کنم کنید طبق سند اسناد لطفا".split()
)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).casefold().translate(TRANSLATION)
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text).replace("\u200c", " ")
    return [word for word in re.findall(r"[^\W_]+", text) if word not in STOPWORDS]


class BM25Index:
    def __init__(self, chunks: Sequence[Chunk]):
        self.chunks = tuple(chunks)
        self.frequencies = tuple(Counter(tokenize(chunk.text)) for chunk in self.chunks)
        self.lengths = tuple(sum(counts.values()) for counts in self.frequencies)
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 1
        self.document_frequency: Counter[str] = Counter()
        for counts in self.frequencies:
            self.document_frequency.update(counts.keys())

    def search(
        self, question: str, top_k: int = 4, document_ids: set[str] | None = None
    ) -> list[SearchHit]:
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")
        terms = set(tokenize(question))
        if not terms or not self.chunks:
            return []
        hits: list[SearchHit] = []
        count = len(self.chunks)
        for chunk, frequencies, length in zip(self.chunks, self.frequencies, self.lengths):
            if document_ids is not None and chunk.document_id not in document_ids:
                continue
            score = 0.0
            for term in terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                df = self.document_frequency[term]
                inverse_frequency = math.log(1 + (count - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.5 * (
                    1 - 0.75 + 0.75 * length / (self.average_length or 1)
                )
                score += inverse_frequency * frequency * 2.5 / denominator
            if score > 0:
                hits.append(SearchHit(chunk, score))
        return sorted(hits, key=lambda hit: (-hit.score, hit.chunk.id))[:top_k]
