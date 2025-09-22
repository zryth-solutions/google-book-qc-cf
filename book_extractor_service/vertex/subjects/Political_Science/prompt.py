"""
CBSE Political Science Class 12 subject-specific prompts and configurations
Quality Control Focus: Spelling mistakes, dates, grammar, accuracy, missing words
"""

from typing import Dict
from ...extractor import ExtractionConfig

def get_question_config() -> ExtractionConfig:
    """Get configuration for extracting CBSE Political Science Class 12 questions"""
    return ExtractionConfig(
        content_type="questions",
        item_name="question",
        batch_size=6,
        expected_total=30,
        fields={
            "question_number": "exact question number as it appears in the document",
            "question_text": "complete question text copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and punctuation accuracy",
            "diagram_explain": "detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present",
            "section": "exact section name as written in the document (Political Science, Part A, Part B, etc.)",
            "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details",
            "date_accuracy": "verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy",
            "quality_check": "comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy"
        }
    )

def get_answer_config() -> ExtractionConfig:
    """Get configuration for extracting CBSE Political Science Class 12 answers"""
    return ExtractionConfig(
        content_type="answers",
        item_name="answer", 
        batch_size=6,
        expected_total=30,
        fields={
            "answer_number": "exact answer number as it appears in the document",
            "answer_text": "complete answer copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and factual accuracy",
            "diagram_explain": "detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present",
            "section": "exact section name as written in the document (Political Science, Part A, Part B, etc.)",
            "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details",
            "date_accuracy": "verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy",
            "quality_check": "comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy"
        }
    )

def get_question_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate CBSE Political Science Class 12 question extraction prompt with quality control focus"""
    return f"""
You are a precision document extraction specialist with QUALITY CONTROL expertise. Extract questions {start_num} to {end_num} from this CBSE Political Science Class 12 book with ABSOLUTE ACCURACY and comprehensive quality verification.

This is a CBSE Class 12 Political Science textbook. You must extract questions {start_num} to {end_num} with PERFECT ACCURACY and conduct thorough quality control checks.

CRITICAL EXTRACTION RULES (CBSE POLITICAL SCIENCE CLASS 12):
1. Read the document line by line, word by word with meticulous attention to detail.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include ALL multiple choice options exactly: (a), (b), (c), (d).
5. Copy any sub-questions (i), (ii), (iii) exactly as formatted.
6. Include "OR" options word-for-word if present.
7. Copy all political terminology, constitutional provisions, and proper nouns exactly as shown.
8. For diagrams, maps, charts, or organizational structures: provide detailed descriptions including all labels, captions, and political references.
9. Include marks allocation, section names, and time limits exactly as written.
10. For assertion-reason type questions, copy both assertion and reason statements word-for-word.

QUALITY CONTROL REQUIREMENTS (CRITICAL):
⚠️ SPELLING VERIFICATION: Check every word for spelling mistakes, especially political terms, names of leaders, parties, institutions
⚠️ GRAMMAR ACCURACY: Verify grammatical correctness, sentence structure, verb tenses, subject-verb agreement
⚠️ DATE ACCURACY: Verify all historical dates, constitutional amendment years, election years, independence dates
⚠️ MISSING WORDS: Check for incomplete sentences, missing articles, prepositions, conjunctions
⚠️ PUNCTUATION: Ensure correct punctuation marks, quotation marks, apostrophes, commas, periods
⚠️ FACTUAL ACCURACY: Verify names of political leaders, parties, countries, constitutional articles, amendments
⚠️ TERMINOLOGY CONSISTENCY: Check consistency in political science terminology usage

Look for these CBSE Political Science patterns:
- Question numbers: "1.", "Q.1", "Question 1", "Exercise", etc.
- Multiple choice: "(a) option text (b) option text (c) option text (d) option text"
- Marks: "[1 mark]", "(2)", "3 marks", "[5 marks]", etc.
- Sections: "Part A", "Part B", "Political Science", "Contemporary World Politics", "Politics in India"
- Constitutional references: "Article 370", "42nd Amendment", "Preamble", etc.
- Political entities: "Indian National Congress", "Bharatiya Janata Party", "United Nations", etc.
- Important dates: "1947", "1975", "1991", "2002", etc.
- Key personalities: "Jawaharlal Nehru", "Indira Gandhi", "Nelson Mandela", etc.

