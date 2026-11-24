import json
from pathlib import Path


REQUIRED_ITEMS = {
    "1",
    "1A",
    "7",
    "7A",
    "8",
}

FORBIDDEN_ITEMS = {
    "11",
    "12",
    "13",
    "15",
    "16",
}


def validate_file(path: Path) -> bool:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    sections = data.get("sections", [])
    item_ids = {section.get("item_id") for section in sections}

    errors = []

    missing = REQUIRED_ITEMS - item_ids
    if missing:
        errors.append(f"Missing required items: {sorted(missing)}")

    forbidden = FORBIDDEN_ITEMS & item_ids
    if forbidden:
        errors.append(f"Forbidden/noisy items found: {sorted(forbidden)}")

    item_8 = next((section for section in sections if section.get("item_id") == "8"), None)
    if item_8 and item_8.get("char_count", 0) < 20_000:
        errors.append("Item 8 is too short. It may be truncated.")

    total_chars = data.get("metadata", {}).get("total_chars", 0)
    if total_chars < 150_000:
        errors.append(f"Total chars too low: {total_chars}")

    print(f"\nValidating {path.name}")
    print("-" * 50)
    print(f"Items: {sorted(item_ids)}")
    print(f"Total chars: {total_chars:,}")

    if errors:
        print("FAILED")
        for error in errors:
            print(f"  - {error}")
        return False

    print("OK")
    return True


def main():
    processed_dir = Path("data/processed")
    parsed_files = sorted(processed_dir.glob("*_parsed.json"))

    if not parsed_files:
        print("No parsed files found.")
        return

    results = [validate_file(path) for path in parsed_files]

    if not all(results):
        raise SystemExit(1)

    print("\nAll parsed reports are valid.")


if __name__ == "__main__":
    main()