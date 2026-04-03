from app.llm_client import LLMError, chat_completion

CHUNK_USER_TEMPLATE = """This is part {index} of {total} of a longer document. Write a short markdown note (no fenced code blocks). Stay close to the text.

Cover:
- What this part is mainly about
- A few bullet points for the key ideas
- Standout facts, names, or numbers if any

Part:
---
{chunk}
---
"""

FINAL_USER_TEMPLATE = """These are notes from different sections of one document. Combine them into a single markdown summary for a reader (no fenced code blocks). Keep tone matter-of-fact, not salesy or stiff.

Use exactly these headings:

## What this document is about
## Key points
## Important details
## Takeaway

Section notes:

---
{combined}
---
"""


def summarize_chunk(chunk: str, index: int, total: int) -> str:
    prompt = CHUNK_USER_TEMPLATE.format(
        index=index,
        total=total,
        chunk=chunk.strip(),
    )
    return chat_completion(
        [
            {
                "role": "system",
                "content": "You summarize document excerpts in plain markdown. Be accurate and brief.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )


def summarize_merged(section_summaries: list[str]) -> str:
    if not section_summaries:
        raise LLMError("No section summaries to merge.")
    combined = "\n\n---\n\n".join(section_summaries)
    prompt = FINAL_USER_TEMPLATE.format(combined=combined)
    return chat_completion(
        [
            {
                "role": "system",
                "content": "You merge section notes into one clear document summary in markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )


def hierarchical_summary(text_chunks: list[str]) -> str:
    if not text_chunks:
        raise LLMError("No text to summarize.")
    total = len(text_chunks)
    section_summaries: list[str] = []
    for i, chunk in enumerate(text_chunks, start=1):
        section_summaries.append(summarize_chunk(chunk, i, total))
    return summarize_merged(section_summaries)
