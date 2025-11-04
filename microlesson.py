import os
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from educhain import Educhain, LLMConfig
from langchain_openai import ChatOpenAI
import streamlit as st

# ============================================================================
# RESPONSE MODELS - MULTIPLE QUESTION TYPES WITH EXPLANATIONS
# ============================================================================

class MCQOption(BaseModel):
    text: str = Field(description="The text of the option")
    correct: bool = Field(description="Whether this option is correct")

class MCQQuestion(BaseModel):
    question_type: str = Field(default="mcq", description="Always 'mcq'")
    question_text: str = Field(description="The question text")
    options: List[MCQOption] = Field(description="List of 4 answer options")
    explanation: str = Field(
        description="Explanation that appears after answering. Should teach something NEW beyond the pre-read - "
        "include why the correct answer is right, address common misconceptions, add an interesting fact or angle, "
        "use analogies or real-world examples. Make it conversational and insightful."
    )

class FillInBlankQuestion(BaseModel):
    question_type: str = Field(default="fill_blank", description="Always 'fill_blank'")
    question_text: str = Field(
        description="Question with _____ for the blank. Example: 'Vector _____ store numerical representations of text.'"
    )
    correct_answer: str = Field(description="The correct word/phrase for the blank")
    distractors: List[str] = Field(
        description="3 plausible wrong answers that could fit the blank"
    )
    explanation: str = Field(
        description="Explanation that appears after answering. Should teach something NEW beyond the pre-read - "
        "explain why this answer makes sense, provide context or additional insights, maybe share a related fact "
        "or application. Make it feel like learning more, not just 'you got it right'."
    )

class TrueFalseQuestion(BaseModel):
    question_type: str = Field(default="true_false", description="Always 'true_false'")
    statement: str = Field(description="A statement that is either true or false")
    correct_answer: bool = Field(description="True or False")
    explanation: str = Field(
        description="Explanation that appears after answering. Should teach something NEW beyond the pre-read - "
        "explain why it's true/false, address the common misconception if false, add surprising facts or nuances, "
        "show real-world implications. Go deeper than just 'correct because X'."
    )

class MatchingPair(BaseModel):
    left: str = Field(description="Left side item (term, concept, etc.)")
    right: str = Field(description="Right side item that matches")

class MatchingQuestion(BaseModel):
    question_type: str = Field(default="matching", description="Always 'matching'")
    instruction: str = Field(
        description="Brief instruction like 'Match each term to its definition'"
    )
    pairs: List[MatchingPair] = Field(
        description="3-4 pairs to match. Right side will be shuffled in UI."
    )
    explanation: str = Field(
        description="Explanation that appears after answering. Should teach something NEW - "
        "explain the relationships between the pairs, why these connections matter, add context or interesting facts "
        "about how these pairs show up in real life. Make the connections memorable."
    )

class OrderingQuestion(BaseModel):
    question_type: str = Field(default="ordering", description="Always 'ordering'")
    question_text: str = Field(
        description="Question asking to put items in correct order"
    )
    correct_order: List[str] = Field(
        description="3-4 items in the CORRECT order (will be shuffled in UI)"
    )
    explanation: str = Field(
        description="Explanation that appears after answering. Should teach something NEW - "
        "explain why this order matters, what happens if you get it wrong, add insights about the process or sequence. "
        "Help them understand the 'why' behind the order, not just 'this is the sequence'."
    )

# Union type for any question
Question = Union[MCQQuestion, FillInBlankQuestion, TrueFalseQuestion,
                 MatchingQuestion, OrderingQuestion]

class QuestionConfig(BaseModel):
    """Configuration for question generation"""
    mcq: int = Field(default=2, ge=0, description="Number of Multiple Choice Questions")
    true_false: int = Field(default=2, ge=0, description="Number of True/False Questions")
    fill_blank: int = Field(default=1, ge=0, description="Number of Fill in the Blank Questions")
    matching: int = Field(default=0, ge=0, description="Number of Matching Questions")
    ordering: int = Field(default=0, ge=0, description="Number of Ordering Questions")

    @property
    def total_questions(self) -> int:
        """Calculate total number of questions"""
        return self.mcq + self.true_false + self.fill_blank + self.matching + self.ordering

    def to_prompt_string(self) -> str:
        """Convert to a string for prompt injection"""
        parts = []
        if self.mcq > 0:
            parts.append(f"{self.mcq} Multiple Choice (MCQ)")
        if self.true_false > 0:
            parts.append(f"{self.true_false} True/False")
        if self.fill_blank > 0:
            parts.append(f"{self.fill_blank} Fill in the Blank")
        if self.matching > 0:
            parts.append(f"{self.matching} Matching")
        if self.ordering > 0:
            parts.append(f"{self.ordering} Ordering")
        return ", ".join(parts)

