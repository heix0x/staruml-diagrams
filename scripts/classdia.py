"""类图（UMLClassDiagram）—— STATUS: verified

依据：视图结构抄自本机实训1 的 test1-26-10-11.mdj（7 个类 + 22 属性 + 12 关联，
同版本 StarUML 打开过）。

元素：
    kind: class
    attributes: ["-私有属性", "+公有属性"]   首字符决定可见性，默认为 -
    operations: ["+方法()"]
    at: [x, y]                              可选，不给就走自动两列网格
    stereotype: 可选

关系：
    kind: association    实线，可带 label；aggregation: 1/2 端聚合，-1/-2 组合
    kind: generalization 实线空心三角，从子类指向父类
"""
from __future__ import annotations

from common import (FONT, LINE_H, assoc_model, auto_sides, box, edge_view,
                    hidden_comp, nid, tw, uml_name_comp)

STATUS = "verified"

MIN_W = 110
PAD = 40
COL_GAP = 90
ROW_GAP = 60


def _dims(el):
    attrs = el.get("attributes") or []
    ops = el.get("operations") or []
    name = el.get("text") or el.get("id")
    widest = tw(name)
    for a in attrs:
        widest = max(widest, tw(a))
    for o in ops:
        widest = max(widest, tw(o))
    w = int(max(MIN_W, widest + 24))
    h = 5 + 25 + (len(attrs) * LINE_H + 8) + (len(ops) * LINE_H + 8)
    return w, h


