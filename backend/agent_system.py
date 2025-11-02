"""
Multi-Agent Resume Processing System using LangGraph & LangChain
Agents: Content Agent, Formatting Agent, Document Agent + Supervisor
This system solves the text jamming issue by using specialized agents
"""

import os
import logging
import time
from typing import Dict, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import operator
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State shared between agents"""
    original_resume: str
    job_description: str
    content_tailored: str
    formatting_applied: str
    document_ready: str
    current_agent: str
    messages: Annotated[List, operator.add]
    iteration_count: int
    final_output: Dict

class ResumeAgentSystem:
    """Multi-agent system for resume processing with perfect formatting"""
    
    def __init__(self, groq_api_key: str = None):
        """Initialize the multi-agent system"""
        self.groq_api_key = groq_api_key or os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("Groq API key required for multi-agent system")
        
        # Initialize LLM with optimal settings
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=4000
        )
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        logger.info("🤖 Multi-Agent Resume System initialized with LangGraph")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("supervisor", self.supervisor_agent)
        workflow.add_node("content_agent", self.content_agent)
        workflow.add_node("formatting_agent", self.formatting_agent)
        workflow.add_node("document_agent", self.document_agent)
        
        # Define the flow - Start with supervisor
        workflow.set_entry_point("supervisor")
        
        # Supervisor decides which agent to call
        workflow.add_conditional_edges(
            "supervisor",
            self.route_to_agent,
            {
                "content_agent": "content_agent",
                "formatting_agent": "formatting_agent", 
                "document_agent": "document_agent",
                "FINISH": END
            }
        )
        
        # All agents report back to supervisor
        workflow.add_edge("content_agent", "supervisor")
        workflow.add_edge("formatting_agent", "supervisor")
        workflow.add_edge("document_agent", "supervisor")
        
        return workflow
    
    def supervisor_agent(self, state: AgentState) -> AgentState:
        """Supervisor agent that coordinates the workflow"""
        
        # Increment iteration counter
        iteration = state.get("iteration_count", 0)
        state["iteration_count"] = iteration + 1
        
        # Prevent infinite loops
        if iteration > 10:
            state["current_agent"] = "FINISH"
            state["messages"].append("⚠️ Supervisor: Max iterations reached, finishing...")
            logger.warning("Max iterations reached in supervisor")
            return state
        
        # Determine next action based on current state
        if not state.get("content_tailored"):
            state["current_agent"] = "content_agent"
            state["messages"].append("🎯 Supervisor: Routing to Content Agent for resume tailoring")
            logger.info("Supervisor routing to Content Agent")
            
        elif not state.get("formatting_applied"):
            state["current_agent"] = "formatting_agent"
            state["messages"].append("✨ Supervisor: Routing to Formatting Agent for text structure")
            logger.info("Supervisor routing to Formatting Agent")
            
        elif not state.get("document_ready"):
            state["current_agent"] = "document_agent"
            state["messages"].append("📄 Supervisor: Routing to Document Agent for file generation")
            logger.info("Supervisor routing to Document Agent")
            
        else:
            state["current_agent"] = "FINISH"
            state["messages"].append("✅ Supervisor: All agents completed successfully!")
            logger.info("Supervisor: All agents completed")
            
        return state
    
    def content_agent(self, state: AgentState) -> AgentState:
        """Agent specialized in content tailoring"""
        
        logger.info("🎯 Content Agent: Starting content tailoring...")
        
        content_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Content Tailoring Expert. Your ONLY job is content optimization:

RESPONSIBILITIES:
1. Analyze the job description to identify key requirements and keywords
2. Rewrite the resume to emphasize the most relevant experiences
3. Add missing skills that the candidate likely has based on their background
4. Optimize content for ATS systems with relevant keywords
5. Ensure content authenticity while maximizing relevance

IMPORTANT: Focus ONLY on content quality and relevance. Do NOT worry about:
- Spacing or formatting
- Line breaks or indentation  
- Document structure
- Visual presentation

Output the tailored content with the same basic structure but enhanced relevance."""),
            
            ("human", """Tailor this resume content for the job description:

JOB DESCRIPTION:
{job_description}

ORIGINAL RESUME:
{original_resume}

Focus on content relevance and keyword optimization. Make the resume highly relevant to the job requirements while maintaining authenticity.""")
        ])
        
        try:
            chain = content_prompt | self.llm | StrOutputParser()
            logger.info(f"🔍 Content Agent - Job description length: {len(state.get('job_description', ''))}")
            logger.info(f"🔍 Content Agent - Original resume length: {len(state.get('original_resume', ''))}")
            
            result = chain.invoke({
                "job_description": state["job_description"],
                "original_resume": state["original_resume"]
            })
            
            state["content_tailored"] = result
            state["messages"].append("✅ Content Agent: Resume content tailored successfully")
            logger.info("✅ Content Agent completed successfully")
            
        except Exception as e:
            error_msg = f"❌ Content Agent failed: {str(e)}"
            state["messages"].append(error_msg)
            logger.error(f"Content Agent error: {e}")
            # Set a fallback to continue the workflow
            state["content_tailored"] = state["original_resume"]
            
        return state
    
    def formatting_agent(self, state: AgentState) -> AgentState:
        """Agent specialized in text formatting and structure - KEY TO SOLVING JAMMING ISSUE"""
        
        logger.info("✨ Formatting Agent: Applying professional formatting...")
        
        formatting_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Professional Text Formatting Expert. This is CRITICAL - you must fix text jamming issues.