class BiteSizedContent(BaseModel):
    pre_read: str = Field(
        description="Engaging 2-3 paragraph introduction (250-350 words). "
        "Conversational tone like talking to a friend over chai. Use 'you', include multiple real-world examples "
        "from different contexts, add humor or surprise, explain jargon immediately, address anticipated questions. "
        "Start with a hook (story/scenario/question). Include at least one 'aha!' moment. "
        "Short paragraphs (2-3 sentences max). Make it compete with social media for attention."
    )

    questions: List[Union[MCQQuestion, FillInBlankQuestion, TrueFalseQuestion,
                          MatchingQuestion, OrderingQuestion]] = Field(
        description="List of questions of VARIED types as specified in the question configuration. "
        "Each question MUST have an explanation that teaches something new beyond the pre-read."
    )

    summary: List[str] = Field(
        description="3-5 concise bullet points (each 1-2 sentences). "
        "Each bullet should be a clear, memorable takeaway - practical and actionable where possible. "
        "Include analogies or 'so what' impact. Make them scannable and easy to recall later."
    )

    tags: List[str] = Field(
        description="3-5 relevant tags including: "
        "(1) The concept name itself, "
        "(2) The topic name, "
        "(3) Key terms/words from the content generated, "
        "(4) Related concepts from other topics, "
        "(5) Practical applications (e.g., 'Career', 'Daily Life', 'Decision Making'), "
        "(6) Cross-topic connections (if applicable). "
        "Tags help users discover related content and navigate the app."
    )

    concept_name: str = Field(description="The concept being taught")
    topic: str = Field(description="The parent topic")
    estimated_time: int = Field(description="Time in minutes (typically 5)")
    difficulty_level: str = Field(description="beginner, intermediate, or advanced")

    def show(self):
        """Display the content in a readable format"""
        print("=" * 80)
        print(f"📚 CONCEPT: {self.concept_name}")
        print(f"📖 TOPIC: {self.topic}")
        print(f"⏱️  TIME: {self.estimated_time} minutes")
        print(f"📊 LEVEL: {self.difficulty_level}")
        print("=" * 80)

        print("\n🔍 PRE-READ:")
        print("-" * 80)
        print(self.pre_read)

        print("\n\n🎯 QUESTIONS:")
        print("-" * 80)
        for i, q in enumerate(self.questions, 1):
            print(f"\n{'='*60}")
            print(f"Question {i} - Type: {q.question_type.upper()}")
            print('='*60)

            if q.question_type == "mcq":
                print(f"Q: {q.question_text}\n")
                for j, opt in enumerate(q.options):
                    marker = "✓" if opt.correct else " "
                    print(f"  [{marker}] {chr(65+j)}. {opt.text}")
                print(f"\n💡 EXPLANATION:\n{q.explanation}")

            elif q.question_type == "fill_blank":
                print(f"Q: {q.question_text}\n")
                print(f"  ✓ Correct: {q.correct_answer}")
                print(f"  Distractors: {', '.join(q.distractors)}")
                print(f"\n💡 EXPLANATION:\n{q.explanation}")

            elif q.question_type == "true_false":
                print(f"Statement: {q.statement}")
                print(f"  ✓ Answer: {'TRUE' if q.correct_answer else 'FALSE'}")
                print(f"\n💡 EXPLANATION:\n{q.explanation}")

            elif q.question_type == "matching":
                print(f"Instruction: {q.instruction}\n")
                for pair in q.pairs:
                    print(f"  {pair.left} ←→ {pair.right}")
                print(f"\n💡 EXPLANATION:\n{q.explanation}")

            elif q.question_type == "ordering":
                print(f"Q: {q.question_text}\n")
                print("  Correct order:")
                for idx, item in enumerate(q.correct_order, 1):
                    print(f"    {idx}. {item}")
                print(f"\n💡 EXPLANATION:\n{q.explanation}")

        print("\n\n✨ SUMMARY:")
        print("-" * 80)
        for i, point in enumerate(self.summary, 1):
            print(f"{i}. {point}")

        print("\n\n🏷️  TAGS:")
        print("-" * 80)
        print(" | ".join(self.tags))

        print("\n" + "=" * 80)

