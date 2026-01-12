# -*- coding: utf-8 -*-
from typing import Any, List


def split_list(data: List[Any], nsplit: int) -> List[List[Any]]:
    n = len(data)
    if n == 0:
        return []

    if nsplit < 1:
        nsplit = 1
    if nsplit == 1:
        return [data]

    # 分割数が要素数を超えないように調整
    nsplit = min(nsplit, n)

    m = n // nsplit  # 基本の要素数
    p = n % nsplit  # 余りの要素数（これを先頭の p グループに1つずつ配分する）

    result = []
    start = 0
    for i in range(nsplit):
        # このグループに割り当てる個数
        size = m + (1 if i < p else 0)
        result.append(data[start : start + size])
        start += size

    return result


if __name__ == "__main__":
    a = list(range(18))
    num_splits = int(len(a) ** 0.5)
    print(f"Original: {a}")
    print(f"Splits:   {split_list(a, num_splits)}")
