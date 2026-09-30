#!/usr/bin/env python3
"""Render contact sheets and report PDF readability, images, and compiler diagnostics."""
import argparse,hashlib,json,re
from pathlib import Path
import pymupdf as f
from PIL import Image,ImageDraw,ImageChops,ImageStat

def verify(pdf,out,source=None,log=None,layout_work=None):
 out.mkdir(parents=True,exist_ok=True);doc=f.open(pdf);report={'pages':len(doc),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'blank_pages':[],'replacement_char_pages':[],'missing_images':[]}
 for i,p in enumerate(doc):
  t=p.get_text()
  if '\ufffd' in t:report['replacement_char_pages'].append(i+1)
  if not t.strip() and not p.get_images() and not p.get_drawings():report['blank_pages'].append(i+1)
 for start in range(0,len(doc),4):
  sheet=Image.new('RGB',(1400,1980),'#ddd');draw=ImageDraw.Draw(sheet)
  for j in range(start,min(start+4,len(doc))):
   page=doc[j];pix=page.get_pixmap(matrix=f.Matrix(1.6,1.6),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.thumbnail((680,950));x=(j-start)%2*700;y=(j-start)//2*990;sheet.paste(im,(x,y+25));draw.text((x+5,y+5),str(j+1),fill='black')
  sheet.save(out/f'contact-{start+1:03d}.jpg',quality=92)
 if source:
  src=f.open(source);report['source_pages']=len(src)
  # Global comparison accommodates reflow. Embedded raster hashes do not cover vector graphics.
  expected={x['digest'] for p in src for x in p.get_image_info(hashes=True)};actual={x['digest'] for p in doc for x in p.get_image_info(hashes=True)}
  report['original_raster_images']=len(expected);report['missing_images']=[x.hex() for x in expected-actual]
 if log:
  lines=log.read_text(errors='replace').splitlines();report['compiler_alerts']=[s for s in lines if any(x in s for x in ('Missing character:','undefined references','Citation `','Overfull \\hbox','Overfull \\vbox'))]
 if layout_work:
  assert source,'--source required for layout preservation verification';bg=f.open(layout_work/'background.pdf');src=f.open(source);alerts=[];protected=json.loads((layout_work/'protected.json').read_text())
  for pr in protected:
   pi=pr['page']-1;rect=f.Rect(pr['bbox']);ims=[]
   for document in (src,bg):
    pix=document[pi].get_pixmap(matrix=f.Matrix(1.5,1.5),clip=rect,alpha=False);ims.append(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
   mean=sum(ImageStat.Stat(ImageChops.difference(*ims)).mean)/3
   if mean>0.5:alerts.append(dict(pr,pixel_difference=mean))
  report['protected_regions']=len(protected);report['protected_background_alerts']=alerts
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path);p.add_argument('--log',type=Path);p.add_argument('--layout-work',type=Path);a=p.parse_args();verify(a.pdf,a.out,a.source,a.log,a.layout_work)
