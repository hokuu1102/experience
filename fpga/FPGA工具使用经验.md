# FPGA 工具使用经验

> **定位**：记录**工具怎么用才顺手**——操作流程、注意事项、容易忘的动作。
> 不涉及代码逻辑（→ `FPGA逻辑调试经验集.md`），也不是报错修复（→ `FPGA问题排查手册.md`）。
>
> **约定**：每次发现新的工具使用技巧或注意事项，自动追加到对应分类，编号接排，顶部索引补行。
> **环境**：VSCode + TerosHDL 7.0.3 + iverilog + GTKWave
> **创建**：2026-08-31

---

## 目录索引

| 编号 | 工具 | 经验摘要 | 重要度 |
|---|---|---|---|
| U01 | TerosHDL | 项目文件**不会自动更新**，需手动增删或用 Watcher | ★★★ |
| U02 | TerosHDL | 多数命令作用于**当前活动编辑器**，先点开目标文件 | ★★★ |
| U03 | TerosHDL | `Set as top level` 有 design / testbench 两种，别选错 | ★★ |
| U04 | GTKWave | ★ 重跑仿真前**必须先关闭 GTKWave** | ★★★ |
| U05 | GTKWave | 手动打开波形 / 波形不刷新的处理 | ★★ |
| U06 | iverilog | 仿真卡住 → 查 vvp 进程 + 检查有没有 `$finish` | ★★ |
| U07 | TerosHDL | build 目录被锁的处理流程 | ★★ |
| U08 | VSCode·Better Align | 1.4.5 崩→回滚 1.4.4 + 重开即用；注意 `<=` 会被拆开，脚本作补充 | ★★ |
| U21 | iverilog·仿真 | 无硬件时"顶层分析链"端到端验证：灌已知信号+实时解码 UART 文本行断言 | ★★★ |
| U22 | Gowin·PLL | GW5AT 用 PLL_ADV（非 rPLL）；wrapper 端口 clkin/clkout0/clkout1/mdclk，mdclk 必须给低频时钟否则 PLL 不锁定 | ★★★ |
| U23 | Gowin·构建 | **"综合零 error 但板子不工作"必看三个构建报告**（PR1014 / Global Clock Signals / 综合 log）；配置类事实查源文件（.ipc/.cst），别信 RTL 注释 | ★★★ |
| U24 | VOFA+ | **折线图与右侧文本日志的时间尺度差 ~1000 倍**（图 20s / 日志 24ms）→ 判稳定性必须看折线图，并把 Y 轴固定后直接量色带上下沿 | ★★★ |
| U25 | Gowin·引脚 | **查"两个引脚物理上是否相邻"**：器件库 `.../data/device/<器件>/PBGA484A.json`（ball→IOB tile/BANK/PAIR）+ P&R 报告引脚表；BGA 行标记跳字母，算距离用 ROW_MARK 序号 | ★★★ |
| U26 | Gowin·工程 | **新建 .v 文件后必须加进工程**：只放到 `src/` 没用，Gowin 只编译 `.gprj` 的 `<FileList>` 里的文件 → 否则 `ERROR (EX3937) Instantiating unknown module` | ★★★ |
| U27 | 数据/串口 | **串口"粘行"污染统计**：UART 丢 `\n` 会把两行粘成一行（首字段变成合法但荒谬的大整数），能解析≠合法 → 必须按字段**合法范围**过滤，并打印剔除行数；均值异常而中位数正常就是信号 | ★★★ |
| U28 | FPGA·调试 | **`raw_dump` 原始序列回传 + 两项结构诊断**：①「样本成对重复率」→ 反推**采集时钟真实频率**（全偶游程 = 重复铁证）②「坏点 × 码边界同翻位数」→ 区分**建立时间型**与模拟噪声型。聚合量定不了的案，抓一帧原始序列（本次 1 天 → 30 秒） | ★★★ |
| U29 | FPGA·构建 | **确认"板上跑的是哪版配置"要查到布线后产物**：`.ipc` → `_mod.v` → **综合网表 `.vg`** → 时序报告 | 源码改了 ≠ 生效，mtime 也不可信（重跑会刷新但不改内容）。时序报告会打印相位的等效 ns（例 `CLKOUT1 rise=7.5ns/周期20ns=135°`）；`.fs`/`.bin` 字节数一致可判"重跑等价" | ★★★ |
| U30 | 仪器·时钟 | **测"疑似异常"的时钟前先用已知频率的脚校准探头；能算出来的频率不要测** | 鳄鱼夹测 ADC 时钟读到 **14.6ns**（真实 **40ns**）＝无效读数（长地线振铃）。先量已知的 `da_clk`(50MHz=20ns) 同时验证探头倍率/接地/时基；PLL 输出频率可由 `fout=fclk_in×MDIV/(IDIV×ODIV)` 直接算 | ★★★ |
| U31 | 编码/输出 | **画图与打印的"字符集"三坑**：matplotlib 方块 / Windows 重定向崩溃 / `.bat` 注释被执行 | ①图上中文：坐标轴（sans-serif）正常，但 `fig.text(family="monospace")` 会全变方块 → **图内状态文字用 ASCII**；②控制台正常但**被管道/重定向捕获时** stdout 退回 GBK，而 `µ(U+00B5)/✓/✗` 不在 GBK → `UnicodeEncodeError` 崩溃 → `reconfigure(errors="replace")` 防护；③UTF-8 写的 `.bat` 中文 REM 被 cmd 按 GBK 读 → 字节里可能出现 `&`/`>` → **cmd 会当命令执行**。见 C12 | ★★★ |
| U32 | 仪器/流程 | **改了仪器设置却没生效时，用"被测系统自带的表"当验证器** | 09-10：信号源面板显示改了频率/幅度，但 ADC 读数连续 6 段完全不变（`period=500`、`vpp=215`）。判据链：① 发 `A0`/`W0`（只动 FPGA 的 DDS）无反应 → **排除"FPGA 自己的 DAC 串回 ADC"**；② 断源后 `vpp` 从 215 塌到 13 → **证明源确实在外面那根线上**；③ 于是只剩"仪器设置未提交"。**最快验证器 = 被测系统自己的频率计**（改完设置看 `period`，10 秒出结论，不用来回跑示波器）。另记"无信号形态"：**`vpp≈15` + `period` 散成几百个值 + `bin/mag=0`** | ★★★ |

---

## 一、TerosHDL

### U01. 项目文件不会自动更新，需手动增删或用 Watcher ★★★

**现象**
磁盘上新建 / 重命名 / 删除了 `.v` 文件，TerosHDL 的项目树**不会跟着变**，还是旧的文件列表。

**原因（已核实）**
- TerosHDL 扩展代码中**没有任何 `FileSystemWatcher`** —— 它不监听文件系统变化。
- 项目文件列表是**静态存储在 `.gprj` 文件**里的，只有明确的"添加/删除/刷新"操作才会改写它。

看一眼项目文件就明白了：
```xml
<!-- HC595_driver.gprj -->
<FileList>
    <File path="src/HC595.v" type="file.verilog" enable="1"/>
    <File path="src/HC595_driver.v" type="file.verilog" enable="1"/>
    <File path="src/hex8.v" type="file.verilog" enable="1"/>
    <File path="src/hex8_HC595_test.v" type="file.verilog" enable="1"/>
    <File path="src/HC595_driver.cst" type="file.cst" enable="1"/>
</FileList>
```
> ⚠️ 注意：这个文件里**没有 `hex_8_HC595_test_tb.v`** —— 你的 testbench 一直不在项目列表中，
> 这是很多功能对 tb 不生效的根源。

**解决办法（三种，按推荐度）**

**① 用 Watcher 功能（一劳永逸，但有限制）**
TerosHDL 有独立的 **Watchers** 视图：
```
TerosHDL 面板 → Watchers → 点 "+" 添加
```
- 支持两种类型：**VUnit**（`run.py`）和 **CSV**（文件列表）
- 这些文件变化时，源文件列表会**自动更新**
- ⚠️ 限制：**不是通用的"监听目录自动加 .v 文件"**，只认 VUnit run.py 或 CSV 清单

**② 手动增删（你现在的做法）**
- 项目树右键 → Add sources / Delete
- 适合改动少的情况

**③ 直接编辑 `.gprj`（最快，改多个文件时）**
用 VSCode 打开 `.gprj`，手动增删 `<File path="..." type="file.verilog" enable="1"/>` 行，保存后刷新 TerosHDL 视图。

**小技巧**
改完文件后，如果项目树没反应，试试：
- 切换一下 TerosHDL 面板的视图标签
- 或 `Ctrl+Shift+P` → `Developer: Reload Window`

**⚠️ 典型症状：改了代码但波形没变化**
这个问题最常见的表现不是报错，而是**波形看起来毫无变化** —— 因为你改的文件根本没被仿真用到。

