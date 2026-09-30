import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
SCRIPTS=Path(__file__).parents[1]/'skills/paper-translation/scripts'
spec=importlib.util.spec_from_file_location('tex_pipeline',SCRIPTS/'tex_pipeline.py');tex=importlib.util.module_from_spec(spec);spec.loader.exec_module(tex)
class TexTests(unittest.TestCase):
 def test_nested_protected_roundtrip(self):
  src=r'''\documentclass{article}
\begin{document}
\section{Title}
A sentence with $x^{2}$, \citep{key}, and \footnote{A note with \emph{emphasis}.}.

\begin{figure}\includegraphics{x.pdf}\caption{English $y$}\end{figure}
\begin{equation}x=\begin{cases}1&x>0\\0&x<0\end{cases}\end{equation}
\begin{table}\begin{tabular}{c}Original\end{tabular}\end{table}
\end{document}'''
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);p=d/'main.tex';p.write_text(src);tex.prepare(p,d/'w');blocks=json.loads((d/'w/blocks.json').read_text());(d/'w/translations.json').write_text(json.dumps({x['id']:x['source'] for x in blocks}));tex.assemble(d/'w',d/'out.tex');self.assertEqual(src,(d/'out.tex').read_text())
   kinds=[x['kind'] for x in json.loads((d/'w/tex_manifest.json').read_text())['protected'].values()];self.assertIn('figure',kinds);self.assertIn('equation',kinds);self.assertIn('table',kinds)
 def test_reject_corrupted_translation(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);p=d/'main.tex';p.write_text(r'\begin{document}Text $x$ here.\end{document}');tex.prepare(p,d/'w');b=json.loads((d/'w/blocks.json').read_text());t={x['id']:x['source'] for x in b};key=b[0]['id'];t[key]=tex.TOKEN.sub('',t[key]);(d/'w/translations.json').write_text(json.dumps(t))
   with self.assertRaises(AssertionError):tex.assemble(d/'w',d/'out.tex')
 def test_escaped_percent_and_comment(self):
  src='Text 10\\% and $x\\$y$ % comment\nnext'
  masked,protected=tex.mask_tex(src,True);rebuilt=tex.TOKEN.sub(lambda m:protected[m[0]]['text'],masked);self.assertEqual(src,rebuilt)
 def test_fragment_and_unknown_macro(self):
  s=r'\custom{Do not modify} \textbf{Translate this} and \(x\).';masked,p=tex.mask_tex(s,True);self.assertNotIn('Do not modify',masked);self.assertIn('Translate this',masked);self.assertEqual(sum(x['kind']=='math' for x in p.values()),1)
 def test_unclosed_math_fails(self):
  with self.assertRaises(ValueError):tex.mask_tex('unfinished $math',True)
 def test_unbalanced_group_fails(self):
  with self.assertRaises(ValueError):tex.mask_tex(r'\cite{broken',True)
class LayoutTests(unittest.TestCase):
 def test_synthetic_pdf_page_local_extraction(self):
  try:import pymupdf as f
  except ImportError:self.skipTest('PyMuPDF not installed')
  spec=importlib.util.spec_from_file_location('pdf_layout',SCRIPTS/'pdf_layout.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);doc=f.open();p=doc.new_page(width=400,height=500);p.insert_text((40,60),'Example text');p.draw_rect(f.Rect(40,100,160,200));doc.save(d/'in.pdf')
   layout={'pdf_info':[{'page_size':[400,500],'preproc_blocks':[{'type':'text','bbox':[40,45,120,65],'lines':[{'spans':[{'type':'text','content':'Example text'}]}]},{'type':'image','bbox':[40,100,160,200],'blocks':[{'type':'image_body','bbox':[40,100,160,200]}]}]}]};(d/'layout.json').write_text(json.dumps(layout));m.prepare(d/'in.pdf',d/'layout.json',d/'w');b=json.loads((d/'w/blocks.json').read_text());self.assertEqual(b[0]['source'],'Example text');self.assertEqual(len(json.loads((d/'w/protected.json').read_text())),1)
if __name__=='__main__':unittest.main()
