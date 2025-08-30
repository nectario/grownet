PDF=main.pdf

all: $(PDF)

$(PDF): main.tex sections/*.tex main.bib
	latexmk -pdf -interaction=nonstopmode main.tex

clean:
	latexmk -C
	rm -f $(PDF)

.PHONY: all clean