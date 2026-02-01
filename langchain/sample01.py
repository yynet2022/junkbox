#
# pip install langchain langchain-openai langgraph pydantic
#
import logging
import sys
from typing import List, Literal, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# from langgraph.prebuilt import ToolNode
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

logging.basicConfig(level=logging.INFO)


# ==========================================
# 1. データ構造定義 (Pydantic / State)
# ==========================================
class ConsultationDecision(BaseModel):
    """AIが思考した結果の構造化データ"""

    thought_process: str = Field(
        description=(
            "現在の会話状況の分析。何が不足しているか、"
            "どの規定を参照すべきかの思考。"
        )
    )
    response_to_user: str = Field(
        description="ユーザーへの回答。質問、または最終的な案内文。"
    )
    status: Literal["continue", "complete"] = Field(
        description=(
            "まだ情報不足で質問を続ける場合は'continue'、"
            "手順が確定した場合は'complete'。"
        )
    )
    final_procedure_markdown: Optional[str] = Field(
        default=None,
        description=(
            "statusが'complete'の時のみ出力される、"
            "確定した手順書のMarkdown本文。"
        ),
    )


class AgentState(TypedDict):
    """グラフ内で保持される状態"""

    messages: List[BaseMessage]  # 会話履歴
    context_data: str  # 検索された社内規定の内容
    is_complete: bool  # 完了フラグ


# ==========================================
# 2. 模擬データベース検索関数 (ここがRAGの接続点)
# ==========================================
def retrieve_guidelines(query: str) -> str:
    """
    【ここを本番のVector DB検索に置き換えます】
    ユーザーのクエリに基づいて、関連する社内規定Markdownを取得する関数。
    今回は動作確認用に、メモリ上の辞書から返す実装にしています。
    """
    # 実際にはここで ChromaDB や FAISS を検索します
    # results = vector_store.similarity_search(query)
    # return results[0].page_content

    print(f"\n[SYSTEM LOG] データベースを検索中... Query: '{query}'")

    # ダミーデータ：本来はPDFから変換・整形されたMarkdown
    full_knowledge_base = """
# 社内規定 A014-004-001: 契約手続きガイドライン

## 1. 契約分類の特定
契約手続きを進める場合、まずは以下の分類に従って担当部署を特定してください。
* **事業計画に関する契約**: 経営企画室へ。
* **知財に関する契約**: 知財部へ。
* **技術に関する契約**: 技術管理部へ。

## 2. 技術契約の詳細 (分類が「技術」の場合)
技術契約の場合、さらに詳細な分類が必要です。
* **共同研究**: 大学や他社と共に研究を行う場合。規定 A017参照。
* **委託研究**: 自社の費用で外部に研究を委託する場合。

# 社内規定 A017-002-001: 共同研究取扱規定
共同研究を行う場合、以下のリスク管理チェックが必須です。
1. **相手先の構成**: 単独機関か、複数機関か？
2. **相手先の種類**: 大学のみか、企業も含むか？
3. **地域**: 国内か、海外か？ (海外の場合は安保理規定チェックが必要)
"""
    return full_knowledge_base


