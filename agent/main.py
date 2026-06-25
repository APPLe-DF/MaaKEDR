import sys
import os
from pathlib import Path

# 设置 stdout 编码为 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 设置工作目录
current_file_path = os.path.abspath(__file__)
current_script_dir = os.path.dirname(current_file_path)
project_root_dir = os.path.dirname(current_script_dir)

if os.getcwd() != project_root_dir:
    os.chdir(project_root_dir)

# 添加自定义模块路径
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

# 导入自定义识别模块（触发装饰器注册）
import custom.recognition  # noqa: F401
from utils.logger import logger


def main():
    logger.info("Agent 启动中...")

    # 初始化资源
    Toolkit.init_option(str(Path(__file__).parent.parent / "resource" / "base"))

    # 启动 Agent Server
    identifier = "maakedr_agent"
    logger.info(f"Agent 标识符: {identifier}")
    AgentServer.start_up(identifier)
    logger.info("AgentServer 启动成功")
    AgentServer.join()
    logger.info("AgentServer 关闭")


if __name__ == "__main__":
    main()
