#!/usr/bin/env python3
"""Checks THIS DESIGN package only. It does not exercise product behavior or release gates."""
import csv, hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
fail=[]; stats={}

def req(assertion,msg):
    if not assertion: fail.append(msg)

def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def load_csv(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
requirements=load_csv('quality/requirements.csv')
tests=load_csv('quality/test_catalog.csv')
ids=[r['id'] for r in requirements]; tids=[r['id'] for r in tests]
req(len(ids)==len(set(ids)),'duplicate requirement ids')
req(len(tids)==len(set(tids)),'duplicate test ids')
req(all(re.fullmatch(r'GD-\d{3}',rid or '') for rid in ids),'requirement id syntax')
req(all(re.fullmatch(r'TEST-\d{3}',tid or '') for tid in tids),'test id syntax')
req(all(r['level']=='MUST' and r['acceptance'] and r['negative'] and r['statement'] and r['test_id'] in tids and r['gate'] in [f'G{i}' for i in range(8)] for r in requirements),'incomplete requirement')
req(all(t['requirement_id'] in ids and t['execution_status']=='NOT_RUN' and t['expected'] and t['setup'] and t['gate'] in [f'G{i}' for i in range(8)] for t in tests),'incomplete test trace or accidental PASS')
req(all(next(t for t in tests if t['id']==r['test_id'])['requirement_id']==r['id'] for r in requirements),'broken inverse trace')
req(all(r['status']=='PLANNED_NOT_RUN' for r in requirements),'preTDD status incorrectly advanced')
req(all('GD-'+str(i).zfill(3) in (ROOT/'docs/02_REQUIREMENTS.md').read_text(encoding='utf-8') for i in range(1,len(requirements)+1)),'missing requirements doc index')
req(all((ROOT/'docs/adr'/f'{i:04d}.md').exists() for i in range(1,19)),'missing ADR')
req(not list((ROOT/'src').rglob('*')) if (ROOT/'src').exists() else True, 'source code exists in preTDD kit')
rows=load_csv('quality/cross_boundary_scenarios.csv')
req(all(all(x in ids for x in s['related_requirement_ids'].split(';')) for s in rows),'cross boundary bad requirement reference')

try:
 from jsonschema import Draft202012Validator, FormatChecker
 from jsonschema.exceptions import ValidationError
 validated=0
 for path in sorted((ROOT/'schemas/v1').glob('*.schema.json')):
    schema=json.loads(path.read_text(encoding='utf-8')); Draft202012Validator.check_schema(schema)
    v=Draft202012Validator(schema,format_checker=FormatChecker())
    key=path.name[:-len('.schema.json')]
    ok=json.loads((ROOT/'examples/v1'/f'{key}.valid.json').read_text(encoding='utf-8'))
    bad=json.loads((ROOT/'examples/v1'/f'{key}.invalid.json').read_text(encoding='utf-8'))
    req(v.is_valid(ok),f'{key}: valid rejected')
    req(not v.is_valid(bad),f'{key}: invalid accepted')
    validated+=1
 stats['schema_examples_checked']=validated
except ImportError:
 fail.append('jsonschema missing: pip install jsonschema>=4.18')


# v2 method decisions / schema example checks: only design conformance, no product TDD.
method_rows=load_csv('quality/research_decisions_20261010.csv')
req(len(method_rows)>=10,'missing research decisions')
req(all(x['decision'] in {'ADOPT','ADAPT','WATCH','REJECT'} and x['url'].startswith('https://') and x['revisit_if'] and x['owner'] for x in method_rows),'bad method decision')
for path in (ROOT/'schemas/v2').glob('*.schema.json'):
    schema=json.loads(path.read_text(encoding='utf-8')); Draft202012Validator.check_schema(schema)
    key=path.name[:-len('.schema.json')]
    v=Draft202012Validator(schema,format_checker=FormatChecker())
    ok=json.loads((ROOT/'examples/v2'/f'{key}.valid.json').read_text(encoding='utf-8'))
    bad=json.loads((ROOT/'examples/v2'/f'{key}.invalid.json').read_text(encoding='utf-8'))
    req(v.is_valid(ok),f'v2 {key}: valid rejected')
    req(not v.is_valid(bad),f'v2 {key}: invalid accepted')
req(len(list((ROOT/'schemas/v2').glob('*.schema.json')))==6,'v2 schema count')

# Manifest lines are tab-separated checksum + relative POSIX path; manifest excludes itself.
manifest=ROOT/'PACKAGE_MANIFEST.sha256'
if manifest.exists():
    rows=[line.split('\t',1) for line in manifest.read_text(encoding='utf-8').splitlines() if line]
    files={str(p.relative_to(ROOT).as_posix()) for p in ROOT.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.sha256'}
    req(len(rows)==len(files),'manifest line count')
    req(set(name for _,name in rows)==files,'manifest incomplete or unknown files')
    for expected,name in rows:
        p=ROOT/name
        if p.exists(): req(sha_file(p)==expected,f'manifest SHA mismatch: {name}')
else:fail.append('manifest missing')

stats.update(research_decisions=len(method_rows),v2_schemas=6,requirements=len(requirements),planned_tests=len(tests),cross_cases=len(load_csv('quality/cross_boundary_scenarios.csv')),issues=fail,status='PASS' if not fail else 'FAIL')
print(json.dumps(stats,ensure_ascii=False,indent=2))
sys.exit(0 if not fail else 1)
