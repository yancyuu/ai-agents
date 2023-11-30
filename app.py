from dotenv import load_dotenv

load_dotenv(verbose=True)
from agent_protocol import Agent
from common_sdk.system.sys_env import get_env
from service.create_code.create_code_service import _agents_api
agent = Agent()
# 初始化代理
agent.setup_agent(_agents_api.task_handler, _agents_api.step_handler)

if __name__ == "__main__":
    # 设置代理的任务处理器和步骤处理器
    agent.start(port=get_env("APP_PORT", 1706))