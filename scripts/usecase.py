"""用例图（UMLUseCaseDiagram）—— STATUS: verified

依据：视图结构抄自本机实训3 的 test3-修正版.mdj（同版本 StarUML 打开过）。

元素：
    kind: actor     参与者，`side: left|right` 决定站在左边还是右边
    kind: usecase   用例（默认），按 4 列网格排布

关系：
    kind: association  参与者与用例的关联（无箭头、实线）
    kind: include      虚线箭头 + «include»（用 UMLDependency 表达，视觉等价）
    kind: extend       虚线箭头 + «extend»
"""
from __future__ import annotations

from common import (FONT, assoc_model, edge_view, hidden_comp, nid, tw,
                    uml_name_comp)

STATUS = "verified"

COLS = 4
UC_W, UC_H = 150, 56
COL_GAP = 46
ROW_GAP = 40
PAD = 40
ACTOR_W, ACTOR_H = 60, 76


def build(spec: dict, project_id: str) -> dict:
    els = spec["elements"]
    rels = spec.get("relations") or []
    by_id = {e["id"]: e for e in els}

    actors = [e for e in els if e.get("kind") == "actor"]
    ucs = [e for e in els if e.get("kind", "usecase") == "usecase"]
    if not ucs:
        raise SystemExit("用例图至少要有一个人 kind: usecase 的元素")

    # 用例布局：给了 at 就用手给的坐标，其余按 4 列网格排
    manual = [u for u in ucs if u.get("at")]
    auto = [u for u in ucs if not u.get("at")]

    for u in manual:
        u["_x"], u["_y"] = int(u["at"][0]), int(u["at"][1])
        u["_w"], u["_h"] = UC_W, UC_H

    rows = (len(auto) + COLS - 1) // COLS if auto else 0
    grid_w = COLS * UC_W + (COLS - 1) * COL_GAP
    left_actors = [a for a in actors if (a.get("side") or "left") == "left"]
    right_actors = [a for a in actors if (a.get("side") or "left") == "right"]
    left_w = ACTOR_W if left_actors else 0

    gx = PAD + left_w + (60 if left_w else 0)
    gy = PAD + 30
    if manual and auto:
        gy = max(gy, max(u["_y"] + u["_h"] for u in manual) + ROW_GAP)

    for i, u in enumerate(auto):
        r, c = divmod(i, COLS)
        u["_x"] = gx + c * (UC_W + COL_GAP)
        u["_y"] = gy + r * (UC_H + ROW_GAP)
        u["_w"], u["_h"] = UC_W, UC_H

    grid_h = rows * UC_H + (rows - 1) * ROW_GAP if rows else UC_H

    top = min([u["_y"] for u in ucs] + [gy])
    bottom = max(u["_y"] + u["_h"] for u in ucs)
    span = max(bottom - top, grid_h)

    def place(grp, x):
        n = len(grp)
        for i, a in enumerate(grp):
            a["_w"], a["_h"] = ACTOR_W, ACTOR_H
            a["_x"] = x
            if a.get("at"):
                a["_x"], a["_y"] = int(a["at"][0]), int(a["at"][1])
                continue
            step = span / max(n, 1)
            a["_y"] = int(top + step * i + step / 2 - ACTOR_H / 2)

    place(left_actors, PAD)
    place(right_actors, (max(u["_x"] + u["_w"] for u in ucs) + 80) if ucs else gx)

    # ---- 模型层 ----
    mg_id = nid()
    dg_id = nid()
    model_ids = {e["id"]: nid() for e in els}
    order = {e["id"]: i for i, e in enumerate(els)}

    owned = {}
    for e in els:
        t = "UMLActor" if e.get("kind") == "actor" else "UMLUseCase"
        owned[e["id"]] = {"_type": t, "_id": model_ids[e["id"]],
                          "_parent": {"$ref": mg_id}, "name": e.get("text", "")}

    # ---- 视图层 ----
    views = []
    view_ids = {}
    for e in els:
        vid = nid()
        view_ids[e["id"]] = vid
        w, h = e["_w"], e["_h"]
        x, y = e["_x"], e["_y"]
        if e.get("kind") == "actor":
            nc = uml_name_comp(vid, model_ids[e["id"]], x, y + h, w, e.get("text", ""))
            comps = [hidden_comp(t, vid, model_ids[e["id"]], x, y) for t in
                     ("UMLAttributeCompartmentView", "UMLOperationCompartmentView",
                      "UMLReceptionCompartmentView", "UMLTemplateParameterCompartmentView")]
            v = {"_type": "UMLActorView", "_id": vid, "_parent": {"$ref": dg_id},
                 "model": {"$ref": model_ids[e["id"]]}, "subViews": [nc] + comps,
                 "font": FONT, "containerChangeable": True,
                 "suppressAttributes": True, "suppressOperations": True,
                 "left": x, "top": y, "width": w, "height": h,
                 "nameCompartment": {"$ref": nc["_id"]}}
            for key, idx in (("attributeCompartment", 1), ("operationCompartment", 2),
                             ("receptionCompartment", 3), ("templateParameterCompartment", 4)):
                v[key] = {"$ref": v["subViews"][idx]["_id"]}
        else:
            nc = uml_name_comp(vid, model_ids[e["id"]], x, y + h / 2 - 12, w, e.get("text", ""))
            # 用例视图必须是 6 个 compartment（含 extensionPoint），并且写死
            # suppressAttributes / suppressOperations：StarUML 每次 update() 都会
            # 用这两个开关重算 compartment 可见性，只写 visible:false 会被覆盖，
            # 椭圆下面就会多出两条没用的横线。
            ep = hidden_comp("UMLExtensionPointCompartmentView", vid, model_ids[e["id"]], x, y)
            v = {"_type": "UMLUseCaseView", "_id": vid, "_parent": {"$ref": dg_id},
                 "model": {"$ref": model_ids[e["id"]]},
                 "subViews": [nc,
                              hidden_comp("UMLAttributeCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLOperationCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLReceptionCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLTemplateParameterCompartmentView", vid, model_ids[e["id"]], x, y),
                              ep],
                 "font": FONT, "containerChangeable": True,
                 "suppressAttributes": True, "suppressOperations": True,
                 "left": x, "top": y, "width": w, "height": h,
                 "nameCompartment": {"$ref": nc["_id"]},
                 "extensionPointCompartment": {"$ref": ep["_id"]}}
            for key, idx in (("attributeCompartment", 1), ("operationCompartment", 2),
                             ("receptionCompartment", 3), ("templateParameterCompartment", 4)):
                v[key] = {"$ref": v["subViews"][idx]["_id"]}
        views.append(v)

    # ---- 关系 ----
    _OBSTACLES.clear()
    for e in els:
        _OBSTACLES.append((e["id"], e["_x"], e["_y"], e["_w"], e["_h"]))

    for i, r in enumerate(rels):
        a, b = by_id.get(r["from"]), by_id.get(r["to"])
        if not a or not b:
            raise SystemExit("relation 引用了不存在的元素：%s -> %s" % (r.get("from"), r.get("to")))
        kind = r.get("kind", "association")

        if kind == "association":
            mid = assoc_model(mg_id, model_ids[a["id"]], model_ids[b["id"]])
            owned["__rel_" + mid["_id"]] = mid
            p = edge_points(a, b, i)
            views.append(edge_view("UMLAssociationView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], p))
        else:
            label = "«include»" if kind == "include" else "«extend»"
            mid = {"_type": "UMLDependency", "_id": nid(), "_parent": {"$ref": mg_id},
                   "source": {"$ref": model_ids[a["id"]]}, "target": {"$ref": model_ids[b["id"]]},
                   "name": label}
            owned["__rel_" + mid["_id"]] = mid
            p = edge_points(a, b, i)
            views.append(edge_view("UMLDependencyView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], p, label))

    diagram = {"_type": "UMLUseCaseDiagram", "_id": dg_id, "_parent": {"$ref": mg_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}

    element_nodes = [owned[e["id"]] for e in els]
    rel_nodes = [v for k, v in owned.items() if k.startswith("__rel_")]

    return {"_type": "UMLModel", "_id": mg_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"],
            "ownedElements": [diagram] + element_nodes + rel_nodes}


_OBSTACLES = []   # [(id, x, y, w, h)]，build() 里填，供连线避让


def _seg_hits(p1, p2, skip) -> bool:
    """线段是否穿过除了 skip 之外的任何一个框。"""
    x1, y1 = p1
    x2, y2 = p2
    for eid, l, t, w, h in _OBSTACLES:
        if eid in skip:
            continue
        if max(x1, x2) < l - 3 or min(x1, x2) > l + w + 3:
            continue
        if max(y1, y2) < t - 3 or min(y1, y2) > t + h + 3:
            continue
        for k in range(1, 24):
            x = x1 + (x2 - x1) * k / 24.0
            y = y1 + (y2 - y1) * k / 24.0
            if l - 3 <= x <= l + w + 3 and t - 3 <= y <= t + h + 3:
                return True
    return False


def _anchor(a, b, as_source: bool):
    """选连接点：按两者的相对位置取「正对」的那条边的中点。

    椭圆的包围盒在中心点上的边中点恰好落在椭圆上，所以连线不会悬空。
    """
    ax, ay = a["_x"] + a["_w"] / 2, a["_y"] + a["_h"] / 2
    bx, by = b["_x"] + b["_w"] / 2, b["_y"] + b["_h"] / 2
    if a.get("kind") == "actor":
        # 参与者站在左边就从身体右侧出发，站右边就从左侧出发
        return (a["_x"] + a["_w"], ay) if bx > ax else (a["_x"], ay)
    dx, dy = bx - ax, by - ay
    if abs(dx) >= abs(dy):
        return (a["_x"] + a["_w"], ay) if dx > 0 else (a["_x"], ay)
    return (a["_x"] + a["_w"] / 2, a["_y"] + a["_h"]) if dy > 0 else (a["_x"] + a["_w"] / 2, a["_y"])


def edge_points(a, b, i: int = 0) -> str:
    """能直连就直连，直连会穿框才折线绕行。

    早先所有线都走「行间通道 + 列间通道」，多条线挤在同一条通道上重叠成一片，
    看着像总线。现在优先直线，折线只作为兜底。
    """
    p1 = _anchor(a, b, True)
    p2 = _anchor(b, a, False)
    skip = {a["id"], b["id"]}

    if not _seg_hits(p1, p2, skip):
        return "%d:%d;%d:%d" % (p1[0], p1[1], p2[0], p2[1])

    # 兜底：走行间通道 + 目标侧边的列间通道
    ax, ay = a["_x"] + a["_w"] / 2, a["_y"] + a["_h"] / 2
    bx, by = b["_x"] + b["_w"] / 2, b["_y"] + b["_h"] / 2
    j = (i % 4 - 1.5) * 7
    down = by > ay

    if a.get("kind") == "actor":
        sx = round(a["_x"] + a["_w"] if bx > ax else a["_x"])
        sy = round(ay)
        gap = round(b["_y"] - ROW_GAP / 2) if down else round(b["_y"] + b["_h"] + ROW_GAP / 2)
        if abs(sy - gap) < 8:
            gap = sy
    else:
        sx = round(ax)
        sy = round(a["_y"] + a["_h"]) if down else round(a["_y"])
        gap = round(a["_y"] + a["_h"] + ROW_GAP / 2) if down else round(a["_y"] - ROW_GAP / 2)

    if bx >= ax:
        corridor = round(b["_x"] - 18)
        edge_x = round(b["_x"])
    else:
        corridor = round(b["_x"] + b["_w"] + 18)
        edge_x = round(b["_x"] + b["_w"])
    ty = round(by)

    return "%d:%d;%d:%d;%d:%d;%d:%d;%d:%d" % (
        sx + j, sy, sx + j, gap + j, corridor, gap + j, corridor, ty, edge_x, ty)
