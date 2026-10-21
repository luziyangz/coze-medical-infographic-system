# 在 Codex、WorkBuddy 中使用 Skill

本仓库同时提供 **Coze 工作流方案**与 **独立智能体 Skill**。它们借鉴同一套内容生产方法，由不同运行环境执行。

## 1. 工作流和 Skill 是两套

| 对比 | Coze 工作流方案 | 本仓库 Skill |
|---|---|---|
| 在哪里执行 | 使用者自己的 Coze 空间 | Codex、WorkBuddy 等支持 Agent Skills 的智能体 |
| 谁安排步骤 | 主对话与工作流节点 | 当前智能体读取技能指令，安排步骤和工具 |
| 提供了什么 | 系统设计、SOP、真实工作流截图、图文案例 | 可安装技能、内容生产方法、项目模板、可选本地脚本 |
| 搜索与模型 | 在 Coze 配置 | 使用宿主已接入的能力 |
| 实际出图 | Coze Graphic 与配置的图像服务 | 宿主中实际可用的图像生成工具 |
| 飞书读写 | Coze 插件、认证与数据表 | 使用者自己在宿主中配置的连接或 API |
| 状态与输入 | Coze 自己的节点协议和会话状态 | 独立 `project.json`；不能直接替代 Coze 输入 |
| 是否相互调用 | 根据 Coze 中实际依赖执行 | 本版本不自动调用、修改或导入 Coze 工作流 |

**安装 Skill 后就可以用智能体整理需求、策划选题、阅读资料、编写文案和分镜。** 能否实际生成图片、读取资产和保存飞书，取决于当前宿主中的工具与个人配置。Skill 不附作者账号权限、密钥、私有资产库或模型服务。

原仓库展示的八张画布和六页候选图片属于 Coze 方案的案例；不是本 Skill 的运行效果承诺。

## 2. 获取独立技能包

