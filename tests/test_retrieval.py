import unittest

from doculens.documents import load_document
from doculens.retrieval import BM25Index, tokenize


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.leave = load_document("leave.md", b"Annual leave is 24 days.\n\nEquipment costs 300 USD.")
        self.remote = load_document("remote.md", b"Remote work is allowed three days per week.")
        self.index = BM25Index(self.leave.chunks + self.remote.chunks)

    def test_expected_evidence_is_first(self):
        hits = self.index.search("How many annual leave days are available?")
        self.assertIn("24 days", hits[0].chunk.text)

    def test_scope_cannot_return_unselected_document(self):
        self.assertEqual(self.index.search("remote", document_ids={self.leave.id}), [])
        self.assertEqual(self.index.search("leave", document_ids=set()), [])

    def test_empty_or_zero_overlap_questions_return_no_hits(self):
        for question in ("", "???", "what is the", "quantum spaceship propulsion"):
            with self.subTest(question=question):
                self.assertEqual(self.index.search(question), [])

    def test_arabic_persian_forms_and_digits_match(self):
        doc = load_document("fa.txt", "تجهیزات شرکت: ۲۴ عدد".encode())
        hits = BM25Index(doc.chunks).search("شركت 24")
        self.assertEqual(len(hits), 1)
        self.assertEqual(tokenize("كتاب"), tokenize("کتاب"))

    def test_score_is_positive_and_not_used_as_probability(self):
        self.assertGreater(self.index.search("equipment")[0].score, 0)


if __name__ == "__main__":
    unittest.main()
