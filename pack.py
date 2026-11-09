"""把 skill 目录打成 zip，输出到 dist/<name>-<version>.zip。

用法：
    python pack.py            # 版本取 SKILL.md 所在目录的 git describe，没有就 0.0.0
    python pack.py --ver 1.1.0

排除：.git / __pycache__ / out / dist / *.pyc
"""
from __future__ import annotations

import argparse
import os
import subprocess
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
NAME = "staruml-diagrams"
EXCLUDE_DIRS = {".git", "__pycache__", "out", "dist", ".idea", ".vscode"}


def guess_version() -> str:
    try:
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                           cwd=ROOT, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().lstrip("v")
    except Exception:
        pass
    return "0.0.0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default=None)
    a = ap.parse_args()
    ver = a.ver or guess_version()

    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, "%s-%s.zip" % (NAME, ver))

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith(".pyc"):
                    continue
                full = os.path.join(base, f)
                rel = os.path.relpath(full, ROOT)
                z.write(full, os.path.join(NAME, rel))
                count += 1

    print("打包 %d 个文件 -> %s（%d 字节）" % (count, out, os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
