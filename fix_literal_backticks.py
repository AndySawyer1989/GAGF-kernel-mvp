from pathlib import Path

files = [
    Path("tests/test_assessment_factory_lite_scope_call_agenda_message_endpoint.py"),
    Path("tests/test_assessment_factory_lite_scope_call_agenda_message_release_marker.py"),
]

for path in files:
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("`r`n", "\n")
    path.write_text(text, encoding="utf-8")
