"""Check documentation links and common sensitive text patterns before a commit."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
RULES={
    'long_private_id':re.compile(r'\b\d{15,22}\b'),
    'feishu_application_id':re.compile(r'\bcli_[A-Za-z0-9]{6,}\b'),
    'github_token':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b'),
    'private_coze_link':re.compile(r'(?:workflow_id|space_id)=\d+'),
    'source_image_link':re.compile(r'https://s\.coze\.cn/t/[^\s"<>)]*'),
    'local_windows_path':re.compile(r'\b[A-Za-z]:[\\/]'),
    'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}
ASSIGNMENT=re.compile(r'''(?i)(?:app_id|app_secret|app_token|table_id|tenant_access_token|api_key|access_token)["']?\s*[:=]\s*["']?([A-Za-z0-9_-]{8,})''')
class HTMLRefs(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get('id'):self.ids.add(d['id'])
        if tag=='a' and d.get('href'):self.refs.append(d['href'])
        if tag=='img' and d.get('src'):self.refs.append(d['src'])

issues=[];files=0;references=0
for path in ROOT.rglob('*'):
    if not path.is_file() or any(p in {'.git','.venv','venv','__pycache__'} for p in path.parts):continue
    rel=path.relative_to(ROOT).as_posix()
    if path.suffix.lower() in {'.zip','.db','.log','.sqlite','.pyc'} or rel in {'.env','config/local.json'}:
        issues.append({'file':rel,'rule':'private_or_generated_file'});continue
    if path.suffix.lower() not in {'.md','.py','.html','.json','.svg','.txt','.css','.example'} and path.name not in {'.gitignore','.gitattributes'}:continue
    files+=1
    value=path.read_text(encoding='utf-8')
    for rule,pattern in RULES.items():
        if pattern.search(value):issues.append({'file':rel,'rule':rule})
    for match in ASSIGNMENT.finditer(value):
        if not match.group(1).startswith(('YOUR_','EXAMPLE_','PLACEHOLDER_')):
            issues.append({'file':rel,'rule':'possible_private_configuration'})
    refs=[]
    if path.suffix=='.md':
        refs=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',value)+re.findall(r'(?:src|href)="([^"]+)"',value)
    elif path.suffix=='.html':
        parser=HTMLRefs();parser.feed(value);refs=parser.refs
        for ref in refs:
            if ref.startswith('#') and ref[1:] not in parser.ids:issues.append({'file':rel,'rule':'missing_anchor'})
    for ref in refs:
        if ref.startswith('#') or urlsplit(ref).scheme:continue
        references+=1
        if not (path.parent/unquote(ref.split('#')[0])).exists():issues.append({'file':rel,'rule':'missing_local_reference','target':ref})
report={'status':'PASS' if not issues else 'FAIL','text_files_checked':files,'local_references_checked':references,'findings':issues,'note':'Text pattern and local reference checks; review new images separately.'}
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(bool(issues))
