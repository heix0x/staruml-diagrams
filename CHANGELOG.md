# 更新日志

## [1.0.0] - 2026-11-09

首个可用版本。

### 新增

- 六类图生成：flowchart / usecase / class / component / deployment / sequence
- `mdj.py` 三个命令：`build` 生成、`check` 自检、`kinds` 列支持类型
- 描述文件支持 YAML 与 JSON，坐标、`_id`、`$ref` 全部由脚本生成
- 自检项：`$ref` 全命中、无重复 id、`head/tail` 与 `source/target` 一一对应、
  LabelView 文本与模型 name 一致、视图重叠、连线穿框、`defaultDiagram` 唯一
- 六份示例描述文件，`tests/run_checks.py` 一键回归
- `pack.py` 打包脚本

### 已知限制

- component / deployment / sequence 三类结构按 `elements.js` 源码推导，
  未在 StarUML 里实际加载验证（`STATUS: derived`），第一次用需开图确认
- 类图自动布局不如手调，需要精确位置时用 `at: [x, y]`
- 一个描述文件只生成一张图
