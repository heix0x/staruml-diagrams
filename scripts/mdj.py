"""mdj 命令行入口。

用法：
    python mdj.py build in.yaml -o out.mdj
    python mdj.py check out.mdj
    python mdj.py kinds

build：读描述文件 → 按 diagram.kind 分派到对应图模块 → 自检 → 写 mdj。
check：对任意 mdj（包括别人给的、官方样例）做结构体检。

约定：所有图模块都暴露 `STATUS`（verified / derived）和 `build(spec, project_id)`，
返回一棵可以直接挂在 Project 下的模块节点（FCFlowchart 或 UMLModel）。
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402
import dsl  # noqa: E402

# diagram.kind -> 模块名
MODULES = {
    "flowchart": "flowchart",
    "usecase": "usecase",
    "class": "classdia",
    "component": "component",
    "deployment": "deployment",
    "sequence": "sequence",
}


def say(msg=""):
    print(msg, flush=True)


def staruml_running() -> bool:
    """StarUML 是否正在运行。

    它不热重载：开着的时候把文件写回去，StarUML 内存里的旧版本会覆盖新文件，
    看起来像「生成失败」。这个检查把它从「记住别忘」变成「不关就报错」。
    """
    try:
        if sys.platform == "win32":
            # tasklist 输出是 GBK，按字节找名字，别解码
            out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq StarUML.exe"],
                                 capture_output=True, timeout=10).stdout or b""
            return b"StarUML.exe" in out
        out = subprocess.run(["pgrep", "-x", "StarUML"],
                             capture_output=True, timeout=10).stdout or b""
        return bool(out.strip())
    except Exception:
        return False


def cmd_build(a):
    raw = dsl.load(a.src)
    errs = dsl.check(raw)
    if errs:
        say("描述文件有问题：")
        for e in errs:
            say("  - " + e)
        return 2

    if not a.force and staruml_running():
        say("StarUML 正在运行，先退出它再生成。")
        say("")
        say("  它在内存里存着打开时的版本，不热重载。你把新文件写进去，")
        say("  只要它在界面上保存一次，就会把旧内容盖回去，看起来像「生成了但图没变」。")
        say("")
        say("  确实要跳过这个检查（比如 StarUML 里开的是别的项目）：加 --force")
        return 4

    bundle = dsl.normalize(raw)
    views = bundle["views"]
    project_id = common.nid()

    nodes, derived = [], []
    for i, view in enumerate(views):
        kind = view["diagram"]["kind"]
        try:
            mod = importlib.import_module(MODULES[kind])
        except ImportError:
            say("这个图类型还没实现：%s（已实现：%s）" %
                (kind, " / ".join(k for k in MODULES if _exists(k))))
            return 2
        try:
            nodes.append(mod.build(view, project_id))
        except SystemExit as e:
            say("第 %d 张图（%s）生成失败：%s" % (i + 1, view["diagram"]["name"], e))
            return 3
        if getattr(mod, "STATUS", "derived") != "verified":
            derived.append(kind)

    project = {"_type": "Project", "_id": project_id,
               "name": bundle["project"], "ownedElements": nodes}
    keep_one_default(project)

    n_id, n_ref, dup, miss = common.selfcheck(project)
    if dup or miss:
        say("自检失败：重复 id %s，未命中引用 %d 个" % (dup, len(miss)))
        for m in miss[:5]:
            say("  缺 " + m)
        return 3

    size = common.dump(project, a.out)
    say("已生成 %s（%d 字节）" % (a.out, size))
    say("工程「%s」共 %d 张图：%s" %
        (bundle["project"], len(views), " / ".join(v["diagram"]["name"] for v in views)))
    say("自检：%d 个对象 / %d 个引用，全部命中" % (n_id, n_ref))

    if derived:
        say("")
        say("⚠️  这些图类型（%s）的 mdj 结构是按 StarUML 源码推导的，**没有在 StarUML 里实际打开过**。" % " / ".join(sorted(set(derived))))
        say("   打开确认无误后，把 references/<kind>.md 和对应脚本里的 STATUS 改成 verified。")

    say("")
    say("打开前记得先完全退出 StarUML——它不热重载，开着的时候会把旧内容写回文件。")
    return 0


def keep_one_default(project):
    """多个模块都会给自家 Diagram 打 defaultDiagram: true，合并后只能留一个。

    保留遍历到的第一个，其余删掉——否则 StarUML 不知道打开哪张图。
    """
    seen = False
    stack = [project]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if o.get("_type", "").endswith("Diagram") and o.get("defaultDiagram"):
                if seen:
                    o.pop("defaultDiagram", None)
                else:
                    seen = True
            stack.extend(reversed(list(o.values())))
        elif isinstance(o, list):
            stack.extend(reversed(o))


def _exists(kind):
    try:
        importlib.import_module(MODULES[kind])
        return True
    except ImportError:
        return False


def cmd_check(a):
    data = json.load(io.open(a.mdj, encoding="utf-8"))
    n_id, n_ref, dup, miss = common.selfcheck(data)

    errs = []
    if dup:
        errs.append("重复 id：%s" % sorted(dup)[:3])
    if miss:
        errs.append("未命中的引用 %d 个：%s" % (len(miss), miss[:3]))

    # 视图与模型的一一对应
    objs = {}

    def walk(o):
        if isinstance(o, dict):
            if "_id" in o:
                objs[o["_id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for i in o:
                walk(i)

    walk(data)

    for oid, o in objs.items():
        t = o.get("_type", "")
        if t.endswith("View") and t not in ("LabelView", "EdgeLabelView") and "head" in o and "tail" in o:
            for k in ("head", "tail"):
                ref = (o.get(k) or {}).get("$ref")
                if ref and ref not in objs:
                    errs.append("%s 的 %s 不是视图 id" % (oid[:8], k))
            m = objs.get((o.get("model") or {}).get("$ref"))
            if not m:
                errs.append("%s 的 model 缺失" % oid[:8])

    diags = [o for o in objs.values() if o.get("_type", "").endswith("Diagram")]
    defaults = [d for d in diags if d.get("defaultDiagram")]
    if len(defaults) > 1:
        errs.append("defaultDiagram 有 %d 个，只能有一个" % len(defaults))

    # 关系模型必须有一条连线视图，否则 StarUML 里画不出来（只在模型树里存在）
    EDGE_MODEL_T = {"FCFlow", "UMLDependency", "UMLAssociation", "UMLCommunicationPath",
                    "UMLSeqMessage", "UMLGeneralization", "UMLInterfaceRealization"}
    EDGE_T = {"FCFlowView", "UMLDependencyView", "UMLAssociationView", "UMLSeqMessageView",
              "UMLCommunicationPathView", "UMLIncludeView", "UMLExtendView",
              "UMLGeneralizationView", "UMLInterfaceRealizationView"}
    drawn = set()
    for d in diags:
        for v in d.get("ownedViews", []):
            if v.get("_type") in EDGE_T:
                ref = (v.get("model") or {}).get("$ref")
                if ref:
                    drawn.add(ref)
    for oid, o in objs.items():
        if o.get("_type") in EDGE_MODEL_T and oid not in drawn:
            src = objs.get((o.get("source") or {}).get("$ref"), {}).get("name", "?")
            dst = objs.get((o.get("target") or {}).get("$ref"), {}).get("name", "?")
            errs.append("关系没有连线视图：%s → %s（%s）"
                        % (src, dst, o.get("_type")))

    # UMLAssociation 及其子类只认 end1/end2；写成 source/target 会被 StarUML 丢掉
    ASSOC_T = {"UMLAssociation", "UMLCommunicationPath"}
    for oid, o in objs.items():
        if o.get("_type") not in ASSOC_T:
            continue
        if "end1" not in o or "end2" not in o:
            errs.append("%s 缺少 end1/end2（StarUML 会整条丢掉，连模型树里都没有）"
                        % o.get("_type"))

    # 顶层节点视图两两不相交（LabelView / compartment / 连线不算）
    rects = []
    for d in diags:
        for v in d.get("ownedViews", []):
            if v.get("_type") in EDGE_T:
                continue
            if all(k in v for k in ("left", "top", "width", "height")):
                rects.append(v)
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            # 只在同一张图内比较：多图工程里不同图的坐标是各自独立的
            if a.get("_parent", {}).get("$ref") != b.get("_parent", {}).get("$ref"):
                continue
            if (a["left"] < b["left"] + b["width"] and b["left"] < a["left"] + a["width"]
                    and a["top"] < b["top"] + b["height"] and b["top"] < a["top"] + a["height"]):
                na = objs.get((a.get("model") or {}).get("$ref"), {}).get("name", a["_id"][:6])
                nb = objs.get((b.get("model") or {}).get("$ref"), {}).get("name", b["_id"][:6])
                errs.append("视图重叠：%s ↔ %s" % (na, nb))

    say("对象 %d / 引用 %d / 图 %d 张" % (n_id, n_ref, len(diags)))
    if errs:
        say("发现 %d 个问题：" % len(errs))
        for e in errs[:10]:
            say("  - " + e)
        return 3
    say("结构体检通过")
    return 0


def cmd_kinds(_):
    for k, m in MODULES.items():
        try:
            mod = importlib.import_module(m)
            say("  %-12s %-10s %s" % (k, getattr(mod, "STATUS", "?"), mod.__doc__.splitlines()[0]))
        except ImportError:
            say("  %-12s %-10s %s" % (k, "missing", "（第二批再做）"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mdj", description="把描述文件编译成 StarUML .mdj")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="生成 mdj")
    b.add_argument("src", help="描述文件（.yaml / .json）")
    b.add_argument("-o", "--out", required=True, help="输出 mdj 路径")
    b.add_argument("--force", action="store_true",
                   help="StarUML 正在运行时也照常写入（默认会拦住）")
    b.set_defaults(func=cmd_build)

    c = sub.add_parser("check", help="体检一个 mdj")
    c.add_argument("mdj")
    c.set_defaults(func=cmd_check)

    k = sub.add_parser("kinds", help="列出支持的图类型和状态")
    k.set_defaults(func=cmd_kinds)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
