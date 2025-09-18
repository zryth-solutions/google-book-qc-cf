"""
Semantic Chunking for Markdown Content
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken
from metadata_extractor import MetadataExtractor, EnhancedMetadata

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    """Represents a semantic chunk of text with enhanced metadata"""
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    metadata: Dict[str, Any]
    enhanced_metadata: Optional[EnhancedMetadata] = None
    
    @property
    def id(self) -> str:
        """Generate unique ID for the chunk"""
        return f"chunk_{self.chunk_index}_{hash(self.content) % 10000:04d}"

class SemanticChunker:
    """Performs semantic chunking on markdown content"""
    
    def __init__(self, 
                 max_chunk_size: int = 1000,
                 overlap_size: int = 200,
                 min_chunk_size: int = 100,
                 encoding_name: str = "cl100k_base",
                 enable_enhanced_metadata: bool = True):
        """
        Initialize the semantic chunker
        
        Args:
            max_chunk_size: Maximum size of each chunk in tokens
            overlap_size: Number of tokens to overlap between chunks
            min_chunk_size: Minimum size of each chunk in tokens
            encoding_name: Tokenizer encoding name
            enable_enhanced_metadata: Whether to extract enhanced metadata
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.enable_enhanced_metadata = enable_enhanced_metadata
        self.metadata_extractor = MetadataExtractor() if enable_enhanced_metadata else None
    
    def chunk_markdown(self, markdown_content: str, book_name: str, chapter: Optional[int] = None) -> List[Chunk]:
        """
        Chunk markdown content semantically
        
        Args:
            markdown_content: The markdown content to chunk
            book_name: Name of the book
            chapter: Optional chapter number
            
        Returns:
            List of Chunk objects
        """
        try:
            # Parse markdown into sections
            sections = self._parse_markdown_sections(markdown_content)
            
            chunks = []
            chunk_index = 0
            
            for section in sections:
                section_chunks = self._chunk_section(
                    section, 
                    book_name, 
                    chapter, 
                    chunk_index
                )
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
            
            logger.info(f"Created {len(chunks)} chunks from markdown content")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking markdown: {str(e)}")
            return []
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown into logical sections"""
        sections = []
        lines = content.split('\n')
        current_section = {
            'title': '',
            'content': '',
            'level': 0,
            'start_line': 0
        }
        
        for i, line in enumerate(lines):
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    'title': header_match.group(2).strip(),
                    'content': line + '\n',
                    'level': len(header_match.group(1)),
                    'start_line': i
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add the last section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _chunk_section(self, section: Dict[str, Any], book_name: str, chapter: Optional[int], start_chunk_index: int) -> List[Chunk]:
        """Chunk a single section into smaller pieces"""
        content = section['content']
        title = section['title']
        level = section['level']
        
        # Split content into paragraphs
        paragraphs = self._split_into_paragraphs(content)
        
        chunks = []
        current_chunk = ""
        current_position = 0
        chunk_index = start_chunk_index
        
        for paragraph in paragraphs:
            paragraph_tokens = len(self.encoding.encode(paragraph))
            current_tokens = len(self.encoding.encode(current_chunk))
            
            # If adding this paragraph would exceed max size, create a chunk
            if current_tokens + paragraph_tokens > self.max_chunk_size and current_chunk:
                # Create chunk
                chunk = self._create_chunk(
                    current_chunk.strip(),
                    chunk_index,
                    current_position,
                    book_name,
                    chapter,
                    title,
                    level
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap_text(current_chunk) + paragraph
                current_position += len(current_chunk)
            else:
                current_chunk += paragraph + "\n\n"
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk.strip(),
                chunk_index,
                current_position,
                book_name,
                chapter,
                title,
                level
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs"""
        # Split by double newlines first
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Further split long paragraphs
        final_paragraphs = []
        for paragraph in paragraphs:
            if len(self.encoding.encode(paragraph)) > self.max_chunk_size:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_para = ""
                for sentence in sentences:
                    if len(self.encoding.encode(current_para + sentence)) > self.max_chunk_size:
                        if current_para:
                            final_paragraphs.append(current_para.strip())
                        current_para = sentence
                    else:
                        current_para += " " + sentence if current_para else sentence
                if current_para:
                    final_paragraphs.append(current_para.strip())
            else:
                final_paragraphs.append(paragraph.strip())
        
        return [p for p in final_paragraphs if p.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of the current chunk"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= self.overlap_size:
            return text
        
        overlap_tokens = tokens[-self.overlap_size:]
        return self.encoding.decode(overlap_tokens)
    
    def _create_chunk(self, content: str, chunk_index: int, position: int, 
                     book_name: str, chapter: Optional[int], title: str, level: int) -> Chunk:
        """Create a Chunk object with enhanced metadata"""
        metadata = {
            'book_name': book_name,
            'section_title': title,
            'section_level': level,
            'chunk_size': len(self.encoding.encode(content)),
            'position': position
        }
        
        if chapter is not None:
            metadata['chapter'] = chapter
        
        # Extract enhanced metadata if enabled
        enhanced_metadata = None
        if self.enable_enhanced_metadata and self.metadata_extractor:
            try:
                enhanced_metadata = self.metadata_extractor.extract_enhanced_metadata(content, chunk_index)
                # Add enhanced metadata to basic metadata for backward compatibility
                metadata.update({
                    'page_numbers': enhanced_metadata.page_numbers,
                    'content_type': enhanced_metadata.content_type,
                    'important_terms': enhanced_metadata.important_terms,
                    'technical_terms': enhanced_metadata.technical_terms,
                    'keywords': enhanced_metadata.keywords,
                    'figures': enhanced_metadata.figures,
                    'tables': enhanced_metadata.tables,
                    'examples': enhanced_metadata.examples,
                    'exercises': enhanced_metadata.exercises,
                    'word_count': enhanced_metadata.word_count,
                    'readability_score': enhanced_metadata.readability_score,
                    'complexity_score': enhanced_metadata.complexity_score
                })
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract enhanced metadata for chunk {chunk_index}: {e}")
        
        chunk = Chunk(
            content=content,
            chunk_index=chunk_index,
            start_position=position,
            end_position=position + len(content),
            metadata=metadata,
            enhanced_metadata=enhanced_metadata
        )
        # Add chapter as attribute for compatibility
        chunk.chapter = chapter
        return chunk
