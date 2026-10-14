import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def start(self):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_demo_question_and_clear_session(self):
        app = self.start()
        self.assertTrue(app.chat_input[0].disabled)
        app.button(key="load_demo").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.session_state["documents"]), 2)
        self.assertFalse(app.chat_input[0].disabled)
        app.chat_input[0].set_value("مرخصی سالانه چند روز است؟").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.session_state["history"]), 1)
        record = app.session_state["history"][0]
        self.assertIsNone(record["answer"])
        self.assertTrue(any("۲۴ روز" in hit.chunk.text for hit in record["hits"]))
        app.button(key="clear_session").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["documents"], {})
        self.assertEqual(app.session_state["history"], [])

    def test_language_switch_and_empty_scope(self):
        app = self.start()
        app.selectbox(key="language").set_value("English").run()
        app.button(key="load_demo").click().run()
        app.multiselect(key="scope").set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.chat_input[0].disabled)

    def test_removing_document_clears_answers_containing_its_text(self):
        app = self.start()
        app.button(key="load_demo").click().run()
        app.chat_input[0].set_value("annual leave").run()
        doc_id = next(iter(app.session_state["documents"]))
        app.button(key=f"remove_{doc_id}").click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertNotIn(doc_id, app.session_state["documents"])
        self.assertEqual(app.session_state["history"], [])


if __name__ == "__main__":
    unittest.main()
