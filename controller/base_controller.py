import asyncio
import openai
import random
import json
import re

from common_sdk.logging.logger import logger
from common_sdk.system.sys_env import get_env
from common_sdk.util.tools_utils import Tool, ToolRegistry

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
    
class BaseController:
    '''基本的流程：
        1. 从一堆工具中选择合适的工具
        2. 用这个工具去引导用户输入
        3. 根据人设和工具获取到的信息，回复用户
    '''

    SYSTEM_PROMPT = """
    你现在需要回答用户问题。
    如果不知道，就说不知道，不要瞎编。
    """

    def __init__(self, registry: ToolRegistry) -> None:
        # 这里的apikey其实是oneapi的key, 此项目不做apikey的分发管理。
        openai.api_base = get_env("OPENAI_API_BASE")
        self.api_keys = get_env("OPENAI_API_KEY")
        # 注册工具范式
        self.tool_registry = registry
        determine_tool_types = self.tool_registry.get_all_tool_names()
        self.tool_registry.register_tool("determine_tool_type", Tool(data={
                    "type": "function",
                    "function": {
                        "name": "determine_tool_type",
                        "description": "Determine the type of tool to use based on user input",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_input": {
                                    "type": "string",
                                    "description": "The user's input request."
                                }
                            },
                            "required": ["user_input"],
                        },
                        "output": {
                            "type": "string",
                            "enum": determine_tool_types, 
                            "description": "The type of tool determined to be used based on the user input."
                        }
                    }
                }, 
                call=None))

    async def determine_tool_type(self, prompt, model="gpt-3.5-turbo"):
        """判断用户意图"""
        apikey_list = self.api_keys.split(",")   
        # 随机选择一个apikey
        openai.api_key = random.choice(apikey_list)
        logger.info(f"get_all_tool_datas  {self.tool_registry.get_all_tool_datas()}")
        completion = await openai.ChatCompletion.acreate(
            model=model,
            temperature=0.7,
            tools=self.tool_registry.get_all_tool_datas(),
            tool_choice = {"type": "function", "function": {"name": "determine_tool_type"}},
            messages=[
                {
                    "role": "system",
                    "content": f"""根据用户输入的提示词，从枚举中选择一个合适的工具,如果没有就输出字符串nothing。""",
                },
                {
                    "role": "user",
                    "content": f"""prompt is: {prompt} """,
                }
            ],
        )
        logger.info(f"completion  {completion}")
        # 解析响应以提取生成的函数参数
        if "tool_calls" in completion.json()["choices"][0]["message"]:
            select_tool_type = completion.json()["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
            logger.info(f"select_tool_type  {select_tool_type}")
            return select_tool_type
        logger.info(f"没有生成有效的函数调用")
        return

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def generate_reply(self, prompt: str, select_tool_type=None, model = "gpt-3.5-turbo"):
        selected_tool = self.tool_registry.get_tool(select_tool_type)
        if not selected_tool:
            return "选择的工具不存在"
        apikey_list = self.api_keys.split(",")   
        # 随机选择一个apikey
        openai.api_key = random.choice(apikey_list)
        completion = await openai.ChatCompletion.acreate(
            model=model,
            temperature=0.7,
            tools=[selected_tool.data],
            messages=[
                {
                    "role": "system",
                    "content": f"""{self.SYSTEM_PROMPT}

        回应用户，编写一个计划，在这个计划中，你需要得到用户输入的参数，去找到自己需要的参数并返回。
                    """,
                },
                {
                    "role": "user",
                    "content": f""" the app prompt is: {prompt} """,
                }
            ],
        )        
        # 解析响应以提取生成的函数参数
        logger.info(f"返回的结果为 {completion.json()}")
        if "tool_calls" in completion.json()["choices"][0]["message"]:
            function_args = completion.json()["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
            # 假设 function_args 是一个 JSON 字符串
            # 执行实际的函数调用
            # 这需要您定义一个能处理这些参数的函数
            result = selected_tool.call(json.loads(function_args))
            print(result)
        else:
            print("没有生成有效的函数调用参数。")


    
    def generate_reply_sync(self, prompt: str, select_tool_type: str = "", model: str = "gpt-3.5-turbo") -> str:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.generate_reply(prompt, select_tool_type, model))
    
    
