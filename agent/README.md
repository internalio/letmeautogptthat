# Agent

An Auto-GPT langchain chain that takes in a task from a database, attempts to process it, and output it.
The agent has a maximum number of steps it can take to cut down on OpenAI API usage.

# Build

### Docker

CD into this project's directory and run:

```bash
docker build -t autogpt-agent:0.0.1 .
```

## Run

### Docker

```bash
docker run -e SUPABASE_URL=<supabase_url> \
-e SUPABASE_KEY=<supabase_key> \
-e OPENAI_API_KEY=<openai_api_key> \
autogpt-agent:0.0.1 <job_id : in supabase>
```
