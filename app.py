import streamlit as st
from microlesson import (
    generate_learning_content, 
    QuestionConfig, 
    BiteSizedContent
)

def init_session_state():
    """Initialize session state variables"""
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = None
    if 'api_configured' not in st.session_state:
        st.session_state.api_configured = False

def check_api_configuration():
    """Check if API keys are configured"""
    try:
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY", "")
        cerebras_key = st.secrets.get("CEREBRAS_API_KEY", "")
        
        if openrouter_key or cerebras_key:
            st.session_state.api_configured = True
            return True
        return False
    except FileNotFoundError:
        return False

def display_api_setup():
    """Display API setup instructions"""
    st.error("🔑 API Configuration Required")
    st.markdown("""
    To use this app, you need to set up an API key in Streamlit secrets:
    
    **Step 1:** Create a `.streamlit` folder in your project directory
    ```bash
    mkdir .streamlit
    ```
    
    **Step 2:** Create a `secrets.toml` file in the `.streamlit` folder
    ```bash
    touch .streamlit/secrets.toml
    ```
    
    **Step 3:** Add one of these API keys to `.streamlit/secrets.toml`:
    
    **Option 1: OpenRouter API**
    ```toml
    OPENROUTER_API_KEY = "your_openrouter_key_here"
    ```
    
    **Option 2: Cerebras API**
    ```toml
    CEREBRAS_API_KEY = "your_cerebras_key_here"
    ```
    
    After creating the secrets file, restart this Streamlit app.
    
    **Note:** Make sure to add `.streamlit/secrets.toml` to your `.gitignore` file to keep your API keys secure!
    """)

def create_sidebar():
    """Create sidebar with input controls"""
    st.sidebar.title("🎯 MicroLesson Configuration")
    
    # Topic and Concept inputs
    st.sidebar.markdown("### 📚 Content Details")
    topic = st.sidebar.text_input(
        "Topic",
        value="Psychology",
        help="The main subject area (e.g., Psychology, Technology, Science)"
    )
    
    concept = st.sidebar.text_input(
        "Concept",
        value="The Zeigarnik Effect",
        help="The specific concept to learn about"
    )
    
    concept_description = st.sidebar.text_area(
        "Concept Description",
        value="Why unfinished tasks bug your brain until you finally check them off",
        help="A brief description or teaser about the concept",
        height=100
    )
    
    st.sidebar.markdown("### 🎲 Question Configuration")
    
    # Question type controls
    mcq_count = st.sidebar.number_input(
        "Multiple Choice Questions",
        min_value=0,
        max_value=10,
        value=2,
        help="Number of MCQ questions to generate"
    )
    
    true_false_count = st.sidebar.number_input(
        "True/False Questions",
        min_value=0,
        max_value=10,
        value=2,
        help="Number of True/False questions to generate"
    )
    
    fill_blank_count = st.sidebar.number_input(
        "Fill in the Blank Questions",
        min_value=0,
        max_value=10,
        value=1,
        help="Number of Fill in the Blank questions to generate"
    )
    
    matching_count = st.sidebar.number_input(
        "Matching Questions",
        min_value=0,
        max_value=5,
        value=0,
        help="Number of Matching questions to generate"
    )
    
    ordering_count = st.sidebar.number_input(
        "Ordering Questions",
        min_value=0,
        max_value=5,
        value=0,
        help="Number of Ordering questions to generate"
    )
    
    # Create question configuration
    question_config = QuestionConfig(
        mcq=mcq_count,
        true_false=true_false_count,
        fill_blank=fill_blank_count,
        matching=matching_count,
        ordering=ordering_count
    )
    
    # Display total questions
    total_questions = question_config.total_questions
    if total_questions == 0:
        st.sidebar.error("⚠️ Please select at least one question type!")
        return None, None, None, None
    
    st.sidebar.success(f"✅ Total Questions: {total_questions}")
    st.sidebar.markdown(f"**Distribution:** {question_config.to_prompt_string()}")
    
    return topic, concept, concept_description, question_config

def display_pre_read(content: BiteSizedContent):
    """Display the pre-read section"""
    st.markdown("## 🔍 Pre-Read")
    st.markdown(f"**⏱️ Estimated Time:** {content.estimated_time} minutes | **📊 Level:** {content.difficulty_level.title()}")
    st.markdown("---")
    st.markdown(content.pre_read)

