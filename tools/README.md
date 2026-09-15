# tools —— 可复用脚本

**约定：遇到同类问题先来这里找，能直接用就别重写。** 脚本一律纯标准库（个别依赖 Windows 自带的 Edge / poppler 的 `pdftotext`）。

## `easyeda.py` —— 立创EDA（EasyEDA）导出件的自动核对

| 子命令 | 什么时候用 | 例子 |
|---|---|---|
| `tel <netlist.tel>` | 刚导出网表，想快速看结构 + **自动挑可疑模式** | `python easyeda.py tel Netlist.tel` |
| `pcb <.epro2>` | 想确认 PCB 上**实际**每个元件每个脚挂在哪个网络、元件坐标 | `python easyeda.py pcb ProDoc_PCB1.epro2` |
| `check <.tel> <.epro2>` | ⭐⭐ **投板前必跑**：原理图 ↔ PCB 是否逐脚一致 | `python easyeda.py check Netlist.tel ProDoc_PCB1.epro2` |
| `svg <file.svg> [x y w h] [scale]` | 原理图 SVG 看不清，要**放大某一块**（给 viewBox 即可，缺省 4×） | `python easyeda.py svg SCH.svg 880 -520 305 290 4` |
| `pdfbox <file.pdf> [位号A 位号B]` | 从 PCB 导出的 PDF 里量**两个器件之间的间距** | `python easyeda.py pdfbox PCB.pdf R10 U1` |

### `tel` 会自动挑出的三类可疑模式（都是真实踩过的坑）

1. **疑似多路并到同一脚** —— 一个网络里有 ≥3 个 IC 的**同一个脚号**（例如 8 路霍尔的输出全接在 `U1.1`）。这是"看起来接上了、其实分不出哪一路"的隐形错误。
2. **单点网络（悬空）** —— 只有一个节点的网络，通常是忘接或改网络名留下的残渣。
3. **两个地网络无公共元件** —— 例如 `AGND` 与 `GND` **完全没有交集** ⇒ 两块地各飘各的，ADC 没有参考地。反之，如果交集**只有一个 0 Ω 电阻**，那就是正确的"单点汇合"。

### 关键实现细节（踩过的坑，别改回去）

- `.tel` 网表里**长网络会折行**，续行以 `,` 结尾 —— 解析前必须先合并，否则网络节点会丢。
- `.epro2` 是个 **zip**，里面 `*.epru` 是**行式 JSON**：一行 `{"type":...}||{数据}|`，**行尾那个 `|` 会让 `json.loads` 失败**，必须 `strip("|")`。这是第一次解析出 0 个元件的原因。
- 工程文件里混着**库定义和未放置的图形**；**只有带 `PAD_NET` 记录的元件才是真正放置在 PCB 上的**，按这个筛才不会把库件当成实物。
- 元件位号在 `ATTR` 记录里（`key="Designator"`，靠 `parentId` 关联到 `COMPONENT`），不在 `COMPONENT` 自身。
- 器件坐标的单位**不是 mm**。先用两个"已知间距"标定比例（例如两个键轴 20 mm、两个 2.54 mm 排针相邻脚），再换算，否则量出来的距离会差好几倍。

## 相关经验条目

- 原理图 SVG 是**按 viewBox 1:1 渲染**的（浏览器不会缩放），所以 `svg` 子命令调整 `viewBox` 就能精确放大任意区域。
- 一个网络的"归属"由**接地符号**决定：`GND` 与 `AGND` 在 PCB 上是两块铜皮，改网络会连带改铺铜 —— 改完必须重新导出再 `check`。
