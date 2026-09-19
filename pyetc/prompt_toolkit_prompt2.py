"""Line-start slash command completer with top-row prompt sample.

This module demonstrates a custom Completer implementation that strictly
triggers completion only when a slash ('/') appears at the start of the line,
and scrolls the terminal so that the prompt is always displayed on the top row
while preserving previous output in the terminal scrollback buffer.
"""

import shutil
import os
import sys
from collections.abc import Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.shortcuts import CompleteStyle

# 利用可能なスラッシュコマンド一覧
COMMAND_LIST: list[str] = ["/exit", "/quit", "/reload", "/help"]


class SlashCommandCompleter(Completer):
    """行頭のスラッシュコマンドのみを補完するカスタム Completer。"""

    def __init__(self, commands: list[str]) -> None:
        """コマンド一覧を保持して初期化します。"""
        self.commands: list[str] = commands

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """行頭が '/' で始まる場合のみコマンド補完候補を生成します。"""
        text_before_cursor: str = document.text_before_cursor
        stripped_leading: str = text_before_cursor.lstrip()

        # 行頭が '/' で始まらない場合は補完しない（空文字の場合は全候補表示）
        if len(stripped_leading) > 0 and not stripped_leading.startswith("/"):
            return

        # コマンドの後にスペースが入力されたらコマンド名補完は終了
        if " " in stripped_leading:
            return

        for cmd in self.commands:
            if cmd.startswith(stripped_leading):
                yield Completion(
                    text=cmd,
                    start_position=-len(stripped_leading),
                )


completer: SlashCommandCompleter = SlashCommandCompleter(COMMAND_LIST)
history: FileHistory = FileHistory("hist.txt")
kb: KeyBindings = KeyBindings()


@kb.add("enter")
def handle_enter(event: KeyPressEvent) -> None:
    """現在のバッファ（入力内容）を確定して受け付けます。"""
    event.current_buffer.validate_and_handle()


@kb.add("c-j")
def handle_ctrl_j(event: KeyPressEvent) -> None:
    """Ctrl+J または Ctrl+Enter で改行を挿入します。"""
    event.current_buffer.insert_text("\n")


def scroll_to_top() -> None:
    """画面を行数分押し上げて、カーソルを最上段へ移動します。

    画面を消去（クリア）するのではなく改行でスクロールアウトさせるため、
    ターミナルを上へスクロールすれば以前の出力履歴を確認できます。
    """
    lines: int = shutil.get_terminal_size().lines

    # ANSIエスケープシーケンスを受け付けるおまじない
    if os.name == 'nt':
        os.system("")

    # sys.stdout.write(f"\033[{lines}S\033[H")
    sys.stdout.write("\n" * lines + "\033[H")
    sys.stdout.flush()


def main() -> None:
    """メイン実行ループ。"""
    # complete_while_typing=False で Tabキー押下時のみ補完
    # complete_style=CompleteStyle.READLINE_LIKE で bash 風の表示
    session: PromptSession[str] = PromptSession(
        history=history,
        key_bindings=kb,
        multiline=True,
        completer=completer,
        complete_while_typing=False,
        complete_style=CompleteStyle.READLINE_LIKE,
    )

    while True:
        # プロンプト表示直前に画面をスクロールして最上段に配置
        scroll_to_top()
        try:
            user_input: str = session.prompt("> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        print(user_input)
        if user_input in ("/exit", "/quit"):
            break


if __name__ == "__main__":
    main()
