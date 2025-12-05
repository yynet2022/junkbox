import httpx
import json
import pprint
import logging
import logging_setup

# CiNii Research API の基本設定
BASE_URL = "https://cir.nii.ac.jp/opensearch/v2/all"

def search_cinii_research(keyword, count=20):
    """
    CiNii Researchを検索し、結果をJSONで返す関数。
    
    :param keyword: 検索キーワード
    :param count: 取得する件数 (最大200)
    :return: 検索結果のJSONデータ (辞書型)
    """
    
    # クエリパラメータを設定
    params = {
        'q': keyword,              # 検索キーワード
        'format': 'json',          # レスポンス形式をJSONに指定
        'count': count,            # 取得件数
        'from': 2025,
        # 'p' : 1,                 # ページ番号 (デフォルト1)
        # 'range': 'all',          # 検索対象 (all, title, author, etc.)
    }

    try:
        # httpxでGETリクエストを送信
        print(f"検索中: {keyword}")
        response = httpx.get(BASE_URL, params=params, timeout=10.0)
        
        # HTTPステータスコードをチェック
        response.raise_for_status() 
        
        # レスポンスボディをJSONとしてパース
        return response.json()

    except httpx.RequestError as e:
        print(f"リクエストエラーが発生しました: {e}")
        return None
    except json.JSONDecodeError:
        print("JSONのデコードエラーが発生しました。不正なレスポンスです。")
        return None

def process_results(data):
    """
    CiNii ResearchのJSON結果から必要な情報を抽出して表示する関数。
    """
    if not data or 'items' not in data:
        print("検索結果が見つかりませんでした。")
        return

    print("\n--- 検索結果 ---")
    
    items = data['items']
    for i, item in enumerate(items):
        # pprint.pprint(item)
        try:
            # 論文タイトル (title)
            # title = item['title'][0]['@value']
            title = item['title']
            
            # 著者名 (creator)
            # 複数の著者名がリストとして入っている場合がある
            creators = [c for c in item.get('dc:creator', [])]
            author_str = ", ".join(creators)
            
            # URL (link)
            url = item['link']['@id']

            # Publication Date
            date = item.get('prism:publicationDate', '')

            print(f"[{i+1}]")
            print(f"  タイトル: {title}")
            print(f"  著者:     {author_str if author_str else '不明'}")
            print(f"  URL:      {url}")
            print(f"  Date:     {date}")
        
        except (KeyError, IndexError) as e:
            # データ構造が不完全なアイテムをスキップ
            print(f"  [データのパースエラー: {e} - このアイテムはスキップされます]")
            continue

if __name__ == "__main__":
    logging_setup.setup()

    search_keyword = "CMOS"  # 検索したいキーワードを設定
    
    # 検索を実行
    search_data = search_cinii_research(search_keyword)
    
    # 結果の処理と表示
    process_results(search_data)
