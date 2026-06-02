from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "public" / "tcf-tv5monde"
DATA_ROOT = ROOT / "data" / "tcf-tv5monde"
MANIFEST_PATH = DATA_ROOT / "manifest.json"
ANSWERS_PATH = ROOT / "data" / "answers.json"


def section_for_question(question_no: int) -> tuple[str, str]:
    if question_no <= 10:
        return "Compréhension orale", "听力理解"
    if question_no <= 20:
        return "Structures de la langue", "语法结构"
    return "Compréhension écrite", "阅读理解"


def save_image(image_file, image_path: Path) -> bool:
    image_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        suffix = Path(image_file.name).suffix.lower()
        if suffix == ".png":
            image_path.write_bytes(image_file.data)
        else:
            temp = image_path.with_suffix(suffix or ".img")
            temp.write_bytes(image_file.data)
            with Image.open(temp) as img:
                img.save(image_path)
            temp.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def clean_page_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "CIEP / TCF" in stripped:
            continue
        if "localhost" in stripped:
            continue
        if "sur 26" in stripped and "13/04/2018" in stripped:
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def import_lesson(num: int) -> dict:
    lesson = f"L{num:02d}"
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8")) if ANSWERS_PATH.exists() else {}
    config = manifest[lesson]
    pdf_name = Path(config["pdf"]).name
    audio_name = Path(config["audio"]).name
    question_count = int(config["questionCount"])
    lesson_dir = PUBLIC_ROOT / lesson
    pdf_path = lesson_dir / pdf_name
    image_dir = lesson_dir / "images"
    reader = PdfReader(str(pdf_path))

    extracted_images = []
    for page_index, page in enumerate(reader.pages, start=1):
        images = list(page.images)
        if not images:
            continue

        # The TV5MONDE PDFs are printed webpages where the real item is embedded
        # as an image. Use the largest image on each page as the review material.
        image_file = max(images, key=lambda item: len(item.data))
        image_name = f"q{question_no:02d}-document.png"
        image_name = f"q{len(extracted_images) + 1:02d}-document.png"
        image_path = image_dir / image_name
        image_ok = save_image(image_file, image_path)
        page_text = clean_page_text(page.extract_text() or "")
        if image_ok:
            extracted_images.append(
                {
                    "documentImage": f"/tcf-tv5monde/{lesson}/images/{image_name}",
                    "questionImage": f"/tcf-tv5monde/{lesson}/images/{image_name}",
                    "documentText": page_text,
                    "sourcePage": page_index,
                }
            )

    questions = []
    lesson_answers = answers.get(lesson, {})
    for question_no in range(1, question_count + 1):
        section, sub_type = section_for_question(question_no)
        image_data = extracted_images[question_no - 1] if question_no - 1 < len(extracted_images) else {}
        correct_answer = str(lesson_answers.get(str(question_no), "")).upper()

        questions.append(
            {
                "id": f"TCF_TV5_{lesson}_Q{question_no:02d}",
                "questionNo": question_no,
                "section": section,
                "subType": sub_type,
                "prompt": "",
                "questionText": "",
                "documentText": image_data.get("documentText", ""),
                "documentImage": image_data.get("documentImage", ""),
                "materialImage": image_data.get("documentImage", ""),
                "questionImage": image_data.get("questionImage", ""),
                "sourcePage": image_data.get("sourcePage"),
                "sourcePdf": config["pdf"],
                "options": {"A": "", "B": "", "C": "", "D": ""},
                "correctAnswer": correct_answer if correct_answer in {"A", "B", "C", "D"} else "",
                "userAnswer": "",
                "explanation": "",
                "translation": "",
                "trap": "",
                "transferableRule": "",
                "audioStart": None,
                "audioEnd": None,
                "needsReview": True,
            }
        )

    return {
        "examType": "TCF",
        "source": "TV5MONDE",
        "livretNo": lesson,
        "title": config["title"],
        "pdfPath": config["pdf"],
        "audioPath": config["audio"],
        "questions": questions,
    }


def main() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    summary = []
    requested = [int(arg) for arg in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 18))
    for num in requested:
        paper = import_lesson(num)
        out_path = DATA_ROOT / f"L{num:02d}.json"
        out_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append((paper["livretNo"], len(paper["questions"])))
    print("Generated TCF TV5MONDE data:")
    for lesson, count in summary:
        print(f"- {lesson}: {count} extracted image-backed items, all needsReview=true")


if __name__ == "__main__":
    main()
