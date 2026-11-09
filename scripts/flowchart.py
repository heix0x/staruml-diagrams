"""流程图（Flowchart 扩展）—— STATUS: verified

依据：实训4 的两张流程图已在本机 StarUML 5.0.2 打开确认。
元素结构取自官方 FlowchartExample.mdj 与本机实际产物。

布局规则：
1. 忽略回边算 rank（最长路径），同 rank 同一行。
2. 列分配走 BFS：能走到「结束」节点的那条出边留在本列，其余开新列；
   标了「否 / else」的分支优先当主干，符合 if-else 的常见画法。
3. 连线一律正交折线；回边从最左绕过，垂直进入判断节点顶部（单入口）。
"""
from __future__ import annotations

from common import (FONT, LINE_H, edge_view, nid, tw, typed_edge)

STATUS = "verified"

GAP_Y = 44
GAP_C = 70
PAD = 40

KIND = {
    "terminator": ("FCTerminator", "FCTerminatorView", 100, 44),
    "process": ("FCProcess", "FCProcessView", 170, 50),
    "decision": ("FCDecision", "FCDecisionView", 180, 90),
    "data": ("FCData", "FCDataView", 180, 50),
}

NO_LABELS = ("否", "no", "n", "false", "else")


def _size(el):
    kind = el.get("kind", "process")
    if kind not in KIND:
        raise SystemExit("不认识的节点类型 %r，可选：%s" % (kind, " / ".join(KIND)))
    _, _, base_w, base_h = KIND[kind]
    text = el.get("text", "")
    if kind == "decision":
        w = max(base_w, tw(text) * 2 + 50)
    elif kind == "terminator":
        w = max(base_w, tw(text) + 46)
    else:
        w = max(base_w, tw(text) + 50)
    return int(w), base_h


