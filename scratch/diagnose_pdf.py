import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.text_cleaner import TextCleaner
from app.ingestion.clause_splitter import ClauseSplitter

def main():
    pdf_path = Path("data/regulations/rbi/KYC - NBFCs.pdf")
    if not pdf_path.exists():
        print(f"Error: File {pdf_path} not found.")
        return

    print("Loading PDF...")
    loader = PDFLoader(pdf_path)
    pages = loader.load_pdf()
    
    print("Cleaning pages...")
    cleaner = TextCleaner()
    cleaned_pages = cleaner.clean_pages(pages)
    
    print("Splitting clauses...")
    splitter = ClauseSplitter()
    clauses = splitter.split_pages(cleaned_pages)
    
    print(f"Total extracted clauses: {len(clauses)}")
    
    unique_ids = set()
    duplicate_ids = set()
    for c in clauses:
        num = c["clause_number"]
        if num in unique_ids:
            duplicate_ids.add(num)
        else:
            unique_ids.add(num)
            
    print(f"Unique clause identifiers: {len(unique_ids)}")
    print(f"Duplicate identifiers: {len(duplicate_ids)}")
    
    if duplicate_ids:
        print("\n--- DUPLICATES DETECTED ---")
        for dup in sorted(list(duplicate_ids))[:10]:
            dup_clauses = [c for c in clauses if c["clause_number"] == dup]
            print(f"Duplicate: clause_number={dup}")
            for dc in dup_clauses:
                safe_text = dc['text'][:80].encode('ascii', errors='replace').decode('ascii')
                print(f"  Page: {dc['page_number']} | Text: {safe_text}...")

    # Print first 50 clauses to see what they look like
    print("\n--- FIRST 50 CLAUSES ---")
    for idx, c in enumerate(clauses[:50]):
        num = c["clause_number"]
        title = c.get("title") or ""
        sec = c.get("section") or ""
        p = c.get("page_number")
        text = c["text"][:100].replace('\n', ' ')
        safe_num = str(num).encode('ascii', errors='replace').decode('ascii')
        safe_title = str(title).encode('ascii', errors='replace').decode('ascii')
        safe_sec = str(sec).encode('ascii', errors='replace').decode('ascii')
        safe_text = str(text).encode('ascii', errors='replace').decode('ascii')
        print(f"[{idx}] Num: '{safe_num}' | Title: '{safe_title}' | Sec: '{safe_sec}' | Page: {p}")
        print(f"    Text: {safe_text}...")

if __name__ == "__main__":
    main()
