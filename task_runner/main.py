import os
import asyncio
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from supabase import create_client, Client
import dotenv

WAIT_SECONDS_WHEN_NO_JOB = 1.0
MAX_WORKERS = 4


def run_autogpt_instance(
    image_name: str,
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    job_id: str,
):
    subprocess.run(
        [
            "docker",
            "run",
            "-e",
            f"SUPABASE_URL={supabase_url}",
            "-e",
            f"SUPABASE_KEY={supabase_key}",
            "-e",
            f"OPENAI_API_KEY={openai_api_key}",
            image_name,
            job_id,
        ]
    )


async def main():
    print("Starting job runner")

    dotenv.load_dotenv("./.env")

    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_KEY")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY")
    image_name: str = os.environ.get("IMAGE_NAME")

    supabase: Client = create_client(supabase_url, supabase_key)
    func = supabase.functions()

    # For some reason python client used the wrong URL for functions
    # need to recheck this when newer version is released
    func.url = f"{supabase_url}/rest/v1/rpc/"

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    # Initialize to true, so we print "No jobs" if there are none at start
    got_job = True

    while True:
        job_data = await func.invoke(
            "select_job_for_update", invoke_options={"body": {}}
        )

        jobs = json.loads(job_data["data"])
        if not jobs:
            if got_job:
                print("No jobs, waiting.")

            got_job = False
            sleep(WAIT_SECONDS_WHEN_NO_JOB)
            continue

        got_job = True

        job = jobs[0]
        job_id = job["id"]

        print(f"Processing job {job_id}")

        executor.submit(
            run_autogpt_instance,
            image_name,
            supabase_url,
            supabase_key,
            openai_api_key,
            job_id,
        )


if __name__ == "__main__":
    asyncio.run(main())
