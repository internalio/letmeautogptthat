import logging
from pathlib import Path
import sys
import os
from colorama import Fore, Style

from autogpt.agent.agent import Agent
from autogpt.commands.command import CommandRegistry
from autogpt.config import Config, check_openai_api_key
from autogpt.configurator import create_config
from autogpt.logs import logger
from autogpt.memory import get_memory
from autogpt.plugins import scan_plugins
from autogpt.prompts.prompt import DEFAULT_TRIGGERING_PROMPT, construct_main_ai_config
from autogpt.workspace.workspace import Workspace
from autogpt.json_utils.json_fix_llm import fix_json_using_multiple_techniques

from autogpt.config.ai_config import AIConfig
from supabase import create_client, Client
from datetime import datetime

from scripts.install_plugin_deps import install_plugin_dependencies
from autogpt.log_cycle.log_cycle import (
    FULL_MESSAGE_HISTORY_FILE_NAME,
    NEXT_ACTION_FILE_NAME,
    LogCycleHandler,
)
from autogpt.llm import chat_with_ai, create_chat_completion, create_chat_message
from autogpt.app import execute_command, get_command
from autogpt.config import Config
from autogpt.json_utils.json_fix_llm import fix_json_using_multiple_techniques
from autogpt.json_utils.utilities import LLM_DEFAULT_RESPONSE_FORMAT, validate_json
from autogpt.llm import chat_with_ai, create_chat_completion, create_chat_message
from autogpt.llm.token_counter import count_string_tokens
from autogpt.log_cycle.log_cycle import (
    FULL_MESSAGE_HISTORY_FILE_NAME,
    NEXT_ACTION_FILE_NAME,
    LogCycleHandler,
)
from autogpt.logs import logger, print_assistant_thoughts
from autogpt.speech import say_text
from autogpt.spinner import Spinner
from autogpt.utils import clean_input
from autogpt.workspace import Workspace

CFG = Config()


class SupabaseThoughtObserver:
    def __init__(self, client, job_id: str, write_every: int = 3):
        self.job_id = job_id
        self.thoughts = []
        self.raw_data = []
        self.total_thoughts = 0
        self.client = client
        self.write_every = write_every

    def _write(self):
        self.client.table("jobs").update(
            {
                "messages": self.thoughts,
                "log": self.raw_data,
            }
        ).eq("id", self.job_id).execute()

    def __call__(self, thought: str, raw_data: str):
        self.thoughts.append(thought)
        self.raw_data.append(raw_data)
        self.total_thoughts += 1

        # Record on first thought for faster results
        # then record every write_every
        if self.total_thoughts == 1 or (self.total_thoughts % self.write_every == 0):
            self._write()

    def flush(self):
        """Write out any remaining thoughts to Supabase"""
        self._write()


class MaxStepsException(Exception):
    pass