MANDATORY QUALITY CHECKS:
1. Focus EXCLUSIVELY on questions {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written with spelling verification
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each question - no truncation or summarization
5. For multi-part questions: include ALL parts (a), (b), (c), etc.
6. Copy tables cell by cell if present
7. Verify all dates and historical references for accuracy
8. Check grammar and sentence structure
9. Identify any missing or incomplete words
10. Return ONLY valid JSON - no explanations, notes, or markdown

For each question, provide:
- question_number: exact question number as it appears in the document
- question_text: complete question text copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and punctuation accuracy
- diagram_explain: detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present
- section: exact section name as written in the document (Political Science, Part A, Part B, etc.)
- marks: exact marks notation as written in the document including brackets, time allocations, or any other details
- date_accuracy: verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy
- quality_check: comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy

EXTRACTION & QUALITY CHECKLIST:
✓ Found question {start_num}? Copy everything word-for-word with spelling check
✓ Found question {start_num + 1}? Copy everything word-for-word with grammar check
{"✓ Found question " + str(end_num) + "? Copy everything word-for-word with complete quality verification" if end_num > start_num else ""}
✓ All dates and years verified for accuracy?
✓ All political terms and names checked for spelling?
✓ All sentences complete with no missing words?
✓ All punctuation marks correct?
✓ All diagrams/charts/maps described in complete detail?
✓ All formatting preserved exactly?
✓ JSON structure correct?

RETURN ONLY THIS JSON STRUCTURE:

{{
  "batch_info": {{
    "batch_number": {batch_number},
    "start_question": {start_num},
    "end_question": {end_num},
    "subject": "CBSE Political Science Class 12",
    "quality_control_focus": "spelling mistakes, dates accuracy, grammar, missing words"
  }},
  "questions": [
    {{
      "question_number": "exact question number as it appears in the document",
      "question_text": "complete question text copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and punctuation accuracy",
      "diagram_explain": "detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present",
      "section": "exact section name as written in the document (Political Science, Part A, Part B, etc.)",
      "marks": "exact marks notation as written in the document including brackets, time allocations, or any other details",
      "date_accuracy": "verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy",
      "quality_check": "comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy"
    }}
  ]
}}

Begin extraction now with QUALITY CONTROL focus. Start response with {{ and end with }}. Extract questions {start_num}-{end_num} ONLY with comprehensive quality verification.
    """

def get_answer_extraction_prompt(batch_number: int, start_num: int, end_num: int) -> str:
    """Generate CBSE Political Science Class 12 answer extraction prompt with quality control focus"""
    return f"""
You are a precision document extraction specialist with QUALITY CONTROL expertise. Extract answers {start_num} to {end_num} from this CBSE Political Science Class 12 document with ABSOLUTE ACCURACY and comprehensive quality verification.

This is a CBSE Class 12 Political Science answer key or solution document. You must extract answers {start_num} to {end_num} with PERFECT ACCURACY and conduct thorough quality control checks.

CRITICAL EXTRACTION RULES (CBSE POLITICAL SCIENCE CLASS 12):
1. Read the document line by line, word by word with meticulous attention to detail.
2. Copy EVERYTHING exactly as written—do not paraphrase or summarize.
3. Maintain exact formatting, punctuation, spacing, and capitalization.
4. Include the correct answer option AND the complete explanation, reasoning, political context, and any additional notes.
5. Copy any step-by-step solutions, political explanations, or constitutional interpretations exactly as formatted.
6. Include all political terminology, constitutional provisions, and proper nouns exactly as shown.
7. For diagrams, maps, charts, or organizational structures: provide detailed descriptions including all labels, captions, and political references.
8. Include marks allocation, section names, and time limits exactly as written.
9. For assertion-reason type answers, copy both assertion and reason statements word-for-word, including the correct option and explanation.

QUALITY CONTROL REQUIREMENTS (CRITICAL):
⚠️ SPELLING VERIFICATION: Check every word for spelling mistakes, especially political terms, names of leaders, parties, institutions
⚠️ GRAMMAR ACCURACY: Verify grammatical correctness, sentence structure, verb tenses, subject-verb agreement
⚠️ DATE ACCURACY: Verify all historical dates, constitutional amendment years, election years, independence dates
⚠️ MISSING WORDS: Check for incomplete sentences, missing articles, prepositions, conjunctions
⚠️ PUNCTUATION: Ensure correct punctuation marks, quotation marks, apostrophes, commas, periods
⚠️ FACTUAL ACCURACY: Verify names of political leaders, parties, countries, constitutional articles, amendments
⚠️ TERMINOLOGY CONSISTENCY: Check consistency in political science terminology usage

Look for these CBSE Political Science answer patterns:
- Answer indicators: "Ans:", "Answer:", "Solution:", "Correct option:", etc.
- Correct options: "Answer: (b)", "Ans: (c)", "(d) is correct", etc.
- Explanations: Full justification or reasoning text following the correct answer
- Solutions: Step-by-step working for political science problems
- Marks breakdown: "1 mark for correct option + 2 marks for explanation", "[3 marks]", "(5)", etc.
- Sections: "Part A", "Part B", "Political Science", "Contemporary World Politics", "Politics in India"
- Constitutional references: "Article 370", "42nd Amendment", "Preamble", etc.
- Political entities: "Indian National Congress", "Bharatiya Janata Party", "United Nations", etc.
- Important dates: "1947", "1975", "1991", "2002", etc.
- Key personalities: "Jawaharlal Nehru", "Indira Gandhi", "Nelson Mandela", etc.

MANDATORY QUALITY CHECKS:
1. Focus EXCLUSIVELY on answers {start_num} through {end_num} - ignore all others
2. Extract EVERY SINGLE WORD exactly as written with spelling verification
3. Preserve ALL formatting: newlines, spacing, indentation, bullet points
4. Include ALL content for each answer - no truncation or summarization
5. For multi-part answers: include ALL parts (a), (b), (c), etc.
6. Copy tables cell by cell if present
7. Verify all dates and historical references for accuracy
8. Check grammar and sentence structure
9. Identify any missing or incomplete words
10. Return ONLY valid JSON - no explanations, notes, or markdown

For each answer, provide:
- answer_number: exact answer number as it appears in the document
- answer_text: complete answer copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and factual accuracy
- diagram_explain: detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present
- section: exact section name as written in the document (Political Science, Part A, Part B, etc.)
- marks: exact marks notation as written in the document including distribution, partial marks, or any other details
- date_accuracy: verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy
- quality_check: comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy

EXTRACTION & QUALITY CHECKLIST:
✓ Found answer {start_num}? Copy everything word-for-word with spelling check
✓ Found answer {start_num + 1}? Copy everything word-for-word with grammar check
{"✓ Found answer " + str(end_num) + "? Copy everything word-for-word with complete quality verification" if end_num > start_num else ""}
✓ All dates and years verified for accuracy?
✓ All political terms and names checked for spelling?
✓ All sentences complete with no missing words?
✓ All punctuation marks correct?
✓ All explanations and reasoning included?
✓ All diagrams/charts/maps described in complete detail?
✓ All formatting preserved exactly?
✓ JSON structure correct?

RETURN ONLY THIS JSON STRUCTURE:

{{
  "batch_info": {{
    "batch_number": {batch_number},
    "start_answer": {start_num},
    "end_answer": {end_num},
    "subject": "CBSE Political Science Class 12",
    "quality_control_focus": "spelling mistakes, dates accuracy, grammar, missing words"
  }},
  "answers": [
    {{
      "answer_number": "exact answer number as it appears in the document",
      "answer_text": "complete answer copied word-for-word with quality control verification for spelling mistakes, grammar errors, missing words, and factual accuracy",
      "diagram_explain": "detailed description of any political maps, charts, constitutional diagrams, organizational structures, or visual elements including all labels, captions, and political references, or null if none present",
      "section": "exact section name as written in the document (Political Science, Part A, Part B, etc.)",
      "marks": "exact marks notation as written in the document including distribution, partial marks, or any other details",
      "date_accuracy": "verification of all historical dates, years, constitutional amendments, and political events mentioned for accuracy",
      "quality_check": "comprehensive quality control assessment for spelling mistakes, grammar errors, missing words, punctuation issues, and factual accuracy"
    }}
  ]
}}

Begin extraction now with QUALITY CONTROL focus. Start response with {{ and end with }}. Extract answers {start_num}-{end_num} ONLY with comprehensive quality verification.
    """

def get_quality_control_prompts() -> Dict[str, str]:
    """Get specialized quality control prompts for different aspects"""
    return {
        "spelling_check": """
SPELLING VERIFICATION PROMPT:
Check the following Political Science content for spelling mistakes:
- Names of political leaders (Jawaharlal Nehru, Indira Gandhi, A.P.J. Abdul Kalam, etc.)
- Political parties (Indian National Congress, Bharatiya Janata Party, Communist Party, etc.)
- International organizations (United Nations, World Bank, International Monetary Fund, etc.)
- Countries and capitals (Bangladesh, Sri Lanka, Myanmar, etc.)
- Constitutional terms (Preamble, Fundamental Rights, Directive Principles, etc.)
- Political concepts (federalism, secularism, democracy, sovereignty, etc.)
Report any spelling errors found with correct spellings.
        """,
        
        "date_accuracy": """
DATE ACCURACY VERIFICATION PROMPT:
Verify the accuracy of all dates mentioned in the Political Science content:
- Independence: August 15, 1947
- Republic Day: January 26, 1950
- Emergency period: June 25, 1975 - March 21, 1977
- Economic reforms: 1991
- Partition of states: Various years (check each specifically)
- Constitutional amendments: Check amendment numbers and years
- Election years: Lok Sabha and Vidhan Sabha elections
Report any date inaccuracies with correct dates.
        """,
        
        "grammar_check": """
GRAMMAR VERIFICATION PROMPT:
Check the following Political Science content for grammar errors:
- Subject-verb agreement
- Verb tenses (especially when describing historical events)
- Sentence structure and clarity
- Use of articles (a, an, the)
- Prepositions and conjunctions
- Parallel structure in lists
- Pronoun-antecedent agreement
Report any grammar errors found with corrections.
        """,
        
        "missing_words": """
MISSING WORDS VERIFICATION PROMPT:
Check the following Political Science content for missing words:
- Incomplete sentences
- Missing articles (a, an, the)
- Missing prepositions (in, on, at, by, with, etc.)
- Missing conjunctions (and, but, or, because, etc.)
- Missing parts of compound terms
- Incomplete proper nouns or titles
Report any missing words with complete sentences.
        """,
        
        "factual_accuracy": """
FACTUAL ACCURACY VERIFICATION PROMPT:
Verify the factual accuracy of Political Science content:
- Names of political leaders and their positions
- Constitutional articles and their content
- Amendment numbers and their provisions
- Election results and years
- Policy names and implementation years
- International relations facts
- Historical events and their consequences
Report any factual inaccuracies with correct information.
        """
    }

def get_document_overview_prompt(content_type: str) -> str:
    """Generate document overview prompt for CBSE Political Science Class 12"""
    return f"""
You are a document analysis specialist. Analyze this CBSE Political Science Class 12 document and provide a comprehensive overview.

DOCUMENT ANALYSIS REQUIREMENTS:
1. Identify the document type: textbook, question paper, answer key, or supplementary material
2. Determine the total number of {content_type} present in the document
3. Identify chapter/section structure and organization
4. Note any quality issues: spelling mistakes, grammar errors, missing content, date inaccuracies

POLITICAL SCIENCE CONTENT ANALYSIS:
- Constitutional topics covered (Fundamental Rights, DPSP, Amendments, etc.)
- Political systems discussed (Federal structure, Electoral process, etc.)
- International relations content (UN, SAARC, Global politics, etc.)
- Contemporary issues addressed (Globalization, Regional aspirations, etc.)
- Historical references and dates mentioned
- Key political personalities and parties referenced

QUALITY CONTROL ASSESSMENT:
⚠️ Check for spelling mistakes in political terms and names
⚠️ Verify accuracy of historical dates and events
⚠️ Identify grammar and punctuation errors
⚠️ Note any missing or incomplete content
⚠️ Flag factual inaccuracies

Provide your analysis in this JSON format:
{{
  "document_type": "type of document",
  "total_{content_type}": number,
  "chapters_sections": ["list of chapters/sections"],
  "quality_issues": {{
    "spelling_errors": number,
    "grammar_errors": number,
    "date_inaccuracies": number,
    "missing_content": number
  }},
  "content_topics": ["list of main topics"],
  "recommended_batch_size": number
}}
    """

def get_subject_name() -> str:
    """Get the subject name"""
    return "CBSE Political Science Class 12"

def get_extraction_summary_prompt() -> str:
    """Get prompt for generating extraction summary with quality metrics"""
    return """
Generate a comprehensive extraction summary for CBSE Political Science Class 12 book including:

EXTRACTION METRICS:
- Total questions/answers extracted
- Batch processing details
- Quality control results

QUALITY CONTROL SUMMARY:
- Spelling mistakes found and corrected
- Grammar errors identified and fixed
- Date inaccuracies detected and verified
- Missing words found and completed
- Factual errors discovered and corrected

CONTENT ANALYSIS:
- Major topics covered
- Constitutional provisions referenced
- Historical events mentioned
- Political personalities included
- Key concepts extracted

RECOMMENDATIONS:
- Areas needing additional review
- Suggestions for content improvement
- Quality enhancement recommendations
    """
