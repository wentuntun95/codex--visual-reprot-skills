# Codex Visual Report Skills

面向视觉汇报工作的 Codex Skill 合集。仓库采用“一个仓库、多个独立 Skill”的结构，便于统一版本管理、跨设备迁移和持续增加新能力。

## Skills

### `ppt-xiaozi`

策划、制作和维护可编辑 PPT。适合从发散沟通建立故事主线，先冻结极简内容草稿，再补证据并进入正式视觉制作。

### `report-long-poster`

制作汇报长图、方案海报和竖版信息图。使用矢量文字与框架、原始图片嵌入和高清重新渲染，支持快速草稿、内部简约和商用设计三种模式。

## 仓库结构

```text
codex-visual-report-skills/
├── README.md
├── LICENSE
├── ppt-xiaozi/
│   ├── SKILL.md
│   ├── agents/
│   ├── references/
│   └── scripts/
└── report-long-poster/
    ├── SKILL.md
    ├── agents/
    ├── references/
    ├── scripts/
    └── assets/
```

每个一级子目录都是一个可以单独安装的 Skill。仓库根目录不是 Skill，不应整体复制为一个 Skill 子目录。

## 安装

克隆仓库后，将需要的 Skill 文件夹复制到 Codex skills 目录。

PowerShell 示例：

```powershell
$codexSkills = if ($env:CODEX_HOME) {
  Join-Path $env:CODEX_HOME "skills"
} else {
  Join-Path $env:USERPROFILE ".codex\skills"
}

Copy-Item -Recurse -Force ".\ppt-xiaozi" "$codexSkills\ppt-xiaozi"
Copy-Item -Recurse -Force ".\report-long-poster" "$codexSkills\report-long-poster"
```

也可以只复制其中一个 Skill。安装或更新后，重新打开 Codex 会话以刷新 Skill 列表。

## 使用

可以显式调用：

```text
使用 $ppt-xiaozi 帮我把这份材料整理成汇报PPT。
使用 $report-long-poster 先制作一版白底长图草稿。
```

两个 Skill 均允许根据任务描述自动触发。

## 新增 Skill

在仓库根目录增加一个同级文件夹，并至少包含：

```text
new-skill/
└── SKILL.md
```

需要时再增加 `agents/`、`references/`、`scripts/` 或 `assets/`。新增后同步更新本 README 的 Skills 列表和目录结构。

## 维护原则

- 仓库保存可迁移的源文件，不提交 `__pycache__`、临时预览和生成结果。
- 每个 Skill 保持自包含，不依赖另一个 Skill 的内部相对路径。
- 修改完成后，同时同步仓库副本和本机已安装版本，避免两处内容长期分叉。
- 重要脚本应有一次真实运行验证，而不仅是语法检查。

## License

MIT，见 [LICENSE](LICENSE)。
