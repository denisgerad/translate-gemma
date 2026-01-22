import re
import json

SCRIPTS = {
    "Hindi": r"\u0900-\u097F",
    "Tamil": r"\u0B80-\u0BFF",
    "Telugu": r"\u0C00-\u0C7F",
    "Malayalam": r"\u0D00-\u0D7F",
    "Kannada": r"\u0C80-\u0CFF"
}


def qa_checks(source, translation, lang):
    issues = []

    # 1. Empty
    if not translation or not str(translation).strip():
        issues.append("EMPTY_OUTPUT")

    text = str(translation or "")
    src = str(source or "")

    # 2. English leakage
    if re.search(r"[A-Za-z]{4,}", text):
        issues.append("ENGLISH_WORDS_PRESENT")

    # 3. Wrong script
    if lang in SCRIPTS:
        if not re.search(f"[{SCRIPTS[lang]}]", text):
            issues.append("WRONG_SCRIPT")

    # 4. Too short
    try:
        if len(text) < 0.6 * len(src):
            issues.append("TOO_SHORT")
    except Exception:
        pass

    # 5. Repeated sentence (naive)
    parts = text.split("।") if lang == "Hindi" else text.split(".")
    if len(parts) >= 3 and parts[-1].strip() and parts[-1].strip() == parts[-2].strip():
        issues.append("DUPLICATED_SEGMENT")

    # 6. Instruction leakage
    bad_words = ["translate", "style", "output", "use formal", "text:"]
    if any(w.lower() in text.lower() for w in bad_words):
        issues.append("PROMPT_LEAKAGE")

    return issues


if __name__ == '__main__':
    import sys
    # quick runner: python tools/qa_checks.py batch_output.json
    if len(sys.argv) < 2:
        print("Usage: python tools/qa_checks.py <batch_output.json>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    report = []
    for entry in data:
        src = entry.get('input', {}).get('text','')
        trans = entry.get('translation', {})
        for lang, out in trans.items():
            if lang == 'Source':
                continue
            issues = qa_checks(src, out, lang)
            report.append({'lang': lang, 'issues': issues, 'output_sample': (out[:120] + '...') if out else ''})
    print(json.dumps(report, ensure_ascii=False, indent=2))
