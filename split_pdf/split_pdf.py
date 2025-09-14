"""
PDF Splitter Module
Splits PDF files based on analysis JSON configuration
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from PyPDF2 import PdfReader, PdfWriter
import tempfile

logger = logging.getLogger(__name__)

class PDFSplitter:
    """Splits PDF files based on chapter analysis"""
    
    def __init__(self):
        """Initialize the PDF splitter"""
        pass
    
    def split_pdf_by_json(
        self,
        pdf_path: str,
        analysis_data: Dict[str, Any],
        output_dir: str
    ) -> List[Dict[str, str]]:
        """
        Split PDF based on analysis JSON data
        
        Args:
            pdf_path: Path to the source PDF file
            analysis_data: Analysis data containing chapter information
            output_dir: Directory to save split PDFs
            
        Returns:
            List of dictionaries with split file information
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Create output directories
            question_dir = os.path.join(output_dir, 'question_papers')
            answer_dir = os.path.join(output_dir, 'answer_keys')
            
            os.makedirs(question_dir, exist_ok=True)
            os.makedirs(answer_dir, exist_ok=True)
            
            # Read the PDF
            reader = PdfReader(pdf_path)
            logger.info(f"Opened PDF with {len(reader.pages)} pages")
            
            split_files = []
            chapters = analysis_data.get('chapters', [])
            
            for idx, chapter in enumerate(chapters, 1):
                try:
                    result = self._split_chapter(reader, chapter, question_dir, answer_dir)
                    if result:
                        split_files.append(result)
                        logger.info(f"Split chapter {idx}: {result['filename']}")
                except Exception as e:
                    logger.error(f"Error splitting chapter {idx}: {str(e)}")
                    continue
            
            logger.info(f"Successfully split PDF into {len(split_files)} files")
            return split_files
            
        except Exception as e:
            logger.error(f"Error splitting PDF: {str(e)}")
            raise
    
    def _split_chapter(
        self,
        reader: PdfReader,
        chapter: Dict[str, Any],
        question_dir: str,
        answer_dir: str
    ) -> Optional[Dict[str, str]]:
        """
        Split a single chapter from the PDF
        
        Args:
            reader: PDF reader object
            chapter: Chapter information from analysis
            question_dir: Directory for question papers
            answer_dir: Directory for answer keys
            
        Returns:
            Dictionary with split file information or None if failed
        """
        # Get chapter details
        start_page = chapter.get('chapter_start_page_number')
        end_page = chapter.get('chapter_end_page_number')
        pdf_filename = chapter.get('pdf_filename')
        pdf_folder = chapter.get('pdf_folder')
        chapter_name = chapter.get('chapter_name', 'unknown')
        
        # Validate required fields
        if start_page is None or end_page is None:
            logger.warning(f"Skipping chapter '{chapter_name}' - missing page numbers")
            return None
        
        if not pdf_filename or not pdf_folder:
            logger.warning(f"Skipping chapter '{chapter_name}' - missing filename or folder")
            return None
        
        # Validate page numbers
        if start_page < 1 or end_page < start_page or start_page > len(reader.pages):
            logger.warning(f"Skipping chapter '{chapter_name}' - invalid page numbers: {start_page}-{end_page}")
            return None
        
        # Create PDF writer for this chapter
        writer = PdfWriter()
        
        # Add pages to the writer (convert to 0-based indexing)
        pages_added = 0
        for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
            try:
                writer.add_page(reader.pages[page_num])
                pages_added += 1
            except Exception as e:
                logger.warning(f"Error adding page {page_num + 1} to chapter '{chapter_name}': {str(e)}")
                continue
        
        if pages_added == 0:
            logger.warning(f"No pages added for chapter '{chapter_name}'")
            return None
        
        # Determine output path
        if pdf_folder == 'question_papers':
            output_path = os.path.join(question_dir, pdf_filename)
        elif pdf_folder == 'answer_keys':
            output_path = os.path.join(answer_dir, pdf_filename)
        else:
            logger.warning(f"Unknown folder type '{pdf_folder}' for chapter '{chapter_name}'")
            return None
        
        # Write the split PDF
        try:
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return {
                'filename': pdf_filename,
                'folder': pdf_folder,
                'path': output_path,
                'pages': f"{start_page}-{end_page}",
                'page_count': pages_added,
                'chapter_name': chapter_name
            }
            
        except Exception as e:
            logger.error(f"Error writing split PDF for chapter '{chapter_name}': {str(e)}")
            return None
    
    def split_pdf_from_json_file(
        self,
        pdf_path: str,
        json_path: str,
        output_dir: str
    ) -> List[Dict[str, str]]:
        """
        Split PDF using analysis data from JSON file
        
        Args:
            pdf_path: Path to the source PDF file
            json_path: Path to the analysis JSON file
            output_dir: Directory to save split PDFs
            
        Returns:
            List of dictionaries with split file information
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            return self.split_pdf_by_json(pdf_path, analysis_data, output_dir)
            
        except Exception as e:
            logger.error(f"Error reading JSON file {json_path}: {str(e)}")
            raise
    
    def validate_analysis_data(self, analysis_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate analysis data structure
        
        Args:
            analysis_data: Analysis data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ['book_title', 'chapters']
        for field in required_fields:
            if field not in analysis_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate chapters
        if 'chapters' in analysis_data:
            chapters = analysis_data['chapters']
            if not isinstance(chapters, list):
                errors.append("Chapters must be a list")
            else:
                for i, chapter in enumerate(chapters):
                    if not isinstance(chapter, dict):
                        errors.append(f"Chapter {i} must be a dictionary")
                        continue
                    
                    # Check required chapter fields
                    required_chapter_fields = [
                        'chapter_name', 'tag', 'chapter_start_page_number', 'chapter_end_page_number'
                    ]
                    for field in required_chapter_fields:
                        if field not in chapter:
                            errors.append(f"Chapter {i} missing required field: {field}")
                    
                    # Validate page numbers
                    start_page = chapter.get('chapter_start_page_number')
                    end_page = chapter.get('chapter_end_page_number')
                    
                    if start_page is not None and not isinstance(start_page, int):
                        errors.append(f"Chapter {i} start_page must be an integer")
                    if end_page is not None and not isinstance(end_page, int):
                        errors.append(f"Chapter {i} end_page must be an integer")
                    
                    if (isinstance(start_page, int) and isinstance(end_page, int) and 
                        start_page > end_page):
                        errors.append(f"Chapter {i} start_page ({start_page}) > end_page ({end_page})")
        
        return len(errors) == 0, errors

def split_pdf_by_json(json_path: str, pdf_root_dir: str = None, split_root_dir: str = None):
    """
    Legacy function for backward compatibility
    
    Args:
        json_path: Path to the analysis JSON file
        pdf_root_dir: Root directory containing PDF files
        split_root_dir: Root directory for split PDFs
    """
    # Set default directories if not provided
    if pdf_root_dir is None:
        pdf_root_dir = os.path.join(os.path.dirname(__file__), 'pdf')
    if split_root_dir is None:
        split_root_dir = os.path.join(os.path.dirname(__file__), 'pdf_split')
    
    # Load analysis data
    with open(json_path, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)
    
    # Determine PDF filename
    pdf_filename = analysis_data.get('pdf_filename')
    if not pdf_filename:
        # Try to infer from JSON filename
        base = os.path.splitext(os.path.basename(json_path))[0]
        pdf_filename = base + '.pdf'
    
    # Find PDF file
    pdf_path = None
    subject = "default"
    
    # Search in subject folders
    if os.path.exists(pdf_root_dir):
        for item in os.listdir(pdf_root_dir):
            item_path = os.path.join(pdf_root_dir, item)
            if os.path.isdir(item_path):
                potential_pdf = os.path.join(item_path, pdf_filename)
                if os.path.exists(potential_pdf):
                    pdf_path = potential_pdf
                    subject = item
                    break
    
    # Fallback to root directory
    if pdf_path is None:
        pdf_path = os.path.join(pdf_root_dir, pdf_filename)
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_filename}")
    
    # Create output directory
    output_dir = os.path.join(split_root_dir, subject)
    os.makedirs(output_dir, exist_ok=True)
    
    # Split the PDF
    splitter = PDFSplitter()
    split_files = splitter.split_pdf_by_json(pdf_path, analysis_data, output_dir)
    
    print(f"Split PDF into {len(split_files)} files:")
    for file_info in split_files:
        print(f"  {file_info['filename']} ({file_info['pages']}) -> {file_info['path']}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python split_pdf.py <json_path> [pdf_root_dir] [split_root_dir]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    pdf_root_dir = sys.argv[2] if len(sys.argv) > 2 else None
    split_root_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        split_pdf_by_json(json_path, pdf_root_dir, split_root_dir)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
