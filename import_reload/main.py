"""
importlib.reload の動作を確認するメインスクリプト
"""

import datetime
import importlib
import time

import my_module


def main():
    # 1. 最初の状態を確認
    print("--- Step 1: Initial Import ---")
    h = my_module.hello
    h()
    print(f"Version: {my_module.version}")

    # 2. my_module.py を書き換える
    print("\n--- Step 2: Modifying my_module.py ---")
    t = datetime.datetime.now()
    new_content = f'''"""
動的インポートとリロードのテスト用モジュール
"""
# FOR SYNTAX_ERROR

def hello():
    print("Hello! (created {t}).")


version = "{t}"
'''
    with open("my_module.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("File modified. Waiting a moment...")
    time.sleep(1)

    # 3. reload しないで呼び出してみる（古いまま）
    print("\n--- Step 3: Calling without reload ---")
    my_module.hello()
    print(f"Version: {my_module.version}")

    # 4. importlib.reload を使って再読み込み
    print("\n--- Step 4: Reloading module ---")
    try:
        importlib.reload(my_module)
        my_module.hello()
        print(f"Version: {my_module.version}")
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")
    h()
    my_module.hello()
    print(f"Version: {my_module.version}")


if __name__ == "__main__":
    main()
