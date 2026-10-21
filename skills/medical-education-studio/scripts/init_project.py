"""Create a standalone skill project, without network calls or overwrites."""
import argparse
import json
from pathlib import Path


def initialize(destination, direction="", audience="", page_count=6):
    if type(page_count) is not int or page_count < 1:
        raise ValueError("page_count must be a positive integer")
    destination = Path(destination).expanduser().resolve()
    template = Path(__file__).resolve().parents[1] / "assets/project.template.json"
    project = json.loads(template.read_text(encoding="utf-8"))
    project["project_id"] = destination.name
    project["intent_info"]["data"].update(
        direction=direction, audience=audience, page_count=page_count
    )
    # exist_ok=False deliberately preserves any prior work, including empty folders.
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "images").mkdir()
    (destination / "project.json").write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="A new project directory")
    parser.add_argument("--direction", default="")
    parser.add_argument("--audience", default="")
    parser.add_argument("--pages", type=int, default=6)
    args = parser.parse_args()
    try:
        destination = initialize(args.destination, args.direction, args.audience, args.pages)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Project not created: {error}\n")
    print(f"Created {destination / 'project.json'}")
    print("No research, images or external records have been generated.")


if __name__ == "__main__":
    main()
