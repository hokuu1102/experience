#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyEDA（立创EDA）导出件的自动化核对工具集

解决的问题：手工核对"原理图网表 ↔ PCB 网络"既慢又容易漏，尤其是
  - 多路并联/重复网络（8 路霍尔全并到一个通道）
  - 两个网络之间完全没有连接（AGND 与 GND 断开）
  - 改过网络归属后原理图与 PCB 不一致（电容的地从 GND 改成 AGND）

子命令:
  tel   <netlist.tel>              解析网表，打印元件表 + 每个网络的节点
  pcb   <proj.epro2>               解析 EasyEDA 专业版工程，打印已放置元件 + 引脚网络 + 坐标
  check <netlist.tel> <proj.epro2> 对比两者，列出差异（重点：每个元件每个脚的网络）
  svg   <file.svg> [x y w h] [scale]  渲染 SVG；给 viewBox 则只渲那一块（放大读图）
  pdfbox <file.pdf> [位号...]       提取 PDF 里文字坐标，量两个器件之间的间距

依赖: 只用标准库。svg 子命令需要 Edge（Windows 自带）；pdfbox 需要 poppler 的 pdftotext。

用法示例:
  python easyeda.py check Netlist.tel ProDoc_PCB1.epro2
  python easyeda.py svg SCH.svg 880 -520 305 290 4