# ============================================================================
# DYNAMIC QUESTION TYPE PROMPT
# ============================================================================

DYNAMIC_PROMPT_TEMPLATE = """
You are creating bite-sized learning content for Unrot, a mobile-first learning app where people spend 5 minutes learning something new every day. The content must compete with social media for attention—it should be vivid, clear, and feel like a rewarding, relevant conversation.

Input:
Topic: {topic}
Concept: {concept}
Concept Description: {concept_description}

IMPORTANT: Understanding the Concept Description
The "Concept Description" is a teaser/hook—not the full scope of what should be covered. It sparks curiosity, but your job is to ensure readers walk away feeling, "Whoa, I actually get this now!" Your content should deliver:
A multi-faceted, well-rounded understanding of the concept
Relatable stories, analogies, or humor (no pop culture reference needed)
Instant, practical "aha" moments—why does this really matter to people?
Concrete, varied examples (not just textbook cases)
Intuitive explanations that anyone can relate to
Answers to the "So what?" behind the idea

Content Structure to Generate

1. PRE-READ (The Hook & Revelation)
Goal: Excite the reader and give them a solid, memorable understanding of the concept.
Requirements:
Length: 250–350 words max—fits comfortably on one phone screen, no endless scrolling
Tone: Imagine explaining something cool to a friend over a cup of chai—energetic, clear, never patronizing or stuffy
Structure:
Start with a story, everyday scenario, playful analogy, or a question that grabs curiosity in the first line.
Speaks directly to the reader ("you," "we"), inviting them into a conversation.
Unpack why this concept shows up everywhere and why it matters—cut to the heart, use humor or surprise.
Explain using real-world examples drawn from different domains (media, daily life, business, etc.).
Every piece of jargon is instantly disarmed with a plain-English translation—no one's left behind.
Anticipate common questions and address them (sometimes as a rhetorical Q&A within the text).
Insert at least one "aha!" insight or offbeat perspective—a fact, metaphor, or counterintuitive angle that makes readers pause and smile.
Keep paragraphs and sentences short and punchy—never a wall of text.
What to Avoid:
Don't just retell the concept description—expand, contextualize, and bring it alive
Don't over-focus on one example; always show variety and surprise
Don't use unexplained jargon; always break it down with analogies or humor
Writing Style Guidance:
Use "you"/"we" to make it direct and personal
Every section should feel like a fun, illuminating chat—not a dry lecture or a listicle

2. QUESTIONS (Test, Teach, Entertain)
Goal: Spark new discoveries—questions should teach as much as they test.
Requirements:
Generate EXACTLY {total_questions} questions with the following distribution:
{question_distribution}

QUESTION TYPE DETAILS:

A) MULTIPLE CHOICE (MCQ):
   - Traditional 4-option question
   - Best for: scenarios, problem-solving, application
   - Keep mobile-friendly: max 2 sentences, options under 15 words
   - All wrong answers should be plausible

B) TRUE/FALSE:
   - Single statement to judge as true or false
   - Best for: testing misconceptions, common myths, key facts
   - Make it thought-provoking, not obvious

C) FILL IN THE BLANK:
   - Sentence with one _____ to complete
   - Provide the correct answer + 3 plausible distractors
   - Best for: terminology, key concepts, definitions
   - Make the blank meaningful, not trivial
   - IMPORTANT: Only use ONE blank per question

D) MATCHING:
   - 3-4 pairs to match (left item to right item)
   - Best for: definitions, relationships, comparisons
   - Keep each item short (under 10 words)

E) ORDERING/SEQUENCING:
   - 3-4 items to put in correct order
   - Best for: processes, steps, chronology, priority
   - Items should be clear and distinct

Each question:
Tests core understanding of the concept
Reveals a fresh use-case, fact, or application not already covered
Avoids trickery—every question is a chance to reveal another angle
Include for each:
Question text (friendly, sometimes informal or story-driven)
Options or expected answer format
Correct answer
Explanation that unpacks why this answer is right, brings in a misconception (if any), and adds a nugget of insight or analogy

3. SUMMARY
Goal: Leave readers with 3–5 pithy, memorable takeaways they can quickly recall and share.
Requirements:
Each bullet is concise (1–2 sentences), practical, and (where possible) tied to an analogy, daily life, or "so what" impact.

4. TAGS (Optional but Recommended)
Goal: Discovery and connection—help users relate this lesson to others.
Requirements:
3–5 relevant tags (concepts, applications, difficulty level, cross-topic ties)

Quality Checklist
Before finalizing, verify:
 Pre-read is engaging from line one—feels like a conversation, not a textbook
 Fits one mobile screen (250–350 words)
 Multiple real-world examples, humor/analogies, and at least one "aha" fact or angle (pop culture not required)
 All jargon is demystified
 EXACTLY {total_questions} questions provided with the specified distribution
 Questions entertain and expand knowledge
 Each question's explanation includes a story or extra insight
 Bullet summary makes key takeaways scannable and applicable
 The whole lesson is as fun and rewarding as scrolling your favorite news or meme page

Creator Notes:
Mobile-first focus!
Every line competes for attention
"Friend test": Would you enjoy explaining this out loud to someone who didn't ask?
"Scroll test": Is it so clear, punchy, and relevant you'd share it in a WhatsApp group?
"So What?": Ensure at least one practical or perspective-changing takeaway
"""

