from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.key_binding import KeyBindings

my_completer = FuzzyWordCompleter(
    ["/exit", "/quit", "/reload", "/help"]
)

history = FileHistory("hist.txt")

kb = KeyBindings()

@kb.add('enter')
def _(event):
    # 現在のバッファ（入力内容）を確定して受け付ける
    event.current_buffer.validate_and_handle()

@kb.add('c-j')
def _(event):
    # Ctrl+J, Ctrl+Enter で改行するように設定
    event.current_buffer.insert_text('\n')

# Create prompt object.
session = PromptSession(history=history,
                        key_bindings=kb,
                        multiline=True,
                        completer=my_completer)

while True:
    user_input = session.prompt("> ").strip()
    print(user_input)
    if user_input in ("/exit", "/quit"):
        break
