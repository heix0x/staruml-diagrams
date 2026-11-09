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

    # 用例网格
    rows = (len(ucs) + COLS - 1) // COLS
    grid_w = COLS * UC_W + (COLS - 1) * COL_GAP
    left_actors = [a for a in actors if (a.get("side") or "left") == "left"]
    right_actors = [a for a in actors if (a.get("side") or "left") == "right"]
    left_w = ACTOR_W if left_actors else 0
    right_w = ACTOR_W if right_actors else 0

    gx = PAD + left_w + (60 if left_w else 0)
    gy = PAD + 30

    for i, u in enumerate(ucs):
        r, c = divmod(i, COLS)
        u["_x"] = gx + c * (UC_W + COL_GAP)
        u["_y"] = gy + r * (UC_H + ROW_GAP)
        u["_w"], u["_h"] = UC_W, UC_H

    grid_h = rows * UC_H + (rows - 1) * ROW_GAP

    def place(grp, x):
        n = len(grp)
        for i, a in enumerate(grp):
            a["_w"], a["_h"] = ACTOR_W, ACTOR_H
            a["_x"] = x
            step = grid_h / max(n, 1)
            a["_y"] = int(gy + step * i + step / 2 - ACTOR_H / 2)

    place(left_actors, PAD)
    place(right_actors, gx + grid_w + 60)

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
            v = {"_type": "UMLActorView", "_id": vid, "_parent": {"$ref": dg_id},
                 "model": {"$ref": model_ids[e["id"]]}, "subViews": [nc], "font": FONT,
                 "containerChangeable": True,
                 "left": x, "top": y, "width": w, "height": h,
                 "nameCompartment": {"$ref": nc["_id"]}}
        else:
            nc = uml_name_comp(vid, model_ids[e["id"]], x, y + h / 2 - 12, w, e.get("text", ""))
            v = {"_type": "UMLUseCaseView", "_id": vid, "_parent": {"$ref": dg_id},
                 "model": {"$ref": model_ids[e["id"]]},
                 "subViews": [nc,
                              hidden_comp("UMLAttributeCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLOperationCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLReceptionCompartmentView", vid, model_ids[e["id"]], x, y),
                              hidden_comp("UMLTemplateParameterCompartmentView", vid, model_ids[e["id"]], x, y)],
                 "font": FONT, "containerChangeable": True,
                 "left": x, "top": y, "width": w, "height": h,
                 "nameCompartment": {"$ref": nc["_id"]}}
        views.append(v)

    # ---- 关系 ----
    for r in rels:
        a, b = by_id.get(r["from"]), by_id.get(r["to"])
        if not a or not b:
            raise SystemExit("relation 引用了不存在的元素：%s -> %s" % (r.get("from"), r.get("to")))
        kind = r.get("kind", "association")

        if kind == "association":
            mid = assoc_model(mg_id, model_ids[a["id"]], model_ids[b["id"]])
            owned["__rel_" + mid["_id"]] = mid
            p = edge_points(a, b)
            views.append(edge_view("UMLAssociationView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], p))
        else:
            label = "«include»" if kind == "include" else "«extend»"
            mid = {"_type": "UMLDependency", "_id": nid(), "_parent": {"$ref": mg_id},
                   "source": {"$ref": model_ids[a["id"]]}, "target": {"$ref": model_ids[b["id"]]},
                   "name": label}
            owned["__rel_" + mid["_id"]] = mid
            p = edge_points(a, b)
            views.append(edge_view("UMLDependencyView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], p, label))

    diagram = {"_type": "UMLUseCaseDiagram", "_id": dg_id, "_parent": {"$ref": mg_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}

    element_nodes = [owned[e["id"]] for e in els]
    rel_nodes = [v for k, v in owned.items() if k.startswith("__rel_")]

    return {"_type": "UMLModel", "_id": mg_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"],
            "ownedElements": [diagram] + element_nodes + rel_nodes}


def edge_points(a, b) -> str:
    """参与者→用例：从角色中心水平连到用例边缘；用例之间按相对位置连。"""
    ax, ay = a["_x"] + a["_w"] / 2, a["_y"] + a["_h"] / 2
    bx, by = b["_x"] + b["_w"] / 2, b["_y"] + b["_h"] / 2

    if a.get("kind") == "actor":
        sx = a["_x"] + a["_w"] if bx > ax else a["_x"]
        sy = a["_y"] + a["_h"] / 2
        tx = b["_x"] if bx > ax else b["_x"] + b["_w"]
        ty = b["_y"] + b["_h"] / 2
        return "%d:%d;%d:%d" % (sx, sy, tx, ty)

    if abs(ay - by) < 1:
        sx, tx = (a["_x"] + a["_w"], b["_x"]) if ax < bx else (a["_x"], b["_x"] + b["_w"])
        return "%d:%d;%d:%d" % (sx, ay, tx, by)

    sx = a["_x"] + a["_w"] / 2
    sy = a["_y"] + a["_h"] if ay < by else a["_y"]
    tx = b["_x"] + b["_w"] / 2
    ty = b["_y"] if ay < by else b["_y"] + b["_h"]
    return "%d:%d;%d:%d" % (sx, sy, tx, ty)