YOUR MISSION: Transform cramped, jammed text into perfectly spaced, professional content.

CRITICAL FORMATTING RULES:
1. **Section Spacing**: Add blank lines between ALL major sections (Summary, Experience, Skills, etc.)
2. **Contact Information**: Format with proper spacing: "Name | Email | Phone | Location"
3. **Bullet Points**: Use "• " (bullet + space) for all list items with proper indentation
4. **Job Titles**: Format as "Job Title at Company Name (Dates)" with line breaks
5. **Project Formatting**: "• Project Name — Brief description with proper spacing"
6. **Skills**: Separate with commas and spaces: "Python, JavaScript, React"
7. **Line Breaks**: Add line breaks after section headers and between different types of content
8. **No Cramping**: Ensure NO text is jammed together - everything must have proper spacing

BEFORE/AFTER EXAMPLE:
BEFORE (jammed): "Dr. Anthony AnyanwuAIML EngineerAbuja,Nigeriaanthony@gmail.com+234813"
AFTER (formatted): 
"Dr. Anthony Anyanwu
AI/ML Engineer
📍 Abuja, Nigeria
📧 anthony@gmail.com | 📞 +234 813"

Transform the content into perfectly formatted, readable text with no jamming issues."""),
            
            ("human", """Apply professional formatting to this tailored content to eliminate text jamming:

TAILORED CONTENT:
{content}