def build(spec: dict, project_id: str) -> dict:
    els = spec["elements"]
    rels = spec.get("relations") or []
    by_id = {e["id"]: e for e in els}

    for e in els:
        e["_w"], e["_h"] = _size(e)

    # 只用于布局的正向边
    back_ids = {r["to"] for r in rels if r.get("back")}
    fwd = [r for r in rels if not r.get("back")]

    out_map = {e["id"]: [] for e in els}
    for r in fwd:
        if r["from"] not in by_id or r["to"] not in by_id:
            raise SystemExit("relation 引用了不存在的节点：%s -> %s" % (r["from"], r["to"]))
        out_map[r["from"]].append(r)

    # 能走到结束节点的集合
    terms = [e for e in els if e.get("kind") == "terminator"]
    end = next((e for e in terms if "结束" in e.get("text", "")), None) or \
        (terms[-1] if terms else els[-1])
    reach = {end["id"]}
    changed = True
    while changed:
        changed = False
        for r in fwd:
            if r["to"] in reach and r["from"] not in reach:
                reach.add(r["from"])
                changed = True

    def pri(r):
        lab = (r.get("label") or "").strip().lower()
        if lab in NO_LABELS and r["to"] in reach:
            return 0
        return 1 if r["to"] in reach else 2

    # 列分配
    start = next((e for e in els if e.get("kind") == "terminator"), els[0])
    col = {start["id"]: 0}
    queue = [start["id"]]
    while queue:
        cur = queue.pop(0)
        outs = sorted(out_map.get(cur, []), key=pri)
        for i, r in enumerate(outs):
            if r["to"] in col:
                continue
            c = col[cur]
            col[r["to"]] = c if i == 0 else c + (-1 if c <= 0 else 1)
            queue.append(r["to"])
    for e in els:
        col.setdefault(e["id"], 0)

    # rank
    rank = {e["id"]: 0 for e in els}
    for _ in range(len(els) + 1):
        changed = False
        for r in fwd:
            v = rank[r["from"]] + 1
            if v > rank[r["to"]]:
                rank[r["to"]] = v
                changed = True
        if not changed:
            break

    # 列宽与列中心
    cols = sorted(set(col.values()))
    col_w = {}
    for c in cols:
        col_w[c] = max(e["_w"] for e in els if col[e["id"]] == c)
    cursor = PAD
    col_x = {}
    for c in cols:
        col_x[c] = cursor + col_w[c] / 2
        cursor += col_w[c] + GAP_C
    total_w = cursor - GAP_C

    # 纵向
    max_rank = max(rank.values(), default=0)
    rows = [[] for _ in range(max_rank + 1)]
    for e in els:
        rows[rank[e["id"]]].append(e)
    y = PAD
    for row in rows:
        rh = max((e["_h"] for e in row), default=0)
        for e in row:
            e["_x"] = int(col_x[col[e["id"]]] - e["_w"] / 2)
            e["_y"] = int(y + (rh - e["_h"]) / 2)
        y += rh + GAP_Y
    total_h = y

    # ---- 组装模型层 ----
    fc_id = nid()
    dg_id = nid()
    model_ids, views = {}, []

    for e in els:
        mid = nid()
        model_ids[e["id"]] = mid
        m = {"_type": KIND[e.get("kind", "process")][0], "_id": mid,
             "_parent": {"$ref": fc_id}, "name": e.get("text", ""), "ownedElements": []}
        e["_mid"] = mid
        views.append(None)  # 占位，稍后按顺序填

    # ---- 连线模型必须挂在源节点下 ----
    flow_models = []
    for r in rels:
        fid = nid()
        fm = {"_type": "FCFlow", "_id": fid, "_parent": {"$ref": model_ids[r["from"]]},
              "source": {"$ref": model_ids[r["from"]]}, "target": {"$ref": model_ids[r["to"]]}}
        if r.get("label"):
            fm["name"] = r["label"]
        flow_models.append((fid, r))

    # ---- 视图层 ----
    views = []
    view_ids = {}
    for e in els:
        mid = model_ids[e["id"]]
        vid = nid()
        view_ids[e["id"]] = vid
        lx = e["_x"] + 10
        ly = e["_y"] + (e["_h"] - 17) / 2
        lw = e["_w"] - 20
        if e.get("kind") == "decision":
            lx = e["_x"] + e["_w"] / 4
            ly = e["_y"] + e["_h"] / 4
            lw = e["_w"] / 2
        elif e.get("kind") == "data":
            g = int(e["_w"] / 6)
            lx = e["_x"] + 10 + g
            lw = e["_w"] - 20 - 2 * g
        lid = nid()
        views.append({
            "_type": KIND[e.get("kind", "process")][1], "_id": vid,
            "_parent": {"$ref": dg_id}, "model": {"$ref": mid},
            "subViews": [{"_type": "LabelView", "_id": lid, "_parent": {"$ref": vid},
                          "font": FONT, "left": round(lx, 2), "top": round(ly, 2),
                          "width": round(lw, 2), "height": 17,
                          "text": e.get("text", ""), "wordWrap": False}],
            "font": FONT,
            "left": e["_x"], "top": e["_y"], "width": e["_w"], "height": e["_h"],
            "wordWrap": False, "nameLabel": {"$ref": lid},
        })

    # ---- 连线视图 ----
    min_x = min(e["_x"] for e in els)
    for fid, r in flow_models:
        a, b = by_id[r["from"]], by_id[r["to"]]
        ac, bc = col[a["id"]], col[b["id"]]
        if r.get("back"):
            xr = max(8, int(min_x - 34))
            ayc = int(a["_y"] + a["_h"] / 2)
            bx = int(b["_x"] + b["_w"] / 2)
            pts = "%d:%d;%d:%d;%d:%d;%d:%d;%d:%d" % (
                a["_x"], ayc, xr, ayc, xr, b["_y"] - 26, bx, b["_y"] - 26, bx, b["_y"])
        elif ac == bc:
            cx = int(a["_x"] + a["_w"] / 2)
            pts = "%d:%d;%d:%d" % (cx, a["_y"] + a["_h"], cx, b["_y"])
        else:
            to_left = bc < ac
            if a.get("kind") == "decision":
                sx = a["_x"] if to_left else a["_x"] + a["_w"]
                sy = int(a["_y"] + a["_h"] / 2)
                tx = int(b["_x"] + b["_w"] / 2)
                pts = "%d:%d;%d:%d;%d:%d" % (sx, sy, tx, sy, tx, b["_y"])
            else:
                sx = int(a["_x"] + a["_w"] / 2)
                sy = a["_y"] + a["_h"]
                tx = int(b["_x"] + b["_w"] / 2)
                my = int(sy + (b["_y"] - sy) / 2)
                pts = "%d:%d;%d:%d;%d:%d;%d:%d" % (sx, sy, sx, my, tx, my, tx, b["_y"])

        views.append(edge_view("FCFlowView", dg_id, fid,
                               view_ids[r["from"]], view_ids[r["to"]], pts,
                               r.get("label") or "", line_style=2))
        views[-1]["fillColor"] = "#ffffd8"

    # ---- 模型层组装 ----
    diagram = {"_type": "FCFlowchartDiagram", "_id": dg_id, "_parent": {"$ref": fc_id},
               "name": spec["diagram"]["name"], "defaultDiagram": True, "ownedViews": views}
    owned = [diagram]
    for e in els:
        m = {"_type": KIND[e.get("kind", "process")][0], "_id": model_ids[e["id"]],
             "_parent": {"$ref": fc_id}, "name": e.get("text", ""), "ownedElements": []}
        for fid, r in flow_models:
            if r["from"] == e["id"]:
                fm = {"_type": "FCFlow", "_id": fid, "_parent": {"$ref": model_ids[e["id"]]},
                      "source": {"$ref": model_ids[e["id"]]},
                      "target": {"$ref": model_ids[r["to"]]}}
                if r.get("label"):
                    fm["name"] = r["label"]
                m["ownedElements"].append(fm)
        owned.append(m)

    return {"_type": "FCFlowchart", "_id": fc_id, "_parent": {"$ref": project_id},
            "name": spec.get("module") or spec["diagram"]["name"], "ownedElements": owned}
