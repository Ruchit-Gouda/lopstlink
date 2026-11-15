"""Manual check for the matching engine.

Run from the backend directory:
    python test_matching.py
"""

from app.services.matching import score_reports

lost_report = {
    "item_name": "Blue Water Bottle",
    "category": "Bottle",
    "description": "A blue plastic water bottle",
    "color": "Blue",
    "brand": "",
    "location_text": "Library",
}

found_report = {
    "item_name": "Blue Plastic Bottle",
    "category": "Bottle",
    "description": "Found a blue water bottle",
    "color": "Blue",
    "brand": "",
    "location_text": "Library",
}

unrelated_report = {
    "item_name": "Black Wallet",
    "category": "Wallet",
    "description": "Leather wallet with an ID card",
    "color": "Black",
    "brand": "",
    "location_text": "Cafeteria",
}

for label, candidate in (
    ("Likely match", found_report),
    ("Unrelated item", unrelated_report),
):
    result = score_reports(lost_report, candidate)
    print(f"{label}: {result['score']}%")
    print(f"  Fields: {result['fields']}")
    print(f"  Reasons: {', '.join(result['reasons']) or 'none'}")
