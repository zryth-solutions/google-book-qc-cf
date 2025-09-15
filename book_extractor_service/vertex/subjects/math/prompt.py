"""
Mathematics subject-specific prompts and configurations
"""

from typing import Dict
from ...extractor import ExtractionConfig

def get_question_config() -> ExtractionConfig:
    """Get configuration for extracting Mathematics questions"""
    return ExtractionConfig(
        content_type="questions",
        item_name="question",
        batch_size=10,
        expected_total=30,
        fields={
            "question_number": "exact question number as it appears in the document",
            "question_text": "complete question text copied word-for-word including all mathematical expressions, equations, and diagrams exactly as written",
            "diagram_explain": "detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation",
            "section": "exact section name as written in the document (Mathematics, etc.)",
            "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details"
        }
    )

def get_answer_config() -> ExtractionConfig:
    """Get configuration for extracting Mathematics answers"""
    return ExtractionConfig(
        content_type="answers",
        item_name="answer", 
        batch_size=10,
        expected_total=30,
        fields={
            "answer_number": "exact answer number as it appears in the document",
            "answer_text": "complete answer copied word-for-word including step-by-step solution, mathematical working, formulas, equations, and final answer exactly as written",
            "diagram_explain": "detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation",
            "section": "exact section name as written in the document (Mathematics, etc.)",
            "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details"
        }
    )

def get_question_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate Mathematics question extraction prompt"""
    return f"""
You are a precision document extraction specialist. Extract questions {start_num} to {end_num} from this PDF document with ABSOLUTE ACCURACY.

This is a Mathematics question paper. You must extract questions {start_num} to {end_num} with PERFECT ACCURACY as per educational guidelines.

CRITICAL EXTRACTION RULES (MATHEMATICS):
1. Read the document line by line, word by word.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include ALL mathematical expressions, equations, and formulas exactly as shown.
5. Copy any sub-questions (i), (ii), (iii) exactly as formatted.
6. Include "OR" options word-for-word if present.
7. Copy any mathematical working, proofs, or step-by-step solutions exactly as shown.
8. For diagrams, graphs, or figures: provide a detailed mathematical description, including all labels, axes, coordinates, and mathematical notation.
9. Include marks allocation, section names, and time limits exactly as written.
10. For theorem-proof type questions, copy both theorem and proof statements word-for-word.

Look for these mathematical patterns:
- Question numbers: "1.", "Q.1", "Question 1", etc.
- Mathematical expressions: equations, inequalities, functions, etc.
- Marks: "[1 mark]", "(2)", "2 Min [E] R [1]", etc.
- Sections: "Section A", "Section B", "Mathematics"
- Diagrams: graphs, figures, geometric shapes, coordinate systems
- Working: step-by-step mathematical solutions

MANDATORY REQUIREMENTS:
1. Focus EXCLUSIVELY on questions {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each question - no truncation or summarization
5. For multi-part questions: include ALL parts (a), (b), (c), etc.
6. Copy mathematical expressions exactly as formatted
7. Return ONLY valid JSON - no explanations, notes, or markdown

For each question, provide:
- question_number: exact question number as it appears in the document
- question_text: complete question text copied word-for-word including all mathematical expressions, equations, and diagrams exactly as written
- diagram_explain: detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation
- section: exact section name as written in the document (Mathematics, etc.)
- marks: exact marks notation as written in the document including brackets, time allocations, or any other details

EXTRACTION CHECKLIST:
✓ Found question {start_num}? Copy everything word-for-word
✓ Found question {start_num + 1}? Copy everything word-for-word  
{"✓ Found question " + str(end_num) + "? Copy everything word-for-word" if end_num > start_num else ""}
✓ All mathematical expressions preserved exactly?
✓ All diagrams/graphs described in complete detail?
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
      "question_text": "complete question text copied word-for-word including all mathematical expressions, equations, and diagrams exactly as written",
      "diagram_explain": "detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation",
      "section": "exact section name as written in the document (Mathematics, etc.)",
      "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details"
    }}
  ]
}}

