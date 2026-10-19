"""Run inside .venv-docling: python tools/docling_convert.py <file>  -> Markdown on stdout."""
import sys
from docling.document_converter import DocumentConverter

sys.stdout.write(DocumentConverter().convert(sys.argv[1]).document.export_to_markdown())
