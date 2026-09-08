import pymupdf as fitz
import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

def normalize_text(text: str) -> str:
    """Normalize whitespace and typographic variations for resilient matching."""
    if not text:
        return ""
    # Normalize unicode quotes and dashes
    t = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    t = t.replace('—', '-').replace('–', '-').replace('…', '...')
    # Replace non-breaking spaces and line breaks with regular space
    t = re.sub(r'[\r\n\t\xa0]+', ' ', t)
    # Collapse multiple spaces
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

class PDFParser:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"PDF file not found: {self.filepath}")
        self.doc = fitz.open(str(self.filepath))
        self.total_pages = len(self.doc)

    def get_page_count(self) -> int:
        return self.total_pages

    def extract_page_text(self, page_num: int) -> Dict[str, Any]:
        """
        Extract text from a 1-indexed page number with layout metadata.
        """
        if page_num < 1 or page_num > self.total_pages:
            raise ValueError(f"Page number {page_num} out of bounds (1-{self.total_pages})")
        
        page = self.doc[page_num - 1]
        raw_text = page.get_text("text")
        
        # Extract blocks for layout awareness (tables / paragraphs)
        blocks = []
        for b in page.get_text("blocks"):
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if b[6] == 0:  # text block
                cleaned_block = normalize_text(b[4])
                if cleaned_block:
                    blocks.append({
                        "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                        "text": cleaned_block,
                        "block_no": b[5]
                    })

        return {
            "page_number": page_num,
            "raw_text": raw_text,
            "normalized_text": normalize_text(raw_text),
            "blocks": blocks,
            "char_count": len(raw_text)
        }

    def extract_document_pages(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract all pages or up to max_pages."""
        limit = min(self.total_pages, max_pages) if max_pages else self.total_pages
        pages = []
        for i in range(1, limit + 1):
            pages.append(self.extract_page_text(i))
        return pages

    def find_text_span(self, target_span: str, page_hint: Optional[int] = None) -> Dict[str, Any]:
        """
        Locate target text span in the document with fuzzy fallback.
        Returns matching page number, matched text, character offset, and confidence.
        """
        normalized_target = normalize_text(target_span)
        if not normalized_target:
            return {"found": False, "page": page_hint or 1, "matched_text": "", "confidence": 0.0}

        pages_to_check = []
        if page_hint and 1 <= page_hint <= self.total_pages:
            # Check hinted page first, then neighboring pages, then full document
            pages_to_check.append(page_hint)
            for offset in [1, -1, 2, -2]:
                p = page_hint + offset
                if 1 <= p <= self.total_pages and p not in pages_to_check:
                    pages_to_check.append(p)
        
        # Add any remaining pages
        for p in range(1, self.total_pages + 1):
            if p not in pages_to_check:
                pages_to_check.append(p)

        best_match = {
            "found": False,
            "page": page_hint or 1,
            "matched_text": target_span,
            "char_start": 0,
            "char_end": len(target_span),
            "confidence": 0.0
        }

        # Step 1: Exact or Normalized substring search
        for p_num in pages_to_check:
            page_data = self.extract_page_text(p_num)
            raw = page_data["raw_text"]
            norm = page_data["normalized_text"]

            # Exact in raw text
            if target_span in raw:
                start_idx = raw.index(target_span)
                return {
                    "found": True,
                    "page": p_num,
                    "matched_text": target_span,
                    "char_start": start_idx,
                    "char_end": start_idx + len(target_span),
                    "confidence": 1.0
                }

            # Exact in normalized text
            if normalized_target in norm:
                start_idx = norm.index(normalized_target)
                return {
                    "found": True,
                    "page": p_num,
                    "matched_text": normalized_target,
                    "char_start": start_idx,
                    "char_end": start_idx + len(normalized_target),
                    "confidence": 0.95
                }

        # Step 2: Token-based fuzzy search across hinted/candidate pages
        target_tokens = normalized_target.split()
        if len(target_tokens) >= 3:
            window_size = len(target_tokens)
            for p_num in pages_to_check[:10]:  # prioritize first candidate pages
                page_data = self.extract_page_text(p_num)
                norm_tokens = page_data["normalized_text"].split()
                if len(norm_tokens) < window_size:
                    continue
                
                # Sliding window token match
                for i in range(len(norm_tokens) - window_size + 1):
                    window = norm_tokens[i:i + window_size]
                    window_text = " ".join(window)
                    ratio = difflib.SequenceMatcher(None, normalized_target, window_text).ratio()
                    if ratio > best_match["confidence"]:
                        best_match = {
                            "found": ratio >= 0.70,
                            "page": p_num,
                            "matched_text": window_text,
                            "char_start": 0,
                            "char_end": len(window_text),
                            "confidence": round(ratio, 3)
                        }
                        if ratio >= 0.90:
                            return best_match

        return best_match

    def close(self):
        self.doc.close()
