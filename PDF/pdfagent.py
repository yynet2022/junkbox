import os
import json
import base64
from openai import OpenAI
import fitz  # PyMuPDF

# =====================================================================
# SECTION 1: PyMuPDF をラップしたツール関数群の定義
# =====================================================================

class PDFAgentTools:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        # アンチエイリアスを最大に設定
        fitz.set_aa_level(8)

    def get_pdf_structure(self) -> str:
        """PDF全体の目次と、各ページの文字数などの概要（地図）を取得する"""
        doc = fitz.open(self.pdf_path)
        structure = {
            "total_pages": len(doc),
            "table_of_contents": doc.get_toc(),
            "pages_summary": []
        }
        for page_num in range(len(doc)):
            page = doc[page_num]
            structure["pages_summary"].append({
                "page": page_num + 1,
                "text_length": len(page.get_text().strip()),
                "has_tables_hint": len(page.find_tables().tables) > 0
            })
        doc.close()
        return json.dumps(structure, ensure_ascii=False)

    def extract_text_by_region(self, page_num: int, bbox: list = None) -> str:
        """指定したページのテキスト、または特定座標(BBox)内のテキストを抽出する"""
        doc = fitz.open(self.pdf_path)
        page = doc[page_num - 1]
        if bbox:
            # bbox = [x0, y0, x1, y1]
            rect = fitz.Rect(bbox)
            text = page.get_text("text", clip=rect)
        else:
            # 指定がなければページ全体のテキスト（blocks形式でレイアウト維持）
            blocks = page.get_text("blocks")
            text = "\n".join([b[4] for b in blocks])
        doc.close()
        return json.dumps({"page": page_num, "text": text}, ensure_ascii=False)

    def find_elements_on_page(self, page_num: int) -> str:
        """ページ内にある「表(Table)」や「図(Drawing)」および「埋め込み画像(Image)」の座標(BBox)を検出する"""
        doc = fitz.open(self.pdf_path)
        page = doc[page_num - 1]
        
        tables = page.find_tables()
        table_bboxes = [list(t.bbox) for t in tables.tables]
        
        drawings = page.get_drawings()
        # 小さなベクター線を除外するため、ある程度の面積を持つ矩形(rect)を抽出
        drawing_bboxes = []
        for d in drawings:
            if "rect" in d and (d["rect"].width > 50 and d["rect"].height > 50):
                drawing_bboxes.append(list(d["rect"]))
                
        # 埋め込みラスター画像の矩形領域を抽出
        image_bboxes = []
        for img_info in page.get_images():
            xref = img_info[0]
            for rect in page.get_image_rects(xref):
                if rect.width > 50 and rect.height > 50:
                    image_bboxes.append(list(rect))

        doc.close()
        return json.dumps({
            "page": page_num,
            "detected_tables_bbox": table_bboxes,
            "detected_drawings_bbox": drawing_bboxes,
            "detected_images_bbox": image_bboxes
        }, ensure_ascii=False)

    def render_region_to_base64(self, page_num: int, bbox: list = None, dpi: int = 200) -> str:
        """指定したページ、または特定座標(BBox)を高画質画像(Base64)化する"""
        doc = fitz.open(self.pdf_path)
        page = doc[page_num - 1]
        
        # 描画対象の矩形を設定
        rect = fitz.Rect(bbox) if bbox else page.rect
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        
        # メモリ上でPNGバイトデータに変換
        img_bytes = pix.tobytes("png")
        doc.close()
        
        # Base64文字列にして返す
        return base64.b64encode(img_bytes).decode("utf-8")


# =====================================================================
# SECTION 2: OpenAI API 用の Function Calling (Tools) 定義
# =====================================================================

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_pdf_structure",
            "description": "PDFの総ページ数、目次(TOC)、各ページの文字数などの概要を取得し、文書の全体マップを把握する。"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_text_by_region",
            "description": "指定したページのテキスト、または特定のBBox(座標)範囲内のテキストを正確に抽出する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_num": {"type": "integer", "description": "ページ番号 (1始まり)"},
                    "bbox": {"type": "array", "items": {"type": "number"}, "description": "[x0, y0, x1, y1] の座標。ページ全体なら省略可。"}
                },
                "required": ["page_num"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_elements_on_page",
            "description": "ページ内にある『表(Table)』や『図・グラフ(Drawing)』および『埋め込み画像(Image)』の正確な座標(BBox)を検出する。画像化して視覚的に解析したい領域の座標を特定するために使用する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_num": {"type": "integer", "description": "ページ番号 (1始まり)"}
                },
                "required": ["page_num"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "render_region_to_base64",
            "description": "指定したページ、または特定のBBox(座標)範囲を高画質画像(Base64)としてレンダリングする。図表の目視確認や、複雑なレイアウトのVision解析が必要な場合に実行する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_num": {"type": "integer", "description": "ページ番号 (1始まり)"},
                    "bbox": {"type": "array", "items": {"type": "number"}, "description": "[x0, y0, x1, y1] の座標。ページ全体なら省略可。"},
                    "dpi": {"type": "integer", "description": "解像度。通常は200、細かい文字は300を指定。", "default": 200}
                },
                "required": ["page_num"]
            }
        }
    }
]


