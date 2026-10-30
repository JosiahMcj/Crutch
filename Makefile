.PHONY: paper figures pdf
paper:
	python3 scripts/tables.py && python3 scripts/build_paper.py
figures:
	python3 scripts/figures.py
pdf:
	python3 scripts/render_pdf.py
