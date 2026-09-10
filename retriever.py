import re


def search_chunks(
    query: str,
    chunks: list[dict[str, int | str]],
    top_k: int = 3,
) -> list[dict[str, int | str]]:
    """Find chunks containing words from the user's query."""

    keywords = re.findall(
        r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+",
        query.lower(),
    )

    results = []

    for chunk in chunks:
        chunk_text = str(chunk["text"]).lower()

        score = sum(
            chunk_text.count(keyword)
            for keyword in keywords
        )

        if score > 0:
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "score": score,
            })

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )
    return results[:top_k]
