from dotenv import load_dotenv

load_dotenv(verbose=True)
from agent_protocol import Agent
from common_sdk.system.sys_env import get_env
from service.customer_support.customer_support_service import _customer_support_agents_api
agent = Agent()
# 初始化客服代理
agent.setup_agent(_customer_support_agents_api.task_handler, _customer_support_agents_api.step_handler)

if __name__ == "__main__":
    # 设置代理的任务处理器和步骤处理器
    agent.start(port=get_env("APP_PORT", 1706))