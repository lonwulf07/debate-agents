import os
import asyncio
import queue
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# CrewAI & Tools
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

# LangChain Cloud Providers
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Autonomous Web-Scraping Debate API")

# Allow all origins so Vercel can communicate with Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Cloud LLM (Groq is blazing fast and runs Llama 3.1 8B for free)
cloud_llm = ChatGroq(
    temperature=0.6,
    model="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

# 2. Cloud Embeddings (768 dimensions, perfectly matches your existing Pinecone Index)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

# 3. Vector Database Connection
vectorstore = PineconeVectorStore(
    index_name="debate-knowledge", 
    embedding=embeddings
)

@tool("Pinecone Database Search")
def search_knowledge(query: str) -> str:
    """Search the internal vector database for factual data."""
    docs = vectorstore.similarity_search(query, k=2)
    return "\n\n".join([doc.page_content for doc in docs]) if docs else "No relevant facts found."

# Initialize the web tools
scrape_tool = ScrapeWebsiteTool()
search_tool = SerperDevTool()

class DebateRequest(BaseModel):
    topic: str

@app.post("/debate")
async def run_debate(request: DebateRequest):
    message_queue = queue.Queue()

    # The Aggressive Garbage Collector Callback
    def make_callback(speaker_name):
        def callback(task_output):
            raw_text = task_output.raw
            
            # Extract only the text after the magic tag
            if "[FINAL_ANSWER]" in raw_text:
                clean_text = raw_text.split("[FINAL_ANSWER]")[-1]
            else:
                clean_text = raw_text
                
            # The expanded list of 8B model brain-leaks
            leakage_markers = [
                "The content of the pages",
                "Read Website Content",
                "Here is the tool call",
                "The actual complete content:",
                "Search results for",
                "```json",
                '{"name":',
                "Observation:",
                "Action:",
                "I will call the",
                "To provide an answer"
            ]
            
            # Snip the text the moment it hits a leakage marker
            for marker in leakage_markers:
                if marker in clean_text:
                    clean_text = clean_text.split(marker)[0] 

            message_queue.put({"speaker": speaker_name, "text": clean_text.strip()})
        return callback

    def generate_debate():
        # --- DEFINING THE STRICT AGENTS ---
        optimist = Agent(
            role='Principal Architect',
            goal='Argue strongly in favor of the technology by finding positive use-cases on the web.',
            backstory='You are an innovative technical leader. CRITICAL INSTRUCTIONS: NEVER narrate your actions. NEVER output JSON. NEVER copy-paste raw text or transcripts from websites. You must synthesize the research into your own words.',
            verbose=True,
            allow_delegation=False,
            llm=cloud_llm,
            tools=[search_knowledge, search_tool, scrape_tool],
            max_iter=3 
        )

        skeptic = Agent(
            role='Risk Director',
            goal='Ruthlessly critique the technology by finding failures, vulnerabilities, and complaints on the web.',
            backstory='You are a highly critical risk manager. CRITICAL INSTRUCTIONS: NEVER narrate your actions. NEVER output JSON. NEVER copy-paste raw text or transcripts from websites. You must synthesize the research into your own words.',
            verbose=True,
            allow_delegation=False,
            llm=cloud_llm,
            tools=[search_knowledge, search_tool, scrape_tool],
            max_iter=3
        )

        judge = Agent(
            role='Chief Technology Officer (CTO)',
            goal='Review the debate, verify the claims using the web, and make a final, objective executive decision.',
            backstory='You are the pragmatic CTO. CRITICAL INSTRUCTIONS: NEVER narrate your actions. NEVER output JSON. NEVER copy-paste raw text or transcripts from websites. You must synthesize the research into your own words.',
            verbose=True,
            allow_delegation=False,
            llm=cloud_llm,
            tools=[search_knowledge, search_tool, scrape_tool],
            max_iter=3
        )

        # --- DEFINING THE STRUCTURED TASKS ---
        opening_argument = Task(
            description=f'Use the search_tool to find information about: {request.topic}. Write an argument supporting it based on what you find.',
            expected_output='You MUST start your response with the exact string "[FINAL_ANSWER]" followed immediately by two paragraphs arguing in favor of the topic.',
            agent=optimist,
            callback=make_callback("Principal Architect (Optimist)")
        )

        rebuttal = Task(
            description=f'Review the previous argument. Use the search_tool to find flaws, risks, and limitations regarding: {request.topic}. Completely tear the previous argument apart.',
            expected_output='You MUST start your response with the exact string "[FINAL_ANSWER]" followed immediately by two paragraphs aggressively critiquing the argument.',
            agent=skeptic,
            callback=make_callback("Risk Director (Skeptic)")
        )

        verdict = Task(
            description='Review both the Optimist and Skeptic arguments. Write a final verdict deciding the path forward. Provide a pragmatic compromise or a definitive ruling.',
            expected_output='You MUST start your response with the exact string "[FINAL_ANSWER]" followed immediately by a final, two-paragraph executive verdict.',
            agent=judge,
            callback=make_callback("Chief Technology Officer (Judge)")
        )

        debate_crew = Crew(
            agents=[optimist, skeptic, judge],
            tasks=[opening_argument, rebuttal, verdict],
            process=Process.sequential
        )

        # Run the crew and drop the sentinel value when finished
        debate_crew.kickoff()
        message_queue.put(None) 

    # --- SERVER-SENT EVENTS (SSE) GENERATOR ---
    async def stream_response():
        loop = asyncio.get_event_loop()
        # Run CrewAI in a background thread so it doesn't block the FastAPI server
        loop.run_in_executor(None, generate_debate)
        
        while True:
            try:
                msg = message_queue.get_nowait()
                if msg is None:
                    break
                yield f"data: {json.dumps(msg)}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.5)

    return StreamingResponse(stream_response(), media_type="text/event-stream")