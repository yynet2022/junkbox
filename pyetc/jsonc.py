import json
import re


def load_jsonc(text):
    # 1. 文字列 ("...")
    # 2. ブロックコメント (/*...*/)
    # 3. 行コメント (//...)
    # これらを順番に探し、コメントの場合だけ空文字に置き換える
    pattern = re.compile(
        r'("(?:\\.|[^"\\])*")|/\*[\s\S]*?\*/|//.*', re.MULTILINE
    )

    def replace(match):
        # group(1) は「文字列」にマッチした部分
        # 文字列にマッチした場合はそのまま返し、そうでなければ（コメン
        # トなら）消去
        if match.group(1):
            return match.group(1)
        else:
            return ""

    clean_text = pattern.sub(replace, text)
    return json.loads(clean_text)


if __name__ == "__main__":
    jsonc_data = """{\n "link": "https://example.com" // OK! \n}"""
    print(load_jsonc(jsonc_data))
