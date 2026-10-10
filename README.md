<!-- About 简介（推送后填写到仓库 About 栏）：
周报复盘专家：工作记录→结构化周报→亮点提炼→风险预警一条龙 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-weekly-review
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, weekly-report, retrospective, workplace -->

# lhg-weekly-review：周报复盘专家，工作记录→可发出的周报一条龙

> **一句话介绍**：给 AI 编程助手装上"周报复盘专家"——丢入原始工作记录，自动写成四段结构化周报（本周完成/关键数据/问题与风险/下周计划），数据按"数字+对比+结论"提炼亮点，问题按"现象+根因+对策"预警；**确定性脚本自动抓空洞表述（"基本完成""有所推进"）和缺失章节**。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-weekly-review
> /plugin install lhg-weekly-review@lhg-plugs
> ```

## 它是什么

`lhg-weekly-review` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`weekly` 周报一条龙，`weekly-data` 数据亮点提炼，`weekly-risk` 风险预警，`weekly-check` 周报确定性自查
- **5 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：周报总纲、STAR 事项描述、数据"数字+对比+结论"、问题"现象+根因+对策"、下周计划 SMART 化
- **2 个专家 agent**：周报撰写专家、周报质检专家
- **1 个硬门 hook**：周报文件写完后自动跑结构审计，有问题即时提示（可一键关闭）
- **7 条确定性审计规则**：纯 Python 标准库、零第三方依赖，检查结构完整性与表述质量

## 信任机制：水周报发不出去

这是本插件与"直接让 AI 写周报"最大的区别：

1. **四段结构强制**：本周完成 / 关键数据 / 问题与风险 / 下周计划，缺一段就报 warning。
2. **空洞表述检测**：脚本内置模糊词表（基本完成、有所推进、稳步推进、取得进展……），命中即报 warning，并给改写方向。
3. **数据三段式**：每个关键数字必须有对比（环比/同比/目标）和结论，裸数字报 warning。
4. **计划 SMART 化**：下周计划每条必须有时间+动作+量化，"继续推进"式条目报 warning。
5. **写完自动审**：hook 在周报文件写入后自动跑审计，问题即时回传提示（`LHG_WEEKLY_HOOK_OFF=1` 可关）。
6. **不编数字**：这是红线——用户没给的数字绝不编造，缺数字就写"暂无量化数据"。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-weekly-review:weekly` | 工作记录→四段周报→亮点提炼→风险预警→审计，一条龙 | `/lhg-weekly-review:weekly "本周做了支付改造、活动页2个，联调阻塞了6小时"` |
| `/lhg-weekly-review:weekly-data` | 数据亮点提炼：裸数字→"数字+对比+结论" | `/lhg-weekly-review:weekly-data ./本周记录.md` |
| `/lhg-weekly-review:weekly-risk` | 风险预警：卡点→"现象+根因+对策"，分级标出 | `/lhg-weekly-review:weekly-risk ./本周记录.md` |
| `/lhg-weekly-review:weekly-check` | 周报确定性自查：结构/空洞表述/数据/SMART 分级报告 | `/lhg-weekly-review:weekly-check ./周报.md` |

## 目录结构

```
lhg-weekly-review/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：weekly / weekly-data / weekly-risk / weekly-check
├── skills/                  # 5 个平台中立 skill（总纲/STAR/数据/问题/计划）
├── agents/                  # 2 个专家 agent（reporter / reviewer）
├── hooks/                   # 周报写完自动审计 hook（fail-open，可一键关闭）
├── scripts/audit/           # 确定性审计：structure_audit.py（零第三方依赖）
├── fixtures/                # 好/坏对照用例 + 生成器
├── smoke_test.py            # 冒烟测试（50 项）
├── ATTRIBUTION.md           # 灵感来源声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**Q：日报/月报能用吗？**
A：日报太细、月报要加趋势分析，都不是这个体裁。本插件专为"周"设计：四段结构、周区间标题、环比锚点都是按周来的。月报可以拿它的"数据三段式"和"问题三段式"去用，但结构要自己调。

**Q：这周没什么产出，全是开会，写什么？**
A：诚实写。"本周完成"写推进了什么（如"完成 3 个需求的评审，输出评审纪要"）；"关键数据"写投入产出（如"评审通过率 100%，无返工"）；"问题与风险"写风险前瞻。不要编产出，也不要只写"本周无产出"就交差。

**Q：数据不好看，能不能不写？**
A：不能。数据不好看更要写，配上根因和对策。写法模板：数字+对比+根因一句话+对策（对策进下周计划）。藏数据被发现的那天，信任就没了。

**Q：AI 会编数字吗？**
A：这是本插件的红线：用户没给的数字绝不编造。缺数字就写"暂无量化数据"，并建议在下周计划里加一条"建立统计口径"。审计脚本的 NUM-001 会提示"全文数字过少"，但那是提醒补充，不是让你编。

**Q：一定要用 Claude Code 吗？**
A：`skills/` 下的方法论是平台中立的纯 Markdown，可直接搬到豆包、Workbuddy 等 agent 平台用。只有 commands/agents/hooks 需要 Claude Code。

**Q：和直接问 AI"帮我写周报"有什么区别？**
A：区别在"结构"和"证据"：四段结构保证不缺"下周计划"；空洞表述检测逼你把"基本完成"换成数字；数据三段式保证每个数字都有对比和结论；问题三段式保证每个卡点都有对策且对策进了下周计划。直接问 AI 没有这些，写出来的多半是流水账。

## 自迭代

- 每个 skill 末尾有「自检与反馈」节：质检门 + 标准冒烟用例 + 一键提 issue。
- 发现规则误报/漏报、方法论不合理：到本仓库提 issue（标题带对应 skill 前缀，如 `[lhg-wr-star]`），附场景与期望行为。

## 出品：刘洪光

刘洪光（https://github.com/lhg-skills）出品，lhg-plugs「小白专家插件」系列之一。
灵感来源见 [ATTRIBUTION.md](./ATTRIBUTION.md)（借鉴思路，实现与文案均为原创）。
