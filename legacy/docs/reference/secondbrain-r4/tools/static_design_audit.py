#!/usr/bin/env python3
"""Design-only self-audit for a Pre-TDD distribution, not implementation tests.

Requires Python >=3.11 and jsonschema. Run from any directory:
  python tools/static_design_audit.py
Checks local files only. It cannot verify forensic/legal validity, provider sync or product behavior.
"""
from __future__ import annotations
import csv, hashlib, json, sys, tomllib, zipfile
from pathlib import Path
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    sys.exit('ERROR: install jsonschema to run design-only fixture validation')
ROOT=Path(__file__).resolve().parents[1]
fail=[];results={}

def require(cond,desc):
    if not cond: fail.append(desc)

def read_csv(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_group(subpath, fixture_dir):
    total=0
    for path in sorted((ROOT/subpath).glob('*.schema.json')):
        schema=json.loads(path.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        base=path.name.removesuffix('.schema.json')
        pos=ROOT/fixture_dir/(base+'.valid.json');neg=ROOT/fixture_dir/(base+'.invalid.json')
        require(pos.exists() and neg.exists(),f'fixture missing: {base}')
        if not (pos.exists() and neg.exists()):continue
        v=Draft202012Validator(schema, format_checker=FormatChecker())
        p=json.loads(pos.read_text());n=json.loads(neg.read_text())
        require(v.is_valid(p),f'positive fixture rejected: {base}, {list(v.iter_errors(p))[:1]}')
        require(not v.is_valid(n),f'negative fixture accepted: {base}')
        total+=1
    return total

req=read_csv('traceability/requirements_to_tests.csv')
ids=[r['requirement_id'] for r in req]
require(len(ids)==len(set(ids)), 'duplicate requirement IDs')
for r in req:
    require(r['planned_test_id']=='TC-'+r['requirement_id'],f'planned test mismatch: {r["requirement_id"]}')
    require((ROOT/r['design_reference']).is_file(),f'broken design_reference: {r["requirement_id"]}')
    require(r['implementation_status']=='PLANNED_NOT_IMPLEMENTED',f'premature implementation claim: {r["requirement_id"]}')
scenarios=read_csv('quality/lifecycle_scenarios.csv')
sids=[x['scenario_id'] for x in scenarios]
require(len(sids)==len(set(sids)),'duplicate scenario IDs')
for row in scenarios:
    require(row['status']=='PLANNED_NOT_RUN',f'premature lifecycle PASS claim: {row["scenario_id"]}')
    require(row['related_requirements'],f'unmapped scenario: {row["scenario_id"]}')
    for reqid in row['related_requirements'].split(';'):
        require(reqid in ids, f'unknown req in scenario: {reqid}')

gates=read_csv('quality/gate_to_requirements.csv')
require([g['gate'] for g in gates]==[f'G{i}' for i in range(8)],'missing/duplicate G0~G7')
for row in gates:
    for r in row['requirements'].split(';'):
        require(r in ids, f'unknown gate requirement: {r}')

results['v2_schema_fixture_pairs']=validate_group('schemas/v2','examples/v2')
results['governance_schema_fixture_pairs']=validate_group('schemas/governance/v1','examples/governance/v1')
results['legacy_schema_count']=len(list((ROOT/'schemas/v1').glob('*.schema.json')))
for p in [ROOT/'config/brain.example.toml',ROOT/'sample-root/90_System/config/brain.toml.example',ROOT/'pyproject.toml']:
    with p.open('rb') as f:tomllib.load(f)
results['toml_parsing']='PASS'
results['requirements']=len(req)
results['new_r3_requirements']=sum(r['requirement_id'].split('-')[1] in ('LIF','QAL','FBK','OBS','RLS','CHG','SUP','DRL','EVA','GOV') for r in req)
results['planned_lifecycle_scenarios']=len(scenarios)
results['gate_count']=len(gates)
results['adr_documents']=len(list((ROOT/'docs/adr').glob('*.md')))
results['product_python_files']=len(list((ROOT/'src').rglob('*.py')))
results['executable_test_python_files']=len(list((ROOT/'tests').rglob('test_*.py')))
require(results['product_python_files']==0,'product implementation exists in Pre-TDD')
require(results['executable_test_python_files']==0,'executable test suite exists in Pre-TDD')
require(results['requirements']==188,'incorrect norm req count')
require(results['v2_schema_fixture_pairs']==14,'incorrect evidence schema pair count')
require(results['governance_schema_fixture_pairs']==8,'incorrect governance schema pair count')
require(results['planned_lifecycle_scenarios']==30,'incorrect planned lifecycle scenario count')
require(results['legacy_schema_count']==8,'legacy schemas lost')
require(results['new_r3_requirements']==54,'R3 requirements lost')
require((ROOT/'history/R2_input.zip').is_file(),'R2 history zip missing')
for hist in ['history/R2_input.zip','history/R1_input.zip']:
    if (ROOT/hist).exists():
        with zipfile.ZipFile(ROOT/hist) as z: require(z.testzip() is None, f'bad archive: {hist}')

# Manifest is generated after reports; optionally validate it if present.
manifest=ROOT/'PACKAGE_MANIFEST.sha256'
if manifest.exists():
    expected={}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        match=line.split('  ',1)
        if len(match)!=2:fail.append('invalid manifest line');continue
        expected[match[1]]=match[0]
    actual={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in ROOT.rglob('*') if p.is_file() and p!=manifest}
    require(actual==expected, f'manifest mismatch missing={sorted(actual.keys()-expected.keys())[:5]} extras={sorted(expected.keys()-actual.keys())[:5]} changed={[p for p in expected.keys()&actual.keys() if expected[p]!=actual[p]][:5]}')
    results['manifest_entries']=len(expected)
else:
    results['manifest_entries']='NOT_GENERATED_YET'
report={'date':'2026-10-09','phase':'DESIGN_ONLY_PRE_TDD','results':results,'failures':fail,
 'limitations':['Does not execute TDD, production or OS sync/restore','Schema fixtures only validate structural subset; semantic and legal conditions untested','Manual approvals are NOT RUN','No AI provider or private data used']}
if '--write-report' in sys.argv:
    # When manifest exists, writing report would make it stale; packaging pipeline removes manifest first.
    (ROOT/'quality/R3_STATIC_AUDIT_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
if fail:sys.exit(1)