排查时先看这里（详见 U05 排查顺序第 2 步）：
1. 打开 `.gprj`，确认 `<FileList>` 里有你改的文件
2. 不在 → 加到项目里再重跑
3. 特别留意**新建的 tb**：默认不会自动加入，跑的还是上一个 tb

---

### U02. 多数命令作用于"当前活动编辑器"，先点开目标文件 ★★★

**现象**
点了 TerosHDL 的某个按钮（如生成文档、运行仿真），结果作用的不是你想要的文件。

**原因**
TerosHDL 的很多命令读取的是 **VSCode 当前活动编辑器**（active editor）的文件路径，而不是你在项目树里选中的项。

**正确做法**
1. **先在编辑器里点开（激活）目标文件**，让它成为当前标签页
2. 再执行命令 / 点按钮

**这也是你说的"点击要修改的文件设置为活动"** —— 这个操作是必需的，不是玄学。

**注意区分两种"选中"**
| 场景 | 作用对象 |
|---|---|
| 编辑器里点开文件（活动编辑器） | 多数编辑类命令（Documenter 等） |
| 项目树里点右键 | 文件管理类命令（Add / Delete / Set as top level） |

---

### U03. `Set as top level` 有 design / testbench 两种，别选错 ★★

**现象**
仿真时报错或用了错的顶层模块。

**说明（已核实）**
在项目树右键文件 → Set as top level，会弹出两个选项：
```
1. Set as top level design            ← 用于综合/上板
2. Set as top level testbench (only for simulation)  ← 仅用于仿真
```

**选择依据**
- **要仿真** → 选第 2 项（`setTestbench`）
- **要综合上板** → 选第 1 项（`add_toplevel_path`）

**提示**
选错时 TerosHDL 会提示 `The testbench can not be set as top level testbench.`（失败）或 `The testbench was set as top level testbench.`（成功）。

**前提**：目标文件必须**已经在项目列表里**（见 U01）。不在列表中的文件无法设置。

---

### U07. build 目录被锁的处理流程 ★★

**现象**
```
FileExistsError: [WinError 183] ...: 'C:\Users\hokuu\.teroshdl\build'
```

**原因**
上次的 `vvp.exe` 进程还在跑，锁住了 build 目录（通常是因为 tb 里没有 `$finish`，仿真不会自己停）。

**处理流程**
1. 结束 vvp 进程：`taskkill /F /IM vvp.exe`
2. 关闭可能占用波形的 GTKWave（见 U04）
3. 删除 / 移走 `C:\Users\hokuu\.teroshdl\build\`
4. 重新仿真

**根本预防**
tb 里一定要有 `$finish`。

---

## 二、GTKWave

### U04. ★ 重跑仿真前必须先关闭 GTKWave ★★★

**现象**
重新跑仿真后：
- 要么报文件无法写入 / build 目录错误
- 要么波形看起来"没变化"，以为代码没生效

**原因（两条，都很关键）**

**① GTKWave 不会自动重新加载波形**
重跑仿真后 `.fst` 文件内容已经更新，但 GTKWave **仍然显示的是旧波形**。
→ 你看到的是上一次的结果，会误以为"改代码没生效"。

**② GTKWave 会占用/锁定波形文件**
在 Windows 上，GTKWave 打开 `.fst` 后可能保持文件句柄，导致 `vvp` 无法覆盖写入，进而引发 `FileExistsError` 一类错误。

**正确做法**
```
重新仿真前：先关闭 GTKWave 窗口 → 再跑仿真 → 再重新打开波形
```

**养成习惯的顺序**
```
改代码 → 关 GTKWave → 跑仿真 → 打开 GTKWave 看新波形
```

**如果只是想刷新（不想关窗口）**
GTKWave 菜单 `File → Reload Waveform`（或快捷键 `Ctrl+R`），可以重新加载当前文件。
但**关掉重开更彻底**，推荐直接关。

---

### U05. 手动打开波形 / 波形不刷新的处理 ★★

**默认波形位置**
TerosHDL 构建目录：`C:\Users\hokuu\.teroshdl\build\wave.fst`

**手动打开**
GTKWave 路径：`C:\iverilog\bin\gtkwave.exe`
（TerosHDL 配置里 `gtkwave_installation_path: C:/iverilog/bin`）

**步骤**
1. 关闭已打开的 GTKWave
2. 运行 `C:\iverilog\bin\gtkwave.exe`
3. `File → Open New Tab` → 选 `wave.fst`

**波形看着不对时的排查顺序**

1. 确认 GTKWave 已关闭并重开（U04）—— **最常见原因**

2. **确认改的代码真的进了仿真** —— 检查 TerosHDL 里的代码文件是否同步更新（U01）

   TerosHDL 的项目文件列表**不会自动更新**，新建的文件不会自动加入。如果刚改/新建的 `.v` 不在列表里，仿真压根没用到它，波形自然"没变化"。

   检查方法：打开工程目录的 `.gprj`，看 `<FileList>` 里有没有你改的那个文件：
   ```xml
   <FileList>
       <File path="src/xxx.v" type="file.verilog" enable="1"/>
       <!-- 你改的文件在这里吗？不在 → 仿真用的是旧的 / 没用到 -->
   </FileList>
   ```
   不在的话：项目树右键 Add sources 加进去（或手动编辑 `.gprj`），再重新仿真。

   > 💡 尤其中招场景：新建 tb 文件后直接跑仿真 —— tb 不在项目列表里，跑的还是上一个 tb。

3. 确认仿真确实跑完了（没有卡住，看输出日志）
4. 确认 `$dumpfile` 路径和你看的文件是同一个
5. 确认 `$dumpvars` 绑定的是当前 tb 顶层
6. 确认文件**已保存**（VSCode 未保存的修改不会写进磁盘，仿真读到的还是旧内容）

---

## 三、iverilog / vvp

### U06. 仿真卡住 → 查 vvp 进程 + 检查 `$finish` ★★

**现象**
点了仿真后一直转，不知道要跑多久，改代码也没反应。

**排查顺序**
1. **tb 里有没有 `$finish`？** —— 没有的话仿真永远不会停（时钟一直在翻转）
   ```verilog
   initial begin
     $dumpfile("wave.fst");
     $dumpvars(0, tb_name);
     rstn = 0;
     #201 rstn = 1;
     #2000_00;
     $finish;      // ← 必须有
   end
   ```
2. **有没有残留的 vvp 进程？**
   ```bash
   tasklist | findstr vvp
   taskkill /F /IM vvp.exe
   ```
3. **GTKWave 是不是开着？**（见 U04）

**提示**
缩小延迟倍数解决不了卡住的问题，**只有 `$finish` 能终止仿真**。

---

## 四、VSCode 扩展（Better Align）

### U08. ★ Better Align 对齐等号不生效的常见原因 ★★

> ⚠️ **重要（2026-08-31 实测）**：扩展面板显示 **"reported 1 个未捕获错误"** 即代表它**在运行时崩了**，不是用法问题。
> ⚠️ **更正（同日复核，原判断有误）**：Better Align **并未停更**——GitHub 仓库 `chouzz/vscode-better-align` 2026 年仍有 commit，最近正式 tag 是 **v1.4.4（2025-11-18）**，Marketplace 当前版就是你装的 **1.4.5**（3 天前那次更新即此版）。所以"崩溃"更可能是 **1.4.5 这个版本自身的回归 bug**，而非老库兼容问题。
> **建议：先回滚到上一个稳定版 v1.4.4**（见本条目末尾"🔙 回滚历史版本"），不要急着换替代品——替代品（Align Text Tokens / Smart Column Indenter / Code Alignment）大多也停更更久，且你已熟悉 Better Align 的用法。

**命令**：命令面板搜 "Align"（命令 id `vscode-better-align.align`），默认快捷键 `Alt+A`。扩展已确认装在你的 profile（`-59357ddf`）里，不是没装。

**为什么没对齐（按概率从高到低）**

1. **没选中多行 / 光标没落在 `=` 上 / 用了列选择**（最常见）
   Better Align 默认逻辑：有选区 → 对齐选区；无选区 → 对齐"光标所在行 + 上下连续含同字符的行"，且对齐的是**离光标最近的那个对齐字符**。
   - 选区必须是**普通多行选区**（鼠标从上往下正常拖选，或 `Shift+↓` 扩选 / 行首 `Shift+点击` 末行）。**不要用 `Alt+拖` 的"方块/列选择"**——Better Align 对列选择通常不做任何事。
   - 选区里必须**包含 `=` 这个字符**（至少覆盖到 `=` 所在列），光标放在 `=` 左侧最稳。只选单行、或只选了 `=` 右侧部分 → 判不出对齐锚点 → 不动。
   → 解决：整行选中那几行再 `Alt+A`；或单光标放在某行 `=` 上再 `Alt+A`（此时以"光标最近的 `=`"为锚点对齐上下连续行）。

2. **以为"打字会自动对齐"，但默认不自动**
   扩展有"回车后自动对齐"功能，但设置 `betterAlign.alignAfterTypeEnter` **默认 false**。
   → 想要自动对齐：在设置里改成 `true`（建议用 `Ctrl+,` 设置界面改，别直接改 profile 的 `settings.json`，会被 VSCode 运行时回写冲掉）。

3. **只对"连续且都含该字符"的行组生效**
   中间夹了空行 / 纯注释行 / 缺 `=` 的行，会把对齐块"断开"，那段就不处理。

4. **⚠️ Better Align 会把 `<=` 当成 `=` 对齐（会拆坏非阻塞赋值）**
   实测：选区里若有 `q <= diff`，Better Align 把 `<=` 里的 `=` 当对齐锚点，在 `<` 与 `=` 之间插空格，结果变成 `q < = diff`——**`<=` 被拆开、非阻塞赋值被破坏**。所以**含 `<=` 的块别和 `=` 混选**；或改用方案 A 的脚本（按 ` = ` 对齐，自动避开 `<=`）。
5. **localparam 那几行"看着没动"通常是已对齐**
   若那几行之前已是齐的（例如粘过排好的版本），Better Align 再跑没有可调空间 → 看起来"没反应"。**验证**：故意把某行 `=` 前空格删几个，整块选中再 `Alt+A`，若 `=` 被重新推齐，说明扩展正常，只是之前已对齐。
6. **含表达式（`/`、`-` 等运算符）的混排块易抽风**
   实测：`parameter`/`localparam` 块里混入 `SECOND / SYSTEM_FREQ`、`KEY_JUDDER / SYSCLK_CYCLE - 1` 这类含 `/`、`-` 运算符的行时，Better Align 对齐基准容易错乱、**整段不动**。它对简单 `a = b` 正常，一加表达式就抽。→ 这种块直接用方案 A 脚本（只认 ` = ` 一个锚点，不受行内运算符干扰，已实战验证通过）。

**一次成功的操作**
```
1. 鼠标纵向选中要对齐的多行（如那 5 个 localparam）
2. Alt+A   （或 Ctrl+Shift+P → 搜 "Align"）
3. 想对齐到 = 而不是 : → 先把光标放在某行 = 上再 Alt+A
```

**相关设置（按需）**
- `betterAlign.alignAfterTypeEnter`: `false`（默认）→ `true` 可自动对齐
- `betterAlign.surroundSpace.assignment`: `[1,1]`（`=` 两侧空格，默认已支持 `=`）

**🔧 多语言对齐方案（替代 Better Align，后续还要写 C / Python）**

手动对齐工具要选**语言无关**的（基于"选中行 + 指定 token"，不依赖语法树），这样 Verilog / C / Python 一套搞定：

- **① Align Text Tokens**（Serge Lamikhov-Center）★ 主推
  选中多行 → 命令面板搜 "Align Text Tokens" → 输入要对齐的字符（如 `=`）即可列对齐。
  定位与 Better Align 几乎一致（选中 → 按 token 对齐），纯语言无关，**Verilog / C / Python 通用**，代码极简不易崩。
  ⚠️ 只有 ~4K 安装，相对小众，但原理稳健，比 Better Align 可靠。
- **② Smart Column Indenter**（Leonardo Machado Carreiro，~71K）备选
  把代码按"列/块"对齐，更通用更流行；适合大段整体列对齐。
- **③ Code Alignment**（经典 VS 扩展的 VSCode 移植版，商店搜 "Code Alignment"）
  老牌跨语言"按字符对齐"工具，可选。

**C 语言：用 clang-format 做"自动"对齐（最省心，不用手动触发）**
- 装 **Clang-Format** 扩展（或 Microsoft C/C++ 自带），在项目根目录放一个 `.clang-format`，加一行：
  ```yaml
  AlignConsecutiveAssignments: true
  ```
- 效果：连续赋值行（如结构体初始化、宏定义）保存时**自动对齐 `=`**，比手动扩展还省事。
- 这是 C 用户对齐等号的最优解，强烈建议配。

**Python：formatter 默认不对齐 `=`**
- Black / autopep8 / Ruff 都**不排版等号对齐**（PEP8 不强制，主流 formatter 不管）。
- 需要手动对齐（如一组 `dict` 赋值、logging 配置）时，用上面 **① Align Text Tokens** 手动做即可。

**🔙 回滚 Better Align 到历史版本（1.4.5 崩溃时的首选方案）**
VSCode **没有"扩展回滚"按钮**，需手动装旧版 `.vsix`：
1. 下载稳定版 vsix（推荐 **v1.4.4**，上一个正式 tag）：
   `https://marketplace.visualstudio.com/_apis/public/gallery/publishers/Chouzz/vsextensions/vscode-better-align/1.4.4/vspackage`
   （若 1.4.4 仍崩，再试更早的 **v1.4.2**）
