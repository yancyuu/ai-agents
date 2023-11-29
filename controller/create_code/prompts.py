import asyncio
import openai
import re
import time
from typing import List, Optional, Callable, Any
from common_sdk.logging.logger import logger
from common_sdk.system.sys_env import get_env
from openai_function_call import openai_function
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)


@openai_function
def file_paths(files_to_edit: List[str]) -> List[str]:
    """
    Construct a list of strings.
    """
    # print("filesToEdit", files_to_edit)
    return files_to_edit

class Prompts:

    SYSTEM_PROMPT = """
    You are a top tier AI developer who is trying to write a program that will generate code for the user based on their intent.
    Do not leave any todos, fully implement every feature requested.

    When writing code, add comments to explain what you intend to do and why it aligns with the program plan and specific instructions from the original prompt.
    """

    def __init__(self) -> None:
        if get_env("OPENAI_API_BASE"):
            openai.api_base = get_env("OPENAI_API_BASE")
        self.api_keys = get_env("OPENAI_API_KEY")
        self.model = get_env("OPENAI_MODEL", "gpt-3.5-turbo-0613")

    def specify_file_paths(self, prompt: str, plan: str):
        apikey_list = self.api_keys.split(",")   
        # 随机选择一个apikey
        openai.api_key = random.choice(apikey_list)
        completion = openai.ChatCompletion.create(
            model=self.model,
            temperature=0.7,
            functions=[file_paths.openai_schema],
            function_call={"name": "file_paths"},
            messages=[
                {
                    "role": "system",
                    "content": f"""{Prompts.SYSTEM_PROMPT}
        Given the prompt and the plan, return a list of strings corresponding to the new files that will be generated.
                    """,
                },
                {
                    "role": "user",
                    "content": f""" I want a: {prompt} """,
                },
                {
                    "role": "user",
                    "content": f""" The plan we have agreed on is: {plan} """,
                },
            ],
        )
        result = file_paths.from_response(completion)
        return result


    def plan(self, prompt: str, stream_handler: Optional[Callable[[bytes], None]] = None, extra_messages: List[Any] = []):
        apikey_list = self.api_keys.split(",")   
        # 随机选择一个apikey
        openai.api_key = random.choice(apikey_list)
        completion = openai.ChatCompletion.create(
            model=self.model,
            temperature=0.7,
            stream=True,
            messages=[
                {
                    "role": "system",
                    "content": f"""{Prompts.SYSTEM_PROMPT}

        In response to the user's prompt, write a plan using GitHub Markdown syntax. Begin with a YAML description of the new files that will be created.
    In this plan, please name and briefly describe the structure of code that will be generated, including, for each file we are generating, what variables they export, data schemas, id names of every DOM elements that javascript functions will use, message names, and function names.
                    Respond only with plans following the above schema.
                    """,
                },
                {
                    "role": "user",
                    "content": f""" the app prompt is: {prompt} """,
                },
                *extra_messages,
            ],
        )

        collected_messages = []
        for chunk in completion:
            chunk_message_dict = chunk["choices"][0]
            chunk_message = chunk_message_dict["delta"]  # extract the message
            if chunk_message_dict["finish_reason"] is None:
                collected_messages.append(chunk_message)  # save the message
                if stream_handler:
                    try:
                        stream_handler(chunk_message["content"].encode("utf-8"))
                    except Exception as err:
                        logger.info("\nstream_handler error:", err)
                        logger.info(chunk_message)
        # if stream_handler and hasattr(stream_handler, "onComplete"): stream_handler.onComplete('done')
        full_reply_content = "".join([m.get("content", "") for m in collected_messages])
        return full_reply_content


    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def generate_code(self, prompt: str, plan: str, current_file: str, stream_handler: Optional[Callable[Any, Any]] = None) -> str:
        apikey_list = self.api_keys.split(",")   
        # 随机选择一个apikey
        openai.api_key = random.choice(apikey_list)
        completion = openai.ChatCompletion.acreate(
            model=self.model,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": f"""{Prompts.SYSTEM_PROMPT}

                In response to the user's prompt,
                Please name and briefly describe the structure of the app we will generate, including, for each file we are generating, what variables they export, data schemas, id names of every DOM elements that javascript functions will use, message names, and function names.

                We have broken up the program into per-file generation.
                Now your job is to generate only the code for the file: {current_file}

                only write valid code for the given filepath and file type, and return only the code.
                do not add any other explanation, only return valid code for that file type.
                    """,
                },
                {
                    "role": "user",
                    "content": f""" the plan we have agreed on is: {plan} """,
                },
                {
                    "role": "user",
                    "content": f""" the app prompt is: {prompt} """,
                },
                {
                    "role": "user",
                    "content": f"""
        Make sure to have consistent filenames if you reference other files we are also generating.

        Remember that you must obey 3 things:
        - you are generating code for the file {current_file}
        - do not stray from the names of the files and the plan we have decided on
        - MOST IMPORTANT OF ALL - every line of code you generate must be valid code. Do not include code fences in your response, for example

        Bad response (because it contains the code fence):
        ```javascript
        console.log("hello world")
        ```

        Good response (because it only contains the code):
        console.log("hello world")

        Begin generating the code now.

        """,
                },
            ],
            stream=True,
        )

        collected_messages = []
        async for chunk in await completion:
            chunk_message_dict = chunk["choices"][0]
            chunk_message = chunk_message_dict["delta"]  # extract the message
            if chunk_message_dict["finish_reason"] is None:
                collected_messages.append(chunk_message)  # save the message
                if stream_handler:
                    try:
                        stream_handler(chunk_message["content"].encode("utf-8"))
                    except Exception as err:
                        logger.info("\nstream_handler error:", err)
                        logger.info(chunk_message)

        # if stream_handler and hasattr(stream_handler, "onComplete"): stream_handler.onComplete('done')
        code_file = "".join([m.get("content", "") for m in collected_messages])

        pattern = r"```[\w\s]*\n([\s\S]*?)```"  # codeblocks at start of the string, less eager
        code_blocks = re.findall(pattern, code_file, re.MULTILINE)
        return code_blocks[0] if code_blocks else code_file


    def generate_code_sync(self, prompt: str, plan: str, current_file: str,
                        stream_handler: Optional[Callable[Any, Any]] = None,
                        model: str = 'gpt-3.5-turbo-0613') -> str:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.generate_code(prompt, plan, current_file, stream_handler, model))