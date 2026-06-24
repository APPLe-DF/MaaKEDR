import sys
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

# 添加自定义模块路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入自定义识别模块（触发装饰器注册）
import custom.recognition  # noqa: F401


def main():
    # 初始化资源
    Toolkit.init_option(str(Path(__file__).parent.parent / "resource" / "base"))

    # 启动 Agent Server
    identifier = "maakedr_agent"
    AgentServer.start_up(identifier)
    AgentServer.join()


if __name__ == "__main__":
    main()