2. 卸载当前 1.4.5（Extensions 视图里 Better Align → 卸载）
3. 从 VSIX 安装：Extensions 视图右上角 `...` → **Install from VSIX...** → 选下载的文件
4. **⚠️ 关键：关闭该扩展自动更新**，否则 VSCode 会很快把它覆盖回 1.4.5：
   - 方式 A（推荐）：Extensions 里 Better Align 右键 → **Disable Auto Update**
   - 方式 B：设置 `"extensions.autoUpdate": false`（全局关闭，影响所有扩展，慎用）

> 💡 **先确诊再回滚（可选但推荐）**：`Help → Toggle Developer Tools → Console`，看红色报错的堆栈，能确认是 1.4.5 特有还是 VSCode 新版本 API 不兼容。前者回滚必解；后者旧版也可能崩，需等作者修或换方案。

> ⚠️ **实测：Code CLI 在无头/无运行实例环境下会静默失败**（`code --install-extension` / `--list-extensions` 无输出、无 exit code）。此时改用 **filesystem 直达**（已验证可用）：
> 1. 下载 vsix（见上方 URL）后 `unzip` 解压，扩展代码在 `extension/` 子目录里（不是根）；
> 2. 把 `extension/` 内全部文件复制到 `C:\Users\hokuu\.vscode\extensions\chouzz.vscode-better-align-1.4.4\`；
> 3. 删除 `...\chouzz.vscode-better-align-1.4.5\`；
> 4. 编辑 profile 的 `extensions.json`（`AppData\Roaming\Code\User\profiles\-59357ddf\`），把该条目的 `version` / `location.path` / `relativeLocation` 改为 1.4.4，并把 `metadata.pinned` 设 `true`（扩展级锁，防自动更新回 1.4.5）；
> 5. 同时在全局 `AppData\Roaming\Code\User\extensions.json` 写 `{"extensions.ignoreAutoUpdate":["chouzz.vscode-better-align"]}` 作双保险。
> 改完**完全退出 VSCode 再重开**才生效。

### 🔧 Better Align 能用，但有坑 + 脚本作补充
> 实测更正：回滚到 v1.4.4 + **完全退出 VSCode 重开**后，Better Align 实际正常（新开 C 文件等号也能对齐）。之前"还是不行"是因为**没重开 VSCode，旧实例（内存里还是被改写前的状态）在跑**——这是 filesystem 改扩展的通病，改完必须重开。
> Better Align 本身可用，但有 `<=` 拆分坑（见原因 4）。脚本方案 A 不替代它，而是作为**含 `<=` / 需要精确控制时的补充工具**。

**方案 A：通用对齐脚本（补充，处理 `<=` 场景最稳）**
- 脚本已放：`C:\Users\hokuu\Desktop\FPGA\tools\align_by_token.py`
- 用法：把要对齐的多行存成 `in.txt`，跑
  ```
  python align_by_token.py in.txt > out.txt
  ```
  默认按 ` = ` 对齐（自动避开 `<=` 非阻塞赋值，不会拆开）；也可指定别的 token：`align_by_token.py in.txt " => "`
- 不含 `=` 的行（空行 / 注释 / 纯声明）保持原样，不会错位。

**方案 B：VSCode 内置「列选择 + 多光标」（零扩展兜底）**
1. 鼠标不按 Alt，纵向选中目标行；
2. `Ctrl+Shift+Alt+↓` 向下扩展列选区，或 `Alt+鼠标拖` 拉方块；
3. 把光标移到各 `=` 前手动补/删空格推平（配合 `End`/`Home`）。
- 缺点：列宽需肉眼估算；胜在永远不崩。

**结论**：Better Align 能用时优先用它（`Alt+A` 最顺手）；遇到 `<=` 被拆、或它偶尔抽风，再用脚本 A 兜底。

---

## 五、日常操作 checklist

### 每次改代码重新仿真前
- [ ] **关闭 GTKWave**（U04）★ 最容易忘
- [ ] **确认改的文件已在 TerosHDL 项目列表里**（U01/U05）★ 新建文件默认不在
- [ ] 确认文件已保存（`Ctrl+S`）—— 未保存的修改不会写进磁盘
- [ ] 确认没有残留 `vvp` 进程（U06）
- [ ] 确认 tb 里有 `$finish`（U06）
- [ ] 若 build 目录报错，清理 `C:\Users\hokuu\.teroshdl\build\`（U07）

### 新建 / 增删源文件后
- [ ] 在 TerosHDL 项目树里同步增删（U01）
- [ ] 或用 Watcher（VUnit / CSV）自动同步（U01）
- [ ] 需要仿真的话，确保 tb 已加入项目并 `Set as top level testbench`（U03）

### 执行 TerosHDL 命令前
- [ ] **先在编辑器里点开目标文件**，让它成为活动编辑器（U02）
- [ ] 确认该文件已在项目列表中（U01）

### 波形看着不对时（按此顺序排查）
- [ ] 关掉 GTKWave 重开（U04）
- [ ] **检查 TerosHDL 里改的文件是否同步进了项目**（U01/U05）
- [ ] 确认文件已保存
- [ ] 确认仿真真的跑完了（看日志）
- [ ] 确认 `$dumpfile` / `$dumpvars` 设置正确

---

### U09. ★ $readmemh 只认 HEX，别给 octal/十进制数据 ★★

**现象**：DDS 用 `$readmemh("xxx.mem", rom)` 加载波形，仿真输出不是平滑正弦，
数值随机跳变（如 512→790→566→36→850），查遍 RTL 无果。

**原因**：Python 生成数据时用了 `'{:04o}'`（octal），但 `$readmemh` 按
**十六进制**解析。octal 文件被当 hex 读 → 每个数错位，波形全乱。
（`$readmemb` 才是二进制；十进制没有对应系统函数）

**解决**：生成文件前先问"读它的函数要什么进制"——
- `$readmemh` → hex（用 `{:03x}` 格式化，每条一行，可带注释 `//`）
- `$readmemb` → binary
- 校验：`head` 看首行应是 `200`（hex 的 512）而非 `1000`（octal 的 512）

