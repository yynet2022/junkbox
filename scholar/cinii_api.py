import httpx
import logging
# import pprint

logger = logging.getLogger(__name__)

# CiNii Research API の基本設定
# all/projectsAndProducts/articles/data/books/dissertations/projects/researchers
BASE_URL = "https://cir.nii.ac.jp/opensearch/v2/articles"


def search_cinii_research(keyword, count=20, start=1):
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
        'sortorder': 0,
        'start': start,           # ページ番号 (デフォルト1)
    }

    logger.info(f"Searching: {keyword}")
    response = httpx.get(BASE_URL, params=params, timeout=10.0)

    # HTTPステータスコードをチェック
    response.raise_for_status()

    return response.json()


def process_results(data):
    """
    CiNii ResearchのJSON結果から必要な情報を抽出して表示する関数。
    """
    if not data or 'items' not in data:
        print("検索結果が見つかりませんでした。")
        return

    print("\n--- 検索結果 ---")

    title = data.get('title', '')
    print(f'Title: {title}')
    total = data.get('opensearch:totalResults', '')
    print(f'Total: {total}')
    sindex = data.get('opensearch:startIndex', '')
    print(f'Start Index: {sindex}')
    nitems = data.get('opensearch:itemsPerPage', '')
    print(f'Items/Page: {nitems}')

    items = data.get('items', [])
    for i, item in enumerate(items):
        # pprint.pprint(item)
        try:
            title = item.get('title', '')
            url = item.get('link', dict()).get('@id', '')
            date = item.get('prism:publicationDate', '')

            print(f"[{i+1}]")
            print(f"  Title: {title}")
            print(f"  Link:  {url}")
            print(f"  Date:  {date}")

        except (KeyError, IndexError) as e:
            logger.error(f'parse error: {e}')
            continue


if __name__ == "__main__":
    import os
    import sys
    target_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
    if target_path not in sys.path:
        sys.path.append(target_path)

    from pyetc import logging_setup
    logging_setup.setup()

    search_keyword = "ロボティクス"  # 検索したいキーワードを設定

    # 検索を実行
    search_data = search_cinii_research(search_keyword, 10)

    # 結果の処理と表示
    process_results(search_data)
