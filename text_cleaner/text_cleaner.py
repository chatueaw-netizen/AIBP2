"""
text_cleaner.py — Claude Code component
Receives raw GPT output from Make.com, cleans formatting, returns polished text.
Run: python text_cleaner.py
Make.com calls POST http://<your-ip>:5000/clean with JSON body {"text": "...", "date": "YYYY-MM-DD"}
"""

import re
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)


def clean_text(text: str) -> str:
    """
    Cleans GPT-generated labor market briefing text:
    - Deduplicates lines
    - Standardizes bullet characters to dashes
    - Normalizes numbered list spacing
    - Collapses excess blank lines
    - Trims trailing whitespace per line
    """
    lines = text.splitlines()

    # Deduplicate non-blank lines while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for line in lines:
        key = line.strip().lower()
        if key == "":
            deduped.append("")
        elif key not in seen:
            seen.add(key)
            deduped.append(line)

    text = "\n".join(deduped)

    # Standardize bullet variants (*, •, ·, –, —) to -
    text = re.sub(r"^[ \t]*[*•·–—]\s+", "- ", text, flags=re.MULTILINE)

    # Normalize numbered list items: "1)" or "1." with inconsistent spacing → "1. "
    text = re.sub(r"^[ \t]*(\d+)[.)]\s+", r"\1. ", text, flags=re.MULTILINE)

    # Trim trailing whitespace on every line
    text = "\n".join(line.rstrip() for line in text.splitlines())

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def validate_structure(text: str) -> dict:
    """
    Checks that the briefing contains all expected sections.
    Returns a dict of which sections are present.
    """
    required = ["SUMMARY", "KEY HIGHLIGHTS", "ACTION ITEMS", "MARKET SENTIMENT"]
    return {section: section in text.upper() for section in required}


@app.route("/clean", methods=["POST"])
def clean_endpoint():
    payload = request.get_json(silent=True)
    if not payload or "text" not in payload:
        return jsonify({"error": "Request body must include a 'text' field"}), 400

    raw = payload["text"]
    date_str = payload.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    cleaned = clean_text(raw)
    structure = validate_structure(cleaned)
    missing = [k for k, v in structure.items() if not v]

    response = {
        "cleaned_text": cleaned,
        "date": date_str,
        "stats": {
            "original_chars": len(raw),
            "cleaned_chars": len(cleaned),
            "chars_removed": len(raw) - len(cleaned),
        },
        "quality": {
            "all_sections_present": len(missing) == 0,
            "missing_sections": missing,
        },
    }

    # Log to console for the run book audit trail
    print(
        f"[{datetime.utcnow().isoformat()}] Cleaned {len(raw)} → {len(cleaned)} chars | "
        f"Missing sections: {missing or 'none'}"
    )

    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


if __name__ == "__main__":
    print("Text Cleaner service starting on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