# =====================================================================
# SECTION 3: Agent メイン制御ループ（ReAct エージェント）
# =====================================================================

def run_pdf_agent(pdf_path: str, user_instruction: str):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    pdf_tools = PDFAgentTools(pdf_path)
    
    # システムプロンプトで Agent の行動指針を決定
    system_prompt = (
        "あなたはPDF文書の高度な解析・構造化を行うAIエージェントです。提供されたツールを自律的に使い、指示されたタスクを達成してください。\n"
        "【行動プロセス】\n"
        "1. まず `get_pdf_structure` で文書の全体像を把握する。\n"
        "2. 必要なページのテキストを読み進める。\n"
        "3. 表、数式、複雑なパワポ図形、レイアウト崩れが疑われる箇所を見つけたら、`find_elements_on_page` で座標を特定し、"
        "`render_region_to_base64` で画像としてあなた自身のVision機能で『二度見（視覚的検証）』して解析する。\n"
        "4. 完全に情報を掌握したら、最終的な構造化データをユーザーに提示する。\n"
        "多少のステップ数がかかっても構いません。確実で高品質な結果を求めています。"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]
    
    max_iterations = 15  # 無限ループ防止のセーフティ
    for iteration in range(max_iterations):
        print(f"\n--- 思考サイクル {iteration + 1} ---")
        
        # LLMの呼び出し
        response = client.chat.completions.create(
            model="gpt-4o",  # ターゲットモデル（Vision対応）
            messages=messages,
            tools=tools_definition,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        # 思考内容のログ出力
        if response_message.content:
            print(f"[Agent Thoughts]: {response_message.content}")
            
        # Tool の呼び出し要求がない場合は、最終回答に達したとみなし終了
        if not response_message.tool_calls:
            print("\nタスク完了。最終出力を生成しました。")
            return response_message.content
            
        # 並列ツール呼び出し時に role: tool の連続性を崩さないための画像メッセージ一時退避リスト
        pending_image_contents = []

        # Tool の実行ループ
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            print(f"[Tool Call]: {function_name} with args {function_args}")
            
            # --- 通常のテキストを返すツールの処理 ---
            if function_name != "render_region_to_base64":
                if function_name == "get_pdf_structure":
                    tool_output = pdf_tools.get_pdf_structure()
                elif function_name == "extract_text_by_region":
                    tool_output = pdf_tools.extract_text_by_region(
                        page_num=function_args.get("page_num"),
                        bbox=function_args.get("bbox")
                    )
                elif function_name == "find_elements_on_page":
                    tool_output = pdf_tools.find_elements_on_page(page_num=function_args.get("page_num"))
                else:
                    tool_output = json.dumps({"error": f"Unknown function: {function_name}"})
                
                # 通常のテキストレスポンスを履歴に追加
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output,
                })
                print(f"[Tool Output]: (テキストデータが返却されました)")

            # --- 画像化ツールの処理（Vision連携） ---
            else:
                base64_image = pdf_tools.render_region_to_base64(
                    page_num=function_args.get("page_num"),
                    bbox=function_args.get("bbox"),
                    dpi=function_args.get("dpi", 200)
                )
                
                # 1. ツール呼び出しに対する正常応答（role: tool）を返却
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({
                        "status": "success",
                        "message": "Image rendered successfully. The image data is provided as visual input."
                    })
                })
                
                # 2. 画像データは直後に挿入せず、リストに退避
                pending_image_contents.append({
                    "type": "text",
                    "text": f"ページ {function_args.get('page_num')} の指定領域のレンダリング画像です:"
                })
                pending_image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
                print(f"[Tool Output]: 画像（Base64）を生成しました。")

        # すべての role: tool メッセージが完了した後に、まとめて視覚情報（role: user）を注入
        if pending_image_contents:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "（システム自動フィードバック）要求された画像です。この視覚情報を元に解析を続けてください。"
                    },
                    *pending_image_contents
                ]
            })
            print(f"[Vision Input]: 画像データをコンテキストに注入しました。")

    print("規定の最大ステップ数に達しました。")
    return "解析がタイムアウトしました。"


# =====================================================================
# 実行例
# =====================================================================
if __name__ == "__main__":
    # 使用例（環境変数に OPENAI_API_KEY がセットされている必要があります）
    # res = run_pdf_agent("sample_paper.pdf", "この論文の第3章にある『実験結果の表』と『システム構成図』を見つけ、JSON形式で詳細に構造化データにしてください。")
    # print(res)
    pass
