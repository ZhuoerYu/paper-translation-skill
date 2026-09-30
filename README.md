# Paper Translation Skill

论文全文翻译技能：优先使用原始 LaTeX，保留原图、表格和公式，输出中文 LaTeX 与经过检查的 PDF。提示词、历史纠错经验、批次缓存和交付检查已集中记录；拿不到原始源码时，提供 MinerU + 原版面保留流程。

中文调用示例：`使用 $paper-translation 翻译这篇论文，正文只要中文，原图、表格、公式保留，PDF 放到 Downloads。`

A reusable agent skill for **LaTeX → Chinese translation → LaTeX → PDF**, with a MinerU-assisted PDF-preservation fallback. Built from an iterative workflow focused on retaining original figures, tables, formulas and readable academic formatting.

## Install

Copy `skills/paper-translation` to your agent's skill directory (for Codex: `~/.codex/skills/`). No credentials or private configuration are included. Agents supporting `SKILL.md` can load the same directory; other agents can read it as a workflow specification.

Invoke, for example:

> Use $paper-translation to translate this paper into Chinese. Preserve all original figures, tables and formulas. Put the PDF in my Downloads folder.

## What is included

- Native-LaTeX masking, stable translation units, immutable math/structure validation and reconstruction.
- Optional resumable translation through an explicitly configured OpenAI-compatible HTTPS API; agents may supply translations directly instead.
- PDF/MinerU fallback using page-local layout, original protected graphics and LaTeX text overlays.
- A maintained Chinese translation prompt, failure history, source-preservation rules and visual-verification checklist.
- Contact-sheet rendering, compiler diagnostics and image/preservation checks.

Start at [SKILL.md](skills/paper-translation/SKILL.md). Detailed execution commands are in [native LaTeX](skills/paper-translation/references/native-latex.md) and [PDF preservation](skills/paper-translation/references/pdf-preservation.md).

## Requirements

Python 3.10+, PyMuPDF and Pillow (`python -m pip install -r requirements.txt`), plus an existing XeLaTeX installation with Chinese fonts for compilation. The native extractor and API translator use only Python's standard library. MinerU is optional, externally configured, and needed only for the fallback's layout input. A translation API is optional; configure its base URL, model and API-key environment variable explicitly.

No installer changes system configuration. API credentials are read at runtime, never included here. API use can transmit paper text to the chosen provider. Use direct agent translation or an appropriate local workflow when external transfer is disallowed.

## Scope and limitations

Defaults: Chinese prose only; original English figures/tables/captions/formulas; exclude dissertations and PDFs over 50 pages; individual PDFs in a folder, no ZIP. Current user instructions override these choices.

The native extractor is a **conservative scanner, not a full TeX parser**. Inspect custom macros, included prose files and extraction coverage. The fallback creates a LaTeX overlay project, not recovered author source. Visual and semantic review remain required; a script reporting no missing images is not proof of scientific or translation correctness.

Default caption/bibliography protection and immutable tokens deliberately prioritize fidelity. Reflow can change the page count. Source materials and translated papers are not bundled or licensed by this repository.

## Validate

```bash
python -m unittest discover -s tests -v
python -m py_compile skills/paper-translation/scripts/*.py
```

Tests cover protected-environment/math round trips, corrupted-placeholder rejection, comment/escape handling and included fragments. A synthetic PDF/MinerU fixture exercises the fallback without redistributing a paper. Real-document verification should also inspect all final rendered pages.

## License

MIT for the original scripts and documentation in this repository. Third-party papers, templates, fonts, models and services retain their own terms. No third-party paper content is distributed.
