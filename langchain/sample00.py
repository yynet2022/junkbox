import os
from typing import Annotated, List, Optional, TypedDict
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

# --- 1. ダミーデータの準備 (本来はVector DBから取得したMarkdown) ---
# ユーザーの質問「契約を進めたい」で検索ヒットしたと仮定する規定データ
DUMMY_CONTEXT_MD = """
# 社内規定 A014-004-001: 契約手続きガイドライン

## 1. 契約分類の特定
契約手続きを進める場合、まずは以下の分類に従って担当部署を特定してください。
* **事業計画に関する契約**: 経営企画室へ。
* **知財に関する契約**: 知財部へ。
* **技術に関する契約**: 技術管理部へ。

## 2. 技術契約の詳細 (分類が「技術」の場合)
技術契約の場合、さらに詳細な分類が必要です。
* **共同研究**: 大学や他社と共に研究を行う場合。
* **委託研究**: 自社の費用で外部に研究を委託する場合。

### 2.1 共同研究の場合の追加確認事項 (規定 A017準拠)
共同研究を行う場合、以下のリスク管理チェックが必要です。
1.  **相手先の構成**: 単独機関か、複数機関か？
2.  **相手先の種類**: 大学のみか、企業も含むか？
3.  **地域**: 国内か、海外か？ (海外の場合は安保理規定チェックが必要)
"""

# --- 2. 構造化出力の定義 (Pydantic) ---
# AIが「次にどう振る舞うべきか」を決定するためのスキーマ
class ConsultationDecision(BaseModel):
    thinking_process: str = Field(description="現在の状況と不足情報の分析")
    missing_info: List[str] = Field(description="手順確定のために不足している情報のリスト")
    next_question: Optional[str] = Field(description="ユーザーに投げかける質問（情報が不足している場合）")
    final_instruction: Optional[str] = Field(description="全ての情報が揃った場合に提示する最終的な手順書")
    status: str = Field(description="'continue' (まだ質問が必要) または 'complete' (完了)")

# --- 3. グラフの状態管理 (State) ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    context: str

# --- 4. ノード関数の定義 ---

def consultation_node(state: AgentState):
    """
    現在の会話履歴と規定コンテキストを元に、次に行うべきアクションを決定する
    """
    messages = state['messages']
    context = state['context']

    # OpenAIモデルの初期化 (Structured Outputを利用)
    # ※実行には環境変数 OPENAI_API_KEY が必要です
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(ConsultationDecision)

    # プロンプトの構築
    system_prompt = f"""
    あなたは社内規定のエキスパートAIです。
    提供された「社内規定(Markdown)」に基づき、ユーザーが適切な手続きを行えるよう案内してください。

    # ルール
    1. いきなり全てを回答せず、規定の分岐条件に従って必要な情報を順番にヒアリングしてください。
    2. ユーザーの意図が曖昧な場合は、選択肢を提示して明確化してください。
    3. 全ての分岐条件（分類、詳細、リスクチェック等）がクリアになったら、
 
    これまでの情報を統合した「あなた専用の手順書」を作成し、statusを'complete'にしてください。

    # 社内規定データ
    {context}
    """

    # AIに判断させる
    decision = structured_llm.invoke([SystemMessage(content=system_prompt)] + messages)

    # 結果の処理
    if decision.status == 'continue':
        # 質問を返す
        return {"messages": [AIMessage(content=decision.next_question)]}
    else:
        # 最終回答を返す
        return {"messages": [AIMessage(content=decision.final_instruction)]}

def should_continue(state: AgentState):
    """
    会話を続けるか終了するかを判定する条件付きエッジ
    """
    last_message = state['messages'][-1]
    # AIが最終回答を出したか、まだ質問しているかを簡易判定
    # (本番ではDecisionオブジェクトをStateに持たせて厳密に判定します)
    if "手順書" in last_message.content or "ありがとうございました" in last_message.content:
        return "end"
    return "continue"

# --- 5. グラフの構築 (LangGraph) ---

workflow = StateGraph(AgentState)

# ノードの追加
workflow.add_node("consultant", consultation_node)

# エントリーポイント
workflow.set_entry_point("consultant")

# 条件付きエッジ (ユーザーの入力を待つか、終了するか)
# Note: 実際のチャットボットではここで一度停止し、ユーザー入力を待ちますが、
# 今回はフロー図としての定義を示します。
workflow.add_edge("consultant", END)

app = workflow.compile()

# --- 6. 実行シミュレーション (重要) ---
# 実際に対話がどのように進むか、手動でメッセージを追加しながらループさせます。

print("--- シミュレーション開始 ---\n")

# 初期状態
chat_history = [HumanMessage(content="契約を進めたいんだけど。")]
print(f"User: {chat_history[-1].content}")

# 1ターン目: AIの応答
result = app.invoke({"messages": chat_history, "context": DUMMY_CONTEXT_MD})
ai_msg_1 = result["messages"][-1]
print(f"AI  : {ai_msg_1.content}\n")
chat_history.append(ai_msg_1)

# 2ターン目: ユーザー回答 (意図的に情報を小出しにする)
user_msg_2 = HumanMessage(content="大学との共同研究なんだけど。")
print(f"User: {user_msg_2.content}")
chat_history.append(user_msg_2)

result = app.invoke({"messages": chat_history, "context": DUMMY_CONTEXT_MD})
ai_msg_2 = result["messages"][-1]
print(f"AI  : {ai_msg_2.content}\n")
chat_history.append(ai_msg_2)

# 3ターン目: ユーザー回答 (全ての質問に答える)
user_msg_3 = HumanMessage(content="相手はX大学1校だけで、国内です。企業は入ってません。")
print(f"User: {user_msg_3.content}")
chat_history.append(user_msg_3)

result = app.invoke({"messages": chat_history, "context": DUMMY_CONTEXT_MD})
ai_msg_3 = result["messages"][-1]
print(f"AI  : {ai_msg_3.content}\n")

