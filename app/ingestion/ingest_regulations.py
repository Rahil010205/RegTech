"""Batch ingestion script for regulatory PDFs."""

import json
from pathlib import Path
from loguru import logger
import fitz

from app.database.session import SessionLocal
from app.ingestion.ingestion_pipeline import IngestionPipeline, IngestionOptions

REGULATIONS_DIR = Path("data/regulations/rbi")
MANIFEST_PATH = REGULATIONS_DIR / "manifest.json"

def load_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["filename"]: item for item in data}
    except Exception as e:
        logger.error("Failed to load manifest: {}", e)
        return {}

def ingest_all():
    manifest = load_manifest()
    
    if not REGULATIONS_DIR.exists():
        print(f"Error: Regulations directory not found at {REGULATIONS_DIR}")
        return
        
    pdf_files = list(REGULATIONS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {REGULATIONS_DIR}")
        return
        
    # Sort files so that KYC - NBFCs.pdf is processed first
    pdf_files.sort(key=lambda p: (0 if "nbfc" in p.name.lower() else 1, p.name.lower()))
    
    print("REGULATORY INGESTION")
    print("====================")
    print(f"\nFound {len(pdf_files)} PDF documents.\n")
    
    processed = 0
    failed = 0
    clauses_created = 0
    embeddings_created = 0
    duplicates_skipped = 0
    
    with SessionLocal() as session:
        pipeline = IngestionPipeline(session)
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            filename = pdf_path.name
            manifest_info = manifest.get(filename, {})
            title = manifest_info.get("title")
            regulator = manifest_info.get("regulator", "RBI")
            source_type = manifest_info.get("source_type", "regulatory_document")
            
            options = IngestionOptions(
                regulator_code=regulator,
                title=title,
                document_type=source_type,
                skip_if_duplicate=True
            )
            
            try:
                result = pipeline.ingest_document(pdf_path, options)
                
                pages = result.pages_processed
                if result.duplicate:
                    duplicates_skipped += 1
                    with fitz.open(pdf_path) as doc:
                        pages = len(doc)
                else:
                    clauses_created += result.clauses_created
                    embeddings_created += result.embeddings_created
                
                processed += 1
                
                print(f"[{idx}/{len(pdf_files)}] {filename}")
                print(f"    Pages: {pages}")
                print(f"    Clauses extracted: {result.clauses_created}")
                print(f"    Embeddings generated: {result.embeddings_created if not result.duplicate else 0}")
                print("    Status: SUCCESS")
                print()
                
            except Exception as e:
                failed += 1
                print(f"[{idx}/{len(pdf_files)}] {filename}")
                print(f"    Status: FAILED")
                print(f"    Error: {e}")
                print()
                logger.exception("Failed to ingest document {}", filename)
                
    print("INGESTION SUMMARY")
    print("=================")
    print(f"Documents discovered: {len(pdf_files)}")
    print(f"Documents processed: {processed}")
    print(f"Documents failed: {failed}")
    print(f"Clauses created: {clauses_created}")
    print(f"Embeddings created: {embeddings_created}")
    print(f"Duplicates skipped: {duplicates_skipped}")

if __name__ == "__main__":
    ingest_all()
