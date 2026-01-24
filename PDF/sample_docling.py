#
# pip install docling
#
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("example.pdf")

# Markdownとして出力
print(result.document.export_to_markdown())
