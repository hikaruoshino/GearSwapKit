# -*- coding: utf-8 -*-
"""1.2.5 の確認: export を手で直したときの書き間違い (ear1== など) を、黙って読み飛ばさずに行番号で知らせる。
読めた装備は今までどおり読む。書き間違いの無いファイルでは、何も知らせない。
実行 (GearSwapKit/ で): python -I tests/test_unread_125.py [確かめる export のファイル …]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import export_parser as EP

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        sys.stdout.buffer.write(("NG: %s\n" % msg).encode("utf-8"))


# 1. ユーザーが試した書き間違い (= が 2 つ・head="" のあとの , が無い)
typo = ('sets.exported = {\n'
        '    main="Nirvana",\n'
        '    head=""\n'
        '    body="Con. Doublet +3",\n'
        '    ear1=="Lugalbanda Earring",\n'
        '    rear=={ name="Beckoner\'s Earring +1", augments={\'Pet: Accuracy+11\',}},\n'
        '    lring="Varar Ring +1",\n'
        '}\n')
got = EP.parse_equipped_set(typo)
check(sorted(got) == ["body", "left_ring", "main"], "読める行は読む (%s)" % sorted(got))
lines = EP.unread_lines(typo)
check([n for n, _ in lines] == [5, 6], "= が 2 つの行を 5・6 行目として知らせる (%s)" % lines)
check(lines and lines[0][1].startswith("ear1=="), "行の中身を添える (%s)" % lines[:1])

# 2. 書き間違いの無いファイル・別名・空の装備・コメントでは知らせない
ok = ('-- コメント ear1=="x"\n'
      '--[[ 複数行の\n'
      'コメント ]]\n'
      'sets.exported={ main="Naegling", head="", ear1="Odnowa Earring +1",\n'
      '  ring2={ name="Gelatinous Ring +1", augments={"Path: A"} } }\n')
check(EP.unread_lines(ok) == [], "正しいファイルでは何も知らせない (%s)" % EP.unread_lines(ok))
check(len(EP.parse_equipped_set(ok)) == 3, "正しいファイルの装備は 3 つ読む")

# 3. 複数行のコメントのあとでも、行番号がずれない
after_block = '--[[\na\nb\n]]\nsets.exported = {\n    neck="Loricate Torque +1",\n    waist=="Flume Belt +1",\n}\n'
check([n for n, _ in EP.unread_lines(after_block)] == [7], "複数行のコメントのあとでも 7 行目と数える (%s)" % EP.unread_lines(after_block))

# 4. スロットの名前の書き間違い (lefft_ear) と、閉じていない引用符
check([n for n, _ in EP.unread_lines('sets.x = {\n  lefft_ear="Etiolation Earring",\n  neck="Sanctity Necklace",\n}')] == [2],
      "スロットでない名前に装備の名前がある行を知らせる")
unclosed = 'sets.x = {\n  neck="Sanctity Necklace",\n  waist="Flume Belt +1,\n  feet="Nyame Sollerets",\n}'
gu = EP.parse_equipped_set(unclosed)
check(gu.get("neck") is not None and gu.get("feet") is not None and gu["feet"].name == "Nyame Sollerets"
      and "waist" not in gu, "閉じていない引用符の行だけを飛ばし、前後の装備は読む (例外で止まらない) (%s)" % gu)
check([n for n, _ in EP.unread_lines(unclosed)] == [3], "閉じていない引用符の行を知らせる (%s)" % EP.unread_lines(unclosed))

# 5. 所持品の一覧 (item= の行) では知らせない
inv = 'main="Naegling"\nmain="Kaja Rod"\nitem="Remedy"\nsub={ name="Ammurapi Shield" }\n'
check(EP.unread_lines(inv) == [], "所持品の一覧の item= の行は知らせない")

# 6. sub=empty (GearSwap の「何も着けない」) は知らせない・変数 (gear.X) は知らせる
emp = 'sets.x = {\n  sub=empty,\n  head=gear.Slip,\n  neck="Sanctity Necklace",\n}'
check([n for n, _ in EP.unread_lines(emp)] == [3], "sub=empty は知らせず、head=gear.Slip は知らせる (%s)" % EP.unread_lines(emp))
check(sorted(EP.parse_equipped_set(emp)) == ["neck"], "sub=empty は装備として読まない")

# 7. スロット名の打ち間違いで、値が augments 付きの表のとき
tt = 'sets.x = {\n  lefft_ear={ name="Etiolation Earring", augments={\'HP+50\',}},\n  neck="Sanctity Necklace",\n}'
check([n for n, _ in EP.unread_lines(tt)] == [2], "lefft_ear={ name=… } を知らせる (%s)" % EP.unread_lines(tt))
check(sorted(EP.parse_equipped_set(tt)) == ["neck"], "打ち間違いの行のあとも読む")

# 8. } の閉じ忘れで、次の行の装備を飲み込まない
br = "sets.exported = {\n    head={ name=\"Nyame Helm\", augments={'Path: B',},\n    body=\"Nyame Mail\",\n}\n"
gb = EP.parse_equipped_set(br)
check("head" not in gb and gb.get("body") is not None and gb["body"].name == "Nyame Mail",
      "} の閉じ忘れの head は読まず、次の body は読む (%s)" % gb)
check([n for n, _ in EP.unread_lines(br)] == [2], "} の閉じ忘れを 2 行目として知らせる (%s)" % EP.unread_lines(br))

# 9. 1 行に複数のスロット (//gs export compact) で引用符の閉じ忘れ: 誤った名前で読まず、次の装備は読む
cp = 'sets.exported={\n    head="Nyame Helm, neck="Loricate Torque +1", left_ear="Etiolation Earring",\n}'
gc = EP.parse_equipped_set(cp)
check("head" not in gc and gc.get("neck") and gc["neck"].name == "Loricate Torque +1" and gc.get("left_ear"),
      "compact の閉じ忘れ: head は読まず、neck・left_ear は読む (%s)" % gc)
check([n for n, _ in EP.unread_lines(cp)] == [2], "compact の閉じ忘れを 2 行目として知らせる (%s)" % EP.unread_lines(cp))

# 10. 1 行に全部書いたファイル (minify): 行の中身は、読めなかったスロットから出す
mn = 'sets.exported={main="Naegling",neck=="Loricate Torque +1",waist="Flume Belt +1",}'
um = EP.unread_lines(mn)
check(len(um) == 1 and um[0][1].startswith("neck=="), "1 行のファイルでも、どの装備か分かる (%s)" % um)
check(sorted(EP.parse_equipped_set(mn)) == ["main", "waist"], "1 行のファイルで、後ろの装備も読む")

# 11. = の書き忘れ
ne = 'sets.x = {\n  neck"Loricate Torque +1",\n  waist "Flume Belt +1",\n  feet="Nyame Sollerets",\n}'
check([n for n, _ in EP.unread_lines(ne)] == [2, 3], "= の書き忘れを知らせる (%s)" % EP.unread_lines(ne))

# 12. メモ帳で保存したファイル (BOM + CRLF) を read_file 経由で読む
import tempfile
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "crlf.lua")
    with open(p, "wb") as f:
        f.write(b"\xef\xbb\xbf" + typo.replace("\n", "\r\n").encode("utf-8"))
    uc = EP.unread_lines(EP.read_file(p))
    check([n for n, _ in uc] == [5, 6] and not any("\r" in s for _, s in uc), "BOM + CRLF でも行番号がずれず、\\r が残らない (%s)" % uc)

# 13. 本物の export では、何も知らせない (誤って警告しないこと)。引数が無ければ、手元の export を読む
paths = sys.argv[1:]
if not paths:
    import glob
    paths = glob.glob(os.path.join(HERE, "..", "..", "GearSwap", "data", "export", "Pesan*.lua"))
for p in paths:
    u = EP.unread_lines(EP.read_file(p))
    check(u == [], "%s: 何も知らせない (%s)" % (os.path.basename(p), u[:3]))

if fails:
    sys.stdout.buffer.write(("FAILED %d 件\n" % len(fails)).encode("utf-8"))
    sys.exit(1)
sys.stdout.buffer.write(("OK 読めなかった行の知らせ: 失敗 0 件 (本物の export %d 個)\n" % len(paths)).encode("utf-8"))
