from pathlib import Path

path = Path("tests/test_assessment_factory_lite_scope_call_agenda_message_documentation.py")

text = path.read_text(encoding="utf-8-sig")

bad_dash = chr(0x00E2) + chr(0x20AC) + chr(0x201D)
good_dash = chr(0x2014)

text = text.replace(bad_dash, good_dash)
text = text.replace("â€”", "—")

path.write_text(text, encoding="utf-8")
