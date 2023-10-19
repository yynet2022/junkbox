# -*- coding: utf-8 -*-
import os
import sys
from jinja2 import Template

def get_directory_tree(path):
    tree = {}
    for root, dirs, files in os.walk(path):
        tree[root] = []
        for file in files:
            tree[root].append(os.path.join(root, file))
    return tree

def render_directory_tree(tree):
    html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ディレクトリツリー</title>
</head>
<body>
  <div class="tree">
    {% for dir in tree %}
    <details>
      <summary>{{ dir }}</summary>
      <ul>
      {% for file in tree[dir] %}
        <li><a href="{{ file }}">{{ file }}</a></li>
      {% endfor %}
      </ul>
    </details>
    {% endfor %}
  </div>
<style>
.tree {
    margin: auto;
    width: 80%;
}
</style>
</body>
</html>
"""
    return Template(html).render(tree=tree)

def main():
    tree = get_directory_tree('.')
    html = render_directory_tree(tree)
    print(html)

if __name__ == '__main__':
    main()
