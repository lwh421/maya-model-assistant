# Maya Model Assistant

利用AI检测Maya建模问题并提供改进建议的作品集项目。

## 项目介绍

本项目致力于通过AI技术辅助Maya建模工作流程，自动检测模型中存在的拓扑、UV、比例等问题，并给出针对性的改进建议。

## 目录结构

- `scripts/` - Python脚本，用于Maya自动化检测和分析
- `models/` - Maya建模文件（.mb/.ma格式）
- `docs/` - 文档和检测报告

## 技术栈

- Autodesk Maya
- Python (PyMel / maya.cmds)
- AI辅助检测算法

## 功能特性

### ✅ 已实现
- 模型拓扑问题检测（N-gon面、重叠面、非流形边）
- 多边形面数统计（顶点、边、面、三角面占比）
- 游离顶点检测与清理建议
- 自动生成优化建议报告

### 🚧 计划中
- UV展开质量分析
- 模型比例与结构检查
- AI辅助问题诊断与改进方案
- 自动修复脚本

## 使用方法

1. 在Maya脚本编辑器中运行 `scripts/model_quality_checker.py`
2. 选择需要检测的模型
3. 查看控制台输出的检测报告和优化建议

详细说明请参考 `docs/usage_guide.md`

## 作者

求职作品集项目
