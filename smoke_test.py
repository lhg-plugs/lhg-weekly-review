#!/usr/bin/env python3
"""lhg-weekly-review 插件冒烟测试：全部绿才算过。

检查项：
 1. 三个 JSON 合法（plugin.json / marketplace.json / hooks.json）
 2. 5 个 SKILL.md 都有 name/description frontmatter，且 150~320 行
 3. 4 个 commands 都有 description frontmatter
 4. 2 个 agents 都有 name/description/tools/model frontmatter
 5. skills 平台中立：不含 Claude Code 专有工具名
 6. fixtures：坏 fixture 的埋点规则必须全部命中且脚本 exit!=0；
    好 fixture 零 warning 且 exit==0；SMART-001 用内联用例单独验证
 7. hooks 脚本：周报 frontmatter 触发审计 / 非周报放行 /
    逃生开关 / fail-open

用法：python3 smoke_test.py [--repo <插件根目录>]
退出码：0=全绿，1=有失败。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond, detail=""):
    results.append((PASS if cond else FAIL, name, detail))
    return cond


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def frontmatter(path):
    text = read(path)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for ln in text[3:end].split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", ln)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


BAD_MUST = {"STR-001", "STR-002", "VAG-001", "STAR-001",
            "DATA-001", "NUM-001"}
NEUTRAL_DENY = ["Task tool", "Bash tool", "Edit tool", "Write tool", "Read tool",
                "AskUserQuestion", "subagent_type", "PreToolUse", "PostToolUse",
                "${CLAUDE_", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR"]

SMART_INLINE = """---
weekly-report: true
---

# 周报 2026-10-06~2026-10-12

## 本周完成

- 完成 3 个需求的上线，成功率 99%

## 关键数据

- 日活 12 万，较上周增长 8%：结论是活动带来回流

## 问题与风险

- 现象：联调阻塞 2 小时；根因：环境共用；对策：周三前迁移独立环境

## 下周计划

