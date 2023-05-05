from __future__ import annotations
import json

from typing import List

from pydantic import ValidationError

from langchain.experimental.autonomous_agents.autogpt.prompt_generator import (
    FINISH_NAME,
)
from langchain.schema import (
    AIMessage,
    Document,
    HumanMessage,
    SystemMessage,
)


from typing import List
from langchain.experimental import AutoGPT
from langchain.experimental.autonomous_agents.autogpt.output_parser import (
    preprocess_json_input,
)


class MaxStepsReachedException(Exception):
    pass


def parse_reply(text: str) -> dict:
    try:
        parsed = json.loads(text, strict=False)
    except json.JSONDecodeError:
        preprocessed_text = preprocess_json_input(text)
        parsed = json.loads(preprocessed_text, strict=False)

    return parsed


class LimitAutoGPT(AutoGPT):
    def run(
        self, goals: List[str], thought_handler=None, max_steps: int | None = None
    ) -> str:
        if thought_handler is None:
            thought_handler = print

        user_input = (
            "Determine which next command to use, "
            "and respond using the format specified above:"
        )
        # Interaction Loop
        loop_count = 0
        while True:
            if max_steps is not None and loop_count >= max_steps:
                raise MaxStepsReachedException()

            # Discontinue if continuous limit is reached
            loop_count += 1

            # Send message to AI, get response
            assistant_reply = self.chain.run(
                goals=goals,
                messages=self.full_message_history,
                memory=self.memory,
                user_input=user_input,
            )

            # Handle Assistant thoughts
            try:
                parsed_reply = parse_reply(assistant_reply)
                assistant_thought = parsed_reply["thoughts"]["text"]
                thought_handler(assistant_thought, assistant_reply)
            except:
                # Do nothing for now
                pass

            self.full_message_history.append(HumanMessage(content=user_input))
            self.full_message_history.append(AIMessage(content=assistant_reply))

            # Get command name and arguments
            action = self.output_parser.parse(assistant_reply)

            tools = {t.name: t for t in self.tools}
            if action.name == FINISH_NAME:
                return action.args["response"]
            if action.name in tools:
                tool = tools[action.name]
                try:
                    observation = tool.run(action.args)
                except ValidationError as e:
                    observation = f"Error in args: {str(e)}"
                result = f"Command {tool.name} returned: {observation}"
            elif action.name == "ERROR":
                result = f"Error: {action.args}. "
            else:
                result = (
                    f"Unknown command '{action.name}'. "
                    f"Please refer to the 'COMMANDS' list for available "
                    f"commands and only respond in the specified JSON format."
                )

            memory_to_add = (
                f"Assistant Reply: {assistant_reply} " f"\nResult: {result} "
            )
            if self.feedback_tool is not None:
                feedback = f"\n{self.feedback_tool.run('Input: ')}"
                if feedback in {"q", "stop"}:
                    print("EXITING")
                    return "EXITING"
                memory_to_add += feedback

            self.memory.add_documents([Document(page_content=memory_to_add)])
            self.full_message_history.append(SystemMessage(content=result))
