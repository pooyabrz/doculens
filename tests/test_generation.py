import copy
import json
import unittest
from unittest.mock import MagicMock, patch

from doculens.documents import load_document
from doculens.generation import GenerationError, OllamaClient, validate_answer
from doculens.retrieval import BM25Index


class GenerationTests(unittest.TestCase):
    def setUp(self):
        doc = load_document("guide.txt", b"Annual leave is 24 days. Manager approval is required.")
        self.hits = BM25Index(doc.chunks).search("annual leave")
        self.valid = {"status": "answered", "claims": [{
            "text": "There are 24 annual leave days.",
            "citations": [{"source_id": "S1", "quote": "Annual leave is 24 days."}],
        }]}

    def test_valid_answer_preserves_original_source(self):
        answer = validate_answer(self.valid, self.hits)
        self.assertEqual(answer.status, "answered")
        self.assertEqual(answer.claims[0].citations[0].chunk.filename, "guide.txt")

    def test_unknown_sources_and_invented_quotes_are_rejected(self):
        for field, value in (("source_id", "S99"), ("quote", "Annual leave is 90 days.")):
            payload = copy.deepcopy(self.valid)
            payload["claims"][0]["citations"][0][field] = value
            with self.subTest(field=field), self.assertRaises(GenerationError):
                validate_answer(payload, self.hits)

    def test_missing_citations_cannot_be_displayed_as_an_answer(self):
        payload = copy.deepcopy(self.valid)
        payload["claims"][0]["citations"] = []
        with self.assertRaises(GenerationError):
            validate_answer(payload, self.hits)

    def test_not_found_is_empty(self):
        answer = validate_answer({"status": "not_found", "claims": []}, self.hits)
        self.assertEqual(answer.claims, ())
        with self.assertRaises(GenerationError):
            validate_answer({"status": "not_found", "claims": self.valid["claims"]}, self.hits)

    def test_malformed_model_payloads_fail_cleanly(self):
        for payload in (None, [], {}, {"status": [], "claims": []}, {"status": "answered", "claims": [1]}):
            with self.subTest(payload=payload), self.assertRaises(GenerationError):
                validate_answer(payload, self.hits)

    def test_remote_or_redirect_destinations_are_not_configurable(self):
        for url in ("https://example.org", "http://localhost.evil.test", "http://localhost/api", "http://user@localhost"):
            with self.subTest(url=url), self.assertRaises(GenerationError):
                OllamaClient("example-model", url)

    @patch("doculens.generation.urllib.request.build_opener")
    def test_adapter_sends_schema_and_validates_response(self, build_opener):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "message": {"content": json.dumps(self.valid)}
        }).encode()
        build_opener.return_value.open.return_value = response
        answer = OllamaClient("example-model").answer("How many leave days?", self.hits, "en")
        request = build_opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"]["type"], "object")
        self.assertEqual(answer.status, "answered")

    @patch("doculens.generation.urllib.request.build_opener")
    def test_no_evidence_never_calls_model(self, build_opener):
        answer = OllamaClient("example-model").answer("Unknown fact", [])
        self.assertEqual(answer.status, "not_found")
        build_opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
