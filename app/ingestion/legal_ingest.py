"""Standalone batch CLI for ingesting legal PDFs (SHOWCASE).

This is a REFERENCE implementation demonstrating the ingestion pipeline:
  1. OCR (tesseract + pdf2image)
  2. Article-based chunking
  3. Embedding generation
  4. Bulk upsert into knowledge base

Not production code — configuration values and model names are illustrative.
"""
import argparse
import hashlib
import os
import sys
import time
from typing import List

import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from app.ingestion.legal_chunker import chunk_legal_text

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

EMBEDDING_MODEL = "example/embedding-model"
EMBEDDING_DIM = 768
BATCH_SIZE = 50
OCR_DPI = 200


def _ocr_pdf(pdf_path: str) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        print("ERROR: pdf2image and pytesseract required.")
        sys.exit(1)
    images = convert_from_path(pdf_path, dpi=OCR_DPI)
    text_parts = []
    for page_num, img in enumerate(images, 1):
        page_text = pytesseract.image_to_string(img, lang="ara+fra")
        text_parts.append(page_text)
        print(f"  OCR'd page {page_num}/{len(images)}", end="\r")
    print()
    return "\n".join(text_parts)


def _process_pdf(
    pdf_path: str,
    model: SentenceTransformer,
    conn: psycopg2.extensions.connection,
) -> int:
    filename = os.path.basename(pdf_path)
    print(f"Processing: {filename}")

    text = _ocr_pdf(pdf_path)
    if not text.strip():
        print(f"  WARNING: No text extracted from {filename}, skipping")
        return 0

    chunks = chunk_legal_text(text, source_pdf=filename)
    if not chunks:
        print(f"  WARNING: No chunks generated for {filename}")
        return 0

    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=16)
    embeddings = [e.tolist() for e in embeddings]

    with conn.cursor() as cur:
        from psycopg2.extras import execute_values
        values = []
        for chunk, emb in zip(chunks, embeddings):
            metadata = chunk["metadata"].copy()
            metadata["category"] = "regulations"
            content_hash = hashlib.sha256(chunk["content"].encode("utf-8")).hexdigest()
            values.append((
                chunk["content"],
                emb,
                metadata,
                "regulations",
                "approved",
                content_hash,
                "pdf",
            ))
        execute_values(
            cur,
            """
            INSERT INTO knowledge_base (content, embedding, metadata, category, moderation_status, content_hash, source_file_type)
            VALUES %s
            ON CONFLICT (content_hash) DO NOTHING
            """,
            values,
            template="(%s, %s::vector, %s::jsonb, %s, %s, %s, %s)",
        )
    conn.commit()
    print(f"  Inserted {len(chunks)} chunks")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest legal PDFs into knowledge base")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing PDF files")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Batch size for DB inserts")
    args = parser.parse_args()

    if not os.path.isdir(args.pdf_dir):
        print(f"ERROR: PDF directory not found: {args.pdf_dir}")
        sys.exit(1)

    pdf_files = sorted([
        os.path.join(args.pdf_dir, f)
        for f in os.listdir(args.pdf_dir)
        if f.lower().endswith(".pdf")
    ])
    if not pdf_files:
        print(f"No PDF files found in {args.pdf_dir}")
        sys.exit(0)
    print(f"Found {len(pdf_files)} PDFs to process")

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded")

    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    conn.autocommit = False
    print("Connected")

    total_chunks = 0
    start_time = time.time()
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            chunk_count = _process_pdf(pdf_path, model, conn)
            total_chunks += chunk_count
            elapsed = time.time() - start_time
            rate = i / elapsed * 3600 if elapsed > 0 else 0
            print(f"  [{i}/{len(pdf_files)}] ~{rate:.0f} PDFs/hr, {total_chunks} total chunks")
        except Exception as e:
            conn.rollback()
            print(f"  ERROR processing {pdf_path}: {e}")

    elapsed = time.time() - start_time
    print(f"\nDone: {len(pdf_files)} PDFs, {total_chunks} chunks in {elapsed/60:.1f} minutes")
    conn.close()


if __name__ == "__main__":
    main()
