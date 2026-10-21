"""Render local Markdown into docs/展示.html without service credentials."""
from pathlib import Path
from html import escape
import re
from urllib.parse import unquote
import mistune

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
CHAPTERS=[
    ('README.md','overview','系统总览'),
    ('01-操作SOP.md','sop','主题处理与SOP'),
    ('02-工作流职责与组合.md','modules','工作流分工'),
    ('03-图文生成与飞书协作.md','production','图文与飞书'),
    ('04-图文效果与应用案例.md','examples','页面效果'),
    ('05-模块复用与拓展.md','reuse','独立使用与拓展'),
    ('使用说明.md','usage','使用说明'),
    ('Skill安装与使用.md','skill','Skill安装与使用'),
]
anchors={name:anchor for name,anchor,_ in CHAPTERS}
md=mistune.create_markdown(escape=False,plugins=['table','strikethrough'])
def link(m):
    href=unquote(m.group(1))
    return 'href="#'+anchors[href]+'"' if href in anchors else m.group(0)
def image(m):
    tag=m.group(0);src=re.search(r'src="([^"]+)"',tag).group(1)
    kind='workflow-figure' if '/workflows/' in src else ('diagram-figure' if '/diagrams/' in src else 'sample-figure')
    return f'<a class="image-link {kind}" href="{src}" target="_blank" rel="noopener">{tag}</a>'
sections=[]
for name,anchor,label in CHAPTERS:
    html=md((DOCS/name).read_text(encoding='utf-8'))
    html=re.sub(r'href="([^"]+)"',link,html)
    if anchor=='modules':
        blocks=[]
        for block in re.split(r'(?=<h2>)',html):
            shot=re.search(r'<p>\s*(<img[^>]+src="assets/workflows/[^>]+>)\s*</p>',block)
            if shot:
                title=re.match(r'(<h2>.*?</h2>)',block,re.S)
                body=block.replace(shot.group(0),'')
                if title:body=body[len(title.group(1)):]
                block=f'<article class="module-card">{title.group(1) if title else ""}<div class="module-copy">{body}</div><div class="module-visual">{shot.group(1)}</div></article>'
            blocks.append(block)
        html=''.join(blocks)
    html=re.sub(r'<img\b[^>]*>',image,html)
    sections.append(f'<section id="{anchor}" class="chapter">{html}</section>')
nav=''.join(f'<a href="#{anchor}"><span>{i:02d}</span>{escape(label)}</a>' for i,(_,anchor,label) in enumerate(CHAPTERS,1))
css=(ROOT/'tools/style.css').read_text(encoding='utf-8')
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>医疗科普图文系统｜工作流、制作方法与使用说明</title><style>{css}</style></head><body><header class="hero"><div class="eyebrow">COZE · WORKFLOW GUIDE</div><h1>医疗科普图文系统</h1><p>从一个主题开始，明确读者与内容目标，制作文案、分镜和系列图片。<br>了解八个工作流怎样协作，怎样使用飞书，以及怎样把这些方法用到自己的项目中。</p><div class="hero-tags"><span>整体流程与SOP</span><span>八个模块的分工</span><span>视觉资产与飞书</span><span>使用与复用方法</span></div></header><div class="layout"><nav aria-label="章节导航">{nav}<p>工作流截图采用缩略概览。<br>点击图片可查看原图。<br>个人配置请使用自己的Coze与飞书空间。</p></nav><main>{''.join(sections)}</main></div><footer>医疗科普图文系统 · 工作流逻辑、使用方式与模块复用</footer></body></html>'''
(DOCS/'展示.html').write_text(page,encoding='utf-8')
print('Generated docs/展示.html')
