#!/usr/bin/env python3
"""lhg-weekly-review 确定性审计：校验周报 Markdown 的结构完整性与表述质量。

输入：周报 Markdown 文件（章节约定见 lhg-wr-structure skill）。
检查：核心章节是否齐全、空洞表述、事项 STAR 要素、数据对比、
      下周计划 SMART 化。

规则注册表：
  STR-001 warning 缺"下周计划"章节
  STR-002 warning 缺核心章节（本周完成/关键数据/问题与风险 任缺其一）
  VAG-001 warning 空洞表述：命中模糊词（基本完成/有所推进/稳步推进…）
  STAR-001 warning "本周完成"条目缺结果要素（无数字且无结果动词）
  DATA-001 warning "关键数据"章节只有裸数字、无对比
  SMART-001 warning "下周计划"条目不 SMART（无量化目标或无时间）
  NUM-001 nit    全文阿拉伯数字少于 3 个（可能通篇定性、无数据）

退出码：2=有 blocker（保留，未启用），1=有 warning，0=干净。
零第三方依赖。
"""

import argparse
import json
import re
import sys

VAGUE_WORDS = ["基本完成", "有所推进", "稳步推进", "取得进展", "积极开展",
               "持续跟进", "有序进行", "大力推进", "扎实推进", "成效显著",
               "基本正常", "总体平稳", "进展顺利", "有序推进"]
RESULT_WORDS = ["完成", "上线", "交付", "修复", "提升", "增长", "下降",
                "发布", "通过", "解决", "降低", "新增", "优化", "落地"]
COMPARE_WORDS = ["同比", "环比", "较上周", "较上月", "上周", "上月", "去年",
                 "提升", "下降", "增长", "降低", "增加", "减少", "%", "百分点",
                 "翻倍", "新高", "新低"]
TIME_WORDS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日",
              "日前", "底前", "之前", "完成", "截止", "前完成", "内完成",
              "号前", "号完成"]
SECTION_ALIASES = {
    "本周完成": ["本周完成", "本周工作", "工作完成", "完成情况"],
    "关键数据": ["关键数据", "数据概览", "核心数据", "数据"],
    "问题与风险": ["问题与风险", "问题", "风险", "阻塞与风险"],
    "下周计划": ["下周计划", "下周工作", "下一步计划", "工作计划"],
}


def finding(rule_id, severity, message, ref=""):
    return {"rule_id": rule_id, "severity": severity,
            "message": message, "ref": ref}


def parse_sections(text):
    """按 ## 二级标题切分章节，返回 {标题: 正文}。"""
    sections = {}
    cur, buf = None, []
    for ln in text.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            if cur:
                sections[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip(), []
        elif cur:
            buf.append(ln)
    if cur:
        sections[cur] = "\n".join(buf)
    return sections


def find_section(sections, key):
    for title, body in sections.items():
        if any(a in title for a in SECTION_ALIASES[key]):
            return title, body
    return None, ""


def items_of(body):
    return [ln.strip() for ln in body.split("\n")
            if re.match(r"^[-*]\s+\S", ln.strip())]


def has(patterns, text):
    return any(p in text for p in patterns)


def audit(text):
    findings = []
    sections = parse_sections(text)

    # STR-001 / STR-002：章节完整性
    for key, rule in (("下周计划", "STR-001"),
                      ("本周完成", "STR-002"),
                      ("关键数据", "STR-002"),
                      ("问题与风险", "STR-002")):
        title, _ = find_section(sections, key)
        if title is None:
            findings.append(finding(
                rule, "warning",
                "缺「%s」章节：周报四段（完成/数据/问题/下周）不完整" % key,
                "sections"))

    # VAG-001：空洞表述
    for w in VAGUE_WORDS:
        for i, ln in enumerate(text.split("\n"), 1):
            if w in ln and not ln.strip().startswith("#"):
                findings.append(finding(
                    "VAG-001", "warning",
                    "空洞表述「%s」（第 %d 行）：请换成数字+事实，如"
                    "「完成 3 个需求的上线」而不是「%s」"
                    % (w, i, w), "line %d" % i))
                break

    # STAR-001：本周完成条目缺结果要素
    title, body = find_section(sections, "本周完成")
    if title:
        for it in items_of(body):
            if not re.search(r"\d", it) and not has(RESULT_WORDS, it):
                findings.append(finding(
                    "STAR-001", "warning",
                    "事项缺结果要素：「%s……」既无数字也无结果动词，"
                    "请按 STAR 补上做了什么、结果如何"
                    % it[:24], title))

    # DATA-001：关键数据缺对比
    title, body = find_section(sections, "关键数据")
    if title:
        compact = re.sub(r"\s+", "", body)
        if not compact:
            findings.append(finding(
                "DATA-001", "warning",
                "「关键数据」章节为空：至少列 2~3 个关键数字", title))
        elif not has(COMPARE_WORDS, body):
            findings.append(finding(
                "DATA-001", "warning",
                "「关键数据」只有裸数字、无对比：请加同比/环比/较上周等"
                "对比，并给一句结论（数字+对比+结论）", title))

    # SMART-001：下周计划不 SMART
    title, body = find_section(sections, "下周计划")
    if title:
        for it in items_of(body):
            lacks_num = not re.search(r"\d", it)
            lacks_time = not has(TIME_WORDS, it)
            if lacks_num or lacks_time:
                why = []
                if lacks_num:
                    why.append("无量化目标")
                if lacks_time:
                    why.append("无时间节点")
                findings.append(finding(
                    "SMART-001", "warning",
                    "下周计划不 SMART：「%s……」（%s），请改成"
                    "「做 X（量化）+ 周几前完成（时间）」"
                    % (it[:24], "、".join(why)), title))

    # NUM-001：全文数字过少
    digits = re.findall(r"\d", text)
    if len(digits) < 3:
        findings.append(finding(
            "NUM-001", "nit",
            "全文只有 %d 个阿拉伯数字：周报通篇定性、没有数据支撑，"
            "建议补充关键数字" % len(digits), "whole"))

    return findings


def summarize(findings):
    s = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        if f["severity"] in s:
            s[f["severity"]] += 1
    return s


def main():
    ap = argparse.ArgumentParser(description="lhg-weekly-review 周报结构审计")
    ap.add_argument("--report", required=True, help="周报 Markdown 路径")
    ap.add_argument("--format", choices=["json", "text"], default="json")
    args = ap.parse_args()

    try:
        with open(args.report, encoding="utf-8") as fh:
            text = fh.read()
    except Exception as e:
        print("周报读取失败：%s" % e, file=sys.stderr)
        return 2

    findings = audit(text)
    summary = summarize(findings)

    if args.format == "json":
        print(json.dumps({"summary": summary, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        print("周报结构审计：blocker=%d warning=%d nit=%d"
              % (summary["blocker"], summary["warning"], summary["nit"]))
        for f in findings:
            print("[%s] %s %s" % (f["severity"].upper(), f["rule_id"],
                                  f["message"]))

    if summary["blocker"]:
        return 2
    if summary["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