"""
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

# ---------------------------------------------------------------- 通用


def _die(msg):
    print("错误: " + msg, file=sys.stderr)
    sys.exit(2)


def _find_edge():
    for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if os.path.exists(p):
            return p
    return None


# ---------------------------------------------------------------- .tel 网表


def parse_tel(path):
    """立创EDA 导出的 .tel 网表 -> {'packages': {位号: 值}, 'nets': {网络: [节点]}}

    行格式:  'NETNAME' ; R1.1 U1.1          （长网络会被折行，续行以逗号结尾）
    """
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    # 去掉折行：以 , 结尾的行与下一行合并
    raw_lines = text.splitlines()
    lines, buf = [], ""
    for ln in raw_lines:
        buf += ln.rstrip().rstrip(",")      # 折行续行：必须把行尾的 , 去掉，否则会多出 "," 节点
        if ln.rstrip().endswith(","):
            continue
        lines.append(buf)
        buf = ""
    if buf:
        lines.append(buf)

    packages, nets = {}, {}
    section = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("$"):
            section = s
            continue
        if not s or s.startswith("!"):
            continue
        if section == "$NETS" and ";" in s:
            name, rest = s.split(";", 1)
            name = name.strip().strip("'")
            nodes = rest.split()
            nets.setdefault(name, []).extend(nodes)
        elif section == "$PACKAGES" and ";" in s:
            head, rest = s.split(";", 1)
            val = head.split("!")[-1].strip()
            for ref in rest.split():
                packages[ref] = val
    return {"packages": packages, "nets": nets}


def tel_usage_report(tel):
    """从网表里挑出可疑模式（这些才是最该看的）"""
    nets = tel["nets"]
    out = []

    # 1) 多个同类器件并到同一个网络的"疑似漏接"：一个网络里含 >1 个 U 的同类引脚
    #    实际判据：一个网络里 IC 引脚数 >= 3 且这些 IC 的脚号相同（例如 8 个霍尔脚全在 CH0）
    for name, nodes in nets.items():
        # 电源/地网络天然就是"很多个脚号相同的器件并联"，跳过，否则全是误报
        if re.match(r"^(\+?\d+(\.\d+)?V\w*|VCC|VDD|VSS|VBUS|VREF|.*GND)$", name, re.I):
            continue
        ic_pins = [n for n in nodes if re.match(r"^U\d+\.\d+$", n)]
        by_pin = {}
        for n in ic_pins:
            by_pin.setdefault(n.split(".")[1], []).append(n)
        for pin, lst in by_pin.items():
            if len(lst) >= 3:
                out.append(("疑似多路并到同一脚", name, f"脚 {pin} 上有 {len(lst)} 个器件: {' '.join(lst)}"))

    # 2) 单节点网络（悬空）
    for name, nodes in nets.items():
        if len(nodes) == 1:
            out.append(("单点网络（悬空）", name, nodes[0]))

    # 3) 地网络互不相连：两个含 GND 字样的网络之间没有公共元件
    grounds = {n: set(v) for n, v in nets.items() if re.search(r"(^|_)GND", n) or n in ("AGND", "GND", "DGND")}
    names = sorted(grounds)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if not (grounds[a] & grounds[b]):
                out.append(("两个地网络无公共元件（可能没接）", f"{a} / {b}",
                            f"{len(grounds[a])} 个节点 vs {len(grounds[b])} 个节点，交集为空"))
    return out


# ---------------------------------------------------------------- .epro2 / .epru


def _jload(s):
    s = s.strip().strip("|").strip()
    if not s.startswith("{"):
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _extract_epro2(path):
    """把 .epro2（zip）解开，返回里面的 .epru 路径（同样可能再套一层）"""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="easyeda_"))
    with zipfile.ZipFile(path) as z:
        z.extractall(tmp)
    epru = list(tmp.rglob("*.epru"))
    if epru:
        return epru[0]
    # 有些导出直接就是 .epru
    return pathlib.Path(path)


def parse_epro(path):
    """EasyEDA 专业版工程 -> 已放置元件列表

    返回 [{'desig','part','x','y','pads':{脚号: 网络}}]，只含"有网络表"的元件
    （工程文件里还混着库定义与未放置的图形，它们没有 PAD_NET）。
    """
    if str(path).lower().endswith(".epro2"):
        path = _extract_epro2(path)
    comp, desig, padnet = {}, {}, {}
    for raw in pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.startswith("{"):
            continue
        parts = raw.split("||")
        head = _jload(parts[0])
        if not head:
            continue
        payload = _jload(parts[1]) if len(parts) > 1 else None
        t = head.get("type")
        if t == "COMPONENT" and payload:
            comp[head.get("id")] = payload
        elif t == "ATTR" and payload and payload.get("key") == "Designator" and payload.get("parentId"):
            desig[payload["parentId"]] = payload.get("value")
        elif t == "PAD_NET" and payload:
            try:
                cid, num = json.loads(head["id"])[1:3]
            except Exception:
                continue
            padnet.setdefault(cid, {})[num] = payload.get("padNet", "") or ""

    out = []
    for cid, c in comp.items():
        if cid not in padnet:          # 只有放置了的元件才有 PAD_NET
            continue
        out.append({
            "desig": desig.get(cid, "?" + cid[:6]),
            "part": c.get("partId", ""),
            "x": c.get("x"), "y": c.get("y"),
            "pads": padnet[cid],
        })
    out.sort(key=lambda r: (len(r["desig"]), r["desig"]))
    return out


# ---------------------------------------------------------------- 对比


def netlist_from_pcb(pcb):
    """PCB 的引脚网络 -> 与 .tel 同构的 nets 字典（网络名 -> [位号.脚号]）"""
    nets = {}
    for c in pcb:
        for pin, net in c["pads"].items():
            if not net:
                continue
            nets.setdefault(net, []).append(f"{c['desig']}.{pin}")
    return nets


def check(tel_path, epro_path):
    tel = parse_tel(tel_path)
    pcb = parse_epro(pcb_path := epro_path)
    tn, pn = tel["nets"], netlist_from_pcb(pcb)
    problems = []

    def norm(node_list):
        return set(node_list)

    only_tel = sorted(set(tn) - set(pn))
    only_pcb = sorted(set(pn) - set(tn))
    if only_tel:
        problems.append(("只存在于网表的网络", ", ".join(only_tel)))
    if only_pcb:
        problems.append(("只存在于 PCB 的网络", ", ".join(only_pcb)))

    for net in sorted(set(tn) & set(pn)):
        a, b = norm(tn[net]), norm(pn[net])
        if a != b:
            miss = sorted(a - b)[:8]
            extra = sorted(b - a)[:8]
            problems.append((f"网络 {net} 节点不一致",
                             f"网表多: {miss}  PCB 多: {extra}"))

    # 元件存在性
    tel_refs = set(tel["packages"])
    pcb_refs = {c["desig"] for c in pcb}
    gone = sorted(r for r in tel_refs if r not in pcb_refs and not r.startswith("#"))
    if gone:
        problems.append(("网表里有、PCB 里没有的元件", ", ".join(gone)))
    return tel, pcb, problems


# ---------------------------------------------------------------- SVG 渲染


def render_svg(svg_path, out_png, viewbox=None, scale=None):
    edge = _find_edge()
    if not edge:
        _die("找不到 Edge，无法渲染 SVG（可改用浏览器手工截图）")
    svg_path = pathlib.Path(svg_path)
    tmp_svg = svg_path
    if viewbox:
        x, y, w, h = viewbox
        s = svg_path.read_text(encoding="utf-8", errors="replace")
        scale = scale or 4.0
        m = re.search(r"<svg[^>]*>", s)
        head = m.group(0)
        new = re.sub(r'viewBox="[^"]*"', f'viewBox="{x} {y} {w} {h}"', head)
        new = re.sub(r'\bwidth="[^"]*"', f'width="{int(w * scale)}"', new, count=1)
        new = re.sub(r'\bheight="[^"]*"', f'height="{int(h * scale)}"', new, count=1)
        tmp_svg = pathlib.Path(tempfile.gettempdir()) / "easyeda_crop.svg"
        tmp_svg.write_text(s.replace(head, new, 1), encoding="utf-8")
    m = re.search(r'width="(\d+)"[^>]*height="(\d+)"', tmp_svg.read_text(encoding="utf-8", errors="replace"))
    if viewbox:
        W, H = int(w * scale), int(h * scale)
    elif m:
        W, H = int(m.group(1)), int(m.group(2))
    else:
        W, H = 1600, 1200
    cmd = [edge, "--headless=new", "--disable-gpu", "--no-first-run",
           f"--user-data-dir={tempfile.gettempdir()}\\easyeda_edge",
           f"--screenshot={out_png}", f"--window-size={W},{H}", "--hide-scrollbars",
           "file:///" + str(tmp_svg).replace("\\", "/")]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_png, (W, H)


# ---------------------------------------------------------------- PDF 文本坐标


def pdf_boxes(pdf_path, keys=None):
    if not shutil.which("pdftotext"):
        _die("需要 poppler 的 pdftotext（用来取 PDF 里文字的坐标）")
    xml = pathlib.Path(tempfile.gettempdir()) / "easyeda_bbox.xml"
    subprocess.run(["pdftotext", "-bbox", str(pdf_path), str(xml)], check=False)
    s = xml.read_text(encoding="utf-8", errors="replace")
    pages = re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', s, re.S)
    result = []
    for i, (w, h, body) in enumerate(pages, 1):
        words = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', body)
        d = {t: (float(a), float(b)) for a, b, c, dd, t in words}
        result.append({"page": i, "w": float(w), "h": float(h), "pos": d})
    return result


# ---------------------------------------------------------------- CLI


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]

    if cmd == "tel":
        tel = parse_tel(argv[2])
        print(f"元件 {len(tel['packages'])} 个，网络 {len(tel['nets'])} 个")
        for name, nodes in sorted(tel["nets"].items()):
            print(f"  {name:14s} {' '.join(nodes)}")
        print("\n可疑模式:")
        for kind, who, detail in tel_usage_report(tel):
            print(f"  [{kind}] {who}: {detail}")

    elif cmd == "pcb":
        pcb = parse_epro(argv[2])
        print(f"已放置（有网络表）元件 {len(pcb)} 个")
        for c in pcb:
            pins = "  ".join(f"{k}={v or '(空)'}" for k, v in
                             sorted(c["pads"].items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0))
            print(f"{c['desig']:8s} {str(c['part'])[:24]:26s} ({c['x']},{c['y']})  {pins}")

    elif cmd == "check":
        tel, pcb, problems = check(argv[2], argv[3])
        print(f"网表: 元件 {len(tel['packages'])} / 网络 {len(tel['nets'])}")
        print(f"PCB : 已放置元件 {len(pcb)} / 网络 {len(netlist_from_pcb(pcb))}")
        print("\n可疑模式（网表）:")
        for kind, who, detail in tel_usage_report(tel):
            print(f"  [{kind}] {who}: {detail}")
        print("\n原理图 ↔ PCB 差异:")
        if not problems:
            print("  ✅ 完全一致")
        for kind, detail in problems:
            print(f"  ⛔ {kind}: {detail}")
        return 0 if not problems else 1

    elif cmd == "svg":
        vb = None
        if len(argv) >= 6:
            vb = tuple(float(v) for v in argv[3:7])
        sc = float(argv[7]) if len(argv) >= 8 else None
        out = argv[2].replace(".svg", "") + (f"_crop.png" if vb else "_full.png")
        p, size = render_svg(argv[2], out, vb, sc)
        print(f"已输出 {p}  {size[0]}x{size[1]}")

    elif cmd == "pdfbox":
        pages = pdf_boxes(argv[2])
        keys = argv[3:] or None
        for pg in pages:
            hits = {k: pg["pos"][k] for k in (keys or []) if k in pg["pos"]} if keys else pg["pos"]
            if not hits:
                continue
            mm = 0.3528
            print(f"--- 第{pg['page']}页 {pg['w']*mm:.0f}x{pg['h']*mm:.0f} mm，命中 {len(hits)} 个")
            for k, (x, y) in list(hits.items())[:30]:
                print(f"    {k:12s} ({x:.1f}, {y:.1f}) pt")
            if keys and len(keys) == 2 and all(k in pg["pos"] for k in keys):
                a, b = (pg["pos"][k] for k in keys)
                d = math.hypot(a[0] - b[0], a[1] - b[1])
                print(f"    ⭐ {keys[0]} ↔ {keys[1]} = {d:.1f} pt = {d*mm:.1f} mm（文字标注间距，含偏移）")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
