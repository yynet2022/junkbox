#
# sample02.py: 承認権限フロー対応エージェント (構造化グラフ版)
#
import logging
import os
import sys
from typing import List, Literal, Optional, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
import operator

logging.basicConfig(level=logging.INFO)


# ==========================================
# 1. データ構造定義
# ==========================================
class ExtractedInfo(BaseModel):
    """ユーザーの発言から抽出する情報"""
    contract_type: Optional[Literal["technical", "software", "university"]] = Field(
        None, description="契約の類型 (technical: 技術, software: ソフトウェア, university: 大学共研)"
    )
    is_group_company: Optional[bool] = Field(
        None, description="相手先がグループ会社かどうか (True/False)"
    )
    annual_amount: Optional[int] = Field(
        None, description="年間の契約金額 (円単位の数値)"
    )


class AgentState(TypedDict):
    """グラフ内で保持される状態"""
    # messages は追加のみ (Annotated[..., operator.add])
    messages: Annotated[List[BaseMessage], operator.add]
    # 現在抽出されている情報
    info: ExtractedInfo
    # 判定された承認者
    approver: Optional[str]
    # 不足している情報のリスト
    missing_fields: List[str]
    # 終了フラグ
    is_complete: bool


# ==========================================
# 2. ノード関数の実装
# ==========================================

def extractor_node(state: AgentState):
    """
    最新のメッセージから必要な情報(類型、相手先、金額)を抽出するノード
    """
    llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL"), temperature=0)
    structured_llm = llm.with_structured_output(ExtractedInfo)

    # 過去の履歴も含めて現在の情報を抽出
    system_prompt = """
    ユーザーとの会話から、以下の情報を抽出してください。
    1. 契約類型 (技術契約, ソフトウェア契約, 大学共研契約のいずれか)
    2. 相手先がグループ会社かどうか
    3. 年間の契約金額 (円単位)

    一度抽出された情報は、ユーザーが訂正しない限り保持してください。
    数値は「1億円」なら「100000000」のように数値に変換してください。
    """

    new_info = structured_llm.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )

    # 既存の情報とマージ (Noneでないものを優先)
    current_info = state.get("info", ExtractedInfo())
    merged_info = ExtractedInfo(
        contract_type=new_info.contract_type or current_info.contract_type,
        is_group_company=new_info.is_group_company if new_info.is_group_company is not None else current_info.is_group_company,
        annual_amount=new_info.annual_amount or current_info.annual_amount
    )

    return {"info": merged_info}


def tech_software_logic_node(state: AgentState):
    """
    技術契約およびソフトウェア契約の承認ロジック
    """
    info = state["info"]
    missing = []
    approver = None

    # 情報不足のチェック
    if info.is_group_company is None:
        missing.append("相手先がグループ会社かどうか")
    if info.annual_amount is None:
        missing.append("年間の契約金額")

    if not missing:
        # memo2.txt のロジックを実装
        amt = info.annual_amount
        if not info.is_group_company:
            # グループ外
            if amt >= 200_000_000:
                approver = "社長"
            elif amt >= 50_000_000:
                approver = "担当役員"
            else:
                approver = "事業部長"
        else:
            # グループ内
            if amt >= 100_000_000:
                approver = "社長"
            else:
                approver = "事業部長"

    return {"approver": approver, "missing_fields": missing}


def university_logic_node(state: AgentState):
    """
    大学共研契約の承認ロジック
    """
    info = state["info"]
    missing = []
    approver = None

    if info.annual_amount is None:
        missing.append("年間の契約金額")

    if not missing:
        # memo2.txt のロジック
        amt = info.annual_amount
        if amt >= 200_000_000:
            approver = "社長"
        elif amt >= 100_000_000:
            approver = "担当役員"
        else:
            approver = "事業部長"

    return {"approver": approver, "missing_fields": missing}


def responder_node(state: AgentState):
    """
    最終的な回答、または追加の質問を生成するノード
    """
    approver = state.get("approver")
    missing = state.get("missing_fields", [])
    info = state["info"]

    llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL"), temperature=0)

    if approver:
        # 完了メッセージ
        content = (
            f"判定の結果、承認者は **{approver}** となります。\n\n"
            f"【判定条件】\n"
            f"- 契約類型: {info.contract_type}\n"
            f"- 相手先: {'グループ会社' if info.is_group_company else 'グループ会社以外'}\n"
            f"- 年間金額: {info.annual_amount:,}円"
        )
        is_complete = True
    else:
        # 質問の生成
        prompt = f"以下の情報が不足しています: {', '.join(missing)}。ユーザーに京都弁で優しく質問してください。"
        response = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
        content = response.content
        is_complete = False

    return {
        "messages": [AIMessage(content=content)],
        "is_complete": is_complete
    }


# ==========================================
# 3. エッジ（分岐）のロジック
# ==========================================

def contract_router(state: AgentState):
    """
    契約類型に基づいて進むべきノードを決定する
    """
    ctype = state["info"].contract_type
    if ctype in ["technical", "software"]:
        return "tech_software_branch"
    elif ctype == "university":
        return "university_branch"
    else:
        return "ask_type"


# ==========================================
# 4. グラフの構築
# ==========================================

def build_graph():
    workflow = StateGraph(AgentState)

    # ノード追加
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("tech_logic", tech_software_logic_node)
    workflow.add_node("uni_logic", university_logic_node)
    workflow.add_node("responder", responder_node)

    # エントリーポイント
    workflow.set_entry_point("extractor")

    # 条件付きエッジ (契約類型による分岐)
    workflow.add_conditional_edges(
        "extractor",
        contract_router,
        {
            "tech_software_branch": "tech_logic",
            "university_branch": "uni_logic",
            "ask_type": "responder" # 類型すらわからん時もresponderで質問させる
        }
    )

    # 各ロジックからは responder へ
    workflow.add_edge("tech_logic", "responder")
    workflow.add_edge("uni_logic", "responder")

    # responder の後は END (一回のターン終了)
    workflow.add_edge("responder", END)

    return workflow.compile()


# ==========================================
# 5. メインループ
# ==========================================

def main():
    print("--- 承認権限エージェント (sample02: 構造化版) ---")
    app = build_graph()

    # 初期状態
    state = {
        "messages": [],
        "info": ExtractedInfo(),
        "approver": None,
        "missing_fields": [],
        "is_complete": False
    }

    print("AI: こんにちは。契約の承認権限についてお調べします。契約の内容を教えていただけますか？")

    while True:
        user_input = input("\nUser: ")
        if user_input.strip() in ["終了", "exit", "quit"]:
            break

        # ユーザーメッセージ追加
        state["messages"] = [HumanMessage(content=user_input)]

        # グラフ実行
        # state は invoke ごとに更新される
        state = app.invoke(state)

        # AIの最新メッセージを表示
        print(f"\nAI: {state['messages'][-1].content}")

        if state["is_complete"]:
            print("\n--- 案内が完了しました ---")
            if input("\n他の相談をしますか？ (y/n): ").lower() != "y":
                break
            else:
                # 状態リセット
                state = {
                    "messages": [],
                    "info": ExtractedInfo(),
                    "approver": None,
                    "missing_fields": [],
                    "is_complete": False
                }
                print("\nAI: 新しい相談をどうぞ。")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("エラー: 環境変数 OPENAI_API_KEY が設定されていません。")
        sys.exit(1)
    main()
