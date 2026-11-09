"""构件图（UMLComponentDiagram）—— STATUS: derived

依据：按 app.asar 内 extensions/essential/uml/elements.js 的视图类定义推导，
**未在 StarUML 中实际打开验证**。第一次使用必须让用户开图确认。

元素：
    kind: component，at 可选（不给就按两列网格排）
关系：
    kind: dependency   虚线箭头，从使用方指向被依赖方
"""
from __future__ import annotations

from common import (FONT, auto_sides, box, edge_view, hidden_comp, nid, tw,
                    typed_edge, uml_name_comp)

STATUS = "derived"

PAD = 40
COL_GAP = 70
ROW_GAP = 60
MIN_W, H = 160, 80


def build(spec: dict, project_id: str) -> dict:
    els = [e for e in spec["elements"] if e.get("kind", "component") == "component"]
    rels = spec.get("relations") or []
    if not els:
        raise SystemExit("构件图至少要有一个 kind: component 的元素")

    for e in els:
        e["_w"] = int(max(MIN_W, tw(e.get("text") or e["id"]) + 50))
        e["_h"] = H
    for e in els:
        if e.get("at"):
            e["_x"], e["_y"] = int(e["at"][0]), int(e["at"][1])

    auto = [e for e in els if not e.get("at")]
    if auto:
        base = max([e["_y"] + e["_h"] for e in els if e.get("at")] + [PAD - ROW_GAP])
        base += ROW_GAP
        colw = max(e["_w"] for e in auto)
        for i, e in enumerate(auto):
            r, c = divmod(i, 2)
            e["_x"] = PAD + c * (colw + COL_GAP)
            e["_y"] = base + r * (H + 40)

    mg_id = nid()
    dg_id = nid()
    mid = {e["id"]: nid() for e in els}

    views, vids = [], {}
    for e in els:
        vid = nid()
        vids[e["id"]] = vid
        x, y, w, h = e["_x"], e["_y"], e["_w"], e["_h"]
        nc = uml_name_comp(vid, mid[e["id"]], x, y + 4, w, e.get("text") or e["id"])
        views.append({
            "_type": "UMLComponentView", "_id": vid, "_parent": {"$ref": dg_id},
            "model": {"$ref": mid[e["id"]]},
            "subViews": [nc,
                         hidden_comp("UMLAttributeCompartmentView", vid, mid[e["id"]], x, y),
                         hidden_comp("UMLOperationCompartmentView", vid, mid[e["id"]], x, y),
                         hidden_comp("UMLReceptionCompartmentView", vid, mid[e["id"]], x, y),
                         hidden_comp("UMLTemplateParameterCompartmentView", vid, mid[e["id"]], x, y)],
            "font": FONT, "containerChangeable": True, "containerCollapse": False,
            "left": x, "top": y, "width": w, "height": h,
            "nameCompartment": {"$ref": nc["_id"]},
        })
        v = views[-1]
        v["attributeCompartment"] = {"$ref": v["subViews"][1]["_id"]}
        v["operationCompartment"] = {"$ref": v["subViews"][2]["_id"]}
        v["receptionCompartment"] = {"$ref": v["subViews"][3]["_id"]}
        v["templateParameterCompartment"] = {"$ref": v["subViews"][4]["_id"]}

    rel_nodes = []
    by_id = {e["id"]: e for e in els}
    for r in rels:
        a, b = by_id.get(r["from"]), by_id.get(r["to"])
        if not a or not b:
            raise SystemExit("relation 引用了不存在的构件：%s -> %s" % (r.get("from"), r.get("to")))
        m = typed_edge("UMLDependency", mg_id, mid[a["id"]], mid[b["id"]],
                       r.get("label") or "")
        rel_nodes.append(m)
        va = next(v for v in views if v["_id"] == vids[a["id"]])
        vb = next(v for v in views if v["_id"] == vids[b["id"]])
        sa, sb = auto_sides(va, vb)
        views.append(edge_view("UMLDependencyView", dg_id, m["_id"],
                               vids[a["id"]], vids[b["id"]], box(va, vb, sa, sb),
                               r.get("label") or ""))

    diagram = {"_type": "UMLComponentDiagram", "_id": dg_id, "_parent": {"$ref": mg_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}

    element_nodes = [{"_type": "UMLComponent", "_id": mid[e["id"]], "_parent": {"$ref": mg_id},
                      "name": e.get("text") or e["id"]} for e in els]

    return {"_type": "UMLModel", "_id": mg_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"],
            "ownedElements": [diagram] + element_nodes + rel_nodes}