**经验迁移**

> ① 用脚本生成 ROM 数据后，**先肉眼核对首行/末行与 min/max** 再仿真；
> ② Python 写数据统一 hex 三位补零（`{:03x}`）最稳，别省事用 `{:o}`；
> ③ ROM 数据错乱的表现是"波形跳变非平滑"，第一反应查文件格式而非 RTL。

---

### U10. 多模块工程交付前跑"回归脚本"——一次验证所有 TB ★★

**场景**：一个工程跨 10+ 个目录（phase0~16），每轮改代码后要确认"没改坏别的模块"。
逐个手动跑 18 个 TB 既慢又易漏。

**做法**：写一个 shell 函数循环（bash，Windows 下 Git Bash 可用）：

```bash
run_tb() {  # 参数：目录 + 该 TB 需要的源文件
  local d="$1"; shift; cd "$ROOT/$d" || return
  iverilog -o _reg.vvp "$@" || { echo "[$d] 编译失败"; return; }
  out=$(timeout 120 vvp _reg.vvp 2>&1); rm -f _reg.vvp _reg.vcd
  echo "[$d] PASS=$(echo "$out"|grep -c PASS) FAIL=$(echo "$out"|grep -c FAIL)"
  echo "$out" | grep FAIL | head -3   # 只看失败详情
}
run_tb phase14 fft64.v fft64_tb.v
run_tb phase16 cmd_parser.v ../phase4/uart_tx.v ... cmd_parser_tb.v
```

**要点**
- 统计口径统一用 `[PASS]/[FAIL]` 文本断言（TB 里每条结论都 $display 前缀）→ 脚本可 grep
- 跨目录模块用相对路径（`../phase4/uart_tx.v`）引用；.mem 文件复制到运行目录
  （见 L18，$readmemh 相对路径）
- 每轮代码改动后跑一遍，几秒到几分钟换"全工程没坏"的确定性

**经验迁移**

> ① TB 的每条断言都带 `[PASS]/[FAIL]` 前缀是可 grep 的前提——写 TB 时就养成；
> ② 交付前跑回归 + 把结果表贴进 README/日志，用户醒来一眼知道现状。

### U11. 示波器看到"两条横线 + 几百 Hz 假读数" = 时基慢了 5 个数量级

**现象**：GDS-2202E 看 100kHz 正弦，屏幕只有两条水平线，
Measure 频率读数 751.9/643.9/397.6Hz（全错）。
**原因**：时基停在 **500ms/div**，而信号周期只有 10us——
横轴每格 500ms、信号 5 万个周期压进一屏，欠采样混叠：
- 波形视觉上塌缩成上下两条包络线
- 频率测量输出混叠伪值（几百 Hz），完全不可信
**解决**：HORIZONTAL SCALE 旋钮拧到 **20us/div**（100kHz 一周期占 2 格），
或直接按 Autoset。拧完后 Frequency 读数才是真值。
**口诀**：看波形先看屏幕底部时基读数——**ms 级看不了 MHz 信号**，
估计值：时基 ≈ 信号周期 ÷ 2（一周期占 2 格最易读）。
**教训迁移**：任何"读数离谱"先怀疑采集端设置，而不是信号源。

---

### U12. 示波器"运行 vs 不运行屏显不同"=信号已到；免示波器用 ChipWatcher/万用表验证

**现象**：GDS-2200E 接 DAC OUT，FPGA 跑 P9（DDS 正弦）时屏幕与"不运行程序"时明显不同；
但按 Autoset 却停在 500ms/div，看起来像两条横线+假频率读数（U11 混叠）。
**原因**：Autoset 在信号幅度偏小或触发难锁时不会自动放大，直接把时基放到最大（500ms/div），
100kHz 正弦被压成上下两条包络线；但"运行/不运行不同"恰恰证明 DAC 已被驱动、信号已到探头。
**解决（二选一）**：
- 用示波器：手动把 HORIZONTAL SCALE 拧到 **20us/div**（别靠 Autoset），volts/div 设 2V，
  触发源 CH1 → 看到真实正弦，Frequency≈100kHz。
- 免示波器：① **Gowin ChipWatcher** 探针 da_clk/da_data/DDS 相位累加器，能看到数字波形即数字链路通；
  ② **万用表 AC 档**碰 DAC OUT，运行读到 AC 电压、不运行≈0V。
**教训迁移**："屏显随程序运行变化"是比"Autoset 是否成功"更可靠的硬件连通证据；
Autoset 失败不代表没信号，先手动调时基再下结论。


### U13. 示波器 Frequency 读数被谐波/噪声带偏——用光标 Δf 或周期格数判断真实基频

**现象**：P9 DDS 正弦上板后，屏幕已能看到正弦波形，但右下角自动 Frequency 读数显示 **353.682kHz**，
与目标 100kHz 不符；而手动光标测得 Δf ≈ **99.40kHz**，正好对应 100kHz。
**原因**：DAC 输出是 50MHz 采样的**阶梯波**，频谱除 100kHz 基波外还有大量 50MHz±N·100kHz 的镜像分量；
示波器自动频率计数器在低采样率/余辉模式下可能抓到某个强谐波或镜像，给出错误读数。
光标测量两个相邻同相点（如一屏内两个波峰）得到的 Δf 才是真实基频。
**解决**：
- 优先用**光标/Cursor**测周期：调一个周期占 2~4 格，放光标在两个相邻峰/过零点，读 Δt 或 Δf
- 或数格：时基 × 格数 = 周期，再取倒数得频率
- 别信右下角自动 Frequency 当波形含有高频台阶/噪声时
**教训迁移**：DAC/数字合成信号上，"波形像正弦"但自动读数离谱，先怀疑计数器抓了谐波，
用光标或格数验证基频最稳。


### U14. GDS-2200E 时基读数位置与调节

**现象**：用户找不到"时基 div"读数和调节位置。
**位置**：
- 时基读数在屏幕**底部正中间**（波形下方），例如显示 `2us`、`20us`、`500ms` 等，即当前 **TIME/DIV**。
- 调节旋钮在面板 **HORIZONTAL** 区，标有 **SCALE** 的大旋钮；往数值变小方向拧（通常逆时针）放大波形。
**当前 P9 合适设置**：100kHz 正弦周期 10us，设 **2us/div** 时一周期占 5 格，最易读。
**附带**：按 **Measure** 键弹出的 Measurement Summary 会挡住波形，再按一次 Measure 或按屏幕下方"关闭"软键即可退出。


### U15. DDS/DAC 输出在示波器上"双影" + Measure 频率在 100/200kHz 间跳

