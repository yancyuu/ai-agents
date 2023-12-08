from agent_protocol import Agent, Step, Task
from controller.base_controller import BaseController
from common_sdk.util.tools_utils import Tool, ToolRegistry
from controller.customer_support.utils import get_order, transfer_to_human
import enum


class AgentsType(str, enum.Enum):
    GET_TOOL = "get_tool"
    GENERATE_REPLY = "generate_reply"

class AgentsAPI(BaseController):
    """这里的api都是BaseActions的父类，可以复用其中的工具和流程"""
    
    SYSTEM_PROMPT = """
    你现在需要回答用户问题。
    如果不知道，就说不知道，不要瞎编。
    你的语气要亲切可爱，像一个小女生一样，每句话中带几个emoji。
    """

    def __init__(self) -> None:
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool("query_order", Tool(data={
                    "type": "function",
                    "function": {
                        "name": "query_order",
                        "description": "Transfer the user to a human assistant.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_input": {
                                    "type": "string",
                                    "description": "User's request for human assistance."
                                }
                            },
                            "required": ["user_input"]
                        }
                    }
                }, call=get_order))
                # 创建工具并注册
        self.tool_registry.register_tool("transfer_to_human", Tool(data={
                    "type": "function",
                    "function": {
                        "name": "query_order",
                        "description": "Query the order status based on user's input.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_input": {
                                    "type": "string",
                                    "description": "User's input mentioning order details."
                                }
                            },
                            "required": ["user_input"]
                        }
                    }
                }, 
                call=transfer_to_human))
        super().__init__(self.tool_registry)

    async def _get_tool(self, step: Step, model) -> Step:
        """找工具的步骤"""
        task = await Agent.db.get_task(step.task_id)
        select_tool = self.determine_tool_type(task.input, model=model)
        await Agent.db.create_step(
        step.task_id,
        AgentsType.GET_TOOL,
        additional_properties={
            "select_tool": select_tool,
        },
        )
        step.output = select_tool
        return step


    async def _generate_reply(self, task: Task, step: Step, model) -> Step:
        select_tool = step.additional_properties["select_tool"]
        reply = self.generate_reply_sync(task.input, select_tool, model=model)
        await Agent.db.create_step(
            step.task_id,
            AgentsType.GENERATE_REPLY,
            additional_properties={
                "reply": reply,
            },
        )
        step.output = reply
        return step

    async def task_handler(self, task: Task) -> None:
        if not task.input:
            raise Exception("No task prompt")
        await Agent.db.create_step(task.task_id, AgentsType.GET_TOOL)


    async def step_handler(self, step: Step) -> Step:
        model = "gpt-3.5-turbo"
        if step.name == AgentsType.GET_TOOL:
            await self._get_tool(step, model)
        else:
            await self._generate_reply(step, model)
        return step

    