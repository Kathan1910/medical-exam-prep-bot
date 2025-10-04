# core/agents/prompts.py
from typing import Dict

DIFFICULTY_DESCRIPTIONS = {
    "intermediate": """
    - Test basic recall and fundamental understanding
    - Focus on definitions, classifications, and core concepts
    - Single-step reasoning required
    - Directly stated in the textbook
    """,
    
    "advanced": """
    - MUST be application-based with clinical/practical scenarios
    - Present a case or situation requiring concept application
    - Integration of multiple related concepts
    - Two-step reasoning process
    - Real-world context
    """,
    
    "complex": """
    - MUST be complex case-based scenarios
    - Multi-step clinical reasoning required
    - Integration across multiple concepts/systems
    - Differential diagnosis or complex decision-making
    - Realistic clinical presentations
    """
}

def get_generation_prompt(difficulty: str, context: str, image_context: str = "") -> str:
    """Generate the main question generation prompt with context-aware application templates"""
    
    # Base instruction varies by difficulty
    if difficulty == "intermediate":
        question_format_instruction = """
**Question Format (INTERMEDIATE):**
Create a straightforward factual question testing basic understanding.

Example structure:
- "What is the primary function of [structure/system]?"
- "Which of the following describes [concept]?"
- "What are the main components of [system]?"
"""
    else:  # advanced or complex
        question_format_instruction = """
**Question Format (APPLICATION-BASED):**

Step 1: **Analyze the content context** to determine the appropriate scenario type:

**For Anatomy/Physiology content** → Patient presentation with anatomical findings:
- "A patient presents with [symptoms]. Examination reveals [findings]. What structure is most likely affected?"
- "During surgery, a surgeon observes [anatomical description]. What is this structure?"

**For Pathology content** → Clinical presentation requiring diagnosis:
- "A [age] [gender] presents with [symptoms] and [history]. Laboratory shows [findings]. What is the most likely diagnosis?"
- "A patient with [condition] develops [new symptoms]. What complication has occurred?"

**For Pharmacology content** → Medication scenario:
- "A patient taking [drug] for [condition] develops [symptoms]. What is the mechanism?"
- "Which medication is most appropriate for a patient with [clinical scenario]?"

**For Diagnostic/Procedure content** → Clinical decision-making:
- "A patient with [presentation] requires evaluation. What is the most appropriate next step?"
- "During [procedure], [finding] is observed. What should be done?"

**For Any other medical content** → Create scenario appropriate to the subject:
- Analyze what the content teaches
- Create a realistic situation where that knowledge applies
- Frame as a decision, diagnosis, or identification question

**CRITICAL RULES:**
1. Base scenario details STRICTLY on the provided context
2. Use realistic parameters (age, gender, symptoms) from the textbook examples
3. Make the scenario require applying the concept, not just recalling it
4. Ensure distractors are plausible alternative applications
"""

    return f"""You are a medical education expert creating high-quality MCQs for exam preparation.

**Difficulty Level**: {difficulty.upper()}
{DIFFICULTY_DESCRIPTIONS[difficulty]}

**Source Material**:
{context}

{f"**Medical Image Context**:\n{image_context}\n" if image_context else ""}

{question_format_instruction}

**Instructions:**
1. **ANALYZE the content type first** - Is this anatomy, pathology, pharmacology, physiology, etc.?
2. **Determine the appropriate scenario format** based on content type and difficulty
3. Create ONE multiple-choice question with 4 options (A, B, C, D)
4. Base ALL scenario details STRICTLY on the provided content
5. For {difficulty} difficulty, {"create a straightforward factual question" if difficulty == "intermediate" else "you MUST create an application-based scenario"}
6. Ensure ONE clearly correct answer
7. Make distractors plausible but definitively incorrect
8. Provide comprehensive explanation

**CRITICAL - Detailed Explanation Format:**
Your explanation MUST include:
1. **Why the Correct Answer is Right**: Explain the medical reasoning with supporting facts
2. **Why Each Distractor is Wrong**: Explain specifically why incorrect options are wrong
3. **Clinical Context**: Explain the real-world relevance
4. **Key Learning Point**: A memorable takeaway

**CRITICAL - Reference Format:**
For each reference, provide:
- Page number
- Exact quote or paraphrased content (20-50 words)
- Section/heading if available

**Response Format** (JSON):
{{
    "question": "{"Direct factual question" if difficulty == "intermediate" else "Complete clinical scenario with question"}",
    "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
    }},
    "correct_answer": "A",
    "explanation": {{
        "correct_reasoning": "Detailed explanation of why the correct answer is right. Minimum 3-4 sentences.",
        "distractor_analysis": {{
            "A": "Why this is incorrect (if not correct)",
            "B": "Why this is incorrect (if not correct)",
            "C": "Why this is incorrect (if not correct)",
            "D": "Why this is incorrect (if not correct)"
        }},
        "clinical_context": "Real-world application or significance. 2-3 sentences.",
        "key_takeaway": "One memorable learning point"
    }},
    "references": [
        {{
            "page": 45,
            "quote": "Exact quote supporting the answer",
            "section": "Section name if available"
        }}
    ],
    "key_concepts": ["concept1", "concept2"],
    "reasoning_type": "recall/application/analysis",
    "question_type": "{"factual" if difficulty == "intermediate" else "case_based"}"
}}

**EXAMPLE - Advanced Pathology Question:**
{{
    "question": "A 55-year-old male with a 30-year smoking history presents with persistent cough, hemoptysis, and weight loss over 3 months. Chest X-ray shows a mass in the right upper lobe. Biopsy reveals malignant cells with keratin production and intercellular bridges. What is the most likely diagnosis?",
    "options": {{
        "A": "Squamous cell carcinoma",
        "B": "Adenocarcinoma", 
        "C": "Small cell carcinoma",
        "D": "Large cell carcinoma"
    }},
    "correct_answer": "A",
    "explanation": {{
        "correct_reasoning": "Squamous cell carcinoma is characterized by keratin production and intercellular bridges (desmosomes) on histology. It typically occurs in the central airways and is strongly associated with smoking. The patient's presentation with central mass and smoking history fits this diagnosis.",
        "distractor_analysis": {{
            "B": "Adenocarcinoma typically shows glandular differentiation and mucin production, not keratin and intercellular bridges. It's usually peripheral, not central.",
            "C": "Small cell carcinoma shows small cells with scant cytoplasm and neuroendocrine markers, not keratin production.",
            "D": "Large cell carcinoma lacks specific differentiation features and doesn't show keratin production or intercellular bridges."
        }},
        "clinical_context": "Recognizing histological features is crucial for lung cancer classification, as different types have different prognoses and treatment approaches. Squamous cell carcinoma accounts for about 30% of lung cancers and is more responsive to surgery when localized.",
        "key_takeaway": "Keratin + intercellular bridges = Squamous cell carcinoma"
    }}
}}

**EXAMPLE - Advanced Anatomy Question:**
{{
    "question": "During a surgical procedure in the femoral triangle, the surgeon identifies a structure lying lateral to the femoral vein and deep to the inguinal ligament. Which structure is this?",
    "options": {{
        "A": "Femoral artery",
        "B": "Femoral nerve",
        "C": "Lymphatic vessels",
        "D": "Saphenous vein"
    }},
    "correct_answer": "A"
}}

Now analyze the provided context and generate an appropriate question:"""

