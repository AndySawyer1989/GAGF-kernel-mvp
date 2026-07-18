from pathlib import Path

endpoint_path = Path("tests/test_assessment_factory_lite_scope_call_agenda_message_endpoint.py")
doc_path = Path("tests/test_assessment_factory_lite_scope_call_agenda_message_documentation.py")

# Fix endpoint test syntax caused by literal PowerShell newline tokens.
text = endpoint_path.read_text(encoding="utf-8-sig")

text = text.replace(
    '"release": "assessment-factory-lite-buyer-delivery-follow-up",`r`n        "version": "2.2.0",`r`n        "recommended_action": "review_assessment_scope_call_package",',
    '"release": "assessment-factory-lite-buyer-delivery-follow-up",\n        "version": "2.2.0",\n        "recommended_action": "review_assessment_scope_call_package",'
)

text = text.replace("`r`n", "\n")
endpoint_path.write_text(text, encoding="utf-8")

# Fix mojibake em dash in documentation tests.
text = doc_path.read_text(encoding="utf-8-sig")
text = text.replace("â€”", "—")
doc_path.write_text(text, encoding="utf-8")
