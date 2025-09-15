import vertexai
from vertexai.generative_models import GenerativeModel, Part
import json
import re
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import os
import pathlib
from google.auth import default
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractionConfig:
    """Configuration for different types of content extraction"""
    content_type: str
    item_name: str  # "question" or "answer"
    batch_size: int
    expected_total: int
    fields: Dict[str, str]  # field_name: description
    
    def get_json_schema(self, batch_number: int, start_num: int, end_num: int) -> str:
        """Generate JSON schema based on fields"""
        field_examples = []
        for field_name, description in self.fields.items():
            field_examples.append(f'      "{field_name}": "{description}"')
        
        return f'''{{
  "batch_info": {{
    "batch_number": {batch_number},
    "start_{self.item_name}": {start_num},
    "end_{self.item_name}": {end_num}
  }},
  "{self.item_name}s": [
    {{
{chr(10).join(field_examples)}
    }}
  ]
}}'''

class VertexAIPDFExtractor:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize Vertex AI with project and location"""
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel("gemini-2.5-pro")
            logger.info(f"Vertex AI initialized successfully - Project: {project_id}, Location: {location}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    def upload_pdf(self, pdf_path: str) -> Optional[Part]:
        """Convert PDF to Part object for Vertex AI"""
        try:
            # Check file size
            file_size = os.path.getsize(pdf_path)
            file_size_mb = file_size / (1024 * 1024)
            logger.info(f"File size: {file_size_mb:.2f} MB")
            
            if not os.path.exists(pdf_path):
                logger.error(f"File not found: {pdf_path}")
                return None
            
            logger.info(f"Processing {os.path.basename(pdf_path)} with Vertex AI...")
            
            # Read PDF file and create Part object
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            
            # Create Part object for Vertex AI
            pdf_part = Part.from_data(
                data=pdf_data,
                mime_type="application/pdf"
            )
            
            logger.info("PDF loaded successfully for Vertex AI processing")
            return pdf_part
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return None
    
    def create_extraction_prompt(self, config: ExtractionConfig, batch_number: int, 
                                start_num: int, end_num: int, subject_extractor=None) -> str:
        """Create extraction prompt based on configuration and subject"""
        
        if subject_extractor:
            if config.content_type == "questions":
                return subject_extractor.get_question_extraction_prompt(batch_number, start_num, end_num)
            else:
                return subject_extractor.get_answer_extraction_prompt(batch_number, start_num, end_num)
        
        # Fallback to generic prompt if no subject extractor provided
        field_descriptions = []
        for field_name, description in config.fields.items():
            field_descriptions.append(f"- {field_name}: {description}")
        
        json_schema = config.get_json_schema(batch_number, start_num, end_num)
        
        return f"""
You are a precision document extraction specialist. Extract {config.item_name}s {start_num} to {end_num} from this PDF document with ABSOLUTE ACCURACY.

