"""描述文件解析与校验。

描述文件支持 YAML 和 JSON，两种写法：

单图（旧格式，一个文件一张图）：

    diagram:
      kind: flowchart          # 必填，决定用哪个图模块
      name: 素数判断流程图       # 必填，图名
    module: 流程图              # 可选，工程树里的模块名，默认取 diagram.name
    elements: [...]            # 必填，各图模块自己解释
    relations: [...]           # 可选

多图（一个文件出一个工程，里面多张图）：

    project: 校园图书借阅系统     # 工程名
    views:
      - diagram: {kind: usecase, name: 场景视图, module: 场景视图}
        elements: [...]
        relations: [...]
      - diagram: {kind: class, name: 逻辑视图}

两种写法都先经 `normalize()` 归一成 {project, views}，下游只认这一种形状。

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


def normalize(raw: dict) -> dict:
    """把单图 / 多图两种写法归一成 {"project": 工程名, "views": [图规格, ...]}。

    多图时每张图的规格形状与单图完全一致（diagram / elements / relations），
    所以各图模块拿到的入参不变，不用改 build()。
    """
    if not isinstance(raw, dict):
        return {"project": "", "views": []}

    views = raw.get("views")
    if isinstance(views, list):
        first = views[0] if views and isinstance(views[0], dict) else {}
        return {"project": raw.get("project") or (first.get("diagram") or {}).get("name", ""),
                "views": views}

    d = raw.get("diagram")
    name = d.get("name", "") if isinstance(d, dict) else ""
    return {"project": raw.get("project") or name, "views": [raw]}


def check(raw: dict) -> list[str]:
    """返回错误列表，空表示通过。单图与多图都走这里。"""
    if not isinstance(raw, dict):
        return ["描述文件顶层必须是对象"]

    errs = []
    if raw.get("views") is not None and not isinstance(raw.get("views"), list):
        return ["views 必须是列表"]

    bundle = normalize(raw)
    multi = isinstance(raw.get("views"), list)

    if not bundle["views"]:
        return ["没有任何图：需要一个 diagram 段，或用 views 列出多张图"]
    if not bundle["project"]:
        errs.append("工程名为空：多图时请写 project: <工程名>")

    seen_name = {}
    for i, v in enumerate(bundle["views"]):
        tag = "views[%d]" % i if multi else "描述文件"
        if not isinstance(v, dict):
            errs.append("%s 不是对象" % tag)
            continue

        d = v.get("diagram")
        if not isinstance(d, dict):
            errs.append("%s 缺少 diagram 段" % tag)
        else:
            kind = d.get("kind")
            if not kind:
                errs.append("%s.diagram.kind 必填，可选：%s" % (tag, " / ".join(KINDS)))
            elif kind not in KINDS:
                errs.append("%s.diagram.kind 不认识：%s，可选：%s"
                            % (tag, kind, " / ".join(KINDS)))
            name = d.get("name")
            if not name:
                errs.append("%s.diagram.name 必填（会作为图名显示在 StarUML 里）" % tag)
            elif name in seen_name:
                errs.append("图名重复：%s（views[%d] 与 views[%d] 同名，StarUML 里分不清）"
                            % (name, seen_name[name], i))
            else:
                seen_name[name] = i

        if not v.get("elements"):
            errs.append("%s.elements 不能为空" % tag)

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
