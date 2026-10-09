#!/usr/bin/env python3
"""R4 design-only semantic blind-spot demonstration. This is not a product test."""
from pathlib import Path
import csv,json,re,hashlib,zipfile,sys
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1]
a=json.loads((root/'quality/R4_SCHEMA_LIMITATION_PROBES.json').read_text(encoding='utf-8'))
base_count=len(a['probes']); checks=[]
for record in a['probes']:
    schema=json.loads((root/f"schemas/v2/{record['schema']}.schema.json").read_text())
    example=json.loads((root/f"examples/v2/{record['schema']}.valid.json").read_text())
    name=record['probe']
    if name=='P1-object-id':example['object_id']='obj-sha256-'+'a'*64
    if name=='P2-vault-path':example['vault_relpath']='10_Evidence/Vault/objects/sha256/aa/aa/'+'a'*64+'/payload'
    if name=='P3-backup-inconsistent':example.update(target_manifest_sha256='a'*64,files_checked=0)
    if name=='P4-custody-gap':example.update(sequence=2,previous_event_hash=None)
    if name=='P6-hold-release':example.update(status='RELEASED')
    if name=='P7-snapshot-zero':example.update(file_count=0,total_bytes=0)
    if name=='P8-production-crossref':example['items'][0]['object_sha256']='a'*64
    accepted=Draft202012Validator(schema,format_checker=FormatChecker()).is_valid(example)
    checks.append({'id':name,'accepted_by_structural_schema':accepted,'expected':record['schema_accepts']})
requirements=list(csv.DictReader((root/'traceability/requirements_to_tests.csv').open(encoding='utf-8-sig')))
ids={r['requirement_id'] for r in requirements}
rows=list(csv.DictReader((root/'quality/R4_SEMANTIC_TEST_ORACLES.csv').open(encoding='utf-8-sig')))
bad_ref=[x['id'] for x in rows if any(y not in ids for y in x['related_requirement_ids'].split(';'))]
active=list((root/'docs/adr').glob('*.md'))
adr_names=[re.match(r'^(\d+)-',x.name).group(1) for x in active]
history=root/'history/R3_input.zip'
with zipfile.ZipFile(history) as z: history_ok=(z.testzip() is None)
fail=[]
if len(rows)!=28:fail.append('oracle-count')
if len(ids)!=188:fail.append('requirement-count')
if bad_ref:fail.append('bad-req-ref:'+str(bad_ref))
if len(adr_names)!=len(set(adr_names)):fail.append('duplicate-active-ADR')
if not history_ok:fail.append('bad-R3-historical-ZIP')
if any(x['accepted_by_structural_schema']!=x['expected'] for x in checks):fail.append('probe-drift')
if any(x['execution_status']!='PLANNED_NOT_RUN' for x in rows):fail.append('unearned-pass')
report={'scope':'R4 DESIGN-ONLY; no runtime implementation','requirements':len(ids),'semantic_oracles':len(rows),'probes':checks,'active_adr_count':len(active),'historical_r3_zip_crc':'PASS' if history_ok else 'FAIL','product_implementation':'NOT RUN','semantic_domain_validator':'NOT IMPLEMENTED','failures':fail}
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(1 if fail else 0)
