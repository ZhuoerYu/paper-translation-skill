# Verification and completion evidence

## Content and structure

- Inventory every input, scope decision, version and output. Exclusions are reported; originals remain untouched.
- Require exact translated block-ID coverage and no empty translations. Detect all unresolved `@@L...@@`/`@@M...@@` tokens in delivered text. Translation API completion is not document completion.
- Validate all math and structural tokens before assembly. Native mode preserves protected spans byte-for-byte; compare original figure/table/formula bodies and source asset hashes after CJK/layout patches too.
- Audit extraction coverage: headings, footnotes, acknowledgments, biographies, custom macros, appendices and included files. References, captions and protected metadata are expected English; unexplained English body prose is not.
- Check cross-page/cross-column sentence fragments for duplication and silent completion. Check numerical values, units, signs, inequality directions, model/dataset names and percentage-vs-percentage-point claims. A numerical regex is only an alert system: “3D→三维” is valid, but OCR “Φ→8” changes meaning.
- Preserve source errors in formulas/scientific statements; a translation is not an unrequested corrigendum.

## Compilation and visuals

1. Require a successful final compile, normally two passes, with no missing characters, missing assets or unresolved citations/references. Inspect overfull boxes; distinguish cosmetic warnings from actual clipping.
2. Render **all final pages** and inspect them, using contact sheets for coverage and full-resolution crops for dense text, math, legends and boundaries. Check first/last pages, every figure/table, headers/footers, paragraph transitions, whitespace and line overlap.
3. Native reflow may change pagination. Match figure/table numbers, section coverage and mathematical content rather than forcing the original page count. A successful compile does not prove all original figures were included.
4. In PDF overlay mode, require original page count/dimensions, no untranslated empty regions, original raster image hashes preserved, and source/background protected-area comparisons. Follow with final visual checks: a protected background can still be covered by the translated overlay.
5. Fix only affected layout/translation regions, recompile and rerender the affected pages. A shared font/layout change requires review across the document. Do not keep rerunning unchanged checks once they pass.

## Delivery receipt

Copy final PDFs only after review. Reopen the **delivered** files; record page counts, file hashes, sizes and verification status in a separate work manifest. Confirm folder count and names, no excluded documents, no unintended ZIP/source/log files. Report actual results and limitations. Do not imply a human-certified translation or scientific validation.

## Reproducibility and API handling

Keep prompts, source hashes, exact model identifier, provider endpoint (without secrets), work manifests, per-batch fingerprints and manual overrides. Cache keys include the prompt/model/endpoint/input, so changing any invalidates stale translations. Invalid draft batches are retained only in the private work directory for diagnosis and must never be treated as validated outputs. On a bounded-retry failure, preserve valid batches, inspect the draft, repair only failing blocks using the same contract, and rerun deterministic validation. Do not weaken token checks to get a build.

Never print credentials, authorization headers, signed URLs or keychain values. Stop retrying rejected authentication; service quota/rate failures require a bounded strategy. Source and translated prose may be sent to the configured API, so respect offline/data-transfer requirements.
