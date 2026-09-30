#!/usr/bin/env python3
"""Resumable OpenAI-compatible JSON translation. Explicit endpoint/model/key env."""
import argparse, concurrent.futures, hashlib, json, os, re, time, urllib.error, urllib.request
from pathlib import Path
PAT=re.compile(r'@@[LM]\d+@@')
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--base-url',required=True);p.add_argument('--model',required=True);p.add_argument('--key-env',default='TRANSLATION_API_KEY');p.add_argument('--workers',type=int,default=3);p.add_argument('--batch-chars',type=int,default=5500);p.add_argument('--prompt',type=Path,default=Path(__file__).parents[1]/'prompts/translation-zh.txt');a=p.parse_args()
 if not a.base_url.startswith('https://'):raise ValueError('Use an HTTPS API endpoint')
 key=os.environ.get(a.key_env)
 if not key:raise ValueError('Required API-key environment variable is not set')
 prompt=a.prompt.read_text();blocks=json.loads((a.work/'blocks.json').read_text());jobs=[];batch=[];size=0
 for b in blocks:
  if batch and (size+len(b['source'])>a.batch_chars or len(batch)>=15):jobs.append(batch);batch=[];size=0
  batch.append({'id':b['id'],'text':b['source']});size+=len(b['source'])
 if batch:jobs.append(batch)
 cache=a.work/'translations';cache.mkdir(exist_ok=True)
 def validate(batch,pairs):
  if [x['id'] for x in pairs]!=[x['id'] for x in batch]:raise ValueError('Translation IDs mismatch')
  for old,new in zip(batch,pairs):
   if not isinstance(new['zh'],str) or not new['zh'].strip():raise ValueError('Empty translation')
   if PAT.findall(old['text'])!=PAT.findall(new['zh']):raise ValueError('Placeholder order mismatch '+old['id'])
   if '@@L' in old['text'] and re.search(r'[\\{}$&#_^~%]',PAT.sub('',new['zh'])):raise ValueError('New raw TeX syntax '+old['id'])
 def run(job):
  num,batch=job;fingerprint=hashlib.sha256(json.dumps([prompt,a.model,a.base_url,batch],ensure_ascii=False).encode()).hexdigest();dest=cache/f'batch-{num:04d}.json'
  if dest.exists():
   old=json.loads(dest.read_text())
   if old.get('hash')==fingerprint:validate(batch,old['pairs']);return old['pairs']
  for attempt in range(4):
   try:
    payload={'model':a.model,'temperature':0.1,'max_tokens':8192,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(batch,ensure_ascii=False)+(('严格按以下顺序保留每项占位符，调整中文句式以适应原顺序，不要将文献作者提前：'+json.dumps({b['id']:PAT.findall(b['text']) for b in batch})) if attempt else '')}]}
    req=urllib.request.Request(a.base_url.rstrip('/')+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=240) as response:result=json.load(response)
    if result['choices'][0].get('finish_reason')=='length':raise ValueError('Output truncated; lower --batch-chars')
    pairs=json.loads(result['choices'][0]['message']['content'])['translations']
    (a.work/f'draft-batch-{num:04d}.json').write_text(json.dumps(pairs,ensure_ascii=False,indent=2))
    validate(batch,pairs)
    temp=dest.with_suffix('.tmp');temp.write_text(json.dumps({'hash':fingerprint,'pairs':pairs,'usage':result.get('usage')},ensure_ascii=False,indent=2));temp.replace(dest);print(f'Batch {num}/{len(jobs)} complete',flush=True);return pairs
   except urllib.error.HTTPError as e:
    if e.code in (401,403):raise RuntimeError('API authentication/authorization rejected') from None
    if attempt==3:raise RuntimeError('API HTTP status '+str(e.code)) from None
   except Exception as e:
    if attempt==3:raise RuntimeError(type(e).__name__+': '+str(e)[:160]) from None
   time.sleep(2**attempt)
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:results=list(pool.map(run,enumerate(jobs,1)))
 translations={x['id']:x['zh'] for pairs in results for x in pairs};assert set(translations)=={b['id'] for b in blocks}
 (a.work/'translations.json').write_text(json.dumps(translations,ensure_ascii=False,indent=2));print('Complete:',len(translations),'blocks')
if __name__=='__main__':main()
