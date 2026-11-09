"""对 examples/ 里的每个描述文件跑 build + check，并断言元素数量对得上。

用法：
    python tests/run_checks.py

退出码：0 全部通过 / 1 有失败。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
EXAMPLES = os.path.join(ROOT, "examples")

# 描述文件 -> 期望的 (节点数, 关系数)；关系数含参与者关联与 include
# 多图工程按所有图合计
EXPECT = {
    "flowchart-prime": (9, 10),
    "usecase-bank": (10, 9),
    "class-bank": (7, 10),
    "component-bank": (6, 5),
    "deployment-bank": (4, 3),
    "sequence-withdraw": (3, 11),
    "4p1-library": (34, 50),
}


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="mdjtest_")
    names = [n[:-5] for n in os.listdir(EXAMPLES) if n.endswith(".yaml")]

    for name in sorted(names):
        src = os.path.join(EXAMPLES, name + ".yaml")
        out = os.path.join(tmp, name + ".mdj")

        # --force：回归只写临时文件，不受「StarUML 开着」守卫影响
        code, log = run([os.path.join(SCRIPTS, "mdj.py"), "build", src, "-o", out, "--force"])
        if code != 0:
            fails.append("%s build 失败：\n%s" % (name, log.strip()[-400:]))
            continue

        code, log = run([os.path.join(SCRIPTS, "mdj.py"), "check", out])
        if code != 0:
            fails.append("%s check 失败：\n%s" % (name, log.strip()[-400:]))
            continue

        data = json.load(open(out, encoding="utf-8"))
        diags = []

        def walk(o):
            if isinstance(o, dict):
                if o.get("_type", "").endswith("Diagram"):
                    diags.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for i in o:
                    walk(i)

        walk(data)
        views = [v for d in diags for v in d.get("ownedViews", [])]
        NODE_T = ("FCTerminatorView", "FCProcessView", "FCDecisionView", "FCDataView",
                  "UMLActorView", "UMLUseCaseView", "UMLClassView",
                  "UMLComponentView", "UMLNodeView", "UMLSeqLifelineView")
        EDGE_T = ("FCFlowView", "UMLDependencyView", "UMLAssociationView",
                  "UMLGeneralizationView", "UMLSeqMessageView", "UMLCommunicationPathView")
        nodes = [v for v in views if v["_type"] in NODE_T]
        edges = [v for v in views if v["_type"] in EDGE_T]

        exp_n, exp_e = EXPECT.get(name, (None, None))
        if exp_n is not None and (len(nodes) != exp_n or len(edges) != exp_e):
            fails.append("%s 数量不符：节点 %d（期望 %d）、关系 %d（期望 %d）"
                         % (name, len(nodes), exp_n, len(edges), exp_e))
            continue

        print("[ok] %-18s 节点 %d · 关系 %d · %d 字节"
              % (name, len(nodes), len(edges), os.path.getsize(out)))

    if fails:
        print("\n失败 %d 项：" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1

    print("\n全部通过（%d 个示例）" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