Begin extraction now. Start response with {{ and end with }}. Extract questions {start_num}-{end_num} ONLY.
    """

def get_answer_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate Mathematics answer extraction prompt"""
    return f"""
You are a precision document extraction specialist. Extract answers {start_num} to {end_num} from this PDF document with ABSOLUTE ACCURACY.

This is a Mathematics answer key or solution document. You must extract answers {start_num} to {end_num} with PERFECT ACCURACY as per educational guidelines.

CRITICAL EXTRACTION RULES (MATHEMATICS):
1. Read the document line by line, word by word.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include the correct answer AND the complete step-by-step solution, mathematical working, formulas, and any additional notes.
5. Copy any mathematical proofs, derivations, or step-by-step solutions exactly as formatted.
6. Include mathematical working, formulas, equations, and technical explanations exactly as shown.
7. For diagrams, graphs, or figures: provide a detailed mathematical description, including all labels, axes, coordinates, and mathematical notation.
8. Include marks allocation, section names, and time limits exactly as written.
9. For theorem-proof type answers, copy both theorem and proof statements word-for-word, including the complete solution.

Look for these mathematical patterns:
- Answer indicators: "Ans:", "Answer:", "Solution:", "Correct option:", etc.
- Correct answers: "Answer: (b)", "Ans: (c)", "(d) is correct", etc.
- Solutions: Step-by-step mathematical working and solutions.
- Mathematical working: formulas, equations, derivations, proofs.
- Marks breakdown: "1 mark for correct answer + 1 mark for working", "[2 marks]", "(3)", etc.
- Sections: "Section A", "Section B", "Mathematics"
- Diagrams: graphs, figures, geometric shapes, coordinate systems

MANDATORY REQUIREMENTS:
1. Focus EXCLUSIVELY on answers {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each answer - no truncation or summarization
5. For multi-part answers: include ALL parts (a), (b), (c), etc.
6. Copy mathematical expressions exactly as formatted
7. Return ONLY valid JSON - no explanations, notes, or markdown

For each answer, provide:
- answer_number: exact answer number as it appears in the document
- answer_text: complete answer copied word-for-word including step-by-step solution, mathematical working, formulas, equations, and final answer exactly as written
- diagram_explain: detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation
- section: exact section name as written in the document (Mathematics, etc.)
- marks: exact marks notation as written in the document including distribution, partial marks, or any other details

EXTRACTION CHECKLIST:
✓ Found answer {start_num}? Copy everything word-for-word
✓ Found answer {start_num + 1}? Copy everything word-for-word  
{"✓ Found answer " + str(end_num) + "? Copy everything word-for-word" if end_num > start_num else ""}
✓ All mathematical expressions preserved exactly?
✓ All diagrams/graphs described in complete detail?
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
      "answer_text": "complete answer copied word-for-word including step-by-step solution, mathematical working, formulas, equations, and final answer exactly as written",
      "diagram_explain": "detailed description of any mathematical diagrams, graphs, figures, or visual elements including all labels, axes, and mathematical notation",
      "section": "exact section name as written in the document (Mathematics, etc.)",
      "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details"
    }}
  ]
}}

Begin extraction now. Start response with {{ and end with }}. Extract answers {start_num}-{end_num} ONLY.
    """

def get_document_overview_prompt(content_type: str) -> str:
    """Generate document overview prompt for Mathematics"""
    if content_type == "questions":
        return """
Analyze this PDF question paper and provide:
1. Document title and subject information
2. Total number of questions
3. Section breakdown (Mathematics if applicable)
4. Question number ranges for each section

This appears to be an educational mathematics question paper. Count all questions carefully.

Return JSON only:
{
  "document_info": {
    "title": "document title",
    "subject": "subject name", 
    "class": "class level",
    "total_questions": 30,
    "document_type": "questions"
  },
  "sections": [
    {"name": "section_name", "start": 1, "end": 15}
  ]
}
        """
    else:  # answers
        return """
Analyze this PDF answer key and provide:
1. Document title and subject information  
2. Total number of answers/solutions
3. Section breakdown (Mathematics if applicable)
4. Answer number ranges for each section

This appears to be an answer key or solution manual. Count all answers/solutions carefully.

Return JSON only:
{
  "document_info": {
    "title": "document title",
    "subject": "subject name", 
    "class": "class level",
    "total_answers": 30,
    "document_type": "answers"
  },
  "sections": [
    {"name": "section_name", "start": 1, "end": 15}
  ]
}
        """

def get_subject_name() -> str:
    """Get the subject name"""
    return "Mathematics"