class CustomAgent(Agent):
    def run(self, thought_recorder):
        # Interaction Loop
        cfg = Config()
        self.cycle_count = 0
        command_name = None
        arguments = None
        user_input = ""

        while True:
            # Discontinue if continuous limit is reached
            self.cycle_count += 1
            self.log_cycle_handler.log_count_within_cycle = 0
            self.log_cycle_handler.log_cycle(
                self.config.ai_name,
                self.created_at,
                self.cycle_count,
                self.full_message_history,
                FULL_MESSAGE_HISTORY_FILE_NAME,
            )
            if (
                cfg.continuous_mode
                and cfg.continuous_limit > 0
                and self.cycle_count > cfg.continuous_limit
            ):
                logger.typewriter_log(
                    "Continuous Limit Reached: ", Fore.YELLOW, f"{cfg.continuous_limit}"
                )
                raise MaxStepsException()

            # Send message to AI, get response
            assistant_reply = chat_with_ai(
                self,
                self.system_prompt,
                self.triggering_prompt,
                self.full_message_history,
                self.memory,
                cfg.fast_token_limit,
            )  # TODO: This hardcodes the model to use GPT3.5. Make this an argument

            assistant_reply_json = fix_json_using_multiple_techniques(assistant_reply)
            for plugin in cfg.plugins:
                if not plugin.can_handle_post_planning():
                    continue
                assistant_reply_json = plugin.post_planning(assistant_reply_json)

            # Print Assistant thoughts
            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, LLM_DEFAULT_RESPONSE_FORMAT)
                # Get command name and arguments
                try:
                    thought_text = assistant_reply_json.get("thoughts", {}).get("text")

                    thought_recorder(thought_text, assistant_reply_json)

                    print_assistant_thoughts(
                        self.ai_name, assistant_reply_json, cfg.speak_mode
                    )
                    command_name, arguments = get_command(assistant_reply_json)

                    arguments = self._resolve_pathlike_command_args(arguments)

                except Exception as e:
                    logger.error("Error: \n", str(e))

            self.log_cycle_handler.log_cycle(
                self.config.ai_name,
                self.created_at,
                self.cycle_count,
                assistant_reply_json,
                NEXT_ACTION_FILE_NAME,
            )

            # Print command
            logger.typewriter_log(
                "NEXT ACTION: ",
                Fore.CYAN,
                f"COMMAND = {Fore.CYAN}{command_name}{Style.RESET_ALL}"
                f"  ARGUMENTS = {Fore.CYAN}{arguments}{Style.RESET_ALL}",
            )

            # Execute command
            if command_name is not None and command_name.lower().startswith("error"):
                result = (
                    f"Command {command_name} threw the following error: {arguments}"
                )
            elif command_name == "human_feedback":
                result = f"Human feedback: {user_input}"
            elif command_name == "write_output":
                return execute_command(
                    self.command_registry,
                    command_name,
                    arguments,
                    self.config.prompt_generator,
                )
            else:
                for plugin in cfg.plugins:
                    if not plugin.can_handle_pre_command():
                        continue
                    command_name, arguments = plugin.pre_command(
                        command_name, arguments
                    )
                command_result = execute_command(
                    self.command_registry,
                    command_name,
                    arguments,
                    self.config.prompt_generator,
                )
                result = f"Command {command_name} returned: " f"{command_result}"

                result_tlength = count_string_tokens(
                    str(command_result), cfg.fast_llm_model
                )
                memory_tlength = count_string_tokens(
                    str(self.summary_memory), cfg.fast_llm_model
                )
                if result_tlength + memory_tlength + 600 > cfg.fast_token_limit:
                    result = f"Failure: command {command_name} returned too much output. \
                        Do not execute this command again with the same arguments."

                for plugin in cfg.plugins:
                    if not plugin.can_handle_post_command():
                        continue
                    result = plugin.post_command(command_name, result)
                if self.next_action_count > 0:
                    self.next_action_count -= 1

            # Check if there's a result from the command append it to the message
            # history
            if result is not None:
                self.full_message_history.append(create_chat_message("system", result))
                logger.typewriter_log("SYSTEM: ", Fore.YELLOW, result)
            else:
                self.full_message_history.append(
                    create_chat_message("system", "Unable to execute command")
                )
                logger.typewriter_log(
                    "SYSTEM: ", Fore.YELLOW, "Unable to execute command"
                )


