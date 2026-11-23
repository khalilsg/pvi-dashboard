"""Bake data/races.json into src/template.html -> index.html (a single self-contained page).

Run after build_data.py:  python3 scripts/build_site.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
data = open(os.path.join(ROOT, "data", "races.json"), encoding="utf-8").read().replace("</", "<\\/")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*__DATA__*/null", data))
print("wrote index.html")
