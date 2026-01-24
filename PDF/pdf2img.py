#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDFファイルをページごとに画像ファイル（JPEGまたはPNG）に変換するスクリプト。

機能:
- 指定されたPDFファイルを1ページずつ画像に変換します。
- 出力ファイル名は、入力ファイル名に基づいて自動的に生成されます。
  (例: input.pdf -> input_1.jpg, input_2.jpg, ...)
- 出力形式はデフォルトでJPEGですが、コマンドライン引数でPNGも指定可能です。

依存ライブラリ:
- PyMuPDF: 'pip install PyMuPDF' コマンドでインストールしてください。

使用方法:
  python pdf2img.py [-x {jpg,jpeg,png}] input.pdf

引数:
  input.pdf            : 変換したいPDFファイルのパス。
  -x, --ext {jpg,jpeg,png} : 出力画像の形式を指定します（任意）。
                           デフォルトは 'jpg' です。大文字小文字は区別しません。
"""

import sys
import os
import argparse
import fitz  # PyMuPDF

def convert_pdf_to_images(pdf_path, output_ext):
    """
    指定されたPDFファイルを画像に変換し、保存する関数。

    Args:
        pdf_path (str): 入力PDFファイルのパス。
        output_ext (str): 出力画像の拡張子 ('jpg' または 'png')。
    """
    # 出力用のベースファイル名を取得 (例: 'A.pdf' -> 'A')
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    try:
        # PDFファイルを開く
        doc = fitz.open(pdf_path)
        print(f"'{pdf_path}' を開きました。総ページ数: {len(doc)}ページ")

    except Exception as e:
        print(f"エラー: '{pdf_path}' を開けませんでした。")
        print(f"詳細: {e}")
        sys.exit(1)

    if not doc.page_count:
        print("エラー: このPDFにはページがありません。")
        doc.close()
        sys.exit(1)

    # 各ページをループして画像として保存
    for i, page in enumerate(doc):
        # ページ番号は1から始める
        page_num = i + 1
        output_path = f"{base_name}_{page_num}.{output_ext}"

        try:
            # ページをピクセルマップにレンダリング
            # DPIを高くすると、より高解像度の画像が得られます
            pix = page.get_pixmap(dpi=200)

            # 画像をファイルに保存
            pix.save(output_path)
            print(f"  -> '{output_path}' を保存しました。")

        except Exception as e:
            print(f"エラー: {page_num}ページ目の変換中にエラーが発生しました。")
            print(f"詳細: {e}")

    # ドキュメントを閉じる
    doc.close()
    print("\n処理が完了しました。")


def main():
    """
    コマンドライン引数を処理し、メインの変換処理を呼び出す関数。
    """
    parser = argparse.ArgumentParser(
        description="PDFをページごとに画像ファイルに変換します。",
        formatter_class=argparse.RawTextHelpFormatter  # ヘルプの改行を維持
    )
    parser.add_argument(
        "input_pdf",
        help="変換するPDFファイルのパス。"
    )
    parser.add_argument(
        "-x", "--ext",
        type=str,
        default="jpg",
        choices=["jpg", "jpeg", "png"],
        metavar="TYPE",
        help="出力画像の形式を指定します (jpg, jpeg, png)。\nデフォルト: jpg"
    )

    args = parser.parse_args()

    # 入力ファイルの存在チェック
    if not os.path.isfile(args.input_pdf):
        print(f"エラー: 指定されたファイルが見つかりません: {args.input_pdf}")
        sys.exit(1)

    # 出力形式の正規化
    output_format = args.ext.lower()
    if output_format == "jpeg":
        output_format = "jpg"

    # メインの変換関数を呼び出し
    convert_pdf_to_images(args.input_pdf, output_format)


if __name__ == "__main__":
    main()
