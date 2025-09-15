from typing import Dict, Type, Any
from abc import ABC, abstractmethod
from .extractor import ExtractionConfig

class SubjectExtractor(ABC):
    """Abstract base class for subject-specific extractors"""
    
    @abstractmethod
    def get_question_config(self) -> ExtractionConfig:
        """Get configuration for extracting questions"""
        pass
    
    @abstractmethod
    def get_answer_config(self) -> ExtractionConfig:
        """Get configuration for extracting answers"""
        pass
    
    @abstractmethod
    def get_question_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        """Get question extraction prompt for this subject"""
        pass
    
    @abstractmethod
    def get_answer_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        """Get answer extraction prompt for this subject"""
        pass
    
    @abstractmethod
    def get_document_overview_prompt(self, content_type: str) -> str:
        """Get document overview prompt for this subject"""
        pass
    
    @abstractmethod
    def get_subject_name(self) -> str:
        """Get the subject name"""
        pass

class ComputerApplicationExtractor(SubjectExtractor):
    """Extractor for Computer Applications subject"""
    
    def __init__(self):
        from .subjects.computer_application.prompt import (
            get_question_config, get_answer_config, get_question_extraction_prompt,
            get_answer_extraction_prompt, get_document_overview_prompt, get_subject_name
        )
        self._get_question_config = get_question_config
        self._get_answer_config = get_answer_config
        self._get_question_extraction_prompt = get_question_extraction_prompt
        self._get_answer_extraction_prompt = get_answer_extraction_prompt
        self._get_document_overview_prompt = get_document_overview_prompt
        self._get_subject_name = get_subject_name
    
    def get_question_config(self) -> ExtractionConfig:
        return self._get_question_config()
    
    def get_answer_config(self) -> ExtractionConfig:
        return self._get_answer_config()
    
    def get_question_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        return self._get_question_extraction_prompt(batch_number, start_num, end_num)
    
    def get_answer_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        return self._get_answer_extraction_prompt(batch_number, start_num, end_num)
    
    def get_document_overview_prompt(self, content_type: str) -> str:
        return self._get_document_overview_prompt(content_type)
    
    def get_subject_name(self) -> str:
        return self._get_subject_name()

class MathExtractor(SubjectExtractor):
    """Extractor for Mathematics subject"""
    
    def __init__(self):
        from .subjects.math.prompt import (
            get_question_config, get_answer_config, get_question_extraction_prompt,
            get_answer_extraction_prompt, get_document_overview_prompt, get_subject_name
        )
        self._get_question_config = get_question_config
        self._get_answer_config = get_answer_config
        self._get_question_extraction_prompt = get_question_extraction_prompt
        self._get_answer_extraction_prompt = get_answer_extraction_prompt
        self._get_document_overview_prompt = get_document_overview_prompt
        self._get_subject_name = get_subject_name
    
    def get_question_config(self) -> ExtractionConfig:
        return self._get_question_config()
    
    def get_answer_config(self) -> ExtractionConfig:
        return self._get_answer_config()
    
    def get_question_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        return self._get_question_extraction_prompt(batch_number, start_num, end_num)
    
    def get_answer_extraction_prompt(self, batch_number: int, start_num: int, end_num: int) -> str:
        return self._get_answer_extraction_prompt(batch_number, start_num, end_num)
    
    def get_document_overview_prompt(self, content_type: str) -> str:
        return self._get_document_overview_prompt(content_type)
    
    def get_subject_name(self) -> str:
        return self._get_subject_name()

class SubjectExtractorFactory:
    """Factory class for creating subject-specific extractors"""
    
    _extractors: Dict[str, Type[SubjectExtractor]] = {
        "computer_applications": ComputerApplicationExtractor,
        "computer_application": ComputerApplicationExtractor,
        "math": MathExtractor,
        "mathematics": MathExtractor,
        "maths": MathExtractor
    }
    
    @classmethod
    def get_extractor(cls, subject: str) -> SubjectExtractor:
        """Get extractor for the specified subject"""
        subject_lower = subject.lower().strip()
        
        if subject_lower not in cls._extractors:
            # Default to Computer Applications if subject not found
            return ComputerApplicationExtractor()
        
        extractor_class = cls._extractors[subject_lower]
        return extractor_class()
    
    @classmethod
    def get_available_subjects(cls) -> list:
        """Get list of available subjects"""
        return list(cls._extractors.keys())
    
    @classmethod
    def register_extractor(cls, subject: str, extractor_class: Type[SubjectExtractor]):
        """Register a new subject extractor"""
        cls._extractors[subject.lower()] = extractor_class
