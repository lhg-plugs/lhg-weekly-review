#!/usr/bin/env python3
"""lhg-weekly-review 硬门：周报写完后自动跑结构审计。

触发：PostToolUse / Write。脚本读取被写入的文件，若其 YAML frontmatter
声明了 `weekly-report: true`（周报文件约定），则运行
scripts/audit/structure_audit.py，把 warning/nit 数量与明细以
additionalContext 形式回传（不拦截写入，仅提示）。

逃生方式（按推荐度排序）：
  1. LHG_WEEKLY_HOOK_OFF=1（环境变量，当前会话有效）：跳过本次自动审计。
  2. /plugin disable lhg-weekly-review（整个插件停用，hooks 不再触发）。

设计原则：内部出错一律 fail-open（直接放行，不审计也不报错）；
零第三方依赖。
"""

import json
import os
import subprocess
import sys


def read_frontmatter(path):
    """极简 YAML frontmatter 解析：只取顶层 key: value。"""
    fm = {}
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read(4096)
    except OSError:
        return fm
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    for ln in text[3:end].split("\n"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def main() -> int:
    if os.environ.get("LHG_WEEKLY_HOOK_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    try:
        fm = read_frontmatter(file_path)
        if fm.get("weekly-report") != "true":
            return 0  # 非周报文件，快速放行

        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), os.pardir)
        script = os.path.join(plugin_root, "scripts", "audit",
                              "structure_audit.py")
        if not os.path.isfile(script):
            return 0

        r = subprocess.run(
            [sys.executable, script, "--report", file_path,
             "--format", "json"],
            capture_output=True, text=True, timeout=25)
        try:
            data = json.loads(r.stdout)
        except Exception:
            return 0
        summary = data.get("summary", {}) or {}
        w, n = summary.get("warning", 0), summary.get("nit", 0)
        if w == 0 and n == 0:
            msg = ("lhg-weekly-review：周报自动审计通过——四段结构完整，"
                   "无空洞表述，数据有对比、下周计划 SMART。")
        else:
            lines = ["lhg-weekly-review：周报自动审计发现 warning=%d nit=%d："
                     % (w, n)]
            for f in (data.get("findings") or [])[:8]:
                lines.append("- [%s] %s %s" % (f.get("severity"),
                                               f.get("rule_id"),
                                               f.get("message")))
            lines.append("用 /weekly-check 看完整报告并优化后再发出。")
            msg = "\n".join(lines)
        out = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                      "additionalContext": msg}}
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0
    except Exception:
        return 0  # 任何内部错误：fail-open


if __name__ == "__main__":
    sys.exit(main())
