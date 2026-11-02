---
order: 2
icon: ri:play-circle-line
---

# 启动与登录协议

启动任务是整条任务链的第一步：拉起游戏进程、点过开始界面与每日登录奖励，最终停在可识别的游戏主页。
它**不接入**通用回主页枢纽 `Common.EnsureHome`——启动阶段游戏可能还没进入游戏内，按返回键有退出游戏的风险。

## 任务入口

| 项     | 值                                                                                 |
| ------ | ---------------------------------------------------------------------------------- |
| 任务名 | 启动游戏（`tasks/startup.json`，`default_check: true`）                            |
| entry  | `LaunchGame`                                                                       |
| 流程   | `resource/base/pipeline/startup.json`                                              |
| 区服包 | `resource/bilibili/pipeline/startup.json`、`resource/taptap/pipeline/startup.json` |
| 选项   | 无                                                                                 |

## 数据链路

```text
tasks/startup.json（无选项）
  → 任务级无 pipeline_override
  → resource/base/pipeline/startup.json：LaunchGame → … → CheckHomePageStable
  → 区服包 startup.json 只覆盖 LaunchGame.action.param.package（改启动哪个安装包）
  → 无 Custom 节点，不涉及 agent 代码
```

## 典型流程

```text
LaunchGame（StartApp 拉起游戏进程）
  → WaitGameLoading（等待加载完成）
  → ClickToStart（点开始游戏，最多 3 次）
  → DailyLoginReward（每日登录奖励弹窗，点 2 次）
  → CheckHomePage（识别主页标记 main_option.png）
       ├─ 命中且仍有弹窗 → [JumpBack]DailyLoginReward 清弹窗后重判
       └─ 未命中 → ClickHomePage（点屏幕中心 5 次）
            → [JumpBack]DailyLoginReward → CheckHomePageStable（主页稳定，叶子节点）
```

## 节点与字段

| 节点                  | 识别 / 动作                                    | 关键字段                                                                            |
| --------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| `LaunchGame`          | DirectHit / `StartApp`                         | `package: com.phxh.official.nld`、`timeout: 60000`                                  |
| `WaitGameLoading`     | TemplateMatch `game_loading.png` / DoNothing   | `roi [595,653,146,64]`、`post_wait_freezes: 500`、`post_delay: 4000`                |
| `ClickToStart`        | TemplateMatch `startgame1.png` / Click         | `repeat: 3`、`pre_delay: 1000`、`post_delay: 4000`、`timeout: 30000`                |
| `DailyLoginReward`    | TemplateMatch `daily_login_reward.png` / Click | `roi [405,115,103,106]`、`repeat: 2`、`post_delay: 500`                             |
| `CheckHomePage`       | TemplateMatch `main_option.png` / DoNothing    | `roi [1199,6,77,83]`、`threshold: 0.75`、`next` 首位是 `[JumpBack]DailyLoginReward` |
| `ClickHomePage`       | DirectHit / Click                              | `target [588,369,9,11]`、`repeat: 5`、`repeat_delay: 500`                           |
| `CheckHomePageStable` | TemplateMatch `main_option.png` / DoNothing    | 叶子节点，任务成功出口                                                              |

## 资源与模板

常用模板位于 `resource/base/image/` 根目录（启动相关图跨任务共用）：

- `game_loading.png` — 加载中画面
- `startgame1.png` — 开始游戏按钮
- `daily_login_reward.png` — 每日登录奖励弹窗
- `main_option.png` — 主页右上角特征（`Common.CheckHomePage` 等节点共用同一张）

## 区服覆盖

三个区服只有启动包名不同，用同名节点覆盖即可，其它任务全部复用 `base`：

| 资源包   | 文件                                      | 覆盖内容                        |
| -------- | ----------------------------------------- | ------------------------------- |
| base     | `resource/base/pipeline/startup.json`     | `com.phxh.official.nld`（官服） |
| bilibili | `resource/bilibili/pipeline/startup.json` | `com.phxh.nlddev.bilibili`      |
| taptap   | `resource/taptap/pipeline/startup.json`   | `com.phxh.taptap.nld`           |

新增区服时优先只改启动包名；确需改登录入口或渠道包差异图时，再往该区服包放同名节点 / 图片。

## 开发注意

- 启动后动画长：用识别节点或 `post_wait_freezes`，避免固定超长 delay
- 弹窗顺序可能变化：`next` 中并列弹窗节点，并用 `[JumpBack]` 处理可重入弹窗
- 主页判定统一用 `main_option.png`（`roi [1199,6,77,83]`、阈值 0.75），不要另造主页特征图
- 结束条件必须落在**叶子节点**（`CheckHomePageStable`），否则任务不会成功收尾

## 改动这类流程要动哪些文件

1. 改启动流程 / 新增界面：编辑 `resource/base/pipeline/startup.json`
2. 改启动包名（换服、换渠道包）：编辑对应区服包的 `pipeline/startup.json`，**不要**改 `base`
3. 新增模板图：放 `resource/base/image/`，文件名用小写 `snake_case`
4. 任务描述 / 默认勾选：编辑 `tasks/startup.json` 的 `description`、`default_check`
5. 校验：`pnpm exec maa-tools check`（pipeline 完整性），提交前 `pnpm check`

## 验收清单

改动本任务后按以下顺序验证：

1. 官服 / B 服 / TapTap 三个资源包分别验证启动链路（区服包名覆盖生效）
2. 冷启动（未开进程）与热启动（已开进程）各跑一遍
3. 每日登录奖励弹窗出现 / 不出现两种路径都验证
4. 启动动画期间截图不早于画面稳定（识别或 `post_wait_freezes` 生效）
5. 启动失败（如网络错误弹窗）有兜底提示而非卡死
6. 全量回归：启动完成后接领取奖励 / 刷取任务跑一遍无冲突