**现象**：P9 100kHz 正弦在 GDS-2200E 上能看到正弦，但波形像两个正弦重叠；
按 Measure 时频率读数在 100kHz 和 200kHz 之间跳。
**原因**：
1. DDS 输出是 50MHz 采样的阶梯波，频谱含大量谐波/镜像；
2. 自动频率计数器阈值附近不稳定，会在基波（100kHz）和二次分量（≈200kHz）之间来回抓；
3. 若开了**余辉（Persistence）**，多次触发点轻微水平抖动会让波形叠成"双影"。
**判断真伪**：光标/Cursor 测两个相邻同相点的 Δf 始终 ≈100kHz，这就是真实基频。
**解决**：
- Display/Acquire 里把 **Persistence 关 Off**，采集模式设 Normal/Average
- TRIG MENU：Source=CH1、Slope=上升沿；LEVEL 旋钮调到正弦中间
- 触发耦合改 **HF Reject/Noise Reject（高频抑制）**，滤除 DAC 台阶高频抖动
- 时基调到 **10us/div**，一周期占 1 格，最易观察
**实际效果**：P9 最终截图在 10us/div、HF Reject 开、噪声抑制关状态下，波形稳定为干净正弦，
一格一周期 = 10us = 100kHz，DAC 台阶毛刺几乎不可见。
**教训迁移**：数字合成信号上，自动频率跳变和双影通常是**显示/触发设置**问题，不是输出频率真的在跳；
用光标周期法判断基频最可靠。


### U16. volts/div 挡位拧过头 → 信号压扁 + 测量读出几十 V 假峰值

**现象**：用户把 VERTS/DIV 误调到 **20V/div**（屏幕左上 `1 = 20V`），
DAC 的 8Vpp 正弦被压成不到半格，Measure/光标读数出现 "80 多 V" 等离谱值。
**原因**：VOLTS/DIV 是 1-2-5 步进（1→2→5→10→20→50V），从 2V 多拧两档就到 20V；
信号幅度相对挡位太小，触发不稳，示波器把噪声/漂移当信号，读出假峰值。
**解决**：逆时针拧 VOLTS/DIV 内层旋钮，看 `1 = xxV` 从 20V 经 10V、5V 回到 **2.00V**。
**判断标准**：volts/div 设对时，正弦波竖直占 **3~6 格**；
只占不到 1 格 = 挡位太大（往小拧）；顶到屏外 = 挡位太小（往大拧）。
**硬约束（ADA107）**：该模块 5V/3.3V 供电，DAC 模拟输出规格为 **±4.3V（8.6Vpp 上限）**
（见 ADA107硬件确认记录.md §1/§4）。任何超出此范围的电压读数（如 40V/80V）都不可能是真实信号，
必为挡位/触发导致的假值。
**补充（2V/div 仍出屏的排查）**：±4.3V（8.6Vpp）信号在真 2V/div 下只占 4.3 格，绝不溢出。
若拧到 2V/div 仍"超出屏幕"，二选一：
- ① **旋钮拧过头**（1-2-5 步进，从 20V 下拧易多拧到 1V/500mV）：看屏幕 `1 = xxV`，
  若是 1.00V/500mV 则往回（数值变大方向）拧到 **2.00V**。
- ② **CH1 菜单 Probe/Attenuation 误设 10X**（示波器把电压显示×10，±4.3V 变 ±43V）：
  按 CH1→菜单改回 **1X**。
**先读 `1 = xxV` 真实挡位**即可区分①/②，不必猜。
**本次确认（P9 现场）**：用户回忆菜单里出现 x10，实测即 **② 探头倍率设成 10X**——
导致 20V/div 下 Measure 读 40V、2V/div 下信号出屏，二者同源。改回 1X 后一切正常。
**坑点**：用 SMA-BNC 同轴线（非 10× 探头）时，CH1 Probe 必须设 **1X**，否则电压读数被放大 10 倍、
且小挡位直接出屏；若某天真换了 10× 无源探头再改回 10X。
**教训迁移**：测量读数与挡位严重不匹配（几 V 信号读出几十 V）时，先查 volts/div 挡位，
而不是怀疑信号源；挡位对了读数才可信。判断真伪优先级：
**格数×时基/volts/div > 光标 > 自动 Measure 菜单**（Measure 在信号过小/触发不稳时专抓噪声尖峰，最不可信）。


### U17. DDS/DAC 直出"噪声大、毛刺多"=阶梯波+镜像，非模块故障；开 BWL 即净
**现象**：P9 改回 1X 后看到 DAC OUT 波形毛刺/噪声明显，怀疑模块坏了。
**原因**：DDS 直出是**阶梯波**——DAC 每时钟沿跳变到量化值，陡峭边沿在频谱上产生大量谐波与
奈奎斯特镜像（如 50MHz 采样 → 镜像在 50M±100k、100M±100k…）；示波器默认 **200MHz 全带宽**
把这些高频成分全显示，视觉即密集毛刺。**这是 DAC 直出固有特性，与模块好坏无关**。
**判断真伪**：
- 规则、周期性毛刺（跟波形周期一致）→ DDS 直出正常，**非模块问题**
- 随机抖动 + 低频漂移 + 50Hz hum（形状乱、不随波形周期）→ 才疑电源/地/参考噪声
**佐证模块正常**：供电正常(5V≈4.9/3.3V≈3.2)、频率与幅度正确(100kHz/±4.3V) → 坏了不会这么标准。
**一键改善（按效果排序）**：
1. **CH1 菜单开 Bandwidth=20MHz（最狠）**：滤掉 >20MHz 台阶/镜像，100kHz 正弦保留，毛刺瞬间消失
2. **Acquire→Average 4/8/16 次**：随机底噪被平均压低
3. HF Reject 触发耦合：主要压触发抖动，对显示毛刺帮助有限
**硬件层**：要真·光滑正弦需在 DAC 后加**抗混叠低通（重建滤波）**；ADA107 通常未加/弱加，
属设计取舍非故障。招新题验收只看"有正弦、频率对、幅度对"，毛刺不影响通过。
**教训迁移**：看到 DAC 输出"噪声大"先开 BWL 验证，别急着怀疑模块；规则毛刺=正常，随机抖动=才查电源地。


### U18. 上板 ROM 铁律：initial $readmemh 行为级 ROM 一律内嵌数据或换 pROM
**现象（P9 证实 + P14/P16 排查）**：DDS/FFT 等 ROM 用 `initial $readmemh("xxx.mem", rom)` 行为级写法，
Gowin 综合**不把外部 .mem 数据打进 bitstream**（高云对该初始化的支持因版本/器件而异，实测 GW5AT-60 不加载）。
后果：ROM 全 0 → DDS 输出恒定、FFT 旋转因子全 0 → 频谱全错；但 **仿真（iverilog）完全正常**，"仿真过≠上板过"。
**修法（推荐①）**：
1. **数据内嵌**：把 .mem 内容直接写进 `initial begin rom[i]=...; end`（已验证路线：P9 sine_rom / P14 fft64 twiddle / P8 wave_rom 均改此）
2. 用高云 **pROM IP**（Tools→IP Core→pROM）加载 .mem，但需手动 IDE 配置，新手易错
**适用范围**：凡**上板综合路径**上的 ROM（DDS 波形表、FFT 旋转因子、任何查表）必须处理；**仅 TB 内部**的 $readmemh（读测试向量）可保留。
**教训迁移**：写任何 ROM 先问"上板用还是仿真用"。上板 ROM 默认内嵌，仿真 $readmemh 只放 TB。


### U19. 按 Default（出厂设置）键 = 所有手动设置归零，"波形突然不一样"先查这个
**现象**：P9 验收后按了一下面板 Default 键，波形显示大变：时基从手动调好的值跳回 **2us/div**、
CH2 自动打开（2mV/div 空通道）、测量项/触发/带宽限制全部重置，误以为信号出了问题。
**原因**：GDS-2200E 的 Default 把时基、垂直挡位、通道开关、触发、测量、BWL 等**全部恢复出厂值**，
不保留任何手动调整。
**关键澄清（100kHz 在不同时基下的视觉密度）**：
- 20us/div：一周期占 0.5 格，一屏 10 格 = **约 20 个周期** → 视觉"密集"，但信号正常
- 10us/div：一周期 1 格，一屏 10 个周期 → 直观
- 2us/div：一周期 5 格，一屏 2 个周期 → 稀疏
**同一信号，时基不同密度完全不同**——显示变密/变稀 ≠ 频率变了。
**自动读数依然是假值**：Default 后 Measure 项重置，重新出现 382kHz/572kHz 之类谐波假读数（U13），
判频永远以 **格数 × 时基** 为准。
**Default 后必做重配清单**：
① 关掉空通道 CH2（不接东西只引噪声）② CH1 菜单确认 Probe=1X、开 BWL=20MHz（滤 DDS 台阶毛刺）
③ 时基调 10us/div（1 格/周期最直观）④ 触发 Source=CH1、LEVEL 旋钮放波形中间
**教训迁移**："波形显示突然变了"先回忆是否按过 Default/Autoset 这类全局重置键；
显示变化 ≠ 信号变化，先用格数验证频率，再怀疑硬件。
**补充（触发耦合 HF Reject vs DC 对照，本次用户实测）**：
- **触发耦合**（注意：不是通道输入耦合！）选 **HF Reject（高频抑制）** → 触发电路忽略 DAC 台阶高频、锁定基频，画面稳定不动 → **验收推荐设置**。
- 选 **DC** → 台阶高频干扰触发点，每次触发位置微抖，画面水平滚动（"一直在刷新新波形"）→ 信号本身没错，只是触发没锁稳，不便于截图/读数。
- **与通道输入耦合区分（易混）**：① 通道输入耦合（CH1 菜单）必须设 **DC**，保留波形直流分量；② 触发耦合（TRIG MENU）用 **HF Reject** 让画面稳。两者独立菜单，都要设对。
- 判频仍以 **格数 × 时基** 为准，与触发耦合无关。


