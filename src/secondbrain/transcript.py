"""Pure projection of ledger-referenced conversion and verified OCR."""
import hashlib
import re
import unicodedata


def has_native_text(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"data:[^\s)]+", "", text)
    text = text.replace("[IMAGE]", "")
    text = re.sub(r"^\|?[\s:|-]+\|?$", "", text, flags=re.M)
    return any(unicodedata.category(char)[0] in "LN" for char in text)


def _verified(item):
    for key, unit in sorted(item.meta["ocr"]["units"].items()):
        if unit["status"] == "verified":
            attempt = unit["attempts"][-1]
            yield key, unit, attempt, (item.path / attempt["file"]).read_bytes().decode("utf-8")


def view(item):
    """Join blocks with two LFs; preserve each block's bytes, including final LFs."""
    blocks = []
    if item.meta["conversion"] is not None:
        blocks.append((item.path / "converted.md").read_bytes().decode("utf-8"))
    for key, unit, attempt, text in _verified(item):
        recorded, verified = attempt["recorded"], attempt["verified"]
        heading = (f"## OCR {key} (source {unit['source']}; "
                   f"transcribed {recorded['peer']}/{recorded['model']} {recorded['date']}; "
                   f"verified {verified['peer']}/{verified['model']} {verified['date']})")
        blocks.append(heading + "\n\n" + text)
    return "\n\n".join(blocks)


def source_digest(item):
    return hashlib.sha256(view(item).encode("utf-8")).hexdigest()


def accepted_text_present(item):
    if item.meta["has_native_text"]:
        return True
    return any(has_native_text(text.replace("[illegible]", "").replace("[no text]", ""))
               for _, _, _, text in _verified(item))