# ============================================================================
# HELPER FUNCTION FOR CONTENT GENERATION
# ============================================================================

def generate_content_prompt(
    topic: str,
    concept: str,
    concept_description: str,
    question_config: Optional[QuestionConfig] = None
) -> str:
    """
    Generate a formatted prompt for content creation with customizable question configuration.

    Args:
        topic: The topic name
        concept: The concept name
        concept_description: Description of the concept
        question_config: Optional QuestionConfig object. If None, uses default (2 MCQ, 2 T/F, 1 Fill-blank)

    Returns:
        Formatted prompt string ready to use with LLM

    Examples:
        # Use default question configuration (2 MCQ, 2 True/False, 1 Fill-blank)
        prompt = generate_content_prompt("Psychology", "Growth Mindset", "Why believing you can improve makes you better")

        # Custom configuration with 3 MCQs and 2 True/False
        config = QuestionConfig(mcq=3, true_false=2, fill_blank=0)
        prompt = generate_content_prompt("Psychology", "Growth Mindset", "...", question_config=config)

        # Include matching and ordering questions
        config = QuestionConfig(mcq=2, true_false=1, matching=1, ordering=1)
        prompt = generate_content_prompt("Psychology", "Growth Mindset", "...", question_config=config)

        # All question types
        config = QuestionConfig(mcq=2, true_false=1, fill_blank=1, matching=1, ordering=1)
        prompt = generate_content_prompt("Psychology", "Growth Mindset", "...", question_config=config)
    """
    if question_config is None:
        question_config = QuestionConfig()  # Use defaults: 2 MCQ, 2 T/F, 1 Fill-blank

    if question_config.total_questions == 0:
        raise ValueError("Question configuration must have at least one question. All question counts are 0.")

    prompt = DYNAMIC_PROMPT_TEMPLATE.format(
        topic=topic,
        concept=concept,
        concept_description=concept_description,
        total_questions=question_config.total_questions,
        question_distribution=question_config.to_prompt_string()
    )

    return prompt