### U20. UART 上位机乱码排查：MSB 被置 1 = 波特率对齐不稳；先降速、用"心跳+回显"自测隔离
**现象**：自测工程每秒发 `'H'`(0x48)，上位机收到 **`0xA8`**（MSB 被置 1）；回显 `'A'` 是 `41` 但对，
偶尔还多出 `0xC1`(41|0x80)。规律：**字节低位对、高位错**。
**原因**：1M 波特率下 PC 端（web 串口工具/CP2102 驱动/线缆）采样对齐不稳，每字节**末端漂移到位沿**
→ 末尾几位读错（典型表现 MSB 被读成 1）；每字节独立重新同步，所以低位总是对。
**解决（按序二分）**
1. **换桌面工具（Tera Term/SSCOM）精确设 1M** 复核——部分 web 工具把 1,000,000 就近取整成 921,600；
2. 仍乱 → **降速**（本次降 500k 即净）；降速后 FPGA RX 要能扛大分频值（见逻辑经验 L23，`clk_cnt` 位宽 bug）；
3. **用"心跳+回显"自测工程隔离链路**：每秒一个固定字符验 TX；敲字符弹回验双向——不依赖 ADC/DAC/FFT 与命令解析，
   5 分钟定位"是 PC 端还是 FPGA 端"。
**VOFA+ Firewater 两个必记点**
- Firewater **只有收到 `\n` 才刷新/解析**；持续无换行的数据会让缓冲区爆满、**软件卡死**（官方 ReadMe 原话）。
  发文本命令**必须带换行**：输入框敲完按回车再点发送，或勾"发送新行"。
- 自测的 `'H'` 不是 Firewater 数字帧，VOFA+ 里不显示是正常的——**看链路用串口助手文本区，看曲线才用 VOFA+**。
**教训迁移**："字节前面对、后面错/MSB 被置 1" → 先怀疑收发波特率对齐，别急着改 FPGA 时钟；
降速是最便宜的判定实验。

### U21. 无硬件时"顶层分析链"端到端仿真验证法 ★★★
**适用**
题1/题2 这类"信号进 ADC → 测量/FFT → UART 上行"链路，SMA/BNC 线没到、示波器不在手时，想先兜底验证逻辑。
**做法**
1. 写顶层 TB（如 `ADDA/sim/tb_top_analysis.v`），把**已知信号**直接灌进 `top_system.ad_data`：
   `ad_data <= 512 + $rtoi(AMP * $sin(2.0*3.14159*t/PERIOD))`；500kHz@50M → `PERIOD=100clk`、幅 200LSB。
2. **实时解码 `report_tx` 的 Firewater 文本行**：TB 里写 UART 监视器（500k→100clk/bit，下降沿起、半位取样、LSB 先收），逐字节重组，遇 `\n` 结束一行，按逗号 split 出 `vpp,period,bin,mag`。
3. 断言期望值（500kHz 正弦：vpp≈400、period=100、bin=16、mag≈125）。
4. **断言挪到 `rep_cnt` 变化沿**的独立块，避开非阻塞赋值"同拍读旧值"陷阱（否则首行 mag 读到 x）。
**验证结果**
题1/题2 分析链仿真 ALL PASS（5 行报告一致），真机只差"信号喂入 + ADC 接口"一跳。
**经验迁移**
① 没示波器也能验证"测量+上报"全链路，比单模块 TB 更接近真机；
② 解码 UART 上行比看内部线网直观，还顺带验证了波特率/协议；
③ iverilog 直接 `src/*.v` 全编译 + `-s tb_xxx` 选顶层即可跑，无需逐个列文件。

---

### U22. Gowin GW5AT 的 PLL IP = PLL_ADV（不是 rPLL）+ 端口/初始化坑 ★★★
**适用**
GW5AT 系列（基石板 GW5AT-LV60）要做 PLL 分频/相移时钟（如 ADC 源同步采样相移 180°）。

**Key facts（实战踩过）**
1. **IP 名字是 `PLL_ADV`**，不是旧系列的 `rPLL`，也不是 `SSCPLL`（展频 PLL，时钟会周期性抖动，绝不可当采样时钟）。路径：`Tools → IP Generator → Hard Module → CLOCK → PLL_ADV`。
2. **顶层 wrapper 端口只有 4 个**：`clkin` / `clkout0` / `clkout1` / `mdclk`。**没有 `lock` 端口**——例化时写 `.lock()` 会编译报"端口不存在"。
3. **`mdclk` 必须给一个低频时钟**（本工程用 `clk50` 8 位计数器分频 50M/256 ≈ 195kHz）驱动内部 `PLL_INIT` 完成初始化。**悬空 = PLL 永远不锁定、无时钟输出**。
4. 两路输出频率都设相同（如都 50MHz），相位分别 **0°**（给 ADC 时钟 `ad_clk_out`）/ **180°**（给 FPGA 采样域 `adc_capture.clk_samp`）。改完相位要**重新点 OK 生成**覆盖 `src/gowin_pll/gowin_pll.v` 才生效。
5. 生成的 `Gowin_PLL` 模块已自动加入 `.gprj`（`enable=1`），无需手动登记。

**经验迁移**
① 不同系列 PLL IP 名字不同，先到 IP Generator 里看真实列表，别凭记忆写 `rPLL`；
② 硬核 IP 的初始化时钟（mdclk 这类）是真需求，例化前先看 wrapper 端口再写；
③ 180° 相移采样修的是"源同步 ADC 建立/保持裕量"，仿真暴露不了（仿真零延迟），只能真机验证。

### U23. ★★★ 高云"综合零 error 但板子不工作"→ 必看三个构建报告 + 注释与 IP 配置漂移核查

**背景（2026-09-10 实战）**：把全设计时钟换成 PLL 输出后，综合/布线**零 error**，
但板子完全没反应。问题**只以 WARN 形式存在**，不看报告根本发现不了。

**必看的三个构建报告位置**
| 文件 | 找什么 | 本次抓到什么 |
|---|---|---|
| `impl/pnr/*.log` | 布局布线阶段的 WARN | `WARN (PR1014)`: 'clk50_d' 将被放到**通用布线**（时钟质量差）|
| `impl/pnr/*.rpt.txt` | **"Global Clock Signals"** 表 | 表里**没有 PLL 输出**作为设计主时钟 → 主时钟根本没上全局时钟网络 |
| `impl/gwsynthesis/*.log` | 各模块是否真的被编译 / 参数是否正确 | `WARN (EX3073)`: 端口未连接（可据此发现自己漏连的新端口）|

**配套纪律：IP/GUI 里的配置改动不会写进 RTL 注释，甚至可能没提交 git**
- 本次踩坑：`top_system.v` 注释写"PLL 180° 采样域"，实际 `gowin_pll.ipc` 里是 **270°** →
  基于注释做的整条时序分析**全部跑偏**（浪费一轮）。
- ✅ **核查方法**：配置类事实**一律去查源文件本身**：
  - PLL 相位/频率 → `src/gowin_pll/gowin_pll.ipc`（搜 `PhaseStaticValue`）
  - 引脚 → `*.cst`；时钟约束 → `*.sdc/*.cst`
  - **同时用 `git status` 看这些文件是否"改了但没提交"**（本次 IP 改了 6 小时没提交）
- ✅ 建议：改完 IP **当场更新 RTL 注释并 commit**；或干脆在注释里写"以 .ipc 为准"。

**关联**：手册 #23；逻辑经验 L31；TROUBLESHOOTING 阶段 26。

---

### U24. VOFA 折线图 vs 右侧文本日志：时间尺度差 ~1000 倍，判稳定性**必须看折线图**

**现象（2026-09-10 实战）**：右侧文本日志看着"数据很稳"（30 行几乎不变），
但折线图上却是**一大片密集的上下毛刺**。用户困惑："为什么数据没啥波动，图上毛刺却很大？"

**原因**：两者显示的时间跨度差 3 个数量级——
| 视图 | 显示范围 | 折算时间（1250 行/s @REPORT_GAP=40000/clk50）|
|---|---|---|
| 右侧**文本日志** | 只有**最后 ~30 行** | **≈ 24 毫秒** |
| **折线图** | 缓冲区 50000 点（横轴 2164ms/格 ×10）| **≈ 20~40 秒** |

→ **图上是"过去 20 多秒的全部数据"，文本只是"最后 24 毫秒"。**
只要毛刺在这 20 秒里出现过就会留痕，而"最后一秒恰好干净"是**采样运气**，
不是"没有毛刺"。（同一坑：连续误判过 3 次的"短窗口判稳定性"。）

