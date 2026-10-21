"""Check local project structure and references; no medical or image review."""
import argparse
from datetime import date
import json
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit


TEMPLATE = Path(__file__).resolve().parents[1] / "assets/project.template.json"
STATES = {
    "research": {"not_started", "ready", "limited", "unverified", "failed"},
    "script": {"not_started", "draft", "ready"},
    "visual": {"not_started", "planned", "generated", "failed"},
    "delivery": {"not_started", "prepared", "saved", "partial", "failed"},
}


def validate(project, root):
    root = Path(root).resolve()
    issues = []

    def require(condition, message):
        if not condition:
            issues.append(message)

    def shape(value, template, path):
        if isinstance(template, dict):
            if not isinstance(value, dict):
                issues.append(f"{path}: expected object")
                return
            require(set(value) == set(template), f"{path}: unexpected or missing fields")
            for key, sample in template.items():
                if key in value:
                    if path == "project.topics" and key == "selected":
                        require(value[key] is None or isinstance(value[key], dict),
                                "topics.selected: expected object or null")
                    else:
                        shape(value[key], sample, f"{path}.{key}")
        elif template is None:
            require(value is None or isinstance(value, str), f"{path}: expected string or null")
        else:
            require(type(value) is type(template), f"{path}: expected {type(template).__name__}")

    shape(project, json.loads(TEMPLATE.read_text(encoding="utf-8")), "project")
    if issues:
        return issues

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def strings(value):
        return isinstance(value, list) and all(text(item) for item in value)

    def indexed(items, key, path, fields):
        result = {}
        for item in items:
            if not isinstance(item, dict) or not all(text(item.get(f)) for f in fields):
                issues.append(f"{path}: each object needs non-empty {', '.join(fields)}")
                continue
            identifier = item[key]
            require(identifier not in result, f"{path}: duplicate {key} {identifier}")
            result[identifier] = item
        return result

    def locator(value, path):
        if not text(value):
            issues.append(f"{path}: missing file or URL")
            return
        url = urlsplit(value)
        if url.scheme in {"https", "http"} and url.netloc:
            return
        if url.scheme or Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
            issues.append(f"{path}: expected HTTP(S) URL or relative project file")
            return
        file = (root / value).resolve()
        if not file.is_relative_to(root):
            issues.append(f"{path}: file escapes project directory")
        elif not file.is_file() or file.stat().st_size == 0:
            issues.append(f"{path}: file missing or empty")

    require(project["schema_version"] == "medical-education-studio/v1", "Unsupported schema_version")
    require(text(project["project_id"]), "project_id is required")
    require(project["stage"] in {"intent", "topics", "research", "script", "visual", "delivery", "done"},
            "Unknown stage")
    for section, allowed in STATES.items():
        require(project[section]["status"] in allowed, f"{section}: unknown status")
    data = project["intent_info"]["data"]
    require(data["page_count"] > 0, "page_count must be positive")
    topics = project["topics"]
    research, script, visual, delivery = (project[k] for k in STATES)
    require(topics["successful_rerecommendations"] >= 0, "Recommendation count must not be negative")
    require(strings(topics["preferences"]), "topics.preferences must contain strings")
    indexed(topics["candidates"], "topic_id", "topics.candidates", ("topic_id", "title", "angle"))
    selected = topics["selected"]
    if selected is not None:
        require(all(text(selected.get(k)) for k in ("topic_id", "title", "angle")),
                "topics.selected needs topic_id, title and angle")

    sources = indexed(research["sources"], "source_id", "research.sources",
                      ("source_id", "title", "locator", "accessed_on"))
    for source in sources.values():
        locator(source["locator"], f"source {source['source_id']}")
        try:
            date.fromisoformat(source["accessed_on"])
        except ValueError:
            issues.append("Source accessed_on must be an ISO date")
    claims = indexed(research["claims"], "claim_id", "research.claims",
                     ("claim_id", "statement", "scope"))
    for claim in claims.values():
        references = claim.get("source_ids")
        require(strings(references) and bool(references), "Each claim needs source_ids")
        if strings(references):
            require(set(references) <= sources.keys(), "Claim refers to unknown source")
    require(strings(research["limits"]), "research.limits must contain strings")
    if research["status"] in {"ready", "limited"}:
        require(bool(sources) and bool(claims), "Ready or limited research needs sources and claims")
        require(selected is not None, "Research needs a selected topic")
    if research["status"] == "limited":
        require(bool(research["limits"]), "Limited research needs explicit limits")

    pages = indexed(script["pages"], "page_id", "script.pages",
                    ("page_id", "title", "text", "visual_brief"))
    for page in pages.values():
        references = page.get("claim_ids")
        require(strings(references), "Each script page needs a claim_ids list")
        if strings(references):
            require(set(references) <= claims.keys(), "Script page refers to unknown claim")
    if script["status"] == "ready":
        evidence_ready = research["status"] == "ready" or (
            research["status"] == "limited" and research["user_accepted_limits"]
        )
        require(evidence_ready, "Ready script requires usable research and accepted limits")
        require(text(data["direction"]) and text(data["audience"]), "Ready script needs direction and audience")
        require(text(script["title"]) and text(script["body"]), "Ready script needs title and body")
        require(len(pages) == data["page_count"], "Script page count differs from planned page_count")

    require(strings(visual["characters"]), "visual.characters must contain descriptions")
    require(strings(visual["assets"]), "visual.assets must contain file or URL strings")
    for asset in visual["assets"]:
        locator(asset, "visual asset")
    visual_pages = indexed(visual["pages"], "page_id", "visual.pages", ("page_id",))
    candidate_count = 0
    for page_id, page in visual_pages.items():
        require(page_id in pages, "Visual page refers to unknown script page")
        candidates = page.get("candidates")
        require(strings(candidates), "Visual candidates must be a list of file or URL strings")
        require(page.get("review") in {"pending", "passed", "needs_fix"}, "Unknown review status")
        if strings(candidates):
            candidate_count += len(candidates)
            for candidate in candidates:
                locator(candidate, f"candidate {page_id}")
            if page.get("review") == "passed":
                require(bool(candidates), "Passed page needs a real candidate")
    if visual["status"] == "generated":
        require(candidate_count > 0, "Generated visual needs at least one candidate")
        require(script["status"] == "ready", "Generated visual needs a ready script")

    require(delivery["target"] in {"local", "feishu"}, "Unknown delivery target")
    records = indexed(delivery["records"], "page_id", "delivery.records", ("page_id",))
    saved_pages = set()
    for page_id, record in records.items():
        require(page_id in pages, "Delivery record refers to unknown page")
        require(record.get("status") in {"saved", "failed"}, "Unknown record status")
        if record.get("status") == "saved":
            saved_pages.add(page_id)
            locator(record.get("reference"), f"delivery record {page_id}")
    if delivery["status"] == "saved":
        require(bool(pages) and saved_pages == pages.keys(), "Saved delivery needs successful records for every page")
    if delivery["status"] == "partial":
        require(bool(saved_pages) and saved_pages < pages.keys(), "Partial delivery needs some saved and some unsaved pages")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Project directory or project.json")
    args = parser.parse_args()
    path = Path(args.project).expanduser().resolve()
    if path.is_dir():
        path = path / "project.json"
    try:
        project = json.loads(path.read_text(encoding="utf-8"))
        issues = validate(project, path.parent)
    except (OSError, ValueError) as error:
        issues = [f"Could not read project: {error}"]
    print(json.dumps({"status": "FAIL" if issues else "PASS", "issues": issues,
                      "scope": "Local structure and references only; no medical, image or remote verification."},
                     ensure_ascii=False, indent=2))
    return bool(issues)


if __name__ == "__main__":
    raise SystemExit(main())
