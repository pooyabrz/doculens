import unittest
from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from doculens.documents import DocumentError, load_document, split_text


def pdf_bytes(texts: list[str], password: str | None = None) -> bytes:
    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=400, height=400)
        if text:
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
            })
            stream = DecodedStreamObject()
            stream.set_data(f"BT /F1 12 Tf 30 350 Td ({text}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = stream
    if password:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class DocumentTests(unittest.TestCase):
    def test_text_has_passages_without_fake_pages(self):
        doc = load_document("../guide.md", "اولین بند.\n\nدومین بند.".encode())
        self.assertEqual(doc.filename, "guide.md")
        self.assertEqual([chunk.passage for chunk in doc.chunks], [1, 2])
        self.assertTrue(all(chunk.page is None for chunk in doc.chunks))

    def test_same_bytes_are_identified_as_duplicate_content(self):
        first = load_document("one.txt", b"Some document text.")
        second = load_document("renamed.txt", b"Some document text.")
        self.assertEqual(first.id, second.id)

    def test_real_pdf_text_keeps_physical_page_numbers(self):
        doc = load_document("guide.pdf", pdf_bytes(["First page evidence", "Second page evidence"]))
        self.assertEqual([chunk.page for chunk in doc.chunks], [1, 2])
        self.assertIn("Second page evidence", doc.chunks[1].text)

    def test_partially_scanned_pdf_keeps_readable_pages_and_warns(self):
        doc = load_document("mixed.pdf", pdf_bytes(["Readable evidence", ""]))
        self.assertEqual(len(doc.chunks), 1)
        self.assertIn("Page 2", doc.warnings[0])

    def test_image_only_pdf_reports_no_text(self):
        with self.assertRaises(DocumentError) as caught:
            load_document("scan.pdf", pdf_bytes([""]))
        self.assertEqual(caught.exception.code, "no_text")

    def test_encrypted_pdf_is_rejected(self):
        with self.assertRaises(DocumentError) as caught:
            load_document("locked.pdf", pdf_bytes(["Hidden"], password="secret"))
        self.assertEqual(caught.exception.code, "encrypted")

    def test_bad_inputs_report_actionable_errors(self):
        cases = [
            ("file.exe", b"content", "unsupported"),
            ("file.txt", b"", "empty"),
            ("file.txt", b"\xff\xfehello", "encoding"),
            ("file.txt", b"h\x00i\x00", "encoding"),
            ("file.pdf", b"not a PDF", "invalid_pdf"),
            ("file.md", b" \n\t", "no_text"),
        ]
        for filename, data, code in cases:
            with self.subTest(filename=filename, code=code):
                with self.assertRaises(DocumentError) as caught:
                    load_document(filename, data)
                self.assertEqual(caught.exception.code, code)

    def test_long_paragraph_keeps_final_evidence(self):
        text = "Important context. " * 150 + "FINAL_EVIDENCE"
        chunks = split_text(text, size=180, overlap=20)
        self.assertTrue(all(len(chunk) <= 180 for chunk in chunks))
        self.assertIn("FINAL_EVIDENCE", chunks[-1])


if __name__ == "__main__":
    unittest.main()
