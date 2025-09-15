"""
PDF Analyzer Module
Analyzes PDF structure and creates JSON with page-wise breaking information
"""

import fitz  # PyMuPDF
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

class PDFAnalyzer:
    """Analyzes PDF files to extract structure and chapter information"""
    
    def __init__(self):
        """Initialize the PDF analyzer"""
        self.patterns = [
            # Match e.g. 'SOLVED Self Assessment Paper-4', 'UNSOLVED Self Assessment Paper-4', 'SOLUTIONS Self Assessment Paper-4'
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)\s+Self\s+Assessment\s+Paper-\d+', re.IGNORECASE | re.MULTILINE),
            # Match e.g. 'Self Assessment Paper-4' (with or without solved/unsolved/solutions)
            re.compile(r'^Self\s+Assessment\s+Paper-\d+', re.IGNORECASE | re.MULTILINE),
            # Match e.g. 'Sample Question Paper-1', 'Sample Question SOLVED Paper-1'
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)?\s*Sample\s+Question\s+(?:SOLVED\s+)?Paper-\d+', re.IGNORECASE | re.MULTILINE),
            # Match e.g. 'Practice Paper-2', 'Mock Test-3', 'Test Paper-4', 'Question Paper-5'
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)?\s*(Practice|Mock|Test|Question)\s+(Paper|Test)?-\d+', re.IGNORECASE | re.MULTILINE),
            # Abbreviations
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)?\s*SQP\s*-\s*\d+', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)?\s*SAP\s*-\s*\d+', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^(SOLVED|UNSOLVED|SOLUTIONS)?\s*PP\s*-\s*\d+', re.IGNORECASE | re.MULTILINE),
            # Mind map, On tips
            re.compile(r'^Mind\s+Map\s*-\s*\d+', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^Mind\s+map', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^On\s+tips', re.IGNORECASE | re.MULTILINE),
            # Generic chapter/unit/part
            re.compile(r'^\s*(SOLVED|UNSOLVED|SOLUTIONS)?\s*(chapter|unit|part)\s*\d+\s*[:.\-]?\s*.*', re.IGNORECASE | re.MULTILINE),
        ]
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyzes a PDF file to extract book title, chapters, and other information.

        Args:
            pdf_path (str): The path to the PDF file.

        Returns:
            Dict[str, Any]: Analysis results with book title, chapters, and metadata.
        """
        try:
            doc = fitz.open(pdf_path)
            logger.info(f"Opened PDF with {doc.page_count} pages")
            
            # Extract book title
            book_title = self._extract_book_title(doc)
            
            # Find chapters using pattern matching
            found_chapters = self._find_chapters(doc)
            
            # Process chapters to determine page ranges
            chapters = self._process_chapters(found_chapters, doc.page_count)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(found_chapters, doc.page_count)
            
            result = {
                "confidence_score": confidence_score,
                "book_title": book_title,
                "book_start_page": 1,
                "book_end_page": doc.page_count,
                "chapters": chapters
            }
            
            doc.close()
            logger.info(f"Analysis completed with {len(chapters)} chapters found")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_book_title(self, doc: fitz.Document) -> str:
        """Extract book title from PDF metadata or first page"""
        # Try metadata first
        metadata = doc.metadata
        book_title = metadata.get('title', '').strip()
        
        if not book_title:
            # Try first page
            try:
                page = doc.load_page(0)
                text = page.get_text("text")
                lines = text.split('\n')
                if lines:
                    book_title = lines[0].strip()
            except Exception as e:
                logger.warning(f"Could not extract title from first page: {str(e)}")
        
        return book_title or "Unknown Title"
    
    def _find_chapters(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Find chapters in the PDF using pattern matching"""
        found_chapters = []
        
        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
                header_text = self._extract_header_text(page)
                
                page_matches = self._match_patterns(header_text)
                
                if page_matches:
                    # Get the best match (most specific)
                    page_matches.sort(key=lambda x: x['specificity'], reverse=True)
                    best_match = page_matches[0]
                    chapter_name = best_match['name']
                    
                    # Extract tag (SOLVED, UNSOLVED, SOLUTIONS, etc.)
                    words = chapter_name.strip().split()
                    tag = words[0] if words else "NA"
                    
                    # Avoid duplicates
                    if not any(fc['name'] == chapter_name and fc['page'] == page_num + 1 for fc in found_chapters):
                        found_chapters.append({
                            "name": chapter_name,
                            "page": page_num + 1,
                            "tag": tag
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing page {page_num + 1}: {str(e)}")
                continue
        
        # Sort by page number
        found_chapters.sort(key=lambda x: x['page'])
        return found_chapters
    
    def _extract_header_text(self, page: fitz.Page) -> str:
        """Extract text from the top portion of a page"""
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, ...)
        header_texts = []
        page_height = page.rect.height
        header_limit = page_height * 0.20  # Top 20% of the page
        
        for block in blocks:
            x0, y0, x1, y1, text, *_ = block
            if y0 < header_limit:
                header_texts.append(text.strip())
        
        return " ".join(header_texts)
    
    def _match_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Match text against chapter patterns"""
        matches = []
        
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                chapter_name = match.group(0).strip().replace('\n', ' ')
                matches.append({
                    "name": chapter_name,
                    "specificity": len(chapter_name)
                })
        
        return matches
    
    def _process_chapters(self, found_chapters: List[Dict[str, Any]], total_pages: int) -> List[Dict[str, Any]]:
        """Process found chapters to determine page ranges and add filename logic"""
        chapters = []
        
        for i, chapter in enumerate(found_chapters):
            start_page = chapter["page"]
            end_page = total_pages
            
            # Determine end page
            if i + 1 < len(found_chapters):
                next_chapter_page = found_chapters[i + 1]["page"]
                if next_chapter_page == start_page:
                    end_page = start_page
                else:
                    end_page = next_chapter_page - 1
            
            # Process chapter name to determine filename and folder
            chapter_name = chapter["name"]
            tag = chapter["tag"]
            
            pdf_filename, pdf_folder = self._determine_filename_and_folder(chapter_name, tag)
            
            chapter_data = {
                "chapter_name": chapter_name,
                "tag": tag,
                "chapter_start_page_number": start_page,
                "chapter_end_page_number": end_page
            }
            
            if pdf_filename and pdf_folder:
                chapter_data["pdf_filename"] = pdf_filename
                chapter_data["pdf_folder"] = pdf_folder
            
            chapters.append(chapter_data)
        
        return chapters
    
    def _determine_filename_and_folder(self, chapter_name: str, tag: str) -> Tuple[Optional[str], Optional[str]]:
        """Determine PDF filename and folder based on chapter name and tag"""
        # Check for Self Assessment Paper pattern
        sa_match = re.search(r'Self\s+Assessment\s+Paper[- ]?(\d+)', chapter_name, re.IGNORECASE)
        
        # Check for Practice Paper pattern
        practice_match = re.search(r'Practice\s+Paper[- ]?(\d+)', chapter_name, re.IGNORECASE)
        
        # Check for Question Paper pattern
        question_match = re.search(r'Question\s+Paper[- ]?(\d+)', chapter_name, re.IGNORECASE)
        
        # Handle Self Assessment Papers (SAP)
        if sa_match and tag == 'UNSOLVED':
            chapter_num = sa_match.group(1)
            return f"SAP-{chapter_num}.pdf", "question_papers"
        
        # Handle Practice Papers (PP)
        elif practice_match and tag == 'UNSOLVED':
            chapter_num = practice_match.group(1)
            return f"PP-{chapter_num}.pdf", "question_papers"
        
        # Handle Question Papers (SQP)
        elif question_match:
            chapter_num = question_match.group(1)
            
            if tag == 'SOLVED':
                return f"SQP-{chapter_num}.pdf", "question_papers"
            elif tag == 'SOLUTIONS':
                return f"SQP-{chapter_num}-SOLUTION.pdf", "answer_keys"
            elif tag == 'UNSOLVED':
                return f"SQP-{chapter_num}.pdf", "question_papers"
        
        return None, None
    
    def _calculate_confidence_score(self, found_chapters: List[Dict[str, Any]], total_pages: int) -> int:
        """Calculate confidence score based on analysis results"""
        if not found_chapters:
            return 30  # Low confidence if no chapters found
        
        # Base confidence
        confidence = 70
        
        # Increase confidence based on number of chapters found
        chapter_ratio = len(found_chapters) / total_pages
        if chapter_ratio > 0.1:  # More than 10% of pages have chapters
            confidence += 10
        
        # Increase confidence if we found specific patterns
        specific_patterns = ['SAP', 'SQP', 'PP', 'Practice', 'Question']
        for chapter in found_chapters:
            chapter_name = chapter['name'].upper()
            if any(pattern in chapter_name for pattern in specific_patterns):
                confidence += 5
                break
        
        return min(confidence, 95)  # Cap at 95%

def analyze_pdf(pdf_path: str) -> str:
    """
    Legacy function for backward compatibility
    
    Args:
        pdf_path (str): The path to the PDF file.
        
    Returns:
        str: JSON string with the analysis results.
    """
    analyzer = PDFAnalyzer()
    result = analyzer.analyze_pdf(pdf_path)
    return json.dumps(result, indent=4)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_pdf.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        analyzer = PDFAnalyzer()
        result = analyzer.analyze_pdf(pdf_path)
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
