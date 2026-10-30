# -*- coding: utf-8 -*-
"""作業のあるジョブが多くても、上の段のボタンが押し出されず、ジョブの一覧が見切れないことの確認 (1.2.4)。
実行 (GearSwapKit/ で): python -I tests/test_gui_jobs_row.py (tkinter が使える Python で)"""
import os
import sys
import tempfile
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import app as A
import set_catalog as C
# 本物の設定ファイルを汚さないよう、テストの間は一時フォルダーに向ける
A.SETTINGS = os.path.join(tempfile.mkdtemp(), "gearswapkit_settings.json")

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        sys.stdout.buffer.write(("NG: %s\n" % msg).encode("utf-8"))


root = tk.Tk()
gui = A.App(root)
gui.project.has_work = lambda job: True          # 全 22 ジョブに作業があることにする
gui.refresh()
one = A.ttk.Label(root, text="WAR").winfo_reqheight()   # 同じ見た目のラベルの 1 行の高さ

# キットの既定の大きさ (1040x700) と、利用者が狭めた窓 (700x600) の 2 通り
for size, must_wrap in (("1040x700+0+0", False), ("700x600+0+0", True)):
    root.geometry(size)
    root.update()
    root.update()
    text = gui.jobs_lbl.cget("text")
    check(all(j in text for j in C.ALL_JOBS), "[%s] 作業のあるジョブの文に、全ジョブが入る" % size)
    win_right = root.winfo_rootx() + root.winfo_width()
    top = gui.root.winfo_children()[0]
    buttons = [w for w in top.winfo_children() if isinstance(w, A.ttk.Button)]
    check(len(buttons) >= 2, "[%s] 上の段に「作業を開く」「作業を保存」のボタンがある" % size)
    for btn in buttons:
        check(btn.winfo_ismapped() and btn.winfo_width() >= btn.winfo_reqwidth() - 2
              and btn.winfo_rootx() + btn.winfo_width() <= win_right,
              "[%s] 上の段のボタン「%s」が押し出されず、窓の中に全部見える" % (size, btn.cget("text")))
    lbl = gui.jobs_lbl
    check(lbl.winfo_rootx() + lbl.winfo_reqwidth() <= win_right, "[%s] ジョブの一覧が窓の幅に収まる" % size)
    if must_wrap:
        check(lbl.winfo_reqheight() > one + 5, "[%s] 狭い窓では、ジョブの一覧が折り返される (1 行より高い)" % size)

root.destroy()
if fails:
    sys.stdout.buffer.write(("FAILED %d 件\n" % len(fails)).encode("utf-8"))
    sys.exit(1)
sys.stdout.buffer.write("OK 作業のあるジョブの行: 失敗 0 件\n".encode("utf-8"))
