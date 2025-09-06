def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200):
    if not text:
        return []
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end].strip()
        if len(chunk) > 10:
            chunks.append(chunk)
        if end == n: break
        start = max(0, end - overlap)
    return chunks

