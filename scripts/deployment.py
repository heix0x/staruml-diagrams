"""部署图（UMLDeploymentDiagram）—— STATUS: derived

依据：按 elements.js 的视图类定义推导，**未在 StarUML 中实际打开验证**。

元素：
    kind: node         立方体节点，字段 w / h / at；`children` 里放节点内的构件名
    kind: component    直接放在图上（不归属任何节点）的构件
    kind: actor        参与者，站在节点外面
关系：
    kind: dependency      虚线箭头（谁连谁）
    kind: communication   节点之间的实线通信路径
"""
from __future__ import annotations

from common import (FONT, auto_sides, box, edge_view, hidden_comp, nid, tw,
                    typed_edge, uml_name_comp)

STATUS = "derived"

PAD = 40


def _comp_view(dg_id, model_id, x, y, w, h, text):
    vid = nid()
    nc = uml_name_comp(vid, model_id, x, y + 4, w, text)
    v = {"_type": "UMLComponentView", "_id": vid, "_parent": {"$ref": dg_id},
         "model": {"$ref": model_id},
         "subViews": [nc,
                      hidden_comp("UMLAttributeCompartmentView", vid, model_id, x, y),
                      hidden_comp("UMLOperationCompartmentView", vid, model_id, x, y),
                      hidden_comp("UMLReceptionCompartmentView", vid, model_id, x, y),
                      hidden_comp("UMLTemplateParameterCompartmentView", vid, model_id, x, y)],
         "font": FONT, "containerChangeable": True,
         "left": x, "top": y, "width": w, "height": h,
         "nameCompartment": {"$ref": nc["_id"]}}
    for i, key in enumerate(("attributeCompartment", "operationCompartment",
                             "receptionCompartment", "templateParameterCompartment"), 1):
        v[key] = {"$ref": v["subViews"][i]["_id"]}
    return v


def build(spec: dict, project_id: str) -> dict:
    els = spec["elements"]
    rels = spec.get("relations") or []
    by_id = {e["id"]: e for e in els}

    mg_id = nid()
    dg_id = nid()
    mid = {e["id"]: nid() for e in els}
    model_of = {e["id"]: ("UMLNode" if e.get("kind") == "node" else
                          "UMLActor" if e.get("kind") == "actor" else "UMLComponent")
                for e in els}

    views, vids = [], {}
    inner_nodes = []

    for e in els:
        kind = e.get("kind", "node")
        x, y = int(e.get("at", [PAD, PAD])[0]), int(e.get("at", [PAD, PAD])[1])
        vid = nid()
        vids[e["id"]] = vid
        text = e.get("text") or e["id"]

        if kind == "node":
            w = int(e.get("w") or 230)
            h = int(e.get("h") or 300)
            nc = uml_name_comp(vid, mid[e["id"]], x, y + 4, w, text)
            v = {"_type": "UMLNodeView", "_id": vid, "_parent": {"$ref": dg_id},
                 "model": {"$ref": mid[e["id"]]},
                 "subViews": [nc,
                              hidden_comp("UMLAttributeCompartmentView", vid, mid[e["id"]], x, y),
                              hidden_comp("UMLOperationCompartmentView", vid, mid[e["id"]], x, y),
                              hidden_comp("UMLReceptionCompartmentView", vid, mid[e["id"]], x, y),
                              hidden_comp("UMLTemplateParameterCompartmentView", vid, mid[e["id"]], x, y)],
                 "font": FONT, "containerChangeable": True, "containerCollapse": False,
                 "left": x, "top": y, "width": w, "height": h,
                 "nameCompartment": {"$ref": nc["_id"]}}
            for i, key in enumerate(("attributeCompartment", "operationCompartment",
                                     "receptionCompartment", "templateParameterCompartment"), 1):
                v[key] = {"$ref": v["subViews"][i]["_id"]}
            views.append(v)

            # 节点内的构件：模型挂在节点模型下，视图挂在节点视图下
            for j, cname in enumerate(e.get("children") or []):
                cmid = nid()
                inner_nodes.append({"_type": "UMLComponent", "_id": cmid,
                                    "_parent": {"$ref": mid[e["id"]]}, "name": cname})
                cw, ch = 120, 60
                cv = _comp_view(vid, cmid, x + 30, y + 50 + j * (ch + 30), cw, ch, cname)
                v["subViews"].append(cv)

        elif kind == "actor":
            w, h = 60, 76
            nc = uml_name_comp(vid, mid[e["id"]], x, y + h, w, text)
            views.append({"_type": "UMLActorView", "_id": vid, "_parent": {"$ref": dg_id},
                          "model": {"$ref": mid[e["id"]]}, "subViews": [nc], "font": FONT,
                          "containerChangeable": True,
                          "left": x, "top": y, "width": w, "height": h,
                          "nameCompartment": {"$ref": nc["_id"]}})

        else:
            w = int(e.get("w") or max(140, tw(text) + 50))
            h = int(e.get("h") or 70)
            views.append(_comp_view(dg_id, mid[e["id"]], x, y, w, h, text))

    rel_nodes = []
    for r in rels:
        a, b = by_id.get(r["from"]), by_id.get(r["to"])
        if not a or not b:
            raise SystemExit("relation 引用了不存在的元素：%s -> %s" % (r.get("from"), r.get("to")))
        kind = r.get("kind", "dependency")
        mtype = "UMLCommunicationPath" if kind == "communication" else "UMLDependency"
        vtype = mtype + "View"
        m = typed_edge(mtype, mg_id, mid[a["id"]], mid[b["id"]], r.get("label") or "")
        rel_nodes.append(m)
        va = next(v for v in views if v["_id"] == vids[a["id"]])
        vb = next(v for v in views if v["_id"] == vids[b["id"]])
        sa, sb = auto_sides(va, vb)
        views.append(edge_view(vtype, dg_id, m["_id"], vids[a["id"]], vids[b["id"]],
                               box(va, vb, sa, sb), r.get("label") or ""))

    diagram = {"_type": "UMLDeploymentDiagram", "_id": dg_id, "_parent": {"$ref": mg_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}

    element_nodes = []
    for e in els:
        node = {"_type": model_of[e["id"]], "_id": mid[e["id"]], "_parent": {"$ref": mg_id},
                "name": e.get("text") or e["id"]}
        if e.get("children"):
            node["ownedElements"] = []
        element_nodes.append(node)
    element_nodes.extend(inner_nodes)

    return {"_type": "UMLModel", "_id": mg_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"],
            "ownedElements": [diagram] + element_nodes + rel_nodes}