def get_validation_prompt(question_data: Dict, source_context: str) -> str:
    """Generate the validation prompt with application-based criteria"""
    
    explanation = question_data.get('explanation', {})
    if isinstance(explanation, str):
        explanation_text = explanation
    else:
        explanation_text = f"""
Correct Reasoning: {explanation.get('correct_reasoning', 'N/A')}
Distractor Analysis: {explanation.get('distractor_analysis', 'N/A')}
Clinical Context: {explanation.get('clinical_context', 'N/A')}
"""
    
    return f"""You are a medical fact-checker reviewing an MCQ for accuracy and quality.

**Question to Review**:
Question: {question_data['question']}
Options: {question_data['options']}
Correct Answer: {question_data['correct_answer']}
Explanation: {explanation_text}
Question Type: {question_data.get('question_type', 'N/A')}

**Source Context**:
{source_context}

**Validation Criteria**:
1. Factual Accuracy: Does the question align with source material?
2. Medical Correctness: Is the medical information accurate?
3. Answer Clarity: Is there definitively ONE correct answer?
4. Distractor Quality: Are wrong options plausible but clearly incorrect?
5. Explanation Completeness: Does it explain correct AND incorrect options?
6. Reference Quality: Are references specific and verifiable?
7. **Application Quality** (if case-based): Is the scenario realistic and based on source content?

**Response Format** (JSON):
{{
    "is_valid": true/false,
    "confidence_score": 0-100,
    "issues": ["List specific problems if any"],
    "suggestions": ["Improvements if needed"],
    "medical_accuracy": true/false,
    "clarity_score": 0-100,
    "explanation_quality_score": 0-100,
    "application_quality_score": 0-100
}}

Provide your validation:"""