def get_api_key():
    """Get API key from either Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY", "")
        cerebras_key = st.secrets.get("CEREBRAS_API_KEY", "")
        return openrouter_key, cerebras_key
    except:
        # Fallback to environment variables
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        cerebras_key = os.getenv("CEREBRAS_API_KEY", "")
        return openrouter_key, cerebras_key

def generate_learning_content(
    topic: str,
    concept: str,
    concept_description: str,
    question_config: Optional[QuestionConfig] = None
):
    """
    Generate bite-sized learning content using Educhain with flexible question configuration.

    Args:
        topic: The main topic (e.g., "Psychology")
        concept: The specific concept (e.g., "The Zeigarnik Effect")
        concept_description: Brief description of the concept
        question_config: Optional QuestionConfig object. If None, uses default (2 MCQ, 2 T/F, 1 Fill-blank)

    Returns:
        BiteSizedContent: Generated learning content

    Examples:
        # Use default configuration
        result = generate_learning_content(
            topic="Psychology",
            concept="Growth Mindset",
            concept_description="Why believing you can improve makes you better"
        )

        # Custom question configuration
        config = QuestionConfig(mcq=3, true_false=2)
        result = generate_learning_content(
            topic="Psychology",
            concept="Growth Mindset",
            concept_description="Why believing you can improve makes you better",
            question_config=config
        )
    """
    # Get API keys
    openrouter_key, cerebras_key = get_api_key()
    
    # Setup LLM
    if openrouter_key:
        deepseek_terminus = ChatOpenAI(
            model="anthropic/claude-sonnet-4.5",
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
    elif cerebras_key:
        deepseek_terminus = ChatOpenAI(
            model="qwen-3-235b-a22b-thinking-2507",
            openai_api_key=cerebras_key,
            openai_api_base="https://api.cerebras.ai/v1"
        )
    else:
        raise ValueError("No API key found. Please configure OPENROUTER_API_KEY or CEREBRAS_API_KEY in secrets.toml or environment variables.")

    deepseek_config = LLMConfig(custom_model=deepseek_terminus)
    client = Educhain(deepseek_config)

    # Set default question config if not provided
    if question_config is None:
        question_config = QuestionConfig()

    # Generate the prompt with question configuration
    prompt = generate_content_prompt(topic, concept, concept_description, question_config)

    try:
        # Generate content
        result = client.qna_engine.generate_questions(
            topic=topic,
            concept=concept,
            num=question_config.total_questions,
            prompt_template=prompt,
            response_model=BiteSizedContent
        )
        
        # Validate result
        if not result or not hasattr(result, 'pre_read'):
            raise ValueError("LLM returned empty or invalid response")
            
        return result
        
    except Exception as e:
        # Enhanced error reporting
        error_msg = f"Error in content generation: {str(e)}"
        if "validation error" in str(e).lower():
            error_msg += "\n\nThis usually means the LLM didn't return properly formatted content. "
            error_msg += "Please check your API key and try again."
        elif "api" in str(e).lower():
            error_msg += "\n\nThis appears to be an API-related error. "
            error_msg += "Please check your API key and internet connection."
        
        raise Exception(error_msg)




# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    topic = "Psychology"
    concept = "The Zeigarnik Effect"
    concept_description = "Why unfinished tasks bug your brain until you finally check them off"

    print("=" * 80)
    print("EXAMPLE 1: Default Question Configuration")
    print("=" * 80)
    # Default: 2 MCQ, 2 True/False, 1 Fill-blank (5 total)
    prompt = generate_content_prompt(topic, concept, concept_description)
    print(f"\nTotal Questions: 5 (2 MCQ, 2 True/False, 1 Fill-blank)")
    print(f"\nPrompt preview (first 300 chars):\n{prompt[:300]}...\n")

    print("\n" + "=" * 80)
    print("EXAMPLE 2: Custom - More MCQs")
    print("=" * 80)
    # Custom: 4 MCQ, 1 True/False (5 total)
    config = QuestionConfig(mcq=4, true_false=1, fill_blank=0)
    prompt = generate_content_prompt(topic, concept, concept_description, question_config=config)
    print(f"\nTotal Questions: {config.total_questions} ({config.to_prompt_string()})")

    print("\n" + "=" * 80)
    print("EXAMPLE 3: Include All Question Types")
    print("=" * 80)
    # All types: 2 MCQ, 1 T/F, 1 Fill-blank, 1 Matching, 1 Ordering (6 total)
    config = QuestionConfig(mcq=2, true_false=1, fill_blank=1, matching=1, ordering=1)
    prompt = generate_content_prompt(topic, concept, concept_description, question_config=config)
    print(f"\nTotal Questions: {config.total_questions} ({config.to_prompt_string()})")

    print("\n" + "=" * 80)
    print("EXAMPLE 4: Just True/False Questions")
    print("=" * 80)
    # Only True/False: 5 True/False (5 total)
    config = QuestionConfig(mcq=0, true_false=5, fill_blank=0)
    prompt = generate_content_prompt(topic, concept, concept_description, question_config=config)
    print(f"\nTotal Questions: {config.total_questions} ({config.to_prompt_string()})")

    print("\n" + "=" * 80)
    print("EXAMPLE 5: Dictionary-style Input")
    print("=" * 80)
    # You can also pass as dictionary
    config_dict = {"mcq": 3, "true_false": 1, "matching": 1}
    config = QuestionConfig(**config_dict)
    prompt = generate_content_prompt(topic, concept, concept_description, question_config=config)
    print(f"\nTotal Questions: {config.total_questions} ({config.to_prompt_string()})")

    print("\n" + "=" * 80)
    print("\nNow you can use these prompts with Educhain or any LLM!")
    print("The BiteSizedContent Pydantic model will validate the response structure.")
    print("=" * 80)
