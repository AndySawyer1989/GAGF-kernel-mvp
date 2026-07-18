from pathlib import Path

files_to_fix_dash = [
    Path("tests/test_assessment_factory_lite_buyer_delivery_follow_up_closeout_documentation.py"),
]

for path in files_to_fix_dash:
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("â€”", "—")
    path.write_text(text, encoding="utf-8")


service_test = Path("tests/test_assessment_factory_lite_scope_call_agenda_message_service.py")
text = service_test.read_text(encoding="utf-8-sig")

# The scope-call agenda message object is 2.3.0, but its source scope-call package stays layered at 2.2.0.
text = text.replace(
    '"release": "assessment-factory-lite-scope-call-conversion",\n        "version": "2.3.0",\n        "recommended_action": "review_assessment_scope_call_package",',
    '"release": "assessment-factory-lite-buyer-delivery-follow-up",\n        "version": "2.2.0",\n        "recommended_action": "review_assessment_scope_call_package",'
)

text = text.replace(
    '"release": "assessment-factory-lite-scope-call-conversion",\r\n        "version": "2.3.0",\r\n        "recommended_action": "review_assessment_scope_call_package",',
    '"release": "assessment-factory-lite-buyer-delivery-follow-up",\r\n        "version": "2.2.0",\r\n        "recommended_action": "review_assessment_scope_call_package",'
)

service_test.write_text(text, encoding="utf-8")
