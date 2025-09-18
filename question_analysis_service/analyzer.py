"""
CBSE Computer Applications Question Paper Analyzer with Batch Analysis + Concise Summary
Detailed batch analysis for accuracy, then concise final report
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CBSEQuestionAnalyzer:
    def __init__(self, api_key=None):
        self.setup_gemini(api_key)
        
    def setup_gemini(self, api_key=None):
        """Initialize Gemini API"""
        if api_key:
            genai.configure(api_key=api_key)
        else:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Please provide API key or set GEMINI_API_KEY environment variable")
            genai.configure(api_key=api_key)
        
        # Check if using placeholder key
        if api_key == "placeholder-gemini-key":
            logger.warning("Using placeholder Gemini API key - analysis will not work properly")
            # Create a mock model for testing
            self.model = None
            return
        
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("✓ Gemini 2.0 Flash API initialized")
        except Exception as e:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✓ Gemini 1.5 Flash API initialized")
            except:
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("✓ Gemini Pro API initialized")

    def load_json_file(self, file_path):
        """Load and parse JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            raise ValueError(f"Error reading {file_path}: {str(e)}")

    def extract_questions_from_json(self, file_path):
        """Extract questions from JSON file"""
        try:
            logger.info(f"📄 Loading questions from: {file_path}")
            data = self.load_json_file(file_path)
            
            if 'questions' not in data:
                raise ValueError("JSON file must contain 'questions' array")
            
            questions = []
            for q in data['questions']:
                question_data = {
                    'number': q.get('question_number'),
                    'text': q.get('question_text', ''),
                    'section': q.get('section', ''),
                    'marks': q.get('marks', ''),
                    'diagram_explain': q.get('diagram_explain')
                }
                questions.append(question_data)
            
            document_info = data.get('document_info', {})
            logger.info(f"✅ Loaded {len(questions)} questions")
            
            return questions, document_info
            
        except Exception as e:
            raise RuntimeError(f"Error extracting questions: {str(e)}")

    def create_questions_batches(self, questions, batch_size=5):
        """Divide questions into manageable batches"""
        batches = []
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batches.append(batch)
        return batches

    def create_detailed_batch_prompt(self, questions_batch, batch_num, total_batches):
        """Create detailed analysis prompt for each batch"""
        
        questions_text = ""
        for q_data in questions_batch:
            questions_text += f"""
--- QUESTION {q_data['number']} ---
SECTION: {q_data['section']} | MARKS: {q_data['marks']}
QUESTION TEXT: {q_data['text']}
{f"DIAGRAM: {q_data['diagram_explain']}" if q_data['diagram_explain'] else ""}

"""
        
        prompt = f"""
You are a CBSE Computer Applications Education Expert conducting THOROUGH analysis of Class 10 Computer Applications questions.

CRITICAL INSTRUCTION: You must examine EVERY word, phrase, technical concept, and procedural detail in each question. Do NOT overlook any issues, no matter how minor they seem.

BATCH {batch_num} of {total_batches}

CBSE CLASS 10 COMPUTER APPLICATIONS SYLLABUS (EXACT TOPICS):
- Unit I: Basic IT concepts including Digital Documentation, Electronic Spreadsheet, Database Management, and Presentation basics.
- Unit II: Internet and Web Technologies, Web Browsers and Search Engines, Instant Messaging and Video Conferencing, E-Learning
- Unit III: Digital Documentation (Advanced), Advanced Word Processing Features, Reviewing and Finalizing Documents, Using References, Creating Forms
- Unit IV: Electronic Spreadsheet (Advanced), Mathematical and Statistical Functions, Lookup Functions and What-if Analysis, Charts and Pivot Tables, Sorting and Filtering
- Unit V: Database Management System, Introduction to Database Concepts, Creating a Database, Data Entry and Validation, Querying and Reporting
- Unit VI: Presentation (Advanced), Working with Slide Master, Animation and Slide Transition, Multimedia Elements Integration, Presentation Delivery Techniques

ANALYZE THESE QUESTIONS WITH EXTREME ATTENTION TO DETAIL:
{questions_text}

FOR EACH QUESTION, SCRUTINIZE:

1. GRAMMAR & LANGUAGE (Check every sentence):
- Spelling mistakes (especially technical terms like "algorithm", "spreadsheet", "database")
- Missing punctuation (periods, question marks, commas)
- Grammatical errors (subject-verb agreement, tense consistency)
- Awkward phrasing or unclear sentences
- Inappropriate vocabulary level for Class 10
- Ambiguous wording that could confuse students

2. TECHNICAL ACCURACY (Verify every technical detail):
- Check ALL software application names for correct spelling and case sensitivity
- Verify hardware component terminology
- Ensure internet protocol terms are accurate
- Check file format specifications and extensions
- Verify programming syntax elements (if any)
- Ensure database terminology is correct
- Check security-related terms for accuracy
- Verify multimedia file formats and concepts

3. SYLLABUS ALIGNMENT (Match with exact CBSE curriculum):
- Is EVERY concept mentioned in CBSE Class 10 Computer Applications syllabus?
- Check if difficulty level matches Class 10 standards
- Verify if examples used are from prescribed curriculum (MS Office Suite)
- Ensure terminology matches NCERT Computer Applications textbook
- Flag any outdated software version references

4. QUESTION CLARITY & CONSTRUCTION:
- Is the question unambiguous and clear?
- Can students understand exactly what technical procedure is being asked?
- Are there multiple interpretations possible?
- Is the language appropriate for 15-16 year olds?
- Are technical instructions clear and complete?
- Do questions test practical, applicable skills?

5. MCQ ANALYSIS (For multiple choice questions):
- Are all options grammatically parallel?
- Are distractors plausible but clearly incorrect?
- Is there only ONE technically correct answer?
- Are options of similar length and complexity?
- Do options avoid absolute terms unless technically accurate?
- Are technical terms spelled consistently across options?

6. MARK ALLOCATION:
- Does the question complexity match the marks allocated?
- Is the cognitive demand appropriate for the marks?
- Are similar technical procedures getting similar marks?
- Does marking align with practical difficulty of the task?

7. CBSE PATTERN COMPLIANCE:
- Does the question format match standard CBSE Computer Applications style?
- Is the question type appropriate for the section?
- Does it test the right competency level (Knowledge/Application/HOTS)?
- Are practical scenarios relevant to real-world computer applications?

8. SOFTWARE-SPECIFIC ACCURACY:
- MS Word: Check document formatting, mail merge, template concepts
- MS Excel: Verify formula syntax, function names, chart terminology
- MS PowerPoint: Check animation, transition, multimedia terminology  
- Database: Verify field types, record operations, table concepts
- Internet: Check browser features, search techniques, email protocols

OUTPUT FORMAT:

BATCH {batch_num} DETAILED ANALYSIS
================================

QUESTION-BY-QUESTION CRITICAL FINDINGS:

Q{q_data['number']}: "{q_data['text'][:80]}..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 GRAMMAR & LANGUAGE: [List EVERY issue found with specific examples, or "No issues detected"]
🔬 TECHNICAL ACCURACY: [List EVERY technical error with corrections, or "All technical details verified correct"]
📚 SYLLABUS ALIGNMENT: [Check against exact CBSE Computer Applications curriculum, note any deviations, or "Perfectly aligned"]
❓ QUESTION CLARITY: [Note any unclear/ambiguous parts with suggestions, or "Crystal clear"]
📊 MCQ QUALITY: [For MCQs only - analyze each option for technical accuracy, or "Not applicable"]
🎯 MARK ALLOCATION: [Comment on appropriateness for technical difficulty, or "Appropriate"]
📋 CBSE COMPLIANCE: [Note any format/style issues, or "Fully compliant"]
💻 SOFTWARE ACCURACY: [Check specific software terminology and procedures, or "All software references correct"]
⭐ OVERALL RATING: [Excellent/Good/Needs Minor Revision/Needs Major Revision/Unsuitable]
💡 SPECIFIC RECOMMENDATIONS: [Concrete suggestions for improvement, or "No changes needed"]

[Repeat detailed analysis for EVERY question in batch]

BATCH CRITICAL SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 Questions with Grammar Issues: [Count] - Q[numbers]
🚨 Questions with Technical Errors: [Count] - Q[numbers]  
🚨 Questions with Syllabus Deviations: [Count] - Q[numbers]
🚨 Questions with Clarity Issues: [Count] - Q[numbers]
🚨 Questions with MCQ Problems: [Count] - Q[numbers]
🚨 Questions with Mark Allocation Issues: [Count] - Q[numbers]
🚨 Questions with CBSE Compliance Issues: [Count] - Q[numbers]
🚨 Questions with Software Accuracy Issues: [Count] - Q[numbers]

REMEMBER: Your job is to catch EVERY possible issue. Be extremely critical and thorough. No detail is too small to examine.
"""
        return prompt

    def analyze_question_batch(self, questions_batch, batch_num, total_batches, verbose=False):
        """Analyze a batch of questions in detail"""
        try:
            if verbose:
                logger.info(f"🔍 Analyzing batch {batch_num}/{total_batches} ({len(questions_batch)} questions)")
            
            # Check if model is available
            if self.model is None:
                return f"[MOCK ANALYSIS] Batch {batch_num} - {len(questions_batch)} questions analyzed (using placeholder API key)"
            
            prompt = self.create_detailed_batch_prompt(questions_batch, batch_num, total_batches)
            
            response = self.model.generate_content([prompt])
            
            if not response.text:
                return f"[ERROR: Empty response for batch {batch_num}]"
            
            return response.text.strip()
            
        except Exception as e:
            error_msg = f"[ERROR: Failed to analyze batch {batch_num} - {str(e)}]"
            logger.error(f"❌ {error_msg}")
            return error_msg

    def create_concise_summary_prompt(self, all_batch_results, total_questions, document_info):
        """Create prompt for concise summary from detailed batch analyses"""
    
        combined_results = "\n\n".join([f"=== BATCH {i+1} RESULTS ===\n{result}" for i, result in enumerate(all_batch_results)])
    
        prompt = f"""
You are a CBSE Computer Applications Education Expert creating a CONCISE SUMMARY from detailed batch analyses.

DOCUMENT: {document_info.get('title', 'Unknown')} - Class {document_info.get('class', '10')} Computer Applications
TOTAL QUESTIONS: {total_questions}

DETAILED BATCH ANALYSIS RESULTS:
{combined_results}

TASK: Create a concise summary report highlighting ONLY the critical issues found across all batches.

OUTPUT FORMAT (Use Markdown):

# CBSE Computer Applications Question Paper Analysis

## Document Information
- **Document:** {document_info.get('title', 'Unknown')}
- **Total Questions:** {total_questions}
- **Analysis Date:** {datetime.now().strftime("%Y-%m-%d")}

## Critical Issues Found

### Grammar & Language Errors
[List specific issues with question numbers, or "None found"]

### Technical Inaccuracies
[List software/hardware/internet errors with question numbers and brief explanation, or "None found"]

### Syllabus Misalignment  
[List off-syllabus content with question numbers, or "None found"]

### Unclear/Ambiguous Questions
[List confusing questions with question numbers and reason, or "None found"]

### Marking Scheme Issues
[List incorrect mark allocations with question numbers, or "None found"]

### MCQ Specific Issues
[List problems with multiple choice questions, or "None found"]

### Software-Specific Problems
[List MS Office, database, or internet-related errors, or "None found"]

## Summary

| Metric | Value |
|--------|-------|
| **Total Critical Issues** | [Number] |
| **Questions with Issues** | [Count] out of {total_questions} |
| **Paper Quality** | [Excellent/Good/Needs Revision/Poor] |
| **Recommendation** | [Ready for use/Minor fixes needed/Major revision required] |

## Unit Distribution Check

| Unit | Questions | Marks | Status |
|------|-----------|-------|--------|
| **Unit I (IT Basics)** | [X questions] | [Y marks] | [Status] |
| **Unit II (Internet & Web)** | [X questions] | [Y marks] | [Status] |
| **Unit III (Digital Documentation)** | [X questions] | [Y marks] | [Status] |
| **Unit IV (Electronic Spreadsheet)** | [X questions] | [Y marks] | [Status] |
| **Unit V (Database Management)** | [X questions] | [Y marks] | [Status] |
| **Unit VI (Presentation)** | [X questions] | [Y marks] | [Status] |

## Priority Fixes Needed

1. [Most critical technical issue that needs immediate attention]
2. [Second priority issue - software accuracy]
3. [Third priority issue - syllabus alignment]  
4. [Fourth priority issue - question clarity]
5. [Fifth priority issue - practical relevance]

---

**Note:** Extract and consolidate ONLY the actual issues found in the detailed analysis. Be specific with question numbers and technical corrections needed.
"""
    
        return prompt

    def generate_concise_summary(self, all_batch_results, total_questions, document_info, verbose=False):
        """Generate concise summary from detailed batch results"""
        try:
            if verbose:
                logger.info(f"📊 Generating concise summary from {len(all_batch_results)} detailed batches...")
            
            prompt = self.create_concise_summary_prompt(all_batch_results, total_questions, document_info)
            
            response = self.model.generate_content([prompt])
            
            if not response.text:
                return "[ERROR: Empty response for summary]"
            
            return response.text.strip()
            
        except Exception as e:
            error_msg = f"[ERROR: Failed to generate summary - {str(e)}]"
            logger.error(f"❌ {error_msg}")
            return error_msg

    def analyze_question_paper(self, file_path, output_path=None, batch_size=5, verbose=False):
        """Main analysis process: detailed batches → concise summary"""
        try:
            logger.info(f"🚀 Starting Detailed CBSE Question Paper Analysis...")
            
            # Step 1: Extract questions
            questions, document_info = self.extract_questions_from_json(file_path)
            total_questions = len(questions)
            
            # Step 2: Create batches for detailed analysis
            batches = self.create_questions_batches(questions, batch_size)
            total_batches = len(batches)
            
            logger.info(f"📋 Analysis Plan: {total_questions} questions in {total_batches} batches")
            
            # Step 3: Detailed batch analysis
            logger.info(f"🔍 Conducting detailed batch analysis...")
            all_batch_results = []
            
            for i, batch in enumerate(batches, 1):
                if verbose:
                    logger.info(f"   Batch {i}/{total_batches}: Questions {batch[0]['number']}-{batch[-1]['number']}")
                
                batch_result = self.analyze_question_batch(batch, i, total_batches, verbose)
                all_batch_results.append(batch_result)
            
            # Step 4: Generate concise summary
            logger.info(f"📊 Generating concise summary report...")
            final_summary = self.generate_concise_summary(all_batch_results, total_questions, document_info, verbose)
            
            # Step 5: Save final report only
            if not output_path:
                source_name = Path(file_path).stem
                output_path = f"{source_name}_Analysis.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_summary)
            
            logger.info(f"✅ Analysis completed!")
            logger.info(f"📊 Analyzed {total_questions} questions in {total_batches} detailed batches")
            logger.info(f"💾 Concise report saved to: {output_path}")
            
            return final_summary, output_path
            
        except Exception as e:
            logger.error(f"❌ Error during analysis: {str(e)}")
            raise
