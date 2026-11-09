<!-- About 简介（推送后填写到仓库 About 栏）：
周报复盘专家：原始工作记录→结构化周报（完成/数据/问题/下周）→数据亮点提炼→风险预警；确定性脚本检查结构完整性与空洞表述。 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-weekly-review
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, weekly-report, review, retrospective, star, smart -->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="lhg-weekly-review — 周报复盘专家">
</p>

> **一句话介绍**：周报复盘专家：原始工作记录→结构化周报（完成/数据/问题/下周）→数据亮点提炼→风险预警；确定性脚本检查结构完整性与空洞表述。

**一键安装**：在 Claude Code 里运行

```bash
/plugin marketplace add lhg-plugs/lhg-weekly-review
/plugin install lhg-weekly-review@lhg-plugs
```

## 它能帮你做出什么

- **冒烟全绿**：`python3 smoke_test.py` 52 项全部通过（JSON 合法、frontmatter 完整、命令/skill/agent 齐全）。

## 它是什么

`lhg-weekly-review` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`weekly` 周报一条龙、`weekly-check` 周报确定性自查、`weekly-data` 数据亮点提炼、`weekly-risk` 风险预警
- **5 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：lhg-wr-data, lhg-wr-issue, lhg-wr-plan, lhg-wr-star, lhg-wr-structure
- **2 个专家 agent**：reporter, reviewer
- **1 个 hooks**（`hooks/`：post_report_audit.py），关键操作前自动把关

## 为什么是它

不是一个 prompt，而是一套互相兜底的机制：

1. **硬门，不是提醒**：hooks 在关键操作前自动拦截或警告（见 `hooks/`），而不是只在文档里写一句"请注意"。
2. **方法论沉淀在 skill 里**：流程、检查清单、口径都写在 `skills/` 的方法论里，命令只是入口；换个 agent 平台也能复用同一套做法。
3. **可验，不是可信**：`fixtures/` 备有坏/好对照用例，`smoke_test.py` 一键验证，规则有没有生效、自己跑一遍就知道。

## 快速上手

```bash
# 1. 安装（Claude Code 里运行）
/plugin marketplace add lhg-plugs/lhg-weekly-review
/plugin install lhg-weekly-review@lhg-plugs

# 2. 周报一条龙：原始工作记录→四段结构化周报（完成/数据/问题/下周）→数据亮点提炼
/lhg-weekly-review:weekly "本周做了支付改造、活动页2个，联调阻塞了6小时"
```

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-weekly-review:weekly` | 周报一条龙：原始工作记录→四段结构化周报（完成/数据/问题/下周）→数据亮点提炼→风险预警→确定性脚本自查。 | `/lhg-weekly-review:weekly "本周做了支付改造、活动页2个，联调阻塞了6小时"` |
| `/lhg-weekly-review:weekly-check` | 周报确定性自查：跑 structure_audit.py 检查四段完整性、空洞表述、STAR要素、数据对比… | `/lhg-weekly-review:weekly-check ./周报.md` |
| `/lhg-weekly-review:weekly-data` | 数据亮点提炼：从工作记录/周报草稿里挖关键数字，按"数字+对比+结论"三段式输出 2~5 个数据点。 | `/lhg-weekly-review:weekly-data ./本周记录.md` |
| `/lhg-weekly-review:weekly-risk` | 风险预警：把卡点/异常写成"现象+根因+对策"，分级标出阻塞项，需要的支持单独列出。 | `/lhg-weekly-review:weekly-risk ./本周记录.md` |

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你需要周报一条龙时 → 用 `/lhg-weekly-review:weekly`
- 你需要周报确定性自查时 → 用 `/lhg-weekly-review:weekly-check`
- 你需要数据亮点提炼时 → 用 `/lhg-weekly-review:weekly-data`

**什么时候不用：**

- 你只需要其中一个零散能力时 → 本插件是成套流程，单点需求用更轻量的 skill 更合适
- 你希望 AI 完全自由发挥、不接受任何自查与硬门时 → 它的规则审计与 hooks 会介入（可关，但那就别装它）
- 你的场景不在上面命令表覆盖范围内时 → 先看命令表，没有对应命令就别硬套

## 目录结构

```
lhg-weekly-review/
├── smoke_test.py          # 一键冒烟测试
├── ATTRIBUTION.md         # 灵感来源与许可声明
├── LICENSE                # MIT
├── README.md              # 本文件
├── .claude-plugin/
├── agents/
├── commands/
├── fixtures/
├── hooks/
├── scripts/
├── skills/
```

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（本次实测 52 项全部通过）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-weekly-review/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

同门插件见 [lhg-plugs](https://github.com/lhg-plugs)，86 个插件的完整矩阵在 [marketplace](https://github.com/lhg-plugs/marketplace) 维护。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