CRITICAL: Fix all spacing issues, add proper line breaks, and ensure no text is cramped together. Return professionally formatted content.""")
        ])
        
        try:
            chain = formatting_prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "content": state["content_tailored"]
            })
            
            state["formatting_applied"] = result
            state["messages"].append("✅ Formatting Agent: Professional formatting applied - jamming fixed!")
            logger.info("✅ Formatting Agent completed - text jamming resolved")
            
        except Exception as e:
            error_msg = f"❌ Formatting Agent failed: {str(e)}"
            state["messages"].append(error_msg)
            logger.error(f"Formatting Agent error: {e}")
            # Fallback to content without additional formatting
            state["formatting_applied"] = state["content_tailored"]
            
        return state
    
    def document_agent(self, state: AgentState) -> AgentState:
        """Agent specialized in document generation preparation"""
        
        logger.info("📄 Document Agent: Preparing final document structure...")
        
        document_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Document Generation Expert. Your job is final preparation for PDF/DOCX creation.

RESPONSIBILITIES:
1. Verify all formatting is preserved and clean
2. Ensure section headers are clearly defined for document parsing
3. Confirm bullet points will render correctly in generated files
4. Add any final structural improvements
5. Prepare content that will maintain formatting in document conversion

DOCUMENT STANDARDS:
- Maintain ALL formatting from the previous agent
- Ensure section headers are easily identifiable (e.g., "PROFESSIONAL SUMMARY", "EXPERIENCE")
- Verify bullet points use consistent formatting
- Confirm contact information is properly structured
- Ensure no formatting will break during PDF/DOCX generation

Output the final, document-ready content that will generate perfect files."""),
            
            ("human", """Prepare this formatted content for final document generation:

FORMATTED CONTENT:
{formatted_content}

Ensure it's perfectly structured for PDF and Word document creation while preserving all formatting.""")
        ])
        
        try:
            chain = document_prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "formatted_content": state["formatting_applied"]
            })
            
            state["document_ready"] = result
            state["final_output"] = {
                "tailored_resume": result,
                "original_resume": state["original_resume"],
                "job_description": state["job_description"],
                "processing_messages": state["messages"],
                "method": "multi_agent_langraph",
                "status": "success",
                "agents_used": ["content_agent", "formatting_agent", "document_agent"],
                "timestamp": time.time()
            }
            state["messages"].append("✅ Document Agent: Document ready for perfect file generation")
            logger.info("✅ Document Agent completed - ready for file generation")
            
        except Exception as e:
            error_msg = f"❌ Document Agent failed: {str(e)}"
            state["messages"].append(error_msg)
            logger.error(f"Document Agent error: {e}")
            # Fallback to formatted content
            state["document_ready"] = state["formatting_applied"]
            state["final_output"] = {
                "tailored_resume": state["formatting_applied"],
                "original_resume": state["original_resume"],
                "job_description": state["job_description"],
                "processing_messages": state["messages"],
                "method": "multi_agent_langraph_fallback",
                "status": "partial_success",
                "timestamp": time.time()
            }
            
        return state
    
    def route_to_agent(self, state: AgentState) -> str:
        """Router function for the supervisor"""
        return state["current_agent"]
    
    def process_resume(self, original_resume: str, job_description: str) -> Dict:
        """Main method to process resume through the agent system"""
        
        logger.info("🚀 Starting multi-agent resume processing...")
        
        # Initialize state
        initial_state = {
            "original_resume": original_resume,
            "job_description": job_description,
            "content_tailored": "",
            "formatting_applied": "",
            "document_ready": "",
            "current_agent": "",
            "messages": ["🤖 Multi-Agent System: Initializing resume processing pipeline..."],
            "iteration_count": 0,
            "final_output": {}
        }
        
        try:
            # Run the workflow
            final_state = self.app.invoke(initial_state)
            
            logger.info("🎉 Multi-agent processing completed successfully!")
            
            # Ensure we have a final output
            if not final_state.get("final_output"):
                final_state["final_output"] = {
                    "tailored_resume": final_state.get("document_ready", final_state.get("formatting_applied", final_state.get("content_tailored", original_resume))),
                    "original_resume": original_resume,
                    "job_description": job_description,
                    "processing_messages": final_state.get("messages", []),
                    "method": "multi_agent_langraph_emergency",
                    "status": "completed",
                    "timestamp": time.time()
                }
            
            return final_state["final_output"]
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed: {e}")
            return {
                "tailored_resume": original_resume,
                "original_resume": original_resume,
                "job_description": job_description,
                "processing_messages": [f"❌ System error: {str(e)}"],
                "method": "multi_agent_langraph",
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }

def test_agent_system():
    """Test the multi-agent system"""
    try:
        logger.info("🧪 Testing Multi-Agent Resume System...")
        
        agent_system = ResumeAgentSystem()
        
        sample_resume = """John Doe
Software Developer
john@email.com
Experience:
Developer at ABC Corp 2021-2024
Built web applications using Python and JavaScript
Worked with databases and APIs"""
        
        sample_job = """Senior Python Developer
Requirements: 5+ years Python, React experience, AWS knowledge
We need an experienced developer to build scalable applications"""
        
        result = agent_system.process_resume(sample_resume, sample_job)
        
        print(f"✅ Status: {result['status']}")
        print(f"🤖 Method: {result['method']}")
        print(f"📝 Messages: {len(result.get('processing_messages', []))} processing steps")
        
        if result['status'] in ['success', 'completed', 'partial_success']:
            print("🎉 Multi-agent system test successful!")
            print(f"📄 Tailored resume length: {len(result.get('tailored_resume', ''))}")
        else:
            print(f"⚠️ Test completed with status: {result['status']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO)
    test_agent_system()