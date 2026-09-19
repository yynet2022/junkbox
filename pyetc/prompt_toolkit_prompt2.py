"""Line-start slash command custom completer sample.

This module demonstrates a custom Completer implementation that strictly
triggers completion only when a slash ('/') appears at the start of the line,
preventing unwanted completions for slashes inside normal text or paths.
"""

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

        # 行頭が '/' で始まらない場合は補完しない
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

    print("=== Custom Slash Completer Sample (Line-start only) ===")
    while True:
        try:
            user_input: str = session.prompt("> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        print(user_input)
        if user_input in ("/exit", "/quit"):
            break


if __name__ == "__main__":
    main()
