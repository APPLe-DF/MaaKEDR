# MaaFramework Skill

## 概述
MaaFramework 是一个自动化框架，用于游戏自动化任务。

## Pipeline 协议
- 使用 JSON 格式定义任务流程
- 支持 TemplateMatch、OCR、Custom 等识别方式
- 支持 Click、Swipe、DoNothing 等动作

## Agent 开发
- 使用 Python 编写自定义识别和动作
- 通过 AgentServer 注册自定义模块
- 支持 loguru 日志记录

## 项目结构
- `resource/base/pipeline/` - Pipeline JSON 文件
- `resource/base/image/` - 模板图片
- `agent/custom/` - 自定义识别和动作
- `tasks/` - 任务配置文件

## 常用命令
- `pnpm format:all` - 格式化所有文件
- `pnpm check` - 运行所有检查
- `python tools/validate_schema.py resource/` - 验证 Schema
