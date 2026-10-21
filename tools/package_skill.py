"""Package the portable skill alone as a reproducible ZIP for local import."""
import argparse
import hashlib
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/medical-education-studio"


def package(destination):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")
    files = []
    for file in sorted(SKILL.rglob("*")):
        if not file.is_file() or "__pycache__" in file.parts:
            continue
        relative = file.relative_to(SKILL)
        allowed = relative.as_posix() == "SKILL.md" or (
            relative.parts[0] in {"agents", "references", "scripts", "assets"}
            and file.suffix in {".md", ".py", ".json", ".yaml"}
        )
        if file.is_symlink() or not file.resolve().is_relative_to(SKILL.resolve()) or not allowed:
            raise ValueError(f"Unexpected skill file: {relative}")
        files.append(file)
    if not (SKILL / "SKILL.md").is_file():
        raise ValueError("SKILL.md is missing")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            name = SKILL.name + "/" + file.relative_to(SKILL).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, file.read_bytes().replace(b"\r\n", b"\n"))
    return len(files), hashlib.sha256(destination.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="New ZIP path, preferably outside this repository")
    args = parser.parse_args()
    try:
        count, digest = package(args.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Package not created: {error}\n")
    print(f"Packaged {count} files; SHA256 {digest}")


if __name__ == "__main__":
    main()
