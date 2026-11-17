"""Matching engine checks.

Run from the backend directory:
    python test_matching.py
"""

from app.services.matching import score_reports


def report(
    report_type: str,
    item_name: str,
    category: str,
    description: str,
    color: str = "",
    brand: str = "",
    location_text: str = "",
    event_date: str = "2026-11-15",
) -> dict:
    return {
        "report_type": report_type,
        "item_name": item_name,
        "category": category,
        "description": description,
        "color": color,
        "brand": brand,
        "location_text": location_text,
        "event_date": event_date,
    }


def score(lost: dict, found: dict) -> float:
    return score_reports(lost, found)["score"]


# The live reports that originally scored far too low.
live_bottle_lost = report(
    "lost",
    "Bottle",
    "Plastic",
    "Two liter plastic bottle of blue colour",
    "Blue",
    location_text="Alvas Hostel C block 521 Room number",
    event_date="2026-11-12",
)
live_bottle_found = report(
    "found",
    "Bottle",
    "plastic",
    "Two liter plastic bottle of blue colour",
    "Blue",
    location_text="Near campus common area",
    event_date="2026-11-14",
)
live_iphone_lost = report(
    "lost",
    "Phone",
    "iphone",
    "iphone 17 pro",
    "White",
    location_text="Alvas boys hostel campus",
    event_date="2026-11-15",
)
live_iphone_found = report(
    "found",
    "Phone",
    "iphone",
    "iphone 17 pro",
    "white",
    location_text="Alvas boys hostel campus",
    event_date="2026-11-15",
)
live_iqoo_lost = report(
    "lost",
    "Iqoo z10",
    "Phone",
    "I have lost it when I go to cut my hairs",
    "BLACK",
    brand="Iqoo",
    location_text="Near hair cutting shop of Moodbidri bus stand",
    event_date="2026-11-13",
)
live_iqoo_found = report(
    "found",
    "Phone",
    "Phone",
    "I found that in moodbidri bus stand",
    "black",
    brand="Iqoo",
    location_text="Moodbidri bus stand",
    event_date="2026-11-16",
)
white_iphone_lost = report(
    "lost",
    "iPhone 17 pro",
    "iphone",
    "iphone 17 pro",
    "White",
    location_text="Alvas boys hostel campus",
)
white_iphone_other = report(
    "found",
    "iPhone 15",
    "iphone",
    "iPhone 15",
    "white",
    location_text="Alvas boys hostel campus",
)
samsung_found = report(
    "found",
    "Samsung Galaxy",
    "Phone",
    "Samsung phone",
    "white",
    location_text="Alvas boys hostel campus",
)
typo_bottle_lost = report(
    "lost",
    "Blue Water Bottel",
    "Bottle",
    "A blue plastic water bottle",
    "Blue",
    location_text="Library",
)
typo_bottle_found = report(
    "found",
    "Blue Plastic Bottle",
    "Bottle",
    "Found a blue water bottle",
    "Blue",
    location_text="Library",
)
black_wallet = report(
    "lost",
    "Black Wallet",
    "Wallet",
    "Leather wallet with an ID card",
    "Black",
    location_text="Cafeteria",
)
black_phone_busstand = report(
    "found",
    "Phone",
    "Phone",
    "I found that in moodbidri bus stand",
    "black",
    brand="Iqoo",
    location_text="Moodbidri bus stand",
)
wallet_cafeteria = report(
    "lost",
    "Black Wallet",
    "Wallet",
    "black leather wallet with my college ID",
    "Black",
    location_text="Cafeteria",
    event_date="2026-11-14",
)
wallet_canteen = report(
    "found",
    "Leather Wallet",
    "Wallet",
    "found a black wallet near the canteen",
    "black",
    location_text="Canteen",
    event_date="2026-11-16",
)
pendrive_lost = report(
    "lost",
    "Pendrive",
    "Accessories",
    "32gb sandisk pendrive",
    brand="SanDisk",
    location_text="Computer lab",
)
usb_found = report(
    "found",
    "USB drive",
    "Accessories",
    "32gb sandisk usb drive",
    brand="SanDisk",
    location_text="Lab",
)
iphone_white = report(
    "lost",
    "iPhone 15",
    "Phone",
    "iphone 15",
    "White",
    brand="Apple",
    location_text="Library",
)
iphone_black = report(
    "found",
    "iPhone 15",
    "Phone",
    "iphone 15",
    "Black",
    brand="Apple",
    location_text="Library",
)
earphones_black = report(
    "lost",
    "Earphones",
    "Accessories",
    "black wired earphones",
    "Black",
    location_text="Room",
)
speaker_black = report(
    "found",
    "Speaker",
    "Accessories",
    "black bluetooth speaker",
    "Black",
    location_text="Room",
)
shirt_blue = report(
    "lost",
    "Blue shirt",
    "Clothing",
    "blue shirt",
    "Blue",
    location_text="Hostel",
)
jeans_blue = report(
    "found",
    "Blue jeans",
    "Clothing",
    "blue jeans",
    "Blue",
    location_text="Hostel",
)
pen_blue = report(
    "lost",
    "Pen",
    "Other",
    "blue pen",
    "Blue",
    location_text="Classroom",
)
pencil_blue = report(
    "found",
    "Pencil",
    "Other",
    "blue pencil",
    "Blue",
    location_text="Classroom",
)

CASES = [
    ("live bottle pair", live_bottle_lost, live_bottle_found, ">=", 90),
    ("live iPhone pair", live_iphone_lost, live_iphone_found, ">=", 95),
    ("live Iqoo pair", live_iqoo_lost, live_iqoo_found, ">=", 75),
    ("Iqoo vs bottle", live_iqoo_lost, live_bottle_found, "<", 25),
    ("bottle vs black Phone", live_bottle_lost, black_phone_busstand, "<", 25),
    ("white iPhone vs black Iqoo", white_iphone_lost, live_iqoo_found, "<", 70),
    ("iPhone 17 vs iPhone 15", white_iphone_lost, white_iphone_other, "<", 70),
    ("iPhone vs Samsung", white_iphone_lost, samsung_found, "<", 70),
    ("iPhone same model, different colour", iphone_white, iphone_black, "<", 70),
    ("typo bottle pair", typo_bottle_lost, typo_bottle_found, ">=", 95),
    ("black wallet vs phone", black_wallet, black_phone_busstand, "<", 25),
    ("black wallet vs bottle", black_wallet, live_bottle_found, "<", 25),
    ("wallet: cafeteria vs canteen", wallet_cafeteria, wallet_canteen, ">=", 90),
    ("pendrive vs USB drive", pendrive_lost, usb_found, ">=", 95),
    ("earphones vs speaker", earphones_black, speaker_black, "<", 25),
    ("shirt vs jeans", shirt_blue, jeans_blue, "<", 25),
    ("pen vs pencil", pen_blue, pencil_blue, "<", 25),
]

failures = 0

for label, lost, found, operator, limit in CASES:
    value = score(lost, found)
    passed = value >= limit if operator == ">=" else value < limit
    status = "PASS" if passed else "FAIL"
    failures += 0 if passed else 1

    print(f"[{status}] {label}: {value}% (expected {operator} {limit}%)")

    if not passed:
        details = score_reports(lost, found)
        print(f"        fields={details['fields']} reasons={details['reasons']}")

if failures:
    raise SystemExit(f"\n{failures} matching check(s) failed")

print("\nAll matching checks passed.")
