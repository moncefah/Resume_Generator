import json
from pathlib import Path
from generator import generate

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"


def ask_number(prompt: str, minimum: int = 0) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            if value >= minimum:
                return value
        except ValueError:
            pass
        print(f"Please enter a whole number >= {minimum}.")


def ask_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def ask_multiline(prompt: str) -> str:
    print(prompt)
    print("Enter as many lines as you need; type END on its own line to finish.")
    lines = []
    while True:
        line = input("> ")
        if line.strip().upper() == "END":
            if lines:
                return "\n".join(lines)
            print("Please describe at least one thing you did.")
            continue
        lines.append(line)


def choose_role(roles: dict) -> str:
    names = list(roles)
    print("\nSelect your target role:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    return choose_from_names(names)


def choose_from_names(names: list[str]) -> str:
    while True:
        n = ask_number("Role number: ", 1)
        if n <= len(names):
            return names[n - 1]
        print(f"Choose a number from 1 to {len(names)}.")


def choose_keywords(recommended: dict[str, str]) -> list[str]:
    """Select technologies by their stable numeric IDs, e.g. 1,3,8."""
    print("\nTechnologies used in this experience/project:")
    for keyword_id, technology in recommended.items():
        print(f"  {keyword_id:>2} - {technology}")

    while True:
        raw = input("IDs (comma-separated, e.g. 1,3,8; Enter for none): ").strip()
        if not raw:
            return []

        ids = [part.strip() for part in raw.split(",")]
        if not all(keyword_id in recommended for keyword_id in ids):
            print("Invalid IDs. Select numbers shown above, separated by commas.")
            continue

        # Preserve the user's selection order and remove duplicates.
        return [recommended[keyword_id] for keyword_id in dict.fromkeys(ids)]


def collect_entry(kind: str, number: int, recommended: dict[str, str]) -> dict:
    print(f"\n===== {kind.upper()} {number} =====")
    entry = {
        "id": f"{'exp' if kind == 'experience' else 'proj'}_{number}",
        "title": ask_required("Position/title: " if kind == "experience" else "Project name: "),
    }
    if kind == "experience":
        entry["company"] = ask_required("Company: ")
    entry["location"] = input("Location (optional): ").strip()
    entry["start_date"] = input("Start date (e.g. 2025-05, optional): ").strip()
    entry["end_date"] = input("End date (e.g. 2025-08 / Present, optional): ").strip()
    entry["technologies"] = choose_keywords(recommended)
    entry["description"] = ask_multiline("Describe everything you did, in your own words:")
    return entry


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_results(results: dict) -> None:
    print("\n========= GENERATED OUTPUT =========")
    for section in ("experiences", "projects"):
        for entry in results[section]:
            print(f"\n{entry['id']}:")
            for i, bullet in enumerate(entry["bullets"], 1):
                print(f"  {i}. {bullet}")
            if not entry["bullets"]:
                print("  (No bullet candidates found.)")
    print("\nNOTE: These are raw-text excerpts from a MOCK generator, not AI-written bullets.")


def get_original(payload: dict, entry_id: str) -> dict:
    for section in ("experiences", "projects"):
        for entry in payload[section]:
            if entry["id"] == entry_id:
                return entry
    raise ValueError(f"Unknown entry id: {entry_id}")


def feedback(payload: dict, results: dict) -> dict:
    while True:
        print_results(results)
        print("\n1. Accept and save")
        print("2. Add context to an entry and regenerate")
        print("3. Edit a mock bullet manually")
        choice = input("Choose 1, 2 or 3: ").strip()
        if choice == "1":
            return results
        if choice not in ("2", "3"):
            print("Invalid choice.")
            continue
        ids = [item["id"] for section in ("experiences", "projects") for item in results[section]]
        print("Entry IDs:", ", ".join(ids))
        entry_id = input("Which entry ID? ").strip()
        if entry_id not in ids:
            print("Unknown entry ID.")
            continue
        if choice == "2":
            original = get_original(payload, entry_id)
            original["description"] += "\n" + ask_multiline("Add more details:")
            updated = generate(payload)
            # Preserve edits to other entries; regenerate only the requested one.
            for section in ("experiences", "projects"):
                for idx, item in enumerate(results[section]):
                    if item["id"] == entry_id:
                        results[section][idx] = next(x for x in updated[section] if x["id"] == entry_id)
            save_json(OUTPUT / "input.json", payload)
        else:
            item = next(x for section in ("experiences", "projects") for x in results[section] if x["id"] == entry_id)
            if not item["bullets"]:
                print("No bullet to edit.")
                continue
            n = ask_number("Bullet number: ", 1)
            if n > len(item["bullets"]):
                print("Bullet out of range.")
                continue
            item["bullets"][n - 1] = ask_required("Replacement text: ")
            item["status"] = "manually_edited"


def main() -> None:
    roles = json.loads((ROOT / "roles.json").read_text(encoding="utf-8"))
    print("=== Resume CLI MVP ===")
    role = choose_role(roles)
    n_exp = ask_number("How many work experiences? ")
    n_proj = ask_number("How many projects? ")
    payload = {"target_role": role, "experiences": [], "projects": []}
    for i in range(1, n_exp + 1):
        payload["experiences"].append(collect_entry("experience", i, roles[role]))
    for i in range(1, n_proj + 1):
        payload["projects"].append(collect_entry("project", i, roles[role]))
    save_json(OUTPUT / "input.json", payload)
    results = feedback(payload, generate(payload))
    save_json(OUTPUT / "result.json", results)
    print("\nSaved: output/input.json and output/result.json")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
