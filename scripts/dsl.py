"""描述文件解析与校验。

描述文件支持 YAML 和 JSON。结构：

    diagram:
      kind: flowchart          # 必填，决定用哪个图模块
      name: 素数判断流程图       # 必填，图名
    module: 流程图              # 可选，工程树里的模块名，默认取 diagram.name
    elements: [...]            # 必填，各图模块自己解释
    relations: [...]           # 可选

校验只查「结构与图无关的硬字段」，元素内部字段由图模块自己查——
因为不同图的元素字段差别太大，放在这里会变成一坨 if。
"""
from __future__ import annotations

import io
import json

KINDS = ("flowchart", "usecase", "class", "component", "deployment", "sequence")


def load(path: str) -> dict:
    txt = io.open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        return json.loads(txt)
    try:
        import yaml
    except ImportError:
        raise SystemExit(
            "需要 PyYAML 才能读 .yaml 描述文件。装：pip install pyyaml\n"
            "或者把描述文件改存成 .json。"
        )
    return yaml.safe_load(txt)


def check(spec: dict) -> list[str]:
    """返回错误列表，空表示通过。"""
    errs = []
    if not isinstance(spec, dict):
        return ["描述文件顶层必须是对象"]

    d = spec.get("diagram")
    if not isinstance(d, dict):
        errs.append("缺少 diagram 段")
    else:
        kind = d.get("kind")
        if not kind:
            errs.append("diagram.kind 必填，可选：" + " / ".join(KINDS))
        elif kind not in KINDS:
            errs.append("diagram.kind 不认识：%s，可选：%s" % (kind, " / ".join(KINDS)))
        if not d.get("name"):
            errs.append("diagram.name 必填（会作为图名显示在 StarUML 里）")

    if not spec.get("elements"):
        errs.append("elements 不能为空")

    return errs


def module_name(spec: dict) -> str:
    return spec.get("module") or spec["diagram"]["name"]


def index_elements(spec: dict, key: str = "id") -> dict:
    """把 elements 变成 id -> element 的字典，同时检查 id 重复与缺失。"""
    out = {}
    for i, el in enumerate(spec.get("elements") or []):
        if not isinstance(el, dict):
            raise SystemExit("elements[%d] 不是对象" % i)
        eid = el.get(key)
        if not eid:
            raise SystemExit("elements[%d] 缺少 %s" % (i, key))
        if eid in out:
            raise SystemExit("elements 里 %s 重复：%s" % (key, eid))
        out[eid] = el
    return out
