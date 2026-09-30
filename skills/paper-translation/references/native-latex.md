# Native LaTeX workflow

## Input and baseline

Identify the root `.tex`, `\input`/`\include` dependencies, bibliography or `.bbl`, class/style files, images and fonts. If downloading source, match the supplied PDF's version and title; reject archive traversal, links and device entries; cap archive size. Record SHA-256 of source PDF and assets. Inspect custom macros and compile the original project in an isolated copy, with `-no-shell-escape`, when feasible. Never execute build scripts from untrusted source automatically.

Use a separate project copy. Keep `.sty`, `.cls`, `.bib`, `.bbl` and figure files unchanged. Do not send figures or secrets to a text-translation API. Any remote translation must fit the user's data-transfer constraints and configured provider authorization.

## Extract → translate → assemble

Let `SKILL` be this skill directory, `WORK` a caller-selected intermediate directory, and `PROJECT` the copied project:

```bash
python "$SKILL/scripts/tex_pipeline.py" prepare "$PROJECT/main.tex" --work "$WORK"
python "$SKILL/scripts/translate_blocks.py" --work "$WORK" \
  --base-url https://your-authorized-provider.example/v1 \
  --model your-model --key-env TRANSLATION_API_KEY
python "$SKILL/scripts/tex_pipeline.py" assemble --work "$WORK" --output "$PROJECT/translated.tex"
```

The API command is optional. An agent can produce `translations.json` as `{block_id: translated_string}` from `blocks.json` using the same prompt, preserving **every placeholder in order**. Place manual corrections in `overrides.json` with the same mapping format. Never overwrite translated prose with a summary.

`tex_pipeline.py` is a conservative scanner, not a full TeX interpreter. It masks the preamble, complete figure/table/math/code/bibliography environments, inline math, non-prose command arguments, braces and TeX syntax. Standard prose macros have their text translated. Unknown macros and author metadata remain protected. **Inspect `blocks.json` and the manifest for missing prose in custom macros, included files and theorem-like structures**. Translate included text files with `--fragment`, using separate work directories; preserve paths and assemble each translated file into the copied project. Expand the explicit prose-command set only after inspecting the macro definition. Verbatim/custom delimiters require manual handling. Do not claim arbitrary TeX is automatically supported.

Protected tokens are ordered deliberately: render “the function, denoted X, introduced by reference Y” in a Chinese sentence that keeps X before Y. Never move structural braces, math or references to make the sentence more idiomatic. The pipeline rejects new raw TeX special characters; use existing tokens or Chinese punctuation. A placeholder mismatch is a failed translation, not grounds to disable validation.

## CJK adaptation and build

Keep reconstructed `translated.tex` unchanged as the integrity baseline. Create a separate compile entry by inserting a documented CJK preamble change before `\begin{document}`:

```latex
\usepackage[UTF8,scheme=plain,fontset=fandol]{ctex}
```

Use a verified local CJK font if the template needs it. Preserve caption names in English when ctex would localize them. Translate abstract/bibliography heading names via explicit template-specific changes if needed. Any required preamble or layout change must be recorded separately from translation. No automatic install is required if the toolchain exists.

Run XeLaTeX twice, without shell escape. Use `latexmk -xelatex -interaction=nonstopmode` or two explicit `xelatex -no-shell-escape -halt-on-error` calls. A supplied `.bbl` is normally resolved by **job name**, not the `\bibliography{...}` argument: copy it to the translated job name in the working project when the `.bib` is absent. If a `.bib` is present, use the required BibTeX/Biber sequence. Never hide undefined citations by deleting citation commands.

If a desktop built-in compiler supports the project, it may be used without opening a panel. Multi-file/assets projects may need the installed external compiler. Respect the user's no-auto-preview preference.

Render the final PDF and complete verification. Original forced page breaks may cause excessive whitespace after Chinese reflow; any removal is a documented layout patch, not a content change. Do not shrink entire papers to force the original page count.
