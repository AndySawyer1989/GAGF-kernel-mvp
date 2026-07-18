from pathlib import Path

files = [
    Path("tests/test_assessment_factory_lite_buyer_conversion_closeout_documentation.py"),
    Path("tests/test_assessment_factory_lite_commercial_offer_closeout_documentation.py"),
    Path("tests/test_assessment_factory_lite_demo_delivery_packaging_closeout_documentation.py"),
    Path("tests/test_assessment_factory_lite_proposal_export_package_closeout_documentation.py"),
    Path("tests/test_assessment_factory_lite_proposal_package_closeout_documentation.py"),
]

bad_dash = chr(0x00E2) + chr(0x20AC) + chr(0x201D)
good_dash = chr(0x2014)

for path in files:
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace(bad_dash, good_dash)
    path.write_text(text, encoding="utf-8")
