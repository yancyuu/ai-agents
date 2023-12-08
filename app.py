from dotenv import load_dotenv
import asyncio
load_dotenv(verbose=True)
from agent_protocol import Agent, server, router
from common_sdk.system.sys_env import get_env
from service.customer_support.customer_support_service import _customer_support_agents_api
agent = Agent()
# 初始化客服代理
agent.setup_agent(_customer_support_agents_api.task_handler, _customer_support_agents_api.step_handler)

if __name__ == "__main__":
    # 设置代理的任务处理器和步骤处理器
    from hypercorn.config import Config
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    Config.debug = True
    # 创建配置实例
    config = Config()
    # 设置配置属性
    config.debug = True
    # 获取环境变量中的端口号
    port = get_env("APP_PORT", 1706)
    # 设置绑定的地址和端口
    config.bind = [f"localhost:{port}"]
    # 开始服务
    server.app.include_router(router)
    asyncio.run(serve(server.app, config))