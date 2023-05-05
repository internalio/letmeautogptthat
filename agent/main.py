import sys
import os
import faiss
from langchain.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
from langchain.tools.file_management.write import WriteFileTool
from langchain.tools.file_management.read import ReadFileTool
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from src.agent import LimitAutoGPT, MaxStepsReachedException
from supabase import create_client, Client

from src.tools.write import WriteTool
from datetime import datetime
from src.thought_observer.supabase import SupabaseThoughtObserver


def create_agent(extra_tools) -> LimitAutoGPT:
    search = DuckDuckGoSearchRun()
    tools = [
        Tool(
            name="search",
            func=search.run,
            description="useful for when you need to answer questions about current events. You should ask targeted questions",
        ),
        WriteFileTool(root_dir="./workarea"),
        ReadFileTool(root_dir="./workarea"),
    ]

    tools.extend(extra_tools)

    # Define your embedding model
    embeddings_model = OpenAIEmbeddings()
    # Initialize the vectorstore as empty

    embedding_size = 1536
    index = faiss.IndexFlatL2(embedding_size)
    vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

    agent = LimitAutoGPT.from_llm_and_tools(
        ai_name="Tom",
        ai_role="Assistant",
        tools=tools,
        llm=ChatOpenAI(temperature=0.3),
        memory=vectorstore.as_retriever(),
    )
    # Set verbose to be true
    # agent.chain.verbose = True

    return agent


def main(job_id: str):
    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_KEY")

    supabase: Client = create_client(supabase_url, supabase_key)

    write_tool = WriteTool()
    agent = create_agent([write_tool])

    response = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if len(response.data) != 1:
        print(f"No job found for id '{job_id}'")
        return

    job = response.data[0]
    job_id = job["id"]

    task = job["task"] + ". Use the write_text tool to output the final result."

    recorder = SupabaseThoughtObserver(supabase, job_id, write_every=1)

    try:
        supabase.table("jobs").update(
            {"status": "started", "started_at": datetime.now().isoformat()}
        ).eq("id", job_id).execute()

        agent.run([task], thought_handler=recorder, max_steps=15)

        recorder.flush()

        supabase.table("jobs").update(
            {"output": write_tool.buffer, "status": "completed"}
        ).eq("id", job_id).execute()
    except MaxStepsReachedException:
        supabase.table("jobs").update(
            {"status": "failed", "status_message": "Taking too many steps"}
        ).eq("id", job_id).execute()
    except:
        supabase.table("jobs").update(
            {"status": "failed", "status_message": "Unknown error"}
        ).eq("id", job_id).execute()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("job id argument expected")
        sys.exit(1)

    local_env_file = "./.env.local"
    if os.path.exists(local_env_file):
        import dotenv

        dotenv.load_dotenv(local_env_file)

    job_id = sys.argv[1]

    main(job_id)