# ==========================================
# 3. ノード関数の実装
# ==========================================
def retrieval_node(state: AgentState):
    """
    会話の初期、または文脈が変わった時に規定を検索するノード
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 既にコンテキストがある場合は検索をスキップするなどの制御も可能ですが、
    # ここではシンプルに最新のユーザー発言で検索を更新するロジックにします
    if isinstance(last_message, HumanMessage):
        retrieved_text = retrieve_guidelines(last_message.content)
        return {"context_data": retrieved_text}
    return {}


def consultant_node(state: AgentState):
    """
    規定と会話履歴を元に、次の方針（質問or回答）を決定するノード
    """
    messages = state["messages"]
    context = state.get("context_data", "")

    # モデル設定
    llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL"), temperature=0)
    # 構造化出力を強制
    structured_llm = llm.with_structured_output(ConsultationDecision)

    system_prompt = f"""
    あなたは論理的な社内規定コンサルタントAIです。
    ユーザーの要望に対し、提供された【社内規定データ】を厳密に参照して手続きを案内してください。

    # 行動指針
    1. 規定上の分岐条件（分類、相手先、条件など）が全てクリアになるまで、ユーザーに質問を繰り返してください（Slot Filling）。
    2. 決して推測で回答しないでください。情報が足りない場合は必ず質問してください。
    3. 必要な情報が全て揃ったら、statusを "complete" にし、詳細な手順書を作成してください。

    # 社内規定データ
    {context}
    """

    # 推論実行
    # SystemMessageで役割を与え、messagesで履歴を渡す
    response: ConsultationDecision = structured_llm.invoke(
        [SystemMessage(content=system_prompt)] + messages
    )

    # 結果をステートに反映
    # AIの回答を履歴に追加
    ai_message = AIMessage(content=response.response_to_user)

    return {
        "messages": [ai_message],
        "is_complete": response.status == "complete",
        # 完了時は最終成果物もログに残すなどの処理が可能
    }


# ==========================================
# 4. エッジ（条件分岐）の実装
# ==========================================
def route_condition(state: AgentState):
    """
    Consultantの判断結果(is_complete)を見て、
    処理を終了するか、ユーザー入力を待つかを決める
    """
    if state["is_complete"]:
        return "end"  # 完了 -> 終了
    else:
        return "continue"  # 未完了 -> ユーザー入力待ちへ


# ==========================================
# 5. グラフの構築 (LangGraph)
# ==========================================
def build_graph():
    workflow = StateGraph(AgentState)

    # ノード登録
    workflow.add_node("retriever", retrieval_node)
    workflow.add_node("consultant", consultant_node)

    # エントリーポイント設定
    # 開始 -> まず検索(retriever) -> 次に思考(consultant)
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "consultant")

    # 条件付きエッジの設定
    # consultantの後は、条件によって終了か継続か分かれる
    workflow.add_conditional_edges(
        "consultant",
        route_condition,
        {
            "continue": END,  # ここでENDに行くと、Graphの1回の実行が終わり、Pythonのinputループに戻る
            "end": END,  # 完了時もENDだが、フラグが立っているのでループを抜ける処理ができる
        },
    )

    return workflow.compile()


# ==========================================
# 6. 対話実行ループ (アプリケーション本体)
# ==========================================
def main():
    print("--- 社内規定RAGエージェント (初期化中...) ---")
    try:
        app = build_graph()
    except Exception as e:
        print(f"グラフ構築エラー: {e}")
        return

    # 会話履歴の初期化
    chat_history = []

    print("AI: こんにちは。社内手続きについて何かお手伝いしましょうか？")
    print("(「終了」と入力すると終わります)")

    while True:
        # 1. ユーザー入力の受付
        try:
            user_input = input("\nUser: ")
        except EOFError:
            break

        if not user_input or user_input.strip() == "":
            continue
        if user_input.strip() in ["終了", "exit", "quit"]:
            print("AI: 終了します。お疲れ様でした。")
            break

        # 2. メッセージ履歴の更新
        user_message = HumanMessage(content=user_input)
        chat_history.append(user_message)

        # 3. グラフの実行 (ここがAIの思考プロセス)
        # 現在の履歴を渡して実行する
        # final_state = None

        # app.streamだと途中経過が見えるが、今回はシンプルにinvokeで結果を取得
        inputs = {
            "messages": chat_history,
            "context_data": "",  # 初回は空、Retrieverが埋める
            "is_complete": False,
        }

        try:
            # グラフ実行
            result_state = app.invoke(inputs)

            # 4. AIの応答を表示
            latest_ai_message = result_state["messages"][-1]
            print(f"AI: {latest_ai_message.content}")

            # 履歴を更新 (AIの返答を履歴に追加しておく)
            # LangGraphのinvokeは新しいメッセージだけを返す設定もできるが、
            # ここではResultから全履歴を取るか、差分を取るか制御が必要。
            # 今回のコードでは、Graph内でappendされたmessagesが返ってくる想定。
            chat_history = result_state["messages"]

            # 5. 完了判定
            if result_state.get("is_complete"):
                print("\n--- 手続き案内が完了しました ---")
                # ここでループを抜けるか、履歴をクリアして次に行くか選べます
                # 今回はリセットして継続するか聞く形にします
                if input("\n他の相談をしますか？ (y/n): ").lower() != "y":
                    break
                else:
                    chat_history = []  # 履歴リセット
                    print("\nAI: 新しい相談をどうぞ。")
        except Exception as e:
            print(f"{e.__class__.__name__}: {e}")
            break


if __name__ == "__main__":
    # APIキーチェック
    import os

    for x in ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"]:
        if not os.environ.get(x):
            print("エラー: 環境変数 OPENAI_API_KEY が設定されていません。")
            sys.exit(1)

    main()
