# PDF preservation fallback

Use only when native source is unavailable or unsuitable. Required inputs: original PDF and a MinerU `layout.json` whose `pdf_info` pages correspond exactly to it. MinerU extraction is an external dependency; reuse the caller's authorized wrapper/API/CLI. Do not copy machine-specific wrappers, keychain names, tokens or private repositories into this skill. Do not upload if the user requires offline processing.

```bash
python "$SKILL/scripts/pdf_layout.py" prepare input.pdf --layout layout.json --work "$WORK"
# Inspect blocks.json, coverage.json, protected.json and issues.json.
python "$SKILL/scripts/translate_blocks.py" --work "$WORK" \
  --base-url https://your-authorized-provider.example/v1 --model your-model
CJK_FONT='FandolSong-Regular.otf' python "$SKILL/scripts/pdf_layout.py" build --work "$WORK"
python "$SKILL/scripts/verify_pdf.py" "$WORK/translated.pdf" --out "$WORK/qa" \
  --source "$WORK/source.pdf" --layout-work "$WORK" --log "$WORK/translated.log"
```

Critical invariants learned from the full workflow:

1. Use MinerU **`preproc_blocks`**, not merged `para_blocks`/paragraph content lists: merged paragraphs can cross pages and cause duplicated or missing text in page-local overlays. Fail on unexpected `cross_page` spans or page count mismatch.
2. Keep figure/table/caption blocks and independent formulas protected. Use their **individual child rectangles**, not a broad union that may swallow a nearby biography or body paragraph. Inspect all overlap alerts. Misclassified `ref_text` and captions can contain real prose; audit residual English and author biographies.
3. Expand removal boxes enough to erase original ascenders/descenders, but do not erase formula brackets through virtual text bounding boxes. Inline mathematical spans are cropped from the source at 4× with baseline/depth metadata and inserted through immutable `@@M...@@` tokens. Native equations and original graphics stay vector where possible.
4. PyMuPDF redaction can remove formula characters even if visible glyphs appear outside the removal box. Restore independent protected regions from the source using clipped `show_pdf_page`, then compare source and redacted background. Do not blindly restore a misclassified large region over Chinese prose.
5. Treat `blocks.json` bounding boxes as layout data requiring review. Adjust paragraph/heading/list fit locally. Maintain readable body text and gaps; a universal shrink factor can make inline-math lists unreadable. `qa.json` flags small Chinese text (<6.8 pt), empty regions and missing glyphs. Prefer widening safe text areas or improving faithful phrasing over tiny fonts.
6. The build caches `background.pdf`. After editing removal boxes or adding/removing blocks, explicitly regenerate it in the working directory; translation-only corrections can reuse it. Keep manual changes in `overrides.json`.
7. Preserve `<sup>`/`<sub>` as superscript/subscript. Literal HTML tags or missing Unicode math glyphs can shrink text or corrupt values. Compile twice for TikZ page positioning.
8. Rendering the final overlay can involve tiny page-coordinate changes. Pixel differences in the final PDF alone do not prove image loss. Compare native raster hashes and exact source/background protected-region renders, then visually check the final page for overlay coverage. Hash checks do not cover vectors.

This is a source-page-backed LaTeX overlay project. It does not reconstruct author LaTeX and must not be described as doing so. Preserve its `background.pdf`, inline assets and source files together in the private working directory for future edits. Deliver the final PDF separately.
