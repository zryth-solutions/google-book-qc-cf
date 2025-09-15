"""
Computer Application subject-specific prompts and configurations
"""

from typing import Dict
from ...extractor import ExtractionConfig

def get_question_config() -> ExtractionConfig:
    """Get configuration for extracting Computer Application questions"""
    return ExtractionConfig(
        content_type="questions",
        item_name="question",
        batch_size=8,
        expected_total=39,
        fields={
            "question_number": "exact question number as it appears in the document",
            "question_text": "complete question text copied word-for-word including all multiple choice options (a), (b), (c), (d) if present, maintaining exact formatting and punctuation",
            "diagram_explain": "for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present",
            "section": "exact section name as written in the document (Computer Applications, etc.)",
            "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details"
        }
    )

def get_answer_config() -> ExtractionConfig:
    """Get configuration for extracting Computer Application answers"""
    return ExtractionConfig(
        content_type="answers",
        item_name="answer", 
        batch_size=8,
        expected_total=39,
        fields={
            "answer_number": "exact answer number as it appears in the document",
            "answer_text": "complete answer copied word-for-word including correct option, full explanation, reasoning, formulas, equations, and any additional notes exactly as written",
            "diagram_explain": "for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present",
            "section": "exact section name as written in the document (Computer Applications, etc.)",
            "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details"
        }
    )

def get_question_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate Computer Application question extraction prompt"""
    return f"""
You are a precision document extraction specialist. Extract questions {start_num} to {end_num} from this PDF document with ABSOLUTE ACCURACY.

This is a CBSE Class 10 Computer Applications question paper. You must extract questions {start_num} to {end_num} with PERFECT ACCURACY as per CBSE guidelines.

CRITICAL EXTRACTION RULES (CBSE COMPUTER APPLICATIONS):
1. Read the document line by line, word by word.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include ALL multiple choice options exactly: (a), (b), (c), (d).
5. Copy any sub-questions (i), (ii), (iii) exactly as formatted.
6. Include "OR" options word-for-word if present.
7. Copy any code snippets, HTML tags, Python code, or pseudo-code exactly as shown.
8. For diagrams, tables, or screenshots: provide a detailed technical description, including all labels, captions, and text.
9. Include marks allocation, section names, and time limits exactly as written.
10. For assertion-reason type questions, copy both assertion and reason statements word-for-word.

Look for these CBSE patterns:
- Question numbers: "1.", "Q.1", "Question 1", etc.
- Multiple choice: "(a) option text (b) option text (c) option text (d) option text"
- Marks: "[1 mark]", "(2)", "2 Min [E] R [1]", etc.
- Sections: "Section A", "Section B", "Computer Applications"
- Assertion-Reason: "Assertion (A):" and "Reason (R):"
- Programming/code: Python, HTML, or pseudo-code blocks

