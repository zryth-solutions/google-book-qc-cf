import re
import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
import nltk
from collections import Counter
import spacy

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMetadata:
    """Enhanced metadata for text chunks with NLP analysis"""
    # Basic metadata
    page_numbers: List[int]
    chapter_number: Optional[int]
    section_title: Optional[str]
    
    # Structural elements
    figures: List[str]
    tables: List[str]
    examples: List[str]
    exercises: List[str]
    
    # Content analysis
    content_type: str  # introduction, explanation, example, exercise, summary, etc.
    important_terms: List[str]
    technical_terms: List[str]
    keywords: List[str]
    
    # NLP features
    entities: List[Dict[str, Any]]  # Named entities
    concepts: List[str]  # Key concepts mentioned
    topics: List[str]  # Main topics
    
    # Text features
    word_count: int
    sentence_count: int
    readability_score: float
    complexity_score: float

class MetadataExtractor:
    """Enhanced metadata extractor with NLP analysis capabilities"""
    
    def __init__(self):
        self.nlp = None
        self._load_nlp_model()
        
        # Technical terms patterns
        self.technical_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w*[a-z]+\w*[A-Z]\w*\b',  # CamelCase
            r'\b\w+\.\w+\b',  # Dotted notation
            r'\b\w+\(\)\b',  # Functions
            r'\b\w+\[\w+\]\b',  # Arrays/lists
        ]
        
        # Content type patterns
        self.content_type_patterns = {
            'introduction': [r'introduction', r'overview', r'basics?', r'fundamentals?'],
            'explanation': [r'explanation', r'description', r'details?', r'how\s+it\s+works'],
            'example': [r'example', r'for\s+instance', r'such\s+as', r'consider'],
            'exercise': [r'exercise', r'practice', r'problem', r'question'],
            'summary': [r'summary', r'conclusion', r'recap', r'overview'],
            'definition': [r'definition', r'means?', r'refers\s+to', r'is\s+defined'],
            'procedure': [r'steps?', r'procedure', r'process', r'method'],
        }
    
    def _load_nlp_model(self):
        """Load spaCy model for NLP processing"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ Loaded spaCy model successfully")
        except OSError:
            logger.warning("⚠️ spaCy model not found. Installing...")
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ Installed and loaded spaCy model")
            except Exception as e:
                logger.error(f"❌ Failed to load spaCy model: {e}")
                self.nlp = None
    
    def extract_page_numbers(self, text: str) -> List[int]:
        """Extract page numbers from _page_X_ patterns"""
        page_pattern = r'_page_(\d+)_'
        matches = re.findall(page_pattern, text)
        return [int(match) for match in matches]
    
    def extract_structural_elements(self, text: str) -> Dict[str, List[str]]:
        """Extract figures, tables, examples, exercises from text"""
        elements = {
            'figures': [],
            'tables': [],
            'examples': [],
            'exercises': []
        }
        
        # Extract figures
        figure_pattern = r'Figure\s+(\d+\.?\d*[a-z]?):?\s*([^.!?]*)'
        figures = re.findall(figure_pattern, text, re.IGNORECASE)
        elements['figures'] = [f"Figure {fig[0]}: {fig[1].strip()}" for fig in figures]
        
        # Extract tables
        table_pattern = r'Table\s+(\d+\.?\d*[a-z]?):?\s*([^.!?]*)'
        tables = re.findall(table_pattern, text, re.IGNORECASE)
        elements['tables'] = [f"Table {tab[0]}: {tab[1].strip()}" for tab in tables]
        
        # Extract examples
        example_pattern = r'Example\s+(\d+\.?\d*[a-z]?):?\s*([^.!?]*)'
        examples = re.findall(example_pattern, text, re.IGNORECASE)
        elements['examples'] = [f"Example {ex[0]}: {ex[1].strip()}" for ex in examples]
        
        # Extract exercises
        exercise_pattern = r'Exercise\s+(\d+\.?\d*[a-z]?):?\s*([^.!?]*)'
        exercises = re.findall(exercise_pattern, text, re.IGNORECASE)
        elements['exercises'] = [f"Exercise {ex[0]}: {ex[1].strip()}" for ex in exercises]
        
        return elements
    
    def extract_chapter_section(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """Extract chapter number and section title"""
        chapter_number = None
        section_title = None
        
        # Extract chapter number
        chapter_pattern = r'Chapter\s+(\d+)'
        chapter_match = re.search(chapter_pattern, text, re.IGNORECASE)
        if chapter_match:
            chapter_number = int(chapter_match.group(1))
        
        # Extract section title from headings
        heading_pattern = r'^#+\s*(.+)$'
        headings = re.findall(heading_pattern, text, re.MULTILINE)
        if headings:
            section_title = headings[0].strip()
        
        return chapter_number, section_title
    
    def extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms using pattern matching"""
        technical_terms = set()
        
        for pattern in self.technical_patterns:
            matches = re.findall(pattern, text)
            technical_terms.update(matches)
        
        # Filter out common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        technical_terms = [term for term in technical_terms if term.lower() not in common_words]
        
        return list(technical_terms)
    
    def extract_important_terms(self, text: str) -> List[str]:
        """Extract important terms using NLP"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        important_terms = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # Multi-word phrases
                important_terms.append(chunk.text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'TECHNOLOGY']:
                important_terms.append(ent.text)
        
        return list(set(important_terms))
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords using frequency analysis"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        
        # Filter tokens
        tokens = [
            token.lemma_.lower() 
            for token in doc 
            if not token.is_stop 
            and not token.is_punct 
            and not token.is_space
            and len(token.text) > 2
        ]
        
        # Count frequencies
        word_freq = Counter(tokens)
        return [word for word, freq in word_freq.most_common(top_n)]
    
    def determine_content_type(self, text: str) -> str:
        """Determine the type of content based on patterns"""
        text_lower = text.lower()
        
        for content_type, patterns in self.content_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return content_type
        
        return 'general'
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'description': spacy.explain(ent.label_)
            })
        
        return entities
    
    def extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from the text"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        concepts = []
        
        # Extract noun phrases that might be concepts
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:
                concepts.append(chunk.text)
        
        # Extract technical terms
        concepts.extend(self.extract_technical_terms(text))
        
        return list(set(concepts))
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate a simple readability score"""
        if not self.nlp:
            return 0.0
        
        doc = self.nlp(text)
        sentences = list(doc.sents)
        words = [token for token in doc if not token.is_punct and not token.is_space]
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(token.text) for token in words) / len(words)
        
        # Simple readability score (lower is more readable)
        readability = (avg_sentence_length * 0.4) + (avg_word_length * 0.6)
        return round(readability, 2)
    
    def calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score"""
        if not self.nlp:
            return 0.0
        
        doc = self.nlp(text)
        
        # Count complex features
        complex_features = 0
        total_features = 0
        
        for token in doc:
            if not token.is_punct and not token.is_space:
                total_features += 1
                if len(token.text) > 6:  # Long words
                    complex_features += 1
                if token.pos_ in ['VERB', 'ADJ', 'ADV']:  # Complex parts of speech
                    complex_features += 1
        
        if total_features == 0:
            return 0.0
        
        complexity = (complex_features / total_features) * 100
        return round(complexity, 2)
    
    def extract_enhanced_metadata(self, text: str, chunk_index: int = 0) -> EnhancedMetadata:
        """Extract comprehensive metadata from text"""
        logger.info(f"🔍 Extracting enhanced metadata for chunk {chunk_index}")
        
        # Basic metadata
        page_numbers = self.extract_page_numbers(text)
        chapter_number, section_title = self.extract_chapter_section(text)
        
        # Structural elements
        structural_elements = self.extract_structural_elements(text)
        
        # Content analysis
        content_type = self.determine_content_type(text)
        important_terms = self.extract_important_terms(text)
        technical_terms = self.extract_technical_terms(text)
        keywords = self.extract_keywords(text)
        
        # NLP features
        entities = self.extract_entities(text)
        concepts = self.extract_concepts(text)
        topics = keywords[:5]  # Top 5 keywords as topics
        
        # Text features
        word_count = len(text.split())
        sentence_count = len(text.split('.'))
        readability_score = self.calculate_readability_score(text)
        complexity_score = self.calculate_complexity_score(text)
        
        metadata = EnhancedMetadata(
            page_numbers=page_numbers,
            chapter_number=chapter_number,
            section_title=section_title,
            figures=structural_elements['figures'],
            tables=structural_elements['tables'],
            examples=structural_elements['examples'],
            exercises=structural_elements['exercises'],
            content_type=content_type,
            important_terms=important_terms,
            technical_terms=technical_terms,
            keywords=keywords,
            entities=entities,
            concepts=concepts,
            topics=topics,
            word_count=word_count,
            sentence_count=sentence_count,
            readability_score=readability_score,
            complexity_score=complexity_score
        )
        
        logger.info(f"✅ Extracted metadata: {len(important_terms)} terms, {len(technical_terms)} technical, {len(keywords)} keywords")
        return metadata
