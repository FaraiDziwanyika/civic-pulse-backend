import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

app = FastAPI()

# Allow your Blogger site to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your blogger URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo purposes to track tasks
tasks_db = {}

class TopicRequest(BaseModel):
    topic: str

def run_ai_crew(task_id: str, topic: str):
    # Initialize tools and agents
    search_tool = SerperDevTool()
    
    scraper = Agent(
        role="Civic Data Scraper",
        goal=f"Extract raw news and official data about {topic}",
        backstory="Expert at parsing public records and media reports.",
        tools=[search_tool],
        verbose=True
    )
    
    analyst = Agent(
        role="Investigative Analyst",
        goal="Isolate core statistics, discrepancies, and key summaries",
        backstory="A data journalist focused on clarity and hard facts.",
        verbose=True
    )
    
    task1 = Task(description=f"Scrape latest data on {topic}", agent=scraper)
    task2 = Task(description="Compile a markdown report summarizing the findings", agent=analyst)
    
    crew = Crew(agents=[scraper, analyst], tasks=[task1, task2])
    
    # Execute the crew
    result = crew.kickoff()
    
    # Save the output
    tasks_db[task_id] = {"status": "completed", "result": str(result)}

@app.post("/start-task/{task_id}")
def start_task(task_id: str, request: TopicRequest, background_tasks: BackgroundTasks):
    tasks_db[task_id] = {"status": "processing", "result": "Agents are working..."}
    background_tasks.add_task(run_ai_crew, task_id, request.topic)
    return {"status": "queued"}

@app.get("/get-task/{task_id}")
def get_task(task_id: str):
    return tasks_db.get(task_id, {"status": "not_found"})