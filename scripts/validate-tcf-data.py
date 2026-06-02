from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "tcf-tv5monde"
PUBLIC_ROOT = ROOT / "public"
FORBIDDEN = "示例题"
REQUIRED_OPTIONS = {"A", "B", "C", "D"}


def site_path_exists(path: str) -> bool:
    if path.startswith(("http://", "https://")):
        return True
    if not path.startswith("/"):
        return False
    real_path = PUBLIC_ROOT / path.lstrip("/")
    if real_path.exists():
        return True
    return (PUBLIC_ROOT / path.removeprefix("/public/").lstrip("/")).exists()


def validate_paper(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if FORBIDDEN in text:
        errors.append(f"{path.name}: contains forbidden text {FORBIDDEN}")
    paper = json.loads(text)
    lesson = paper.get("livretNo", path.stem)
    for field in ["examType", "source", "livretNo", "title", "pdfPath", "audioPath", "questions"]:
        if field not in paper:
          errors.append(f"{path.name}: missing paper field {field}")
    if not site_path_exists(paper.get("pdfPath", "")):
        errors.append(f"{path.name}: pdfPath missing on disk: {paper.get('pdfPath')}")
    if not site_path_exists(paper.get("audioPath", "")):
        errors.append(f"{path.name}: audioPath missing on disk: {paper.get('audioPath')}")

    questions = paper.get("questions", [])
    if not isinstance(questions, list) or not questions:
        errors.append(f"{path.name}: questions must be a non-empty list")
        return errors

    for index, question in enumerate(questions, start=1):
        prefix = f"{lesson} Q{index:02d}"
        for field in ["id", "questionNo", "section", "prompt", "options", "correctAnswer", "needsReview"]:
            if field not in question:
                errors.append(f"{prefix}: missing field {field}")
        if question.get("questionNo") != index:
            errors.append(f"{prefix}: questionNo should be {index}")
        options = question.get("options", {})
        if set(options.keys()) != REQUIRED_OPTIONS:
            errors.append(f"{prefix}: options must contain A/B/C/D")
        if not question.get("prompt") and not question.get("needsReview"):
            errors.append(f"{prefix}: empty prompt requires needsReview=true")
        if not question.get("correctAnswer") and not question.get("needsReview"):
            errors.append(f"{prefix}: empty correctAnswer requires needsReview=true")
        image = question.get("documentImage", "")
        if image and not site_path_exists(image):
            errors.append(f"{prefix}: documentImage missing on disk: {image}")
    return errors


def main() -> None:
    errors: list[str] = []
    for num in range(1, 18):
        path = DATA_ROOT / f"L{num:02d}.json"
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        errors.extend(validate_paper(path))

    if errors:
        print("TCF data validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("TCF data validation passed for L01-L17.")


if __name__ == "__main__":
    main()
