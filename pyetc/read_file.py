import os
from dataclasses import dataclass
from typing import Optional, Tuple


# 擬似的な設定クラス
class Config:
    def __init__(self, target_dir: str):
        # 基準となるディレクトリ（この外へのアクセスは禁止する）
        self.target_dir = os.path.abspath(target_dir)


@dataclass
class FileContentResult:
    content: str
    is_truncated: bool
    lines_shown: Tuple[int, int]
    original_line_count: int
    error: Optional[str] = None


class ReadFileTool:
    def __init__(self, config: Config):
        self.config = config

    def validate(
        self, file_path: str, offset: int = 0, limit: Optional[int] = None
    ) -> Optional[str]:
        """パラメータの検証とセキュリティチェックを行います"""
        if not file_path:
            return "file_path is required"

        # 1. パスの解決: 相対パスを絶対パスに変換
        # target_dir と結合することで、絶対パスを生成
        resolved_path = os.path.abspath(
            os.path.join(self.config.target_dir, file_path)
        )

        # 2. セキュリティチェック (Directory Traversal Prevention)
        # 解決されたパスが、本当に target_dir の中にあるかを確認します。
        # '../../windows/system32/...' みたいなパス指定を防ぐ重要な処理です。
        try:
            # commonpath は共通の親ディレクトリを返します
            if (
                os.path.commonpath([self.config.target_dir, resolved_path])
                != self.config.target_dir
            ):
                return (
                    "Access denied: "
                    f"{file_path} is outside the target directory."
                )
        except ValueError:
            # ドライブ文字が異なる場合など
            return f"Access denied: {file_path} is invalid."

        if offset < 0:
            return "Offset must be a non-negative number"
        if limit is not None and limit <= 0:
            return "Limit must be a positive number"

        return None

    def execute(
        self, file_path: str, offset: int = 0, limit: Optional[int] = None
    ):
        """ファイルを読み込みます"""
        # バリデーション実行
        error = self.validate(file_path, offset, limit)
        if error:
            return {"error": error}

        resolved_path = os.path.abspath(
            os.path.join(self.config.target_dir, file_path)
        )

        # デフォルトの上限値（TypeScript側でも制限があるため）
        effective_limit = limit if limit is not None else 10000

        try:
            if not os.path.isfile(resolved_path):
                return {"error": f"File not found: {resolved_path}"}

            # アルゴリズムのポイント:
            # readlines() で全行読み込むと巨大なファイルでメモリがパンクするので、
            # イテレータを使って「必要な行だけ」メモリに入れるようにします。

            lines_buffer = []
            total_lines = 0

            # encoding は環境に合わせて適切に設定（utf-8が無難）
            with open(
                resolved_path, "r", encoding="utf-8", errors="replace"
            ) as f:
                # enumerate で (行番号, 行内容) のペアを取得
                for i, line in enumerate(f):
                    total_lines = i + 1

                    # 必要な範囲だけバッファに追加
                    if offset <= i < (offset + effective_limit):
                        lines_buffer.append(line)

            # 結果の組み立て
            content = "".join(lines_buffer)
            is_truncated = len(lines_buffer) < total_lines

            # 表示用に 1-based index に変換
            start_display = offset + 1 if lines_buffer else 0
            end_display = offset + len(lines_buffer)

            # 切り捨て発生時のメッセージ付与
            if is_truncated:
                header = (
                    f"\nIMPORTANT: The file content has been truncated.\n"
                    f"Status: Showing lines {start_display}-{end_display} of "
                    f"{total_lines} total lines.\n"
                    f"Action: To read more, use offset={end_display} "
                    "in the next call.\n"
                    f"--- FILE CONTENT (truncated) ---"
                )
                content = header + content

            return {
                "content": content,
                "lines_shown": (start_display, end_display),
                "total_lines": total_lines,
            }

        except Exception as e:
            return {"error": str(e)}


# --- 動作確認用 ---
if __name__ == "__main__":
    # カレントディレクトリを安全な範囲として設定
    tool = ReadFileTool(Config(os.getcwd()))

    # 自分自身 (このスクリプト) を読んでみる
    my_name = "py/read-file.py"

    print(f"--- {my_name} の最初の 10行を読む ---")
    result = tool.execute(my_name, limit=10)

    if "error" in result:
        print("Error:", result["error"])
    else:
        print(result["content"])