**正确用法（判稳定性）**
1. **看折线图，不看文本日志**（日志只用于抽样核对数值）
2. **把 Y 轴改成固定范围**（如 0~1024 或测得的量程）→ **直接量粉带/色带的上下沿**，
   一眼读出真实波动范围，不会被自动缩放骗
3. 需要精确数据时，把**日志行数拉到最大**，或直接存 CSV

**本次从图上量出的结论（示例）**：l0(max码) 色带跨 **~612→880**、l3(min码) 跨 **~115→500**
→ 说明波动**不是偶发尖刺，而是密集、高频发生**（文本 30 行里看不到纯属运气）。
其中 `880 − 622 = 258 ≈ 256 = bit8` → 除 bit5 外 **bit8 也可能在翻**（值得单独查）。

**关联**：逻辑集 L29/L30（长窗口判据 / 差值拆分量）。

---

### U25. ★★★ 查"两个引脚在物理上是否相邻"：Gowin 器件库 JSON + P&R 报告（2026-09-10）

**用途**：判定"高速输出与敏感输入是否落在同一 IOB tile / 相邻 ball"——**纯离线，不用上板**。

**器件库位置**：
```
C:\Gowin\<版本>\IDE\data\device\<器件>\<封装>.json
例：C:\Gowin\Gowin_V1.9.12.03_x64\IDE\data\device\GW5AT-60B\PBGA484A.json
```
结构：
```json
{ "ROW_MARK": "A,B,C,D,...,AA,AB",   // BGA 行标记顺序（用于算行距离）
  "ROW_COUNT": 22, "COL_COUNT": 22,
  "PIN_DATA": [ { "INDEX": "P17",       // ball 名（就是 .cst 里 IO_LOC 用的名字）
                  "NAME":  "IOB140B",    // ★ IOB tile（A/B 是 tile 的两半）
                  "TYPE":  "I/O",        // I/O / POWER / GROUND
                  "BANK":  6,
                  "PAIR":  "IOB140A" },  // ★ 同 tile 的另一半
                ... ] }
```

**P&R 报告里的对应信息**：`impl/pnr/*.rpt.txt` 的引脚表
```
Port Name | Diff Pair | Loc./Bank | Constraint | Dir. | Site | ... | IO Type | Drive | Pull Mode | ...
ad_data[5]| -         | P17/6     | Y          | in   | IOB140[B] | ...
```

**操作步骤**：
1. 从 `.rpt.txt` 取每个端口的 `Loc`（ball）与 `Site`（IOB tile）
2. 从 JSON 里查这些 ball 的 `ROW_MARK` 序号 + 列号 → 算**曼哈顿距离**
3. 找"距离 ≤2"的 输出/输入 组合 → 这些就是**潜在串扰对**
4. 顺便看 `TYPE`：邻居里有 `VSS`/`VCCIO` 是好事（有地/电源隔离），有高速输出是坏事

**本次实战结论（示例）**：
```
ad_data[5] = P17 = IOB140B  ←→  da_data[4] = N17 = IOB140A   （同一个 tile！）
P17 的 8 邻居：N17/R17/R18 三个都是 DAC 数据脚 → 该位实测间歇翻转
```

**要点 / 坑**：
- ⚠️ **从端口名上完全看不出邻接关系**（`P17` / `N17` / `R17` 名字毫无线索）→ 必须查表
- ⚠️ JSON 里 tile 名是 `IOB140B`，P&R 报告里写成 `IOB140[B]` → 比对时要**去掉方括号**
- ✅ 同一 tile 的 `A`/`B` 两半共享电源/地，且封装内紧邻 → **最容易互相干扰**
- ✅ BGA 行标记会跳字母（`A,B,C,D,E,F,G,H,J,K,M,N,P,R,T,U,V,W,Y,AA,AB`，**没有 I/O/Q/S/X/Z**），
  算距离要用 `ROW_MARK` 里的**序号**，不能用字母序/ASCII

**顺带能查到**：`BANK`（能否共用 VCCIO）、`TYPE`（是不是电源/地脚）、`DIFF`/`TRUELVDS`（能否做差分）

**关联**：逻辑集 L32/L33；TROUBLESHOOTING 阶段 33。

---

### U26. ★★★ 新建 .v 文件后必须"加进工程"——否则 EX3937 unknown module（2026-09-10）

**现象**：
```
ERROR (EX3937) : Instantiating unknown module 'glitch_count'
                (".../src/top_system.v":209)
```
但文件明明在 `src/glitch_count.v`，`ls` 得到，iverilog 也编得过。

**原因**：**Gowin 只编译工程文件列表里的文件**，`src/` 目录里"躺着"的文件不会被自动纳入。
列表写在 `<工程名>.gprj` 里（XML）：
```xml
<FileList>
    <File path="src/adc_capture.v" type="file.verilog" enable="1"/>
    ...
</FileList>
```

**两种修法**：
1. **IDE 内（最可靠）**：Project → **Add Files**… 选中新文件（会自动写进 .gprj）。
2. **直接改 .gprj**：在 `<FileList>` 里插一行
   `<File path="src/xxx.v" type="file.verilog" enable="1"/>`

**⚠️ 关键坑（务必记住）**：
- **Gowin 打开工程期间，外部对 `.gprj` 的修改会被 IDE 保存时覆盖**（IDE 用内存里的副本写回）。
  → 外部改 .gprj **必须先把 Gowin 工程完全关掉**，改完再打开；Gowin 开着时请改用方法 1。
- 改完可以用脚本核对"磁盘上的 .v 是否都在 .gprj 里"：
  ```python
  import io,os,re
  listed=set(re.findall(r'<File path="([^"]+)"', io.open('ADDA.gprj',encoding='utf-8').read()))
  disk=[os.path.relpath(os.path.join(r,f),'.').replace('\\','/')
        for r,ds,fs in os.walk('src') for f in fs if f.endswith('.v')]
  print("漏加:", [p for p in disk if p not in listed])
  ```
- 本工程实际漏加过：`glitch_count.v`（致 ERROR）+ 题5 的 `zero_cross.v / phase_detector.v /
  dpll_pi.v / top_pll_sync.v`（尚未用到的，做 题5 时会同样报错，要提前加）

**为什么容易漏**：iverilog/ModelSim 用 `-y <dir>` 自动搜目录，**编得过**；
而 Gowin 走工程列表 → **同一份代码在两个工具里一个过、一个报错**。别被"iverilog 通过了"骗到。

**关联**：手册（Gowin 构建流程）；TROUBLESHOOTING 阶段 36。

---

### U27. ★★★ 串口数据的"粘行"污染：统计前必须按字段**合法范围**过滤（2026-09-10）

**现象**：一份 96241 行的日志，`glitch` 字段均值算出 **610.9**——而该字段只有 8 bit（最大 255）。
中位数却是 8，明显是极少数异常行把均值拉飞。

**根因**：UART 偶尔丢一个 `\n`，两行被**粘成一行**：
```
正常两行:   000010,0,2,120
            000005,...
粘行结果:   00001000005,0,2,120     ← 首字段变成 11 位数字
```
这个首字段 **`int()` 解析完全成功**（合法整数 1000005），所以"能不能解析"型的校验**抓不到**。
本次 6 行 / 96241 行（0.006%）就把均值从 **7.86 抬到 610.9**（78 倍）。

**做法**：
1. 给每个字段定义**合法范围表**（`FIELD_RANGE`），逐行校验，越界即剔除并计数
2. **报告里必须打印"剔除了多少行"**，否则读者不知道数据是否被动过
3. 统计**永远同时看均值和最大值**：均值异常而中位数正常 = 有离群/损坏行

**本机实现**：`tools/vofa_logger.py` 的 `FIELD_RANGE` / `vals_sane()`，
在实时记录、`--analyze`、分组表三处都已生效。

**通用性**：任何"文本协议 + 无校验和"的采集（串口/网口日志）都有这个坑。
根治办法是协议带校验（长度/校验和/序号），但**分析端做范围校验是最低成本的兜底**。

**关联**：TROUBLESHOOTING 阶段 44 的注意事项；`tools/vofa_logger.py`

---

### U28. ★★★ `raw_dump`：原始序列回传 + 两项"结构诊断"（2026-09-10）

**背景**：`vpp`/毛刺点数这类**聚合量**（每窗口两个数字）折腾一整天也定不了根因；
抓 **1024 点原始 ADC 序列**后 30 秒看清。**排查前先问"我需要的证据形态是什么"。**

