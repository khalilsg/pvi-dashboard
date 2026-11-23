"""Bake data/races.json and the version into src/template.html -> index.html (a single self-contained page).

Run after build_data.py:  python3 scripts/build_site.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(ROOT, "src", "template.html"), encoding="utf-8").read()
data = open(os.path.join(ROOT, "data", "races.json"), encoding="utf-8").read().replace("</", "<\\/")
version = re.search(r"VERSION = '([^']+)'", open(os.path.join(ROOT, "src", "version.js"), encoding="utf-8").read()).group(1)
states = open(os.path.join(ROOT, "data", "us_states.json"), encoding="utf-8").read()
html = tpl.replace("/*__DATA__*/null", data).replace("/*__MAP__*/null", states).replace("__VERSION__", version)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("wrote index.html", version)