def display_questions(content: BiteSizedContent):
    """Display all questions with proper formatting"""
    st.markdown("## 🎯 Interactive Questions")
    st.markdown("---")
    
    for i, question in enumerate(content.questions, 1):
        st.markdown(f"### Question {i} - {question.question_type.replace('_', ' ').title()}")
        
        if question.question_type == "mcq":
            st.markdown(f"**Q:** {question.question_text}")
            
            # Display options
            for j, option in enumerate(question.options):
                icon = "✅" if option.correct else "❌"
                st.markdown(f"{chr(65+j)}. {option.text} {icon if option.correct else ''}")
            
            # Show correct answer
            correct_option = next((opt for opt in question.options if opt.correct), None)
            if correct_option:
                st.success(f"**Correct Answer:** {correct_option.text}")
        
        elif question.question_type == "fill_blank":
            st.markdown(f"**Q:** {question.question_text}")
            st.success(f"**Correct Answer:** {question.correct_answer}")
            st.info(f"**Distractors:** {', '.join(question.distractors)}")
        
        elif question.question_type == "true_false":
            st.markdown(f"**Statement:** {question.statement}")
            answer_text = "TRUE" if question.correct_answer else "FALSE"
            st.success(f"**Correct Answer:** {answer_text}")
        
        elif question.question_type == "matching":
            st.markdown(f"**Instruction:** {question.instruction}")
            st.markdown("**Correct Pairs:**")
            for pair in question.pairs:
                st.markdown(f"• {pair.left} ↔ {pair.right}")
        
        elif question.question_type == "ordering":
            st.markdown(f"**Q:** {question.question_text}")
            st.markdown("**Correct Order:**")
            for idx, item in enumerate(question.correct_order, 1):
                st.markdown(f"{idx}. {item}")
        
        # Display explanation
        with st.expander("💡 Explanation", expanded=False):
            st.markdown(question.explanation)
        
        st.markdown("---")

def display_summary(content: BiteSizedContent):
    """Display the summary section"""
    st.markdown("## ✨ Key Takeaways")
    st.markdown("---")
    
    for i, point in enumerate(content.summary, 1):
        st.markdown(f"**{i}.** {point}")

def display_tags(content: BiteSizedContent):
    """Display tags"""
    st.markdown("## 🏷️ Tags")
    
    # Create columns for tags
    cols = st.columns(len(content.tags))
    for i, tag in enumerate(content.tags):
        with cols[i % len(cols)]:
            st.markdown(f"`{tag}`")

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="MicroLesson Generator",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # App header
    st.title("📚 MicroLesson Generator")
    st.markdown("Create bite-sized learning content with interactive questions using AI")
    st.markdown("---")
    
    # Check API configuration
    if not check_api_configuration():
        display_api_setup()
        return
    
    # Create sidebar with inputs
    sidebar_result = create_sidebar()
    if sidebar_result[0] is None:  # Check if inputs are valid
        st.warning("⚠️ Please configure your question settings in the sidebar.")
        return
    
    topic, concept, concept_description, question_config = sidebar_result
    
    # Generate button
    if st.sidebar.button("🚀 Generate MicroLesson", type="primary", use_container_width=True):
        with st.spinner("🧠 Generating your personalized MicroLesson..."):
            try:
                # Generate content
                content = generate_learning_content(
                    topic=topic,
                    concept=concept,
                    concept_description=concept_description,
                    question_config=question_config
                )
                
                st.session_state.generated_content = content
                st.success("✅ MicroLesson generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating content: {str(e)}")
                
                # Show helpful suggestions based on error type
                if "validation error" in str(e).lower():
                    st.info("💡 **Tip**: This usually means the LLM response wasn't properly formatted. Try again in a moment.")
                elif "api" in str(e).lower() or "key" in str(e).lower():
                    st.info("💡 **Tip**: Check your API key configuration in `.streamlit/secrets.toml`")
                else:
                    st.info("💡 **Tip**: Check your internet connection and try again.")
                
                # Option to show full error details
                with st.expander("🔍 Show detailed error info"):
                    import traceback
                    st.code(traceback.format_exc())
                return
    
    # Display generated content
    if st.session_state.generated_content:
        content = st.session_state.generated_content
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display header info
            st.markdown(f"# {content.concept_name}")
            st.markdown(f"**Topic:** {content.topic}")
            
            # Display pre-read
            display_pre_read(content)
            
            # Display questions
            display_questions(content)
        
        with col2:
            # Sidebar content
            st.markdown("### 📊 Lesson Info")
            st.info(f"""
            **Concept:** {content.concept_name}
            
            **Topic:** {content.topic}
            
            **Time:** {content.estimated_time} minutes
            
            **Level:** {content.difficulty_level.title()}
            
            **Questions:** {len(content.questions)}
            """)
            
            # Display summary
            display_summary(content)
            
            # Display tags
            display_tags(content)
            
            # Download option
            if st.button("📥 Download as Text", use_container_width=True):
                # Create text version
                text_content = f"""
# {content.concept_name}
Topic: {content.topic}
Time: {content.estimated_time} minutes
Level: {content.difficulty_level}

## Pre-Read
{content.pre_read}

## Questions
"""
                for i, q in enumerate(content.questions, 1):
                    text_content += f"\n{i}. {q.question_text if hasattr(q, 'question_text') else q.statement}\n"
                    if hasattr(q, 'explanation'):
                        text_content += f"   Explanation: {q.explanation}\n"

                text_content += f"\n## Summary\n"
                for i, point in enumerate(content.summary, 1):
                    text_content += f"{i}. {point}\n"
                
                text_content += f"\n## Tags\n{', '.join(content.tags)}"
                
                st.download_button(
                    label="Download MicroLesson",
                    data=text_content,
                    file_name=f"{content.concept_name.replace(' ', '_')}_microlesson.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()