- 继续推进联调工作
- 优化页面体验
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    AUDIT = os.path.join(repo, "scripts", "audit")

    # 1. JSON 合法
    for rel in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                "hooks/hooks.json"]:
        p = os.path.join(repo, rel)
        try:
            d = json.loads(read(p))
            check("JSON 合法: " + rel, True)
            if rel.endswith("plugin.json"):
                check("plugin.json name==lhg-weekly-review",
                      d.get("name") == "lhg-weekly-review", str(d.get("name")))
                check("plugin.json version==1.0.0",
                      d.get("version") == "1.0.0", str(d.get("version")))
                check("plugin.json 有 description/author",
                      all(d.get(k) for k in ("description", "author")))
            if rel.endswith("marketplace.json"):
                ps = d.get("plugins", [])
                check("marketplace.json source==./",
                      len(ps) == 1 and ps[0].get("source") == "./" and
                      ps[0].get("name") == "lhg-weekly-review", str(ps))
            if rel.endswith("hooks.json"):
                check("hooks.json 顶层有 hooks 包装", "hooks" in d)
                check("hooks.json 有 PostToolUse", "PostToolUse" in d["hooks"],
                      str(list(d["hooks"].keys())))
        except Exception as e:
            check("JSON 合法: " + rel, False, str(e))

    # 2. SKILL.md
    for skill in ["lhg-wr-structure", "lhg-wr-star", "lhg-wr-data",
                  "lhg-wr-issue", "lhg-wr-plan"]:
        p = os.path.join(repo, "skills", skill, "SKILL.md")
        fm = frontmatter(p)
        check("skill frontmatter: " + skill,
              bool(fm.get("name")) and bool(fm.get("description")),
              "name=%s" % fm.get("name"))
        nlines = len(read(p).split("\n"))
        check("skill 行数 150~320: %s (%d 行)" % (skill, nlines),
              150 <= nlines <= 320, str(nlines))
        body = read(p)
        bad_words = [w for w in NEUTRAL_DENY if w in body]
        check("skill 平台中立: " + skill, not bad_words, "命中: %s" % bad_words)
        check("skill 有出品区: " + skill,
              "出品：刘洪光" in body and "https://github.com/lhg-skills" in body)
        check("skill 有自检与反馈: " + skill, "自检与反馈" in body)

    # 3. commands
    for cmd in ["weekly", "weekly-data", "weekly-risk", "weekly-check"]:
        p = os.path.join(repo, "commands", cmd + ".md")
        fm = frontmatter(p)
        check("command description: " + cmd, bool(fm.get("description")),
              str(fm.get("description"))[:60])

    # 4. agents
    for ag in ["reporter", "reviewer"]:
        p = os.path.join(repo, "agents", ag + ".md")
        fm = frontmatter(p)
        check("agent frontmatter: " + ag,
              all(fm.get(k) for k in ("name", "description", "tools", "model")),
              str({k: fm.get(k) for k in ("name", "model")}))

    # 5. 审计脚本冒烟
    def audit_hits_text(text=None, target=None):
        if target:
            cmd = [sys.executable, os.path.join(AUDIT, "structure_audit.py"),
                   "--report", os.path.join(repo, target), "--format", "json"]
            r = run(cmd)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".md",
                                             delete=False,
                                             encoding="utf-8") as fh:
                fh.write(text)
                tmp = fh.name
            try:
                r = run([sys.executable,
                         os.path.join(AUDIT, "structure_audit.py"),
                         "--report", tmp, "--format", "json"])
            finally:
                os.unlink(tmp)
        try:
            d = json.loads(r.stdout)
        except Exception:
            return None, r.returncode, []
        return d["summary"], r.returncode, [f["rule_id"] for f in d["findings"]]

    s, code, ids = audit_hits_text(target="fixtures/report-bad/report.md")
    check("坏 fixture exit!=0", code != 0, "exit=%d" % code)
    check("坏 fixture warning>0", s and s["warning"] > 0, str(s))
    missing = BAD_MUST - set(ids)
    check("坏 fixture 埋点全命中 (%d/%d)"
          % (len(BAD_MUST - missing), len(BAD_MUST)),
          not missing, "缺失: %s" % sorted(missing))

    s, code, _ = audit_hits_text(target="fixtures/report-good/report.md")
    check("好 fixture 零 warning", s and s["warning"] == 0, str(s))
    check("好 fixture exit==0", code == 0, "exit=%d" % code)

    s, code, ids = audit_hits_text(text=SMART_INLINE)
    check("SMART-001 内联用例命中", "SMART-001" in ids, str(sorted(set(ids))))
    check("SMART-001 内联用例 exit!=0", code != 0, "exit=%d" % code)

    # 6. hooks：周报写完自动审计
    def hook(payload, env=None, plugin_root=None):
        e = dict(os.environ)
        e["CLAUDE_PLUGIN_ROOT"] = plugin_root or repo
        e.update(env or {})
        return run([sys.executable,
                    os.path.join(repo, "hooks", "post_report_audit.py")],
                   input=payload, env=e)

    with tempfile.TemporaryDirectory() as td:
        report = os.path.join(td, "周报.md")
        with open(report, "w", encoding="utf-8") as fh:
            fh.write(read(os.path.join(repo, "fixtures/report-bad/report.md")))

        payload = json.dumps({"tool_input": {"file_path": report}})
        r = hook(payload)
        check("hook: 周报文件触发审计并提示",
              r.returncode == 0 and "warning=8" in r.stdout, r.stdout[:120])

        plain = os.path.join(td, "notes.md")
        with open(plain, "w", encoding="utf-8") as fh:
            fh.write("# 普通笔记\n")
        r = hook(json.dumps({"tool_input": {"file_path": plain}}))
        check("hook: 非周报文件快速放行",
              r.returncode == 0 and not r.stdout.strip(), r.stdout[:80])

        good = os.path.join(td, "好周报.md")
        with open(good, "w", encoding="utf-8") as fh:
            fh.write(read(os.path.join(repo, "fixtures/report-good/report.md")))
        r = hook(json.dumps({"tool_input": {"file_path": good}}))
        check("hook: 好周报审计通过有提示",
              r.returncode == 0 and "审计通过" in r.stdout, r.stdout[:120])

        r = hook(payload, env={"LHG_WEEKLY_HOOK_OFF": "1"})
        check("hook: 逃生开关生效",
              r.returncode == 0 and not r.stdout.strip(), r.stdout[:80])

        r = hook("not-json{{{")
        check("hook: 非法输入 fail-open", r.returncode == 0, r.stdout[:80])

    # 报告
    print("=" * 60)
    print("lhg-weekly-review 冒烟测试报告")
    print("=" * 60)
    fails = 0
    for st, name, detail in results:
        mark = "✓" if st == PASS else "✗"
        print("%s %s %s" % (mark, st, name))
        if detail and st == FAIL:
            print("    → %s" % detail)
        if st == FAIL:
            fails += 1
    print("=" * 60)
    print("共 %d 项，通过 %d，失败 %d" % (len(results), len(results) - fails, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