**实现（本工程已有，可直接搬）**
| 部件 | 位置 |
|---|---|
| RTL：1024×10bit 循环缓冲 + 冻结 + 十进制上行 | `ADDA/src/raw_dump.v`（串口命令 **`R`** 触发，与正常上报共用 TX，`dump_busy` 二选一） |
| 仿真 TB（位流导出 + Python 解码） | `ADDA/sim/tb_raw_dump.v` |
| 上位机（抓帧/存 CSV/分析/画图） | `FPGA招新题/tools/raw_dump_capture.py` |
| 启动器（cmd/PS 通用、可双击） | `FPGA招新题/tools/run_rawdump.bat` |

**★ 两项结构诊断（本次就是靠它们定案的，已内置在 `--analyze`）**

**① 样本重复率 → 反推"采集时钟的真实频率"**
```
v[2k]==v[2k+1] 99.8%  且  相同值游程长度全为偶数(2/4/6/8/10…)
  ⇒ 数据每 2 个系统时钟才更新一次 ⇒ 采集时钟 = 缓冲区写速率 / 2 = 25MHz
```
本次由此发现 **PLL 向导里输入频率填了 100MHz、板载实际 50MHz → 所有输出静默减半**。
⚠️ 这类"采样率不对"在聚合量里**完全看不出来**，只有原始序列能暴露。

**② 坏点 × 码边界「同时翻转位数」→ 区分故障类型**
```
把每个坏点事件与它跨越的码边界对应，数 popcount(lo ^ hi)：
  同翻 10 位 → 偏差 ±340      (中码 511↔512)
  同翻  6 位 → 偏差 ±20
  同翻  2 位 → 偏差 ±10~16
⇒ 偏差 ∝ 同翻位数 = **采样点落在数据跳变过程里（建立时间不足）**
   而不是耦合/接触不良（那类不会与码边界强相关）
```

**其它要点**
- **抓一帧要"窗口对齐"**：本次 1024 点恰 = `vpp` 窗口 20.48µs，抓到的坏点就是影响读数的那些
- 单点坏值会在相邻差里留下**两个**跳变（进/出）→ 看序号是否相邻即可区分"单点"还是"连续平台"
- 帧格式用**纯文本十进制**（`#RAW` + 每行一个点 + `#END`）最省事，Python 侧一行 `int()` 就解析
- 踩过的两个坑（见逻辑集 **L36/L37**）：循环缓冲写指针**必须复位**；子 FSM 别在 `done` 同拍重启

**关联**：逻辑集 L38/L39/L40；TROUBLESHOOTING 46/47 号

---

### U29. ★★★ 确认"板上跑的是哪版配置"：一路查到**布线后产物**（2026-09-10）

**问题**：改完源码 / 改了 IP 参数，凭什么说"板上就是这一版"？注释会漂移、`.ipc` 只是配置意图、
下载的 `.fs` 可能是旧的、文件 mtime 也被重跑刷新过。

**四步核查链（从意图到产物，逐级可验证）**

| 步 | 查什么 | 本轮实例（确认 135° 已进 bitstream） |
|---|---|---|
| 1 | IP 配置 `.ipc` | `Clkout1PhaseStaticValue=135` |
| 2 | IP 生成文件的 defparam | `CLKOUT1_PE_COARSE=5 / CLKOUT1_PE_FINE=2`（＝135°） |
| 3 | **综合网表** `impl/gwsynthesis/*.vg`（喂给布线的输入） ← **最关键** | 同样是 `COARSE=5 / FINE=2` |
| 4 | **时序报告**里工具自己的建模 | `CLKOUT1 rise=7.5ns / 周期 20ns` = 135° |

**顺带能从网表确认的事**
- **顶层是不是我要的那个**：本轮 `top_system` 在、且 `u_raw_dump`/`dump_req` 在
  → 说明 `R` 命令确实包含在这版里（不是误编译了别的 top）；
- **重跑是否等价**：`ADDA.fs` / `ADDA.bin` 的**字节数**与上一版一致 → 同一条结果，不是新变量。

**关联**：U23（构建报告必看三项）、U22（PLL IP 端口坑）、TROUBLESHOOTING 53 号

---

### U30. 频率测量的三条纪律（2026-09-10）

1. **能算出来的频率不要测**：PLL/IP 输出频率由参数直接决定
   （`fout = fclk_in × MDIV / (IDIV × ODIV)`；本轮 = `fclk_in/2` 是**恒等式**）。
   当配置里的输入频率本身填错时，实测读数反而会把人带偏。
2. **测之前先用已知频率的脚校准**：本轮用 BNC 转鳄鱼夹测 ADC 时钟读到 **14.6ns**，真实是 **40ns**。
   校准方法：先测同一块板上已知的时钟脚（本轮 `da_clk` = clk50 = 50MHz = 20ns），
   同时验证探头倍率、接地弹簧、时基。⚠️ 鳄鱼夹长地线在高速时钟上会引入振铃，
   示波器的周期测量可能计到**振铃边沿**而非时钟周期。
3. **优先用"数据反推"做交叉验证**：本轮真正定案的是「样本成对重复率 + 游程长度全偶」
   → 采集时钟 = 缓冲写速率的一半。**不需要额外仪器，且比直接测时钟更可靠。**
   （相关：U28 的结构诊断）

**关联**：U28（raw_dump 结构诊断）、TROUBLESHOOTING 53 号、逻辑集 L39（裕量要用实测频率）

---

### U31. ★★★ 画图与打印的"字符集"三坑（2026-09-10）

**坑 1：matplotlib 里中文变方块（而且只变一部分）**
- 默认字体 DejaVu Sans **没有中文字形** → 需 `matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', ...]`
  （本机实测可用：Microsoft YaHei / SimHei / SimSun / Source Han Sans SC）。
- **但设了字体后仍会有一部分变方块**：`fig.text(..., family="monospace")` 用的是**等宽字体列表**，
  里面没有中文字体 → 那一行全变 □，而坐标轴标签（默认 sans-serif）却是正常的。
  实测同一张图里：`时间/频率/幅度/ADC 码` 正常显示，`锁定/真实采样率/窗长/配对相位` 全是 □。
- **对策：图内状态文字一律用 ASCII**（数字+英文），中文只留给坐标轴；或加 `--en` 全英文。

**坑 2：交互式控制台正常，一被重定向/管道就崩**
- Windows 下交互式控制台 Python 走 **Unicode 控制台 API（PEP 528）** → 中文、`µ` 都正常；
- **但 `stdout` 被管道/重定向捕获时**，退回本地代码页（中文系统 = **cp936/GBK**），
  而 `µ (U+00B5)`、`✓`、`✗` **不在 GBK 里** → `UnicodeEncodeError` 直接崩（本次实测崩在 `print("µs")`）。
- **对策**：`sys.stdout.reconfigure(errors="replace")`（只放宽错误处理，不换编码）→ 退化而不是崩。
- ⚠️ 这个坑**特别阴**：你自己在终端里跑一万次都不崩，**一进脚本/CI/管道就崩**。

**坑 3：`.bat` 的编码 —— 中文注释会被 cmd 当命令执行**
- 用 UTF-8 写的中文 `REM` 注释，cmd 按 ANSI/GBK 解码 → 拆出的字节里可能出现 `&`、`|`、`>` →
  **cmd 会把它当命令分隔符执行**（本次实测报 `'xx' is not recognized as an internal or external command`，
  还把注释片段当命令跑了）。
- **对策**：`.bat` 一律用 **ANSI/GBK** 写（PowerShell：`Set-Content -Encoding Default`），
  或注释只写 ASCII。

**关联**：`共性问题集` C12；`tools/live_scope.py`；`tools/run_scope.bat`

---

## 附录：常用路径速查

```
TerosHDL 项目文件     <工程目录>/<工程名>.gprj
TerosHDL 用户配置     <工程目录>/<工程名>.gprj.user
默认构建目录          C:\Users\hokuu\.teroshdl\build\
默认波形文件          C:\Users\hokuu\.teroshdl\build\wave.fst

GTKWave               C:\iverilog\bin\gtkwave.exe
iverilog              C:\iverilog\bin\iverilog.exe
vvp                   C:\iverilog\bin\vvp.exe
fst2vcd               C:\iverilog\bin\fst2vcd.exe

TerosHDL 扩展目录     C:\Users\hokuu\.vscode\extensions\teros-technology.teroshdl-7.0.3\
```

---

*最后更新：2026-09-10（新增 U23~U28 …；**U29 确认板上配置要查到布线后产物（ipc→_mod.v→.vg→时序报告）；U30 频率测量三条纪律（能算就别测 / 先校准探头 / 用数据反推交叉验证）；U31 画图与打印的"字符集"三坑（matplotlib 方块 / Windows 重定向崩溃 / `.bat` 注释被执行）**）*
*配套文档：*
- *`C:\Users\hokuu\Desktop\经验\fpga\FPGA问题排查手册.md` —— 环境配置 / 编译报错 / 命令速查*
- *`C:\Users\hokuu\Desktop\经验\fpga\FPGA逻辑调试经验集.md` —— 代码逻辑 / 时序 / 调试方法论*
- *`C:\Users\hokuu\Desktop\经验\器件积累.md` —— 电子元器件积累*
