#
# pip install pymupdf4llm
#
import pymupdf4llm

# Markdown 文字列として取得
md_text = pymupdf4llm.to_markdown("example.pdf")

print(md_text)