def main(job_id: str, debug: bool, gpt3only: bool, gpt4only: bool):
    speak = False
    # Configure logging before we do anything else.
    logger.set_level(logging.DEBUG if debug else logging.INFO)
    logger.speak_mode = speak

    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_KEY")

    supabase: Client = create_client(supabase_url, supabase_key)

    response = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if len(response.data) != 1:
        print(f"No job found for id '{job_id}'")
        return

    job = response.data[0]
    job_id = job["id"]

    task = job["task"]

    recorder = SupabaseThoughtObserver(supabase, job_id, write_every=1)

    cfg = Config()
    # TODO: fill in llm values here
    check_openai_api_key()
    create_config(
        ai_settings_file=None,
        continuous=True,
        continuous_limit=15,
        skip_reprompt=True,
        speak=False,
        debug=debug,
        gpt3only=True,
        gpt4only=False,
        memory_type="local",
        browser_name="chrome",
        allow_downloads=True,
        skip_news=True,
    )

    install_plugin_dependencies()

    workspace_directory = Path(__file__).parent / "scratchpad"
    # TODO: pass in the ai_settings file and the env file and have them cloned into
    #   the workspace directory so we can bind them to the agent.
    workspace_directory = Workspace.make_workspace(workspace_directory)
    cfg.workspace_path = str(workspace_directory)

    # HACK: doing this here to collect some globals that depend on the workspace.
    file_logger_path = workspace_directory / "file_logger.txt"
    if not file_logger_path.exists():
        with file_logger_path.open(mode="w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    cfg.file_logger_path = str(file_logger_path)

    cfg.set_plugins(scan_plugins(cfg, cfg.debug_mode))
    # Create a CommandRegistry instance and scan default folder
    command_registry = CommandRegistry()

    cfg.disabled_command_categories = [
        "autogpt.commands.analyze_code",
        "autogpt.commands.audio_text",
        "autogpt.commands.execute_code",
        "autogpt.commands.git_operations",
        "autogpt.commands.image_gen",
        "autogpt.commands.improve_code",
        "autogpt.commands.twitter",
        "autogpt.commands.write_tests",
        "autogpt.commands.task_statuses",
        "autogpt.app",
    ]

    command_categories = [
        "autogpt.commands.analyze_code",
        "autogpt.commands.audio_text",
        "autogpt.commands.execute_code",
        "autogpt.commands.file_operations",
        "autogpt.commands.git_operations",
        "autogpt.commands.google_search",
        "autogpt.commands.image_gen",
        "autogpt.commands.improve_code",
        "autogpt.commands.twitter",
        "autogpt.commands.web_selenium",
        "autogpt.commands.write_tests",
        "autogpt.app",
        "autogpt.commands.task_statuses",
        "autogpt.commands.write_output",
    ]
    logger.debug(
        f"The following command categories are disabled: {cfg.disabled_command_categories}"
    )
    command_categories = [
        x for x in command_categories if x not in cfg.disabled_command_categories
    ]

    logger.debug(f"The following command categories are enabled: {command_categories}")

    for command_category in command_categories:
        command_registry.import_commands(command_category)

    ai_name = ""
    ai_config = construct_main_ai_config()

    ai_config.ai_goals = [task]
    ai_config.command_registry = command_registry
    # print(prompt)
    # Initialize variables
    full_message_history = []
    next_action_count = 0

    # add chat plugins capable of report to logger
    if cfg.chat_messages_enabled:
        for plugin in cfg.plugins:
            if hasattr(plugin, "can_handle_report") and plugin.can_handle_report():
                logger.info(f"Loaded plugin into logger: {plugin.__class__.__name__}")
                logger.chat_plugins.append(plugin)

    # Initialize memory and make sure it is empty.
    # this is particularly important for indexing and referencing pinecone memory
    memory = get_memory(cfg, init=True)
    logger.typewriter_log(
        "Using memory of type:", Fore.GREEN, f"{memory.__class__.__name__}"
    )
    logger.typewriter_log("Using Browser:", Fore.GREEN, cfg.selenium_web_browser)
    system_prompt = (
        ai_config.construct_full_prompt()
        + 'If you have completed all your tasks, make sure to use the "task_complete" command.'
    )
    if cfg.debug_mode:
        logger.typewriter_log("Prompt:", Fore.GREEN, system_prompt)

    agent = CustomAgent(
        ai_name=ai_name,
        memory=memory,
        full_message_history=full_message_history,
        next_action_count=next_action_count,
        command_registry=command_registry,
        config=ai_config,
        system_prompt=system_prompt,
        triggering_prompt=DEFAULT_TRIGGERING_PROMPT,
        workspace_directory=workspace_directory,
    )

    try:
        supabase.table("jobs").update(
            {"status": "started", "started_at": datetime.now().isoformat()}
        ).eq("id", job_id).execute()

        result = agent.run(thought_recorder=recorder)

        recorder.flush()

        supabase.table("jobs").update({"output": result, "status": "completed"}).eq(
            "id", job_id
        ).execute()
    except MaxStepsException:
        supabase.table("jobs").update(
            {"status": "failed", "status_message": "Taking too many steps"}
        ).eq("id", job_id).execute()
        return


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("job id argument expected")
        sys.exit(1)

    local_env_file = "./.env"
    if os.path.exists(local_env_file):
        import dotenv

        dotenv.load_dotenv(local_env_file)

    main(job_id=sys.argv[1], debug=False, gpt3only=True, gpt4only=False)