- 技能源码：[medical-education-studio](../skills/medical-education-studio/SKILL.md)。
- 可导入安装包：[下载 medical-education-studio.zip](https://github.com/luziyangz/coze-medical-infographic-system/releases/download/skill-v1.0.0/medical-education-studio.zip)。
- 版本说明与校验值：[Skill v1.0.0](https://github.com/luziyangz/coze-medical-infographic-system/releases/tag/skill-v1.0.0)。

安装包只包含这一个技能及其引用文件。它不包含整个文档仓库、工作流截图、原始导出包或私人配置。

```text
medical-education-studio/
  SKILL.md
  agents/openai.yaml
  references/
  assets/project.template.json
  scripts/init_project.py
  scripts/validate_project.py
```

完整目录必须一起安装；仅复制 `SKILL.md` 会遗漏方法、模板和可选脚本。脚本使用 Python 3.10+ 标准库，无需安装第三方依赖；没有 Python 也可由智能体按模板手工维护项目。

## 3. 在 Codex 中安装

下载独立 ZIP 并解压，将整个 `medical-education-studio` 文件夹放入用户主目录的 `.agents/skills/`。也可以克隆仓库后复制 `skills/medical-education-studio/`。Codex 当前官方文档将这个目录列为用户级技能目录。[Codex Skills 官方说明](https://developers.openai.com/codex/skills/)

在仓库根目录执行以下 PowerShell 命令可以安装到当前用户，已有同名目录时会停止，方便先备份再决定更新：

```powershell
$skillSource = Join-Path (Get-Location) 'skills/medical-education-studio'
$skillTarget = Join-Path $HOME '.agents/skills/medical-education-studio'
if (Test-Path -LiteralPath $skillTarget) { throw '同名技能已存在，请先备份或检查版本。' }
New-Item -ItemType Directory -Path (Split-Path $skillTarget) -Force | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillTarget -Recurse
```

macOS/Linux 同样将文件夹放入 `~/.agents/skills/`。若只想在某个项目使用，可以放入该项目的 `.agents/skills/`；选一种安装范围即可，避免出现同名技能的重复条目。

安装后打开新的任务，使用技能选择器或输入 `$medical-education-studio`。若未出现，重启或刷新宿主后再查看。[技能发现与调用方式](https://developers.openai.com/codex/skills/)

```text
请使用 $medical-education-studio。
我想做面向家长的儿童睡眠科普，先帮我明确需求与具体选题。
暂时只做策划，不生成图片。
```

## 4. 在 WorkBuddy 中安装

下载上面的独立技能 ZIP。在 WorkBuddy 左侧进入“专家·技能·连接器”，选择“技能”，再通过“添加技能 → 上传技能”选择本地技能包；导入后在“已安装”中确认已启用。这是 WorkBuddy 官方提供的本地技能包导入入口。[WorkBuddy 技能官方说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)

对话里使用技能名称和自然语言说明任务，例如：

```text
请使用“医疗科普创作工作室”（medical-education-studio）技能。
根据我提供的已确认资料，制作六页家长版科普的文案、分镜和水彩视觉方案。
这一轮只交付制作包。
```

WorkBuddy 的对话安装入口主要面向技能市场；本仓库是自行提供的技能包，请使用上传入口。安装本包不表示已上架 WorkBuddy 技能市场。[官方导入方式](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)

## 5. 在其他智能体中使用

如果宿主支持包含 YAML 元数据的 `SKILL.md`，按其安装目录或本地包导入方式安装完整文件夹。`agents/openai.yaml` 是 Codex 的可选界面元数据，其他宿主可忽略；核心指令、方法与脚本不依赖 Codex 专有工具名称。[Agent Skills 格式规范](https://agentskills.io/specification)

宿主完全不支持 Skills 时，也可以让它读取本地 `SKILL.md`，并按需读取相邻 `references/`；这属于手工加载指令，不等于已完成原生技能安装。

## 6. 按本次需要选择用法

| 需要什么 | 可以怎样说 | 产物 |
|---|---|---|
| 只整理需求 | “先把我的科普想法整理成需求简报。” | 已知需求、未确定项与必要追问 |
| 只做选题 | “围绕这个方向，给我适合家长阅读的几个切入点。” | 可比较的具体问题与选题角度 |
| 研究与文案 | “选择第二个问题，查资料后给我证据卡和正文。” | 真实来源、适用边界与文案 |
| 从资料到分镜 | “用这份资料做六页，先看每页文字和画面说明。” | 标题、正文、逐页分镜 |
| 只做视觉方案 | “保留文字，给我一套统一的3D风格制作包。” | 风格、角色、布局与逐页提示词 |
| 实际出图 | “按确认后的分镜生成候选图片。” | 有图像工具时生成实际图片，并反馈缺页与复核情况 |
| 飞书归档 | “把这套已生成图文保存到我指定的飞书表。” | 有个人连接和写入权限时保存，并反馈真实记录 |

医学研究会区分已支持、证据有限、待核实和技术失败；视觉方案、真实候选图、质量复核与保存结果分别记录。用户因此可以先使用已有产物，再继续后续阶段。

## 7. 保存任务，下一轮继续

让智能体把结果保存在独立目录即可，例如：“把这个项目保存为 `outputs/sleep-parent/`，后面继续修改。”目录中记录需求、选题、来源、文案、视觉和交付状态；不是保存账号配置的位置。

也可以在仓库根目录用可选脚本初始化：

```bash
python skills/medical-education-studio/scripts/init_project.py outputs/sleep-parent --direction "儿童睡眠科普" --audience "家长" --pages 6
python skills/medical-education-studio/scripts/validate_project.py outputs/sleep-parent
```

初始化只建立状态文件和图片目录，不会检索、生成医学内容、出图或调用飞书，也不会覆盖已有项目。结构检查用于发现字段、引用和本地文件问题，不验证医学事实或图片质量。

续做时说：“继续 `outputs/sleep-parent/`，保留文字，风格改为水彩。”智能体读取已有项目，更新受影响阶段。同方向换选题保留需求；明确换科普方向则新开项目。

## 8. 维护与重新打包

修改 `skills/medical-education-studio/` 后，在仓库根目录运行：

```bash
python -m unittest discover -s tests -v
python tools/render_docs.py
python tools/check_release.py
python tools/package_skill.py ../medical-education-studio.zip
```

新包输出路径必须尚不存在。把 ZIP 放在仓库外，避免与包含私人认证的原始工作流导出包混在一起。发布前核对技能引用、安装说明、实际脚本与包内文件一致；个人项目和连接配置不要放入技能源码。

[返回首页](../README.md) · [Coze 方案使用说明](使用说明.md)