def build(spec: dict, project_id: str) -> dict:
    els = [e for e in spec["elements"] if e.get("kind", "class") == "class"]
    rels = spec.get("relations") or []
    by_id = {e["id"]: e for e in els}

    for e in els:
        e["_w"], e["_h"] = _dims(e)

    # 布局：有 at 用 at，没有的排两列网格
    auto = [e for e in els if not e.get("at")]
    for e in els:
        if e.get("at"):
            e["_x"], e["_y"] = int(e["at"][0]), int(e["at"][1])
    if auto:
        base_y = max([e["_y"] + e["_h"] for e in els if e.get("at")] + [PAD])
        base_y += ROW_GAP if any(e.get("at") for e in els) else 0
        col_w = max(e["_w"] for e in auto)
        for i, e in enumerate(auto):
            r, c = divmod(i, 2)
            e["_x"] = PAD + c * (col_w + COL_GAP)
            e["_y"] = base_y + r * (e["_h"] + 30)

    mg_id = nid()
    dg_id = nid()
    model_ids = {e["id"]: nid() for e in els}

    views = []
    view_ids = {}
    for e in els:
        mid = model_ids[e["id"]]
        vid = nid()
        view_ids[e["id"]] = vid
        x, y, w, h = e["_x"], e["_y"], e["_w"], e["_h"]
        attrs = e.get("attributes") or []
        ops = e.get("operations") or []
        ah = len(attrs) * LINE_H + 8
        oh = len(ops) * LINE_H + 8

        nc = uml_name_comp(vid, mid, x, y + 5, w, e.get("text") or e["id"])

        acomp_id = nid()
        asubs = []
        for i, a in enumerate(attrs):
            pub = str(a).startswith("+")
            txt = ("+" if pub else "-") + str(a).lstrip("+-")
            am = {"_type": "UMLAttribute", "_id": nid(), "_parent": {"$ref": mid},
                  "name": str(a).lstrip("+-"), "visibility": "public" if pub else "private"}
            e.setdefault("_attr_models", []).append(am)
            asubs.append({"_type": "UMLAttributeView", "_id": nid(),
                          "_parent": {"$ref": acomp_id}, "model": {"$ref": am["_id"]},
                          "font": FONT, "left": round(x + 5, 2), "top": round(y + 30 + i * LINE_H, 2),
                          "width": round(w - 10, 2), "height": 13, "text": txt,
                          "horizontalAlignment": 0})
        acomp = {"_type": "UMLAttributeCompartmentView", "_id": acomp_id,
                 "_parent": {"$ref": vid}, "model": {"$ref": mid}, "subViews": asubs,
                 "font": FONT, "left": x, "top": y + 30, "width": w, "height": ah}

        ocomp_id = nid()
        osubs = []
        for i, o in enumerate(ops):
            txt = str(o) if str(o).startswith(("+", "-", "#", "~")) else "+" + str(o)
            om = {"_type": "UMLOperation", "_id": nid(), "_parent": {"$ref": mid},
                  "name": str(o).lstrip("+-#~"), "visibility": "public"}
            e.setdefault("_op_models", []).append(om)
            osubs.append({"_type": "UMLOperationView", "_id": nid(),
                          "_parent": {"$ref": ocomp_id}, "model": {"$ref": om["_id"]},
                          "font": FONT, "left": round(x + 5, 2),
                          "top": round(y + 30 + ah + i * LINE_H, 2),
                          "width": round(w - 10, 2), "height": 13, "text": txt,
                          "horizontalAlignment": 0})
        ocomp = {"_type": "UMLOperationCompartmentView", "_id": ocomp_id,
                 "_parent": {"$ref": vid}, "model": {"$ref": mid}, "subViews": osubs,
                 "font": FONT, "left": x, "top": y + 30 + ah, "width": w, "height": oh}

        views.append({
            "_type": "UMLClassView", "_id": vid, "_parent": {"$ref": dg_id},
            "model": {"$ref": mid},
            "subViews": [nc, acomp, ocomp,
                         hidden_comp("UMLReceptionCompartmentView", vid, mid, x, y),
                         hidden_comp("UMLTemplateParameterCompartmentView", vid, mid, x, y)],
            "font": FONT, "containerChangeable": True,
            "left": x, "top": y, "width": w, "height": h,
            "nameCompartment": {"$ref": nc["_id"]},
            "attributeCompartment": {"$ref": acomp_id},
            "operationCompartment": {"$ref": ocomp_id},
        })
        v = views[-1]
        v["receptionCompartment"] = {"$ref": v["subViews"][3]["_id"]}
        v["templateParameterCompartment"] = {"$ref": v["subViews"][4]["_id"]}

    # ---- 关系 ----
    rel_nodes = []
    for r in rels:
        a, b = by_id.get(r["from"]), by_id.get(r["to"])
        if not a or not b:
            raise SystemExit("relation 引用了不存在的类：%s -> %s" % (r.get("from"), r.get("to")))
        kind = r.get("kind", "association")
        va = views[[e["id"] for e in els].index(a["id"])]
        vb = views[[e["id"] for e in els].index(b["id"])]
        sa, sb = auto_sides(va, vb)
        pts = box(va, vb, sa, sb)

        if kind == "generalization":
            mid = {"_type": "UMLGeneralization", "_id": nid(), "_parent": {"$ref": mg_id},
                   "source": {"$ref": model_ids[a["id"]]},
                   "target": {"$ref": model_ids[b["id"]]}}
            rel_nodes.append(mid)
            views.append(edge_view("UMLGeneralizationView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], pts))
        else:
            mid = assoc_model(mg_id, model_ids[a["id"]], model_ids[b["id"]],
                              r.get("label") or "", int(r.get("aggregation") or 0))
            rel_nodes.append(mid)
            views.append(edge_view("UMLAssociationView", dg_id, mid["_id"],
                                   view_ids[a["id"]], view_ids[b["id"]], pts,
                                   r.get("label") or "", distance=18))

    diagram = {"_type": "UMLClassDiagram", "_id": dg_id, "_parent": {"$ref": mg_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}

    element_nodes = []
    for e in els:
        node = {"_type": "UMLClass", "_id": model_ids[e["id"]], "_parent": {"$ref": mg_id},
                "name": e.get("text") or e["id"],
                "attributes": e.get("_attr_models") or [],
                "operations": e.get("_op_models") or []}
        if e.get("stereotype"):
            node["stereotype"] = e["stereotype"]
        element_nodes.append(node)

    return {"_type": "UMLModel", "_id": mg_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"],
            "ownedElements": [diagram] + element_nodes + rel_nodes}
