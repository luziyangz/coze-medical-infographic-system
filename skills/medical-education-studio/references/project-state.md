# Skill 独立项目状态

这是本 Skill 自己的 `medical-education-studio/v1` 格式，用于跨轮次续做。它不是 Coze 的输入输出协议；接入已有 Coze 应用需要另写映射并核对线上协议。不要直接将这个文件传给原工作流。

## 本地文件

```text
my-project/
  project.json
  01-brief.md
  02-research.md
  03-script.md
  04-visual-plan.md
  05-delivery.md
  images/
```

只创建当前已需要的正文和图片；初始化只创建状态与空图片目录。使用模板 [../assets/project.template.json](../assets/project.template.json)，所有空值有固定类型。

| 部分 | 内容与规则 |
|---|---|
| `schema_version`、`project_id` | 格式版本与本地项目名；标识不是账号或工作流 ID |
| `stage` | `intent/topics/research/script/visual/delivery/done`，记录本轮进行到哪一步 |
| `intent_info.data` | 需求业务字段唯一存储位置；未确定的可选文本为 `null`，方向和读者为字符串 |
| `topics.candidates` | 数组；每个对象为 `topic_id/title/angle` |
| `topics.selected` | `null` 或一个 `topic_id/title/angle` 对象，与候选数组保持分开；用户自带选题可直接建立稳定标识 |
| `topics.successful_rerecommendations` | 非负整数，同方向不重置 |
| `topics.preferences` | 用户提出的具体偏好字符串数组 |
| `research` | 独立状态、来源、主张、限制与受限内容确认 |
| `script` | 独立状态、整篇标题正文及逐页计划 |
| `visual` | 独立状态、全局风格、角色、实际资产及逐页候选 |
| `delivery` | 独立状态、`local/feishu`目标及逐页保存记录 |

`intent_info.data` 包括 `direction/audience/age_range/reader_problem/platform/format/audience_mode/style/aspect_ratio/page_count`。`page_count` 为正整数；初始化的六页仅是可更改的起点。`intent_info.confirmed` 记录整份简报是否经过确认，不由初始化脚本替用户确认。

## 最小对象形态

以下为结构示例，文字是格式说明，不是已核验内容。实际项目填入真实材料。

```json
{
  "source": {
    "source_id": "s01",
    "title": "实际阅读的资料标题",
    "locator": "sources/provided-material.md",
    "accessed_on": "2026-10-21"
  },
  "claim": {
    "claim_id": "c01",
    "statement": "由实际来源支持的主张",
    "source_ids": ["s01"],
    "scope": "适用人群、情境及限制"
  },
  "script_page": {
    "page_id": "p01",
    "title": "页面标题",
    "text": "锁定的页面文字",
    "visual_brief": "本页画面任务",
    "claim_ids": ["c01"]
  },
  "visual_page": {
    "page_id": "p01",
    "candidates": ["images/p01-v1.png"],
    "review": "pending"
  },
  "delivery_record": {
    "page_id": "p01",
    "status": "saved",
    "reference": "images/p01-v1.png"
  }
}
```

来源 `locator` 可为实际读取的 HTTPS/HTTP 链接，或项目内已有的相对文件。图片候选与保存记录的 `reference` 同样允许工具返回的链接或项目内相对路径。本地引用必须留在项目目录内，避免把其他目录的私人文件纳入交付。

来源与主张通过 `source_id/claim_id` 关联，各页通过 `page_id` 关联。引用已删除的来源或页面时，应修正关联或撤回下游产物。

`visual.characters` 为角色描述字符串数组；`visual.assets` 为实际参考文件或 URL 的字符串数组。风格文字保存在 `style_guide`，尚未产生的参考图不登记为实际资产。

## 状态

- `research.status`：`not_started/ready/limited/unverified/failed`。`ready`与`limited`需要来源和主张；后者还需要非空限制。只有 `ready`，或用户已接受限制的 `limited`，才可形成可用文案。
- `script.status`：`not_started/draft/ready`。`draft`可为待核实提纲；`ready`需要有效研究、标题正文及页面计划。
- `visual.status`：`not_started/planned/generated/failed`。`generated`至少有一张可定位的真实候选。`passed`只表示该页已经实际复核，不能由结构检查推断。
- `delivery.status`：`not_started/prepared/saved/partial/failed`。`prepared`表示仅有本地交付准备；`saved`表示本轮计划页面均有成功保存记录；部分保存使用 `partial`。

`stage = done`表示用户本次要求的终点已完成，例如只要需求简报也可以结束；它不代表全部阶段都执行过。

## 修改的失效范围

| 用户修改 | 保留 | 重做或核对 |
|---|---|---|
| 同方向换选题 | 需求、偏好与推荐次数 | 已选对象、研究、文案、视觉和交付 |
| 改受众或年龄 | 方向与仍适用的选题 | 研究适用范围；受影响文案及下游 |
| 只换风格 | 已确认选题、研究及仍适用的文字 | 全局视觉、图片和后续归档 |
| 改平台、比例或页数 | 选题及仍适用依据 | 文案长度、分页、布局与图片 |
| 明确换科普方向 | 旧项目历史 | 新建项目，重新收集新方向需求 |

修改前保留已完成版本或另建版本目录；不要留下新需求配旧图片、旧研究的混合状态。技术错误只修改相应状态，不清空已成功阶段。

执行 [../scripts/validate_project.py](../scripts/validate_project.py) 可检查固定结构、ID关联、已完成状态前提及本地文件存在性。它不会访问网络，不会判断医学真实性，不会确认远程链接仍有效，也不会做图像审核。