MANDATORY REQUIREMENTS:
1. Focus EXCLUSIVELY on {config.item_name}s {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each {config.item_name} - no truncation or summarization
5. For multi-part questions/answers: include ALL parts (a), (b), (c), etc.
6. Copy tables cell by cell if present
7. Return ONLY valid JSON - no explanations, notes, or markdown

For each {config.item_name}, provide:
{chr(10).join(field_descriptions)}

RETURN ONLY THIS JSON STRUCTURE:

{json_schema}

Begin extraction now. Start response with {{ and end with }}. Extract {config.item_name}s {start_num}-{end_num} ONLY.
        """
    
    def extract_content_batch(self, pdf_part: Part, config: ExtractionConfig, 
                             batch_number: int, start_num: int, end_num: int, subject_extractor=None) -> Optional[str]:
        """Extract a specific batch of content using Vertex AI"""
        
        prompt = self.create_extraction_prompt(config, batch_number, start_num, end_num, subject_extractor)
        
        try:
            # Generate content using Vertex AI
            response = self.model.generate_content([pdf_part, prompt])
            
            if response.text:
                return response.text.strip()
            else:
                logger.error(f"No response text received for batch {batch_number}")
                return None
            
        except Exception as e:
            logger.error(f"Error in batch {batch_number}: {e}")
            return None

    def get_document_overview(self, pdf_part: Part, config: ExtractionConfig, subject_extractor=None) -> Optional[Dict]:
        """Get document structure and total items using Vertex AI"""
        
        if subject_extractor:
            analysis_prompt = subject_extractor.get_document_overview_prompt(config.content_type)
        else:
            # Fallback to generic prompt
            if config.content_type == "questions":
                analysis_prompt = f"""
Analyze this PDF question paper and provide:
1. Document title and subject information
2. Total number of questions
3. Section breakdown if applicable
4. Question number ranges for each section

This appears to be an educational question paper. Count all questions carefully.
"""
            else:  # answers
                analysis_prompt = f"""
Analyze this PDF answer key and provide:
1. Document title and subject information  
2. Total number of answers/solutions
3. Section breakdown if applicable
4. Answer number ranges for each section

This appears to be an answer key or solution manual. Count all answers/solutions carefully.
"""

        prompt = f"""
{analysis_prompt}

Return JSON only:
{{
  "document_info": {{
    "title": "document title",
    "subject": "subject name", 
    "class": "class level",
    "total_{config.item_name}s": {config.expected_total},
    "document_type": "{config.content_type}"
  }},
  "sections": [
    {{"name": "section_name", "start": 1, "end": 16}}
  ]
}}
        """
        
        try:
            response = self.model.generate_content([pdf_part, prompt])
            
            if response.text:
                return self.clean_json_response(response.text.strip())
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error getting overview: {e}")
            return None

    def clean_json_response(self, response_text: str) -> Optional[Dict]:
        """Clean and extract JSON from response"""
        if not response_text:
            return None
            
        # Remove markdown backticks completely - handle cases with or without json keyword
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)  # Handle backticks without language specifier too
        
        # Extract JSON - find the first opening and last closing brace
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            logger.error("No valid JSON structure found in response")
            return None
            
        json_text = response_text[start:end]
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON error: {e}")
            # Try fixing common issues
            try:
                # Fix trailing commas which are common JSON parsing errors
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', json_text)
                return json.loads(fixed_json)
            except json.JSONDecodeError as e2:
                logger.error(f"Additional fix attempt failed: {e2}")
                # If we still can't parse, try more aggressive cleaning
                try:
                    # Try removing all non-JSON characters around the braces
                    cleaner_json = re.search(r'({.*})', json_text, re.DOTALL)
                    if cleaner_json:
                        return json.loads(cleaner_json.group(1))
                    return None
                except:
                    logger.error("All JSON parsing attempts failed")
                    return None
    
    def extract_all_content(self, pdf_part: Part, config: ExtractionConfig, subject_extractor=None) -> Dict:
        """Extract all content using batched approach with Vertex AI"""
        
        logger.info(f"Getting document overview for {config.content_type}...")
        overview = self.get_document_overview(pdf_part, config, subject_extractor)
        
        if not overview:
            logger.warning("Could not get document overview, using default batching...")
            total_items = config.expected_total
            batch_size = config.batch_size
            batches = []
            for i in range(0, total_items, batch_size):
                start = i + 1
                end = min(i + batch_size, total_items)
                batch_num = (i // batch_size) + 1
                batches.append((batch_num, start, end))
        else:
            total_items = overview.get('document_info', {}).get(f'total_{config.item_name}s', config.expected_total)
            batch_size = config.batch_size
            batches = []
            for i in range(0, total_items, batch_size):
                start = i + 1
                end = min(i + batch_size, total_items)
                batch_num = (i // batch_size) + 1
                batches.append((batch_num, start, end))
        
        all_items = []
        document_info = overview.get('document_info') if overview else {
            "title": f"Sample {config.content_type.title()}",
            "subject": "Computer Applications",
            "class": "10",
            f"total_{config.item_name}s": config.expected_total,
            "document_type": config.content_type
        }
        
        logger.info(f"Processing {len(batches)} batches with {config.batch_size} {config.item_name}s each using Vertex AI Gemini 2.5 Pro...")
        
        for batch_num, start_num, end_num in batches:
            if end_num == start_num:
                item_range = f"{config.item_name.title()} {start_num}"
            else:
                item_range = f"{config.item_name.title()}s {start_num}-{end_num}"
            
            logger.info(f"Extracting batch {batch_num}: {item_range}")
            
            raw_response = self.extract_content_batch(pdf_part, config, batch_num, start_num, end_num, subject_extractor)
            
            if raw_response:
                batch_result = self.clean_json_response(raw_response)
                
                if batch_result and f'{config.item_name}s' in batch_result:
                    items = batch_result[f'{config.item_name}s']
                    all_items.extend(items)
                    logger.info(f"Batch {batch_num}: {len(items)} {config.item_name}s extracted")
                    
                    # Show extracted item numbers for verification
                    if items:
                        number_field = f'{config.item_name}_number'
                        numbers = [item.get(number_field) for item in items if item.get(number_field)]
                        if numbers:
                            logger.info(f"Extracted {config.item_name} numbers: {numbers}")
                else:
                    logger.error(f"Batch {batch_num}: Failed to parse response")
                    # Try more aggressive JSON recovery
                    logger.info(f"Attempting to recover batch {batch_num} data...")
                    try:
                        # Try stripping all backticks and markdown formatting
                        cleaned_response = re.sub(r'```[\s\S]*?```', '', raw_response)  # Remove all code blocks
                        cleaned_response = re.sub(r'```[a-z]*\s*', '', cleaned_response) # Remove starting backticks
                        cleaned_response = re.sub(r'```', '', cleaned_response)  # Remove any remaining backticks
                        
                        # Look for JSON-like structure
                        json_match = re.search(r'({[\s\S]*})', cleaned_response)
                        if json_match:
                            try:
                                recovered_json = json.loads(json_match.group(1))
                                if f'{config.item_name}s' in recovered_json:
                                    recovered_items = recovered_json[f'{config.item_name}s']
                                    all_items.extend(recovered_items)
                                    logger.info(f"Recovered {len(recovered_items)} {config.item_name}s from batch {batch_num}")
                                    
                                    # Show recovered item numbers
                                    number_field = f'{config.item_name}_number'
                                    numbers = [item.get(number_field) for item in recovered_items if item.get(number_field)]
                                    if numbers:
                                        logger.info(f"Recovered {config.item_name} numbers: {numbers}")
                                    continue
                            except json.JSONDecodeError:
                                pass
                        
                        logger.error(f"Could not recover batch {batch_num} data - manual inspection required")
                    except Exception as e:
                        logger.error(f"Error during recovery attempt: {e}")
            else:
                logger.error(f"Batch {batch_num}: No response received")
        
        logger.info(f"EXTRACTION SUMMARY: Total {config.item_name}s extracted: {len(all_items)}")
        
        return {
            "document_info": document_info,
            f"{config.item_name}s": all_items
        }
    
    def process_pdf(self, pdf_path: str, config: ExtractionConfig, subject_extractor=None) -> Optional[Dict]:
        """Complete workflow using Vertex AI"""
        logger.info(f"Processing {pdf_path} for {config.content_type} extraction with Vertex AI Gemini 2.5 Pro...")
        pdf_part = self.upload_pdf(pdf_path)
        
        if not pdf_part:
            return None
            
        result = self.extract_all_content(pdf_part, config, subject_extractor)
        
        if result:
            item_count = len(result.get(f'{config.item_name}s', []))
            logger.info(f"Successfully extracted {item_count} {config.item_name}s using Vertex AI Gemini 2.5 Pro!")
            
            # Check for completeness
            expected = result.get('document_info', {}).get(f'total_{config.item_name}s', config.expected_total)
            if item_count < expected:
                logger.warning(f"Expected {expected} {config.item_name}s, got {item_count}")
        
        return result
