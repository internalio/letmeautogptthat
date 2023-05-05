# Task Runner

A python script that polls Supabase for jobs and launches docker images.

The script takes in environment variables from a `.env` file and passes them along to the
docker containers it creates. This way, the containers don't have to have config values in them.

## Setup

1. Create a `.env` file and populate it with the values from `.env.template`
2. Run the `main.py` file
