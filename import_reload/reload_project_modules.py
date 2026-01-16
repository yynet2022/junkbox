import sys
import importlib
from pathlib import Path

def reload_project_modules(target_dir):
    root = Path(target_dir).resolve()
    
    # 1. まずリロード対象のモジュールをリストアップする
    to_reload = []
    for name, module in list(sys.modules.items()):
        file_path = getattr(module, "__file__", None)
        if file_path:
            p = Path(file_path).resolve()
            if p.is_relative_to(root):
                to_reload.append((name, module))

    # 2. リロードを実行
    # 本来は依存関係順が理想だが、簡易的にはアルファベット順や
    # 深さ順（深いものを先にするなど）に並べ替えると成功率が上がることがある
    for name, module in to_reload:
        try:
            importlib.reload(module)
            print(f"Reloaded: {name}")
        except Exception as e:
            print(f"Failed to reload {name}: {e}")

# 実行
reload_project_modules("./src")
