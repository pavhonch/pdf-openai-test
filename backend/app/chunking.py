def chunk_text(
    text: str,
    target: int = 7000,
    hard_max: int = 8800,
    merge_if_under: int = 800,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(current.strip())
            current = ""

    for para in paragraphs:
        if len(para) > hard_max:
            flush()
            start = 0
            while start < len(para):
                end = min(start + target, len(para))
                piece = para[start:end]
                chunks.append(piece.strip())
                start = end
            continue

        addition = para if not current else f"{current}\n\n{para}"
        if len(addition) <= hard_max:
            current = addition
        else:
            flush()
            current = para

    flush()

    if len(chunks) >= 2 and len(chunks[-1]) < merge_if_under:
        merged = f"{chunks[-2]}\n\n{chunks[-1]}"
        if len(merged) <= hard_max + 500:
            chunks[-2] = merged
            chunks.pop()

    return [c for c in chunks if c]
