# Build instructions for the IEEE paper

Requirements:
- `pdflatex` or `latexmk` (TeX Live recommended)

Build PDF:

```bash
cd paper
latexmk -pdf zero_day_ieee.tex
# or:
pdflatex zero_day_ieee.tex
bibtex zero_day_ieee
pdflatex zero_day_ieee.tex
pdflatex zero_day_ieee.tex
```

The generated PDF will be `zero_day_ieee.pdf` in the `paper/` directory.
