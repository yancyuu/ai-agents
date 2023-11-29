from agent_protocol import Agent
from service.create_code.create_code_service import _agents_api

# 初始化代理
agent = Agent()
agent.setup_agent(_agents_api.task_handler, _agents_api.step_handler)

if __name__ == "__main__":
    # 设置代理的任务处理器和步骤处理器
    agent.start(port=1706)
