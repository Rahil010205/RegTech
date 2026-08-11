"""Regulatory document ingestion pipeline.

Orchestrates the full flow:
    PDF → PDFLoader → TextCleaner → ClauseSplitter → MetadataExtractor → JSON

Usage (run from project root)::

    python ingestion/ingestion_pipeline.py --pdf data/raw/rbi_kyc.pdf
    python ingestion/ingestion_pipeline.py --pdf data/raw/rbi_kyc.pdf --out data/processed/

Output file: ``<out_dir>/<pdf_stem>_clauses.json``

Each record in the output JSON has shape::

    {
        "id":             "RBI-KYC-3.1",
        "chapter":        "Customer Due Diligence",
        "clause_number":  "3.1",
        "level":          2,
        "parent_clause":  "3",
        "text":           "...",
        "regulator":      "RBI",
        "document_name":  "Master Direction – KYC Direction, 2016",
        "document_type":  "master direction",
        "effective_date": "2016-02-25",
        "page_number":    null,
        "filename":       "rbi_kyc.pdf"
    }
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# ── Allow running from repo root without installing the package ──────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ingestion.clause_splitter import ClauseSplitter
from app.ingestion.metadata_extractor import MetadataExtractor
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.text_cleaner import TextCleaner

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("ingestion_pipeline")


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def _build_clause_id(regulator: str, doc_name: str, clause_number: str) -> str:
    """Build a deterministic clause ID like ``RBI-KYC-3.1``.

    Algorithm:
        - Regulator code (up to 5 chars, uppercase)
        - Abbreviated doc name: first letters of significant words, max 6 chars
        - Clause number as-is
    """
    reg = (regulator or "DOC").upper()[:5]

    # Abbreviate document name: pick words ≥3 chars, take first letter
    words = re.findall(r"[A-Za-z]{3,}", doc_name or "")
    stop_words = {"the", "and", "for", "with", "from", "that", "this",
                  "direction", "directions", "master", "circular", "rbi"}
    abbrev_parts = [w[0].upper() for w in words if w.lower() not in stop_words]
    abbrev = "".join(abbrev_parts[:6]) or "DOC"

    return f"{reg}-{abbrev}-{clause_number}"


# ---------------------------------------------------------------------------
# Required metadata fields for completeness reporting
# ---------------------------------------------------------------------------
_REQUIRED_META_FIELDS = ["regulator", "document_name", "effective_date", "chapter"]


def run_pipeline(pdf_path: Path, out_dir: Path) -> Path:
    """Execute the full ingestion pipeline.

    Args:
        pdf_path: Path to the source PDF.
        out_dir:  Directory where the JSON output will be written.

    Returns:
        Path to the written JSON file.
    """
    logger.info("═══ Ingestion Pipeline Start ═══")
    logger.info("Input:  %s", pdf_path)
    logger.info("Output: %s", out_dir)

    # ── Step 1: Load PDF ──────────────────────────────────────────────────
    logger.info("[1/4] Loading PDF …")
    loader = PDFLoader(pdf_path)
    pages = loader.load_pdf()
    pdf_meta = loader.get_metadata()
    logger.info("      Loaded %d pages from '%s'", pdf_meta["total_pages"], pdf_meta["filename"])

    # ── Step 2: Clean text ────────────────────────────────────────────────
    logger.info("[2/4] Cleaning text …")
    cleaner = TextCleaner()
    clean_doc = cleaner.clean_document(pages)
    logger.info("      Cleaned document: %d characters", len(clean_doc))

    # ── Step 3: Split into clauses ────────────────────────────────────────
    logger.info("[3/4] Splitting clauses …")
    splitter = ClauseSplitter()
    clause_records = splitter.split(clean_doc)
    logger.info("      Extracted %d clause candidates", len(clause_records))

    # ── Step 4: Extract metadata ──────────────────────────────────────────
    logger.info("[4/4] Extracting document metadata …")
    extractor = MetadataExtractor()
    doc_meta = extractor.extract(clean_doc, pdf_path.name)
    doc_meta["total_pages"] = pdf_meta["total_pages"]
    logger.info(
        "      regulator=%s  doc_type=%s  date=%s",
        doc_meta.get("regulator", "?"),
        doc_meta.get("document_type", "?"),
        doc_meta.get("effective_date", "?"),
    )

    # ── Assemble output records ───────────────────────────────────────────
    output_records: list[dict] = []
    clauses_missing_meta: list[str] = []

    for clause in clause_records:
        clause_id = _build_clause_id(
            doc_meta.get("regulator", ""),
            doc_meta.get("document_name", ""),
            clause["clause_number"],
        )

        record = {
            "id":             clause_id,
            "chapter":        doc_meta.get("chapter", ""),
            "clause_number":  clause["clause_number"],
            "level":          clause["level"],
            "parent_clause":  clause["parent_clause"],
            "text":           clause["text"],
            "regulator":      doc_meta.get("regulator", ""),
            "document_name":  doc_meta.get("document_name", ""),
            "document_type":  doc_meta.get("document_type", ""),
            "effective_date": doc_meta.get("effective_date", ""),
            "page_number":    None,   # page-level mapping is a future enhancement
            "filename":       pdf_path.name,
        }

        # Track completeness
        missing = [f for f in _REQUIRED_META_FIELDS if not record.get(f)]
        if missing:
            clauses_missing_meta.append(clause_id)

        output_records.append(record)

    # ── Write output JSON ─────────────────────────────────────────────────
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{pdf_path.stem}_clauses.json"
    with out_file.open("w", encoding="utf-8") as fp:
        json.dump(output_records, fp, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────
    logger.info("")
    logger.info("═══ Ingestion Pipeline Summary ═══")
    logger.info("  Total clauses extracted  : %d", len(output_records))
    logger.info("  Clauses missing metadata : %d", len(clauses_missing_meta))
    if clauses_missing_meta:
        logger.info(
            "  Affected IDs (sample)    : %s",
            ", ".join(clauses_missing_meta[:5]) + (" …" if len(clauses_missing_meta) > 5 else ""),
        )
    logger.info("  Output written to        : %s", out_file)
    logger.info("══════════════════════════════════")

    return out_file


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a regulatory PDF and produce a structured JSON clause file."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        type=Path,
        help="Path to the source PDF file (e.g. data/raw/rbi_kyc.pdf)",
    )
    parser.add_argument(
        "--out",
        default=Path("data/processed"),
        type=Path,
        help="Output directory (default: data/processed/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        out_file = run_pipeline(args.pdf, args.out)
        print(f"\n✅  Done. Clauses saved to: {out_file}")
    except Exception as exc:  # noqa: BLE001
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        sys.exit(1)
