"""mdj 公共构件：id 生成、坐标估算、LabelView、边视图、结构自检。

设计约定（改代码前先读这一段）：

1. StarUML 的 mdj 是纯 JSON，视图坐标是**画布绝对坐标**，不认相对坐标。
2. 所有对象都有 `_id`（24 字符 base64），所有引用写成 `{"$ref": id}`，
   父指针字段名是 `_parent`，不是 `parent`。
3. `_id` 里不能出现 `/`（官方样例的字符集里没有它）。
4. 一个 Diagram 的 `ownedViews` 决定绘制顺序，**后出现的画在上层**。
5. LabelView 的坐标也是绝对坐标，不是相对父视图的偏移。

用法：

    from common import nid, tw, label, uml_name_comp, hidden_comp, edge_view, selfcheck, dump
"""
from __future__ import annotations

import base64
import io
import json

FONT = "Arial;13;0"
LINE_H = 15


def nid() -> str:
    """24 字符 base64 id，保证不含 '/'。"""
    while True:
        s = base64.b64encode(__import__("os").urandom(16)).decode()
        if "/" not in s:
            return s


def tw(text: str) -> float:
    """估算文本像素宽度：中日韩字符 13px，西文 7.3px。"""
    total = 0.0
    for ch in str(text):
        total += 13.0 if ord(ch) > 0x2E80 else 7.3
    return total


def label(pid: str, text: str, x: float, y: float, w: float, h: float = 13,
          font: str = FONT, align: int = 2, visible=None, underline=None) -> dict:
    """一个 LabelView。align: 0 左 / 1 右 / 2 中。"""
    d = {"_type": "LabelView", "_id": nid(), "_parent": {"$ref": pid},
         "font": font, "left": round(x, 2), "top": round(y, 2),
         "width": round(w, 2), "height": h, "text": text,
         "horizontalAlignment": align}
    if visible is False:
        d["visible"] = False
    if underline is not None:
        d["underline"] = underline
    return d


def uml_name_comp(view_id: str, model_id: str, x: float, y: float, w: float,
                  text: str, h: float = 25, name_font: str = "Arial;13;1") -> dict:
    """UML 类/用例/构件/节点共用的名称栏：一个 compartment 包 4 个 LabelView。

    顺序固定为 [stereotypeLabel, nameLabel, namespaceLabel, propertyLabel]，
    后三个默认隐藏。
    """
    cid = nid()
    s1 = {"_type": "LabelView", "_id": nid(), "_parent": {"$ref": cid}, "visible": False,
          "font": FONT, "left": round(x, 2), "top": round(y, 2), "height": 13}
    s2 = {"_type": "LabelView", "_id": nid(), "_parent": {"$ref": cid}, "font": name_font,
          "left": round(x + 5, 2), "top": round(y + 6, 2), "width": round(w - 10, 2),
          "height": 13, "text": text, "horizontalAlignment": 2}
    s3 = {"_type": "LabelView", "_id": nid(), "_parent": {"$ref": cid}, "visible": False,
          "font": FONT, "left": round(x, 2), "top": round(y, 2), "width": 120, "height": 13}
    s4 = {"_type": "LabelView", "_id": nid(), "_parent": {"$ref": cid}, "visible": False,
          "font": FONT, "left": round(x, 2), "top": round(y, 2), "height": 13,
          "horizontalAlignment": 1}
    return {"_type": "UMLNameCompartmentView", "_id": cid, "_parent": {"$ref": view_id},
            "model": {"$ref": model_id}, "subViews": [s1, s2, s3, s4], "font": FONT,
            "left": round(x, 2), "top": round(y, 2), "width": round(w, 2), "height": h,
            "stereotypeLabel": {"$ref": s1["_id"]}, "nameLabel": {"$ref": s2["_id"]},
            "namespaceLabel": {"$ref": s3["_id"]}, "propertyLabel": {"$ref": s4["_id"]}}


def hidden_comp(typ: str, view_id: str, model_id: str, x: float, y: float,
                w: float = 10, h: float = 10) -> dict:
    """隐藏的 compartment。分类器类视图缺了它会少一条分隔线。"""
    return {"_type": typ, "_id": nid(), "_parent": {"$ref": view_id},
            "model": {"$ref": model_id}, "visible": False, "font": FONT,
            "left": round(x, 2), "top": round(y, 2), "width": w, "height": h}


