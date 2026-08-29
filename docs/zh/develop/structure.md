---
title: "项目结构说明"
order: 5
icon: "ri:folder-tree-fill"
---

# 项目结构

```text
MaaKEDR/
├── interface.json                  # MaaFW 项目定义
├── maa-project.json / .lock.json   # 工具状态文件
├── package.json                    # Node 工具链
├── maatools.config.mts             # MaaTools 配置
│
├── resource/base/
│   ├── default_pipeline.json       # 全局默认参数
│   ├── pipeline/                   # Pipeline 节点定义
│   │   ├── startup.json            # 启动游戏
│   │   ├── claim_rewards.json      # 领取奖励
│   │   ├── farm_resources.json     # 资源刷取
│   │   ├── pvp.json                # 玩家对战
│   │   ├── stamina.json            # 体力信息
│   │   └── event_stage.json        # 活动关卡与活动商店
│   ├── image/                      # 模板图片
│   │   ├── claim_rewards/          # 奖励相关图片
│   │   ├── farm_resources/         # 刷取相关图片
│   │   ├── pvp/                    # PVP 相关图片
│   │   ├── event_stage/            # 活动相关图片
│   │   └── ...                     # 通用图片
│   ├── model/ocr/                  # PaddleOCR v5 模型
│   └── announcement/               # GUI 欢迎公告
│
├── agent/                          # Python Agent
│   ├── bootstrap.py                # 入口：环境检查 → main.py
│   ├── main.py                     # 转接 → run_agent()
│   ├── agent_runtime.py            # 核心：注册 → AgentServer
│   ├── custom/
│   │   ├── recognition/            # 自定义识别
│   │   ├── action/                 # 自定义动作
│   │   └── sink/                   # 自定义事件监听（如分辨率检查）
│   └── utils/                      # 工具模块
│
├── tasks/                          # 任务入口定义
│   ├── startup.json                # 启动游戏
│   ├── claim_rewards.json          # 奖励领取
│   ├── farm_resources.json         # 资源刷取
│   ├── farm_remaining_stamina.json # 剩余体力刷取
│   ├── pvp.json                    # 玩家对战
│   ├── stamina_info.json           # 体力信息
│   ├── event_stage.json            # 活动关卡与商店
│   └── preset/                     # 任务预设（Daily / Activity）
│
├── tools/                          # 开发工具
│   ├── build-release.mjs           # 打包发布
│   ├── check-project.mjs           # 项目检查
│   ├── sync-runtime.mjs            # 运行时同步
│   ├── validate-schema.mjs         # Schema 校验
│   └── schema/                     # JSON Schema
│
└── docs/                           # 文档
    └── ...
```

## 三层架构

```text
tasks/*.json ──→ pipeline/*.json ──→ agent/custom/
(task 入口)      (节点图)            (Python 自定义逻辑)
```

- **Layer 1 — Tasks**：`tasks/*.json`，定义 GUI 中显示的任务和选项
- **Layer 2 — Pipeline**：`resource/base/pipeline/*.json`，JSON 节点有向图，90% 的逻辑在此
- **Layer 3 — Agent**：`agent/custom/`，Python 代码处理复杂逻辑
