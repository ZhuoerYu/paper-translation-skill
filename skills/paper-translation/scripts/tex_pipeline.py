#!/usr/bin/env python3
"""Conservative LaTeX prose extraction; immutable math/assets/macros; no API calls."""
import argparse, collections, hashlib, json, re
from pathlib import Path
PROTECTED_ENVS = {'figure','figure*','table','table*','tabular','tabular*','longtable','equation','equation*','align','align*','alignat','alignat*','gather','gather*','multline','multline*','displaymath','math','eqnarray','eqnarray*','verbatim','Verbatim','lstlisting','minted','tikzpicture','algorithm','algorithm*','algorithmic','thebibliography'}
PROSE_COMMANDS = {'title','section','subsection','subsubsection','paragraph','subparagraph','chapter','part','footnote','footnotetext','textbf','textit','texttt','emph','textrm','textsf','textnormal','underline','thanks','caption','captionof'}
TOKEN = re.compile(r'@@L\d{6}@@')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def group_end(s,i):
    """Exclusive end of a balanced {} or [] group, respecting escapes/comments."""
    opening=s[i];closing={'{':'}','[':']'}[opening];depth=1;j=i+1
    while j<len(s):
        if s[j]=='\\': j+=2;continue
        if s[j]=='%':
            end=s.find('\n',j);j=len(s) if end<0 else end+1;continue
        if s[j]==opening:depth+=1
        elif s[j]==closing:
            depth-=1
            if depth==0:return j+1
        j+=1
    raise ValueError('Unbalanced group at '+str(i))
def mask_tex(source, fragment=False):
    masked=[];protected={};i=0
    def put(text,kind):
        key=f'@@L{len(protected)+1:06d}@@';protected[key]={'text':text,'kind':kind,'sha256':sha(text)};masked.append(key)
    if not fragment:
        m=re.search(r'\\begin\{document\}',source)
        if not m:raise ValueError('No document environment: use --fragment for included files')
        put(source[:m.end()],'preamble');i=m.end()
    while i<len(source):
        c=source[i]
        if c=='%':
            e=source.find('\n',i);e=len(source) if e<0 else e+1;put(source[i:e],'comment');i=e;continue
        m=re.match(r'\\begin\{([^}]+)\}',source[i:])
        if m and m[1] in PROTECTED_ENVS:
            env=m[1];pattern=re.compile(r'\\(begin|end)\{'+re.escape(env)+r'\}');depth=0;e=None
            for mm in pattern.finditer(source,i):
                depth+=1 if mm[1]=='begin' else -1
                if depth==0:e=mm.end();break
            if e is None:raise ValueError('Unclosed environment '+env)
            put(source[i:e],env);i=e;continue
        if c=='$' or source.startswith(('\\(','\\['),i):
            delimiter='$$' if source.startswith('$$',i) else '$' if c=='$' else source[i:i+2]
            closing={'\\(':'\\)','\\[':'\\]'}.get(delimiter,delimiter);j=i+len(delimiter)
            while True:
                e=source.find(closing,j)
                if e<0:raise ValueError('Unclosed math at '+str(i))
                # A delimiter preceded by an odd run of backslashes is escaped ($ only).
                backslashes=len(source[:e])-len(source[:e].rstrip('\\'))
                if closing.startswith('\\') or backslashes%2==0:break
                j=e+len(closing)
            e+=len(closing);put(source[i:e],'math');i=e;continue
        if c=='\\':
            m=re.match(r'\\(?:[A-Za-z@]+\*?|.)',source[i:],re.S)
            if not m:raise ValueError('Trailing backslash')
            e=i+m.end();name=m[0][1:].rstrip('*')
            if name not in PROSE_COMMANDS:
                # Preserve unknown commands and attached arguments. Review coverage for custom prose macros.
                while True:
                    j=e
                    while j<len(source) and source[j] in ' \t':j+=1
                    if j<len(source) and source[j] in '[{':e=group_end(source,j)
                    else:break
            put(source[i:e],'command');i=e;continue
        if c in '{}&#_^~':put(c,'syntax');i+=1;continue
        masked.append(c);i+=1
    return ''.join(masked),protected

def prepare(path,work,fragment=False):
    source=path.read_text();masked,protected=mask_tex(source,fragment);parts=re.split(r'(\n\s*\n)',masked);blocks=[];template=[]
    for part in parts:
        visible=TOKEN.sub('',part)
        if re.search(r'[A-Za-z]{2}',visible):
            ident=f't{len(blocks)+1:05d}';blocks.append({'id':ident,'source':part});template.append({'id':ident})
        else:template.append({'literal':part})
    work.mkdir(parents=True,exist_ok=True)
    data={'schema':1,'source_name':path.name,'source_sha256':sha(source),'fragment':fragment,'protected':protected,'template':template}
    (work/'tex_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(work/'blocks.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2))
    print(json.dumps({'blocks':len(blocks),'protected_kinds':dict(collections.Counter(x['kind'] for x in protected.values()))}))

def assemble(work,output):
    manifest=json.loads((work/'tex_manifest.json').read_text());blocks=json.loads((work/'blocks.json').read_text());translations=json.loads((work/'translations.json').read_text());overrides=work/'overrides.json'
    if overrides.exists():translations.update(json.loads(overrides.read_text()))
    assert set(translations)=={b['id'] for b in blocks},'Missing or extra translation IDs'
    for b in blocks:
        zh=translations[b['id']];assert zh.strip(),'Empty translation'
        assert TOKEN.findall(zh)==TOKEN.findall(b['source']),'Structural token order changed: '+b['id']
        remainder=TOKEN.sub('',zh)
        assert not re.search(r'[\\{}$&#_^~%]',remainder),'Unescaped LaTeX added in '+b['id']
    text=''.join(translations[x['id']] if 'id' in x else x['literal'] for x in manifest['template'])
    for key,value in manifest['protected'].items():
        assert text.count(key)==1,'Protected region missing/duplicated: '+key
    text=TOKEN.sub(lambda m:manifest['protected'][m[0]]['text'],text)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(text)
    # Check round-trip protected regions before adding separate CJK wrapper or explicit format patch.
    _,actual=mask_tex(text,manifest['fragment']);expected=[x['text'] for x in manifest['protected'].values() if x['kind']!='comment'];found=[x['text'] for x in actual.values() if x['kind']!='comment']
    assert expected==found,'Protected LaTeX changed during assembly'
    report={'protected_regions':len(actual),'protected_unchanged':True,'translated_blocks':len(blocks),'output_sha256':sha(text)}
    (work/'tex_integrity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('prepare');a.add_argument('input',type=Path);a.add_argument('--work',type=Path,required=True);a.add_argument('--fragment',action='store_true')
    a=sub.add_parser('assemble');a.add_argument('--work',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.action=='prepare':prepare(args.input,args.work,args.fragment)
    else:assemble(args.work,args.output)
if __name__=='__main__':main()
