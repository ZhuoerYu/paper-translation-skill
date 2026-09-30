#!/usr/bin/env python3
"""PDF/MinerU page-local preservation fallback. Requires PyMuPDF and XeLaTeX."""
import argparse,json,re,sys,subprocess,collections,shutil,os
from pathlib import Path
import pymupdf as f
def prepare(source,layout,r):
 name=source.stem;r.mkdir(parents=True,exist_ok=True)
 if (r/'blocks.json').exists():raise ValueError('Work already prepared; reuse it or choose a new directory')
 shutil.copy2(source,r/'source.pdf')
 data=json.loads(layout.read_text())['pdf_info']; src=f.open(r/'source.pdf')
 if len(data)!=len(src):raise ValueError(f'{name}: parsed {len(data)} / original {len(src)} pages')
 shutil.copy2(layout,r/'layout.json');assets=r/'inline_math';assets.mkdir(exist_ok=True)
 items=[];maths={};protected=[];issues=[];coverage=[]
 for pi,page in enumerate(data):
  p=src[pi];sw,sh=page['page_size'];sx=p.rect.width/sw;sy=p.rect.height/sh
  def rect(bb):return f.Rect(bb[0]*sx,bb[1]*sy,bb[2]*sx,bb[3]*sy)
  spans=[s for b in p.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans']]
  pb=[]
  for b in page['preproc_blocks']:
   if b['type'] in ('image','chart','table','interline_equation','code','algorithm'):
    parts=b.get('blocks') or [b]
    for child in parts:
     bb=rect(child['bbox'])
     pb.append(bb);protected.append({'page':pi+1,'type':child['type'],'bbox':list(bb)})
  for bi,b in enumerate(page['preproc_blocks']):
   if b['type'] not in ('text','title','abstract','list','paragraph','footnote'):continue
   if not b.get('lines'):continue
   bb=rect(b['bbox']); ss=[s for s in spans if bb.contains(f.Point((s['bbox'][0]+s['bbox'][2])/2,(s['bbox'][1]+s['bbox'][3])/2))]
   if ss:
    fs=collections.Counter({})
    for s in ss:fs[round(s['size'],1)]+=len(s['text'])
    fontsize=fs.most_common(1)[0][0]
    # Original text bounds ensure ascenders and descenders are fully erased.
    for s in ss:bb|=f.Rect(s['bbox'])
   else:fontsize=max(7,min(12,bb.height/max(1,len(b['lines']))*.8))
   if any((bb&pr).get_area()>min(bb.get_area(),pr.get_area())*.04 for pr in pb):
    issues.append({'page':pi+1,'index':bi,'issue':'text overlaps protected area','bbox':list(bb)})
   rows=[]
   for li,line in enumerate(b['lines']):
    chunks=[]
    for sp in line['spans']:
     if sp.get('cross_page'):raise ValueError('preproc cross page unexpectedly merged')
     if sp['type']=='inline_equation':
      key=f'@@M{len(maths)+1:06d}@@';mr=rect(sp['bbox'])+(-.4,-.4,.4,.4);mr&=p.rect
      namepng=f'math-{len(maths)+1:06d}.png';p.get_pixmap(matrix=f.Matrix(4,4),clip=mr,alpha=False).save(assets/namepng)
      near=[s for s in ss if abs((s['bbox'][1]+s['bbox'][3])/2-(mr.y0+mr.y1)/2)<fontsize*.7]
      baseline=collections.Counter(round(s['origin'][1],1) for s in near).most_common(1)
      depth=mr.y1-baseline[0][0] if baseline else mr.height*.2
      maths[key]={'file':'inline_math/'+namepng,'width':mr.width,'height':mr.height,'depth':max(-1,min(depth,fontsize*.5)),'latex':sp.get('content',''),'bbox':list(mr),'page':pi+1}
      chunks.append(key)
     else:chunks.append(sp.get('content',''))
    rows.append(' '.join(chunks))
   text='\n'.join(rows);text=re.sub(r'(?<=[A-Za-z])-\n(?=[a-z])','',text).replace('\n',' ').strip()
   if not text:continue
   # Chinese original paragraphs and pure numeric decorations need no replacement.
   if not re.search('[A-Za-z]{2}',text):continue
   items.append({'id':f'p{pi+1:04d}b{bi:03d}','page':pi+1,'bbox':list(bb),'font_size':fontsize,'kind':b['type'],'source':text})
  coverage.append({'page':pi+1,'translated_blocks':sum(x['page']==pi+1 for x in items),'types':dict(collections.Counter(b['type'] for b in page['preproc_blocks']))})
 for namefile,obj in [('blocks',items),('maths',maths),('protected',protected),('issues',issues),('coverage',coverage)]:
  (r/(namefile+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
 print(name,len(src),'pages',len(items),'blocks',len(maths),'inline formula crops',len(issues),'overlap alerts',flush=True)

ESC={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','^':r'\textasciicircum{}','~':r'\textasciitilde{}','\n':r'\\ ','λ':r'$\lambda$','α':r'$\alpha$','σ':r'$\sigma$','ϵ':r'$\epsilon$','×':r'$\times$','∈':r'$\in$','≤':r'$\leq$','≥':r'$\geq$','−':'-','–':'-',' ':' ','µ':r'$\mu$','μ':r'$\mu$','ω':r'$\omega$','°':r'$^{\circ}$','²':r'$^2$','³':r'$^3$','π':r'$\pi$','θ':r'$\theta$','δ':r'$\delta$','Δ':r'$\Delta$','β':r'$\beta$','η':r'$\eta$','τ':r'$\tau$','∞':r'$\infty$','±':r'$\pm$','≈':r'$\approx$','∑':r'$\sum$','∂':r'$\partial$','∇':r'$\nabla$','ε':r'$\epsilon$','φ':r'$\phi$','ρ':r'$\rho$','ψ':r'$\psi$','Φ':r'$\Phi$','Ω':r'$\Omega$','κ':r'$\kappa$','γ':r'$\gamma$','ν':r'$\nu$','ξ':r'$\xi$','ζ':r'$\zeta$','Γ':r'$\Gamma$','Σ':r'$\Sigma$','Π':r'$\Pi$','χ':r'$\chi$','ϕ':r'$\varphi$','ϑ':r'$\vartheta$','→':r'$\to$','·':r'$\cdot$'}
ESC.update({'∼':r'$\sim$','∗':r'$\ast$','∝':r'$\propto$'})
def escape(s):
 parts=re.split(r'(<(?:sup|sub)>.*?</(?:sup|sub)>)',s)
 out=[]
 for part in parts:
  m=re.fullmatch(r'<(sup|sub)>(.*?)</\1>',part)
  if m:out.append(('\\textsuperscript{' if m[1]=='sup' else '\\textsubscript{')+escape(m[2])+'}')
  else:out.append(''.join(ESC.get(c,c if ord(c)>=32 else '') for c in part))
 return ''.join(out)
def build(r):
 name=r.name
 items=json.loads((r/'blocks.json').read_text());tr=json.loads((r/'translations.json').read_text());maths=json.loads((r/'maths.json').read_text());src=f.open(r/'source.pdf');bg=f.open(r/'source.pdf')
 overrides=r/'overrides.json'
 if overrides.exists():tr.update(json.loads(overrides.read_text()))
 assert {i['id'] for i in items}<=set(tr)
 bypage=collections.defaultdict(list)
 for i in items:bypage[i['page']].append(i)
 if not (r/'background.pdf').exists():
  for pi,p in enumerate(bg):
   for i in bypage[pi+1]:p.add_redact_annot(f.Rect(i['bbox']),fill=False)
   if bypage[pi+1]:
    p.apply_redactions(images=0,graphics=0,text=0)
    for i in bypage[pi+1]:p.draw_rect(f.Rect(i['bbox']),color=None,fill=(1,1,1),overlay=True)
  # Restore original protected graphics as vectors after redaction; text virtual bboxes can intersect formula brackets.
  for pr in json.loads((r/'protected.json').read_text()):
   pi=pr['page']-1;rect=f.Rect(pr['bbox']);bg[pi].draw_rect(rect,color=None,fill=(1,1,1),overlay=True)
   bg[pi].show_pdf_page(rect,src,pi,clip=rect,overlay=True)
  bg.save(r/'background.pdf',garbage=4,deflate=True)
 def content(i):
  zh=tr[i['id']];assert sorted(re.findall(r'@@M\d+@@',zh))==sorted(re.findall(r'@@M\d+@@',i['source'])),i['id']
  out=[]
  for s in re.split(r'(@@M\d+@@)',zh):
   if s not in maths:out.append(escape(s));continue
   m=maths[s];out.append(r'\raisebox{%.3fbp}{\includegraphics[width=%.3fbp,height=%.3fbp]{%s}}'%(-m['depth'],m['width'],m['height'],m['file']))
  return ''.join(out)
 lines=[r'\documentclass{article}',r'\usepackage[UTF8,fontset=none]{ctex}',r'\setCJKmainfont{'+os.environ.get('CJK_FONT','FandolSong-Regular.otf')+'}',(r'\setmainfont{'+os.environ['LATIN_FONT']+'}' if os.environ.get('LATIN_FONT') else ''),r'\usepackage{amsmath,amssymb,pdfpages,graphicx,tikz,adjustbox}',r'\pagestyle{empty}',r'\setlength{\parindent}{0pt}',r'\begin{document}']
 for pi in range(len(src)):
  nodes=[]
  for i in bypage[pi+1]:
   x,y,x1,y1=i['bbox'];w=x1-x;h=y1-y;fs=i['font_size'];body=content(i)
   for following in bypage[pi+1]:
    fx,fy,fx1,fy1=following['bbox']
    if h>35 and fy>y+35 and min(x1,fx1)-max(x,fx)>min(w,fx1-fx)*0.5:h=min(h,fy-y-float(i.get('gap_after',4)))
   h=max(h,5)
   if i['kind']=='title':body=r'\bfseries '+body
   nodes.append(r'\node[anchor=north west,inner sep=0pt] at ([xshift=%.3fbp,yshift=-%.3fbp]current page.north west){\adjustbox{max width=%.3fbp,max totalheight=%.3fbp}{\begin{minipage}[t]{%.3fbp}\fontsize{%.2f}{%.2f}\selectfont\sloppy %s\end{minipage}}};'%(x,y,w,h,w,fs,fs*1.18,body))
  lines.append(r'\includepdf[pages=%d,fitpaper=true,pagecommand={\thispagestyle{empty}\begin{tikzpicture}[remember picture,overlay]%s\end{tikzpicture}}]{background.pdf}'%(pi+1,''.join(nodes)))
 lines.append(r'\end{document}');(r/'translated.tex').write_text('\n'.join(lines))
 chunks=[('translated',lines)];logs=[]
 for stem,chunklines in chunks:
  (r/(stem+'.tex')).write_text('\n'.join(chunklines))
  for count in range(2):
   proc=subprocess.run([shutil.which('xelatex') or '/Library/TeX/texbin/xelatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error',stem+'.tex'],cwd=r,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   (r/f'{stem}-compile-{count+1}.log').write_text(proc.stdout)
   if proc.returncode:print('COMPILE FAILED',name,stem,proc.stdout[-1500:],flush=True);raise RuntimeError('LaTeX compile failed')
  logs.append((r/(stem+'.log')).read_text())
 if len(chunks)>1:
  out=f.open()
  for stem,_ in chunks:
   with f.open(r/(stem+'.pdf')) as part:out.insert_pdf(part)
  out.save(r/'translated.pdf',garbage=4,deflate=True)
  (r/'translated.log').write_text('\n'.join(logs))
 result=f.open(r/'translated.pdf');tiny=[];empty=[]
 for i in items:
  p=result[i['page']-1];ch=[s for b in p.get_text('dict',clip=f.Rect(i['bbox'])+(-1,-1,1,1))['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans'] if re.search('[\u4e00-\u9fff]',s['text'])]
  if re.search('[\u4e00-\u9fff]',tr[i['id']]) and not ch:empty.append(i['id'])
  if ch and min(s['size'] for s in ch)<6.8:tiny.append({'id':i['id'],'size':min(s['size'] for s in ch),'zh':tr[i['id']]})
 report={'source_pages':len(src),'output_pages':len(result),'translated_blocks':len(items),'empty_regions':empty,'small_text':tiny,'missing_glyph_lines':[s for s in (r/'translated.log').read_text().splitlines() if 'Missing character:' in s]}
 (r/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BUILT',name,'pages',len(result),'empty',len(empty),'tiny',len(tiny),'glyph warnings',len(report['missing_glyph_lines']),flush=True)

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 a=sub.add_parser('prepare');a.add_argument('input',type=Path);a.add_argument('--layout',type=Path,required=True);a.add_argument('--work',type=Path,required=True);a.add_argument('--max-pages',type=int,default=50)
 a=sub.add_parser('build');a.add_argument('--work',type=Path,required=True)
 args=p.parse_args()
 if args.action=='prepare':
  with f.open(args.input) as src:
   if len(src)>args.max_pages:raise ValueError('PDF exceeds configured page limit')
  prepare(args.input,args.layout,args.work)
 else:build(args.work)
if __name__=='__main__':main()