def edge_view(vtype: str, parent_id: str, model_id: str, tail_id: str, head_id: str,
              points: str, name: str = "", line_style: int = 1,
              alpha: float = 1.5707963267948966, distance: float = 15) -> dict:
    """有向关系的视图：依赖 / 关联 / 包含 / 通信路径等。

    `tail` 是起点视图 id，`head` 是终点视图 id —— 是**视图** id，不是模型 id。
    """
    vid = nid()
    lid = nid()
    el = {"_type": "EdgeLabelView", "_id": lid, "_parent": {"$ref": vid},
          "model": {"$ref": model_id}, "visible": bool(name), "font": FONT,
          "left": 0, "top": 0, "height": 13, "alpha": alpha,
          "distance": distance, "hostEdge": {"$ref": vid}, "edgePosition": 1}
    if name:
        el["text"] = name
    return {"_type": vtype, "_id": vid, "_parent": {"$ref": parent_id},
            "model": {"$ref": model_id}, "subViews": [el], "font": FONT,
            "head": {"$ref": head_id}, "tail": {"$ref": tail_id},
            "lineStyle": line_style, "points": points, "nameLabel": {"$ref": lid}}


def typed_edge(mtype: str, parent_model_id: str, source_model_id: str,
               target_model_id: str, name: str = "", extra: dict | None = None) -> dict:
    """有向关系的模型：UMLDependency / UMLCommunicationPath 等。"""
    mid = nid()
    m = {"_type": mtype, "_id": mid, "_parent": {"$ref": parent_model_id},
         "source": {"$ref": source_model_id}, "target": {"$ref": target_model_id}}
    if name:
        m["name"] = name
    if extra:
        m.update(extra)
    return m


def assoc_model(parent_model_id: str, a_id: str, b_id: str, name: str = "",
                agg_end: int = 0) -> dict:
    """UMLAssociation 模型。agg_end: 0 无 / 1 A 端聚合 / 2 B 端聚合 / -1/-2 组合。"""
    aid = nid()
    e1 = {"_type": "UMLAssociationEnd", "_id": nid(), "_parent": {"$ref": aid},
          "reference": {"$ref": a_id}}
    e2 = {"_type": "UMLAssociationEnd", "_id": nid(), "_parent": {"$ref": aid},
          "reference": {"$ref": b_id}}
    if agg_end == 1:
        e1["aggregation"] = "shared"
    elif agg_end == 2:
        e2["aggregation"] = "shared"
    elif agg_end == -1:
        e1["aggregation"] = "composite"
    elif agg_end == -2:
        e2["aggregation"] = "composite"
    m = {"_type": "UMLAssociation", "_id": aid, "_parent": {"$ref": parent_model_id},
         "end1": e1, "end2": e2}
    if name:
        m["name"] = name
    return m


def box(a: dict, b: dict, side_a: str = "bottom", side_b: str = "top") -> str:
    """两个视图矩形之间的直线 points（自动选连接边）。"""
    def anchor(v, side):
        l, t, w, h = v["left"], v["top"], v["width"], v["height"]
        return {
            "top": (l + w / 2, t),
            "bottom": (l + w / 2, t + h),
            "left": (l, t + h / 2),
            "right": (l + w, t + h / 2),
        }[side]

    p1 = anchor(a, side_a)
    p2 = anchor(b, side_b)
    return "%d:%d;%d:%d" % (p1[0], p1[1], p2[0], p2[1])


def auto_sides(a: dict, b: dict):
    """按相对位置猜两侧锚点：上下关系走 bottom/top，左右关系走 right/left。"""
    ax, ay = a["left"] + a["width"] / 2, a["top"] + a["height"] / 2
    bx, by = b["left"] + b["width"] / 2, b["top"] + b["height"] / 2
    if abs(ax - bx) < 1:
        return ("bottom", "top") if ay < by else ("top", "bottom")
    if abs(ay - by) < 1:
        return ("right", "left") if ax < bx else ("left", "right")
    return ("bottom", "top") if ay < by else ("top", "bottom")


def selfcheck(data: dict):
    """返回 (对象数, 引用数, 重复 id 集合, 未命中引用列表)。"""
    ids, refs = [], []

    def walk(o):
        if isinstance(o, dict):
            if "_id" in o:
                ids.append(o["_id"])
            for k, v in o.items():
                if k == "$ref":
                    refs.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for i in o:
                walk(i)

    walk(data)
    dup = {i for i in ids if ids.count(i) > 1}
    miss = [r for r in refs if r not in set(ids)]
    return len(ids), len(refs), dup, miss


def dump(data: dict, path: str) -> int:
    """写 mdj，返回字节数。断言引用完整，不完整直接抛错。"""
    n_id, n_ref, dup, miss = selfcheck(data)
    if dup or miss:
        raise ValueError("引用自检失败：重复 %s，未命中 %d 个 %s" % (dup, len(miss), miss[:5]))
    txt = json.dumps(data, ensure_ascii=False, indent="\t")
    io.open(path, "w", encoding="utf-8").write(txt)
    return len(txt.encode("utf-8"))