MANDATORY REQUIREMENTS:
1. Focus EXCLUSIVELY on questions {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each question - no truncation or summarization
5. For multi-part questions: include ALL parts (a), (b), (c), etc.
6. Copy tables cell by cell if present
7. Return ONLY valid JSON - no explanations, notes, or markdown

For each question, provide:
- question_number: exact question number as it appears in the document
- question_text: complete question text copied word-for-word including all multiple choice options (a), (b), (c), (d) if present, maintaining exact formatting and punctuation
- diagram_explain: for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present
- section: exact section name as written in the document (Computer Applications, etc.)
- marks: exact marks notation as written in the document including brackets, time allocations, or any other details

EXTRACTION CHECKLIST:
✓ Found question {start_num}? Copy everything word-for-word
✓ Found question {start_num + 1}? Copy everything word-for-word  
{"✓ Found question " + str(end_num) + "? Copy everything word-for-word" if end_num > start_num else ""}
✓ All diagrams/tables described in complete detail?
✓ All formatting preserved exactly?
✓ JSON structure correct?

RETURN ONLY THIS JSON STRUCTURE:

{{
  "batch_info": {{
    "batch_number": {batch_number},
    "start_question": {start_num},
    "end_question": {end_num}
  }},
  "questions": [
    {{
      "question_number": "exact question number as it appears in the document",
      "question_text": "complete question text copied word-for-word including all multiple choice options (a), (b), (c), (d) if present, maintaining exact formatting and punctuation",
      "diagram_explain": "for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present",
      "section": "exact section name as written in the document (Computer Applications, etc.)",
      "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details"
    }}
  ]
}}

Begin extraction now. Start response with {{ and end with }}. Extract questions {start_num}-{end_num} ONLY.
    """

def get_answer_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate Computer Application answer extraction prompt"""
    return f"""
You are a precision document extraction specialist. Extract answers {start_num} to {end_num} from this PDF document with ABSOLUTE ACCURACY.

This is a CBSE Class 10 Computer Applications answer key or solution document. You must extract answers {start_num} to {end_num} with PERFECT ACCURACY as per CBSE guidelines.

CRITICAL EXTRACTION RULES (CBSE COMPUTER APPLICATIONS):
1. Read the document line by line, word by word.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include the correct answer option AND the complete explanation, reasoning, formulas, and any additional notes.
5. Copy any step-by-step solutions, code snippets, HTML tags, Python code, or pseudo-code exactly as formatted.
6. Include mathematical working, formulas, equations, and technical explanations exactly as shown.
7. For diagrams, tables, or screenshots: provide a detailed technical description, including all labels, captions, and text.
8. Include marks allocation, section names, and time limits exactly as written.
9. For assertion-reason type answers, copy both assertion and reason statements word-for-word, including the correct option and explanation.

Look for these CBSE patterns:
- Answer indicators: "Ans:", "Answer:", "Solution:", "Correct option:", etc.
- Correct options: "Answer: (b)", "Ans: (c)", "(d) is correct", etc.
- Explanations: Full justification or reasoning text following the correct answer.
- Solutions: Step-by-step working for programming/code or numerical problems.
- Marks breakdown: "1 mark for correct option + 1 mark for explanation", "[2 marks]", "(3)", etc.
- Sections: "Section A", "Section B", "Computer Applications"
- Programming/code: Python, HTML, or pseudo-code blocks

MANDATORY REQUIREMENTS:
1. Focus EXCLUSIVELY on answers {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each answer - no truncation or summarization
5. For multi-part answers: include ALL parts (a), (b), (c), etc.
6. Copy tables cell by cell if present
7. Return ONLY valid JSON - no explanations, notes, or markdown

For each answer, provide:
- answer_number: exact answer number as it appears in the document
- answer_text: complete answer copied word-for-word including correct option, full explanation, reasoning, formulas, equations, and any additional notes exactly as written
- diagram_explain: for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present
- section: exact section name as written in the document (Computer Applications, etc.)
- marks: exact marks notation as written in the document including distribution, partial marks, or any other details

EXTRACTION CHECKLIST:
✓ Found answer {start_num}? Copy everything word-for-word
✓ Found answer {start_num + 1}? Copy everything word-for-word  
{"✓ Found answer " + str(end_num) + "? Copy everything word-for-word" if end_num > start_num else ""}
✓ All diagrams/tables described in complete detail?
✓ All formatting preserved exactly?
✓ JSON structure correct?

RETURN ONLY THIS JSON STRUCTURE:

{{
  "batch_info": {{
    "batch_number": {batch_number},
    "start_answer": {start_num},
    "end_answer": {end_num}
  }},
  "answers": [
    {{
      "answer_number": "exact answer number as it appears in the document",
      "answer_text": "complete answer copied word-for-word including correct option, full explanation, reasoning, formulas, equations, and any additional notes exactly as written",
      "diagram_explain": "for computer applications questions, diagram needs to be analyzed very well in a technical manner, detailed word-for-word description of any diagrams, tables, charts, or visual elements including all labels and text, or null if none present",
      "section": "exact section name as written in the document (Computer Applications, etc.)",
      "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details"
    }}
  ]
}}

Begin extraction now. Start response with {{ and end with }}. Extract answers {start_num}-{end_num} ONLY.
    """

def get_document_overview_prompt(content_type: str) -> str:
    """Generate document overview prompt for Computer Applications"""
    if content_type == "questions":
        return """
Analyze this PDF question paper and provide:
1. Document title and subject information
2. Total number of questions
3. Section breakdown (Computer Applications if applicable)
4. Question number ranges for each section

This appears to be an educational question paper. Count all questions carefully.

Return JSON only:
{
  "document_info": {
    "title": "document title",
    "subject": "subject name", 
    "class": "class level",
    "total_questions": 39,
    "document_type": "questions"
  },
  "sections": [
    {"name": "section_name", "start": 1, "end": 16}
  ]
}
        """
    else:  # answers
        return """
Analyze this PDF answer key and provide:
1. Document title and subject information  
2. Total number of answers/solutions
3. Section breakdown (Computer Applications if applicable)
4. Answer number ranges for each section

This appears to be an answer key or solution manual. Count all answers/solutions carefully.

Return JSON only:
{
  "document_info": {
    "title": "document title",
    "subject": "subject name", 
    "class": "class level",
    "total_answers": 39,
    "document_type": "answers"
  },
  "sections": [
    {"name": "section_name", "start": 1, "end": 16}
  ]
}
        """

def get_subject_name() -> str:
    """Get the subject name"""
    return "Computer Applications"
