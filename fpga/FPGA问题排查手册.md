# FPGA 问题排查手册

> **用途**：记录 `C:\Users\hokuu\Desktop\FPGA` 工程开发过程中遇到的所有问题及解决办法。
> **约定**：每次解决一个新问题后，自动追加到本文档对应分类下，并在顶部目录索引补一行。
> **环境**：VSCode + TerosHDL 7.0.3 + iverilog(icarus) + GTKWave + ModelSim linting
> **创建**：2026-08-31

---

## 目录索引

| 编号 | 分类 | 问题摘要 |
|---|---|---|
| 01 | 工具链 | VSCode 设置改了不生效（Profile 路径混淆） |
| 02 | 工具链 | Better Todo Tree 报 `vscode-ripgrep` 缺失 |
| 03 | 工具链 | `//===xxx===` 风格分节注释不显示 |
| 04 | 工具链 | TerosHDL 波形入口消失（icarus 下无 wave.fst 可点） |
| 05 | 工具链 | TerosHDL 构建报 `FileExistsError: build 目录已存在` |
| 06 | 仿真 | iverilog `syntax error`（中文全角分号） |
| 07 | 仿真 | `Unable to bind xxx_tb`（`$dumpvars` 绑错模块） |
| 08 | 仿真 | vvp 仿真一直跑不结束（缺 `$finish`） |
| 09 | 仿真 | defparam 引用已删除的参数（`MCNT_DLY not found`） |
| 10 | 时序 | `sel_cnt` 比 `sel` 早一个时钟周期（**正常现象**） |
| 11 | 时序 | `TURN_FREQ` 设置过高导致 595 数据撕裂 |
| 12 | 时序 | 仿真时长不足，看不到位选循环 |
| 13 | 时序 | ★ HC595 级联错位：`qh_o` 写成寄存器导致每级丢 1 bit |
| 14 | 技巧 | 用 `fst2vcd` + Python 分析波形 |
| 15 | 技巧 | VCD 解析陷阱：iverilog 去前导零 vs fst2vcd 零填充 |
| 16 | 技巧 | 最小复现法：写独立 tb 验证单个模块 |
| 17 | 硬件对接 | 16_AD_DA_TEST 的 `da_data[4]=F20` 不在 J14 上 |
| 18 | 硬件对接 | ADA107 接 J14 的引脚特殊功能核查与最优布线分配 |
| 19 | 综合报错 | Gowin `EX3937 unknown module` / `EX3828 层次引用未解析` |
| 20 | 布局布线 | Gowin `PR2017/PR2028`：约束引脚是 CPU 专用脚（R19） |
| 21 | 硬件对接 | ★★★ ADA107 排针插错位 → DAC 平线（RTL 全对也白搭） |
| 22 | 硬件对接 | ★ 核心板与扩展板没插紧 → Gowin Programmer "Device not found" |
| 23 | 时钟/IP | ★★ 全设计改用 PLL 输出时钟 → 综合通过但板子完全不工作 |
| 24 | 时钟/IP | ★★★ IP 向导输入频率填错 → 所有输出**静默减半**（不报错） |
| 25 | ADC/时序 | ★★★ ADC 偶发坏码：先判"是否采在数据跳变过程里" |

---

## 一、环境 / 工具链

### 01. VSCode 设置改了不生效（Profile 路径混淆）

**现象**
改了 `settings.json`，重启 VSCode 后配置依然不生效；界面里看到的设置和实际文件也对不上。

**根因**
用户激活的是 VSCode **Profile**，配置不在默认目录。

- ✅ 生效的目录：`C:\Users\hokuu\AppData\Roaming\Code\User\profiles\-59357ddf\`
- ❌ 改了无效：`C:\Users\hokuu\AppData\Roaming\Code\User\settings.json`（默认 profile）

**解决**
所有 VSCode 配置（settings.json / keybindings.json）一律改 `profiles\-59357ddf\` 下的文件。

**避坑**
- ⚠️ **VSCode 运行时会回写覆盖外部编辑**：改完若用户在设置界面动过东西（或自动保存），它会把内存里的旧版本写回文件，外部加的配置会被悄悄冲掉（实测 `scanMode` 就这样丢过一次）。
- 对策：改完用**独立进程复核**；发现被冲掉就**让用户用设置界面（Ctrl+,）自己设**，那是 100% 可靠的；或改完立刻 Reload Window，中间别动设置界面。
- 动手前先确认当前激活的是哪个 profile（profiles 目录下可能有多个）。

---

### 02. Better Todo Tree 报 `vscode-ripgrep` 缺失

**现象**
`Todo-Tree: Failed to find vscode-ripgrep...`，`command 'todo-tree.refresh' not found`，重启无效。

**根因**
旧版 Gruntfuggly Todo Tree 依赖 `vscode-ripgrep` 模块，该模块缺失/损坏。

**解决**
1. 卸载旧版 Gruntfuggly Todo Tree
2. 安装 `FanaticPythoner.better-todo-tree`（**自带 ripgrep**，无 vscode-ripgrep 依赖）

**避坑**
配置前缀从 `todo-tree.*` 变成 `better-todo-tree.*`，旧配置不会自动迁移。

---

### 03. `//===xxx===` 风格分节注释不显示

**现象**
`//===上升沿、下降沿===` 这类分节注释在 Todo Tree 面板里不显示。

**根因**
默认正则匹配不到 `===xxx===` 模式；且 `tree.flat` 默认 false 会折叠。

**解决**
在 `profiles\-59357ddf\settings.json` 加两条（**已定稿，勿再改动**）：

```json
"better-todo-tree.tree.flat": true,
"better-todo-tree.regex.regex": "(\\/\\/|#)\\s*(($TAGS)|={3,}.*?={3,})"
```

- `={3,}.*?={3,}` 分支专门匹配 `//===xxx===`
- `$TAGS` 按 `($TAGS)` 整块替换，不要拆开

**避坑**
- `scanMode` **不加**，用默认 `workspace`（用户明确选择）。
- 用户偏好最小化改动，别顺手加一堆别的设置。

---

### 04. TerosHDL 波形入口消失（icarus 下无 wave.fst 可点）

**现象**
Testbench Output 里可点的 `wave.fst` 入口消失，只剩 build folder，需要手动进文件夹找。

**根因**
TerosHDL 的 `edalize.js` 里 `is_waveform()` **出厂只对 ghdl 返回 true**，icarus 分支返回 `wave.vcd`（不存在），所以 icarus 下没有入口。

**历史**
- 8-27 给 `edalize.js` 打过补丁（is_waveform 对 icarus 也返回 true；get_waveform_path 的 icarus 分支返回 `wave.fst`）
- 8-28 因"打开闪退"要求回滚所有扩展补丁 → 入口消失
- **闪退元凶更可能是 `run_edalize.py` 的 `makedirs(exist_ok=True)` 改动**，不是 edalize.js 的波形补丁

**解决（需用户明确授权，属"改扩展源码"）**
只重打 `edalize.js` 两处，**不动 `run_edalize.py`**：

```js
// get_waveform_path 的 icarus 分支
return path_lib.join(this.working_directory, 'wave.fst');   // 原 wave.vcd

// is_waveform
if (st === ghdl || st === icarus) { return true; }          // 原仅 ghdl
```

**避坑**
- TerosHDL 更新后补丁会被覆盖，需要重打。
- 临时替代：`wave.fst` 一直由 `$dumpvars` 正常生成，可用 `C:\iverilog\bin\gtkwave.exe` 手动打开（默认在 `C:\Users\hokuu\.teroshdl\build\wave.fst`）。

---

### 05. TerosHDL 构建报 `FileExistsError: build 目录已存在`

**现象**
```
FileExistsError: [WinError 183] ...: 'C:\Users\hokuu\.teroshdl\build'
```
来自 `run_edalize.py` 的 `os.makedirs(working_directory)`。

**根因**
`vvp.exe` 进程还在跑，锁住了 build 目录（通常是上次仿真没结束，缺 `$finish`）。

**解决**
1. 结束 vvp 进程：`taskkill /F /IM vvp.exe`（或任务管理器结束）
2. 删除/移走 build 目录：`C:\Users\hokuu\.teroshdl\build`

**避坑**
- 根本预防：tb 里一定要有 `$finish`（见问题 08）。
- 用户偏好**自己关进程/清目录**，不要给 `run_edalize.py` 打 `makedirs(exist_ok=True)` 补丁绕过。

---

## 二、Verilog 语法 / 仿真错误

### 06. iverilog `syntax error`（中文全角分号）

**现象**
```
hex8_tb.v:24: syntax error
I give up.
```

**根因**
代码里混入了**中文全角分号 `；`**（或全角括号、逗号），iverilog 无法识别。

```verilog
always #10；clk = ~clk;   // ← ；是全角
```

**解决**
改成半角 `;`：

```verilog
always #10; clk = ~clk;
```

**避坑**
- 中文输入法下打代码是高频踩坑点。报错定位到某一行时，优先检查该行所有标点是否为半角。
- 常见全角字符：`；` `，` `（` `）` `：` `""` `''`

---

### 07. `Unable to bind xxx_tb`（`$dumpvars` 绑错模块）

**现象**
`key_filter_tb` 仿真报 `Unable to bind uart_byte_tx_tb`。

**根因**
`$dumpvars` 的目标是**从别处复制过来的残留模块名**，不是当前 tb 的顶层。

```verilog
$dumpvars(0, uart_byte_tx_tb);   // ← 复制残留
```

**解决**
改成当前 tb 自己的模块名：

```verilog
$dumpvars(0, key_filter_tb);
```

**避坑**
复制 tb 模板时，`module` 名、`$dumpvars` 目标、实例化名三者要一起改。

---

### 08. vvp 仿真一直跑不结束（缺 `$finish`）

**现象**
`vvp` 启动后一直跑，不知道要多久，改代码也没反应。

**根因**
`always #10 clk = ~clk;` 这类时钟永远在翻转，tb 里**没有 `$finish`**，仿真不会自己停。

**解决**
在 tb 的 initial 块末尾加 `$finish`：

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

**避坑**
- 缩小延迟倍数**解决不了**这个问题，只有 `$finish` 能终止仿真。
- 这也是问题 05（build 目录被锁）的根源。

---

### 09. defparam 引用已删除的参数（`MCNT_DLY not found`）

**现象**
`uart_byte_tx_tb` 报 `MCNT_DLY not found`。

**根因**
tb 里用 `defparam` 设置了 DUT 中**已经删除**的参数。

```verilog
defparam uart_byte_tx_inst.MCNT_DLY = 1;   // ← DUT 里已无此参数
```

**解决**
删掉该 defparam 行，或改成 DUT 当前实际存在的参数名。

**避坑**
改 DUT 参数后，所有引用它的 tb 都要同步检查。

---

### 19. Gowin 综合报错：`EX3937 unknown module` / `EX3828 层次引用未解析`

**现象**
Gowin 综合 ADDA 工程时报两条错：
- `EX3937 : instantiating unknown module 'adc_capture_simple'`（`top_dds_dac_adcloop.v:42`）
- `EX3828 : external reference 'u_fft.busy' remains unresolved, please declare "u_fft" before using`（`top_system.v:126`）

**根因**
- EX3937：模块文件虽存在，但**没登记进 `.gprj` 的 `<FileList>`**。Gowin 只编译工程文件列表里 `enable="1"` 的文件；命令行 iverilog 手动把文件加进编译参数能过，**不代表 Gowin 能看到它**。
- EX3828：代码用跨模块**层次引用** `u_fft.busy` 去读子模块输出。Gowin 综合器对层次引用支持差；且该 wire（`fft_busy`）声明在引用点**之后**，iverilog 同样报 `declared here / declaration after use`。

**解决**
- EX3937：把 `adc_capture_simple.v` 加进 `ADDA.gprj` 的 FileList（`type="file.verilog" enable="1"`），重新打开工程生效。
- EX3828：在父模块声明 wire 并连到子模块端口（`wire fft_busy; ... .busy(fft_busy)`），并把 wire 声明**上移到引用它的 always 块之前**，代码里改用 `fft_busy` 而非 `u_fft.busy`。

**避坑**
- 新增 `.v` 文件后必须同步登记 `.gprj`，别只靠命令行仿真验证"能编过"。
- 要读子模块状态一律用**端口连出的 wire**，别写 `u_xxx.signal` 层次引用——高云综合器不支持，且 wire 声明必须先于使用（iverilog 也检查）。

---

### 20. Gowin P&R 报 `PR2017/PR2028`：约束引脚是 CPU 专用脚（R19）

**现象**
综合通过，Place & Route 报：
- `PR2028 : The constrained location is useless in current package`
- `PR2017 : 'ad_data[5]' cannot be placed according to constraint, for the location is a dedicated pin (CPU)`

**根因**
`top_system.cst` 里 `ad_data[5]` 约束到 **R19**。在 GW5AT-LV60PG484AC2（AC2 硅片）上 R19 是 **CPU 专用脚**（硬核 ARM 的 JTAG/专用功能），不能作普通用户 IO——哪怕扩展板 J14.12 物理上确实连到 R19 也不行。这类"CPU dedicated"脚在原理图/netlist 里看不出区别，只有 P&R 阶段才报。

**解决**
1. 把该信号**物理飞线改接**到旁边可用的普通 IO（本例：ADC_D5 → P17 测试点，1-pin 空闲脚、官方 16_AD_DA_TEST 作过普通 IO，物理上最顺手）。
2. 同步改 `.cst`：`IO_LOC "ad_data[5]" P17;`。
3. 备用脚优先选**空闲、官方例程验证过、物理顺手**的（P17/V18/P19 三个 1-pin 测试点都是，按接线方便度挑即可），别选离簇太远或零先例的脚；**注意别撞同工程已占用的 ball**（如 R17 已被 da_data[2] 占用）。

**避坑**
- 建引脚表时别只信 netlist/原理图连线——**连线存在 ≠ 该 ball 可作 IO**；GW5AT(带硬核 CPU) 的专用脚要以 Gowin P&R/引脚规划器实测为准。
- 换脚后三处要同步：物理飞线、`.cst`、引脚映射文档（本次已改 `ADA107硬件确认记录.md` §6）。

---

## 三、时序 / 逻辑分析

### 10. `sel_cnt` 比 `sel` 早一个时钟周期（**正常现象**）

**现象**
波形里 `sel_cnt` 的变化领先 `sel` 整整 1 个 clk。

**根因**
两个**串联寄存器**的固有特性：

```verilog
always @(posedge clk ...) if (div_cnt == MCNT) sel_cnt <= sel_cnt + 1;  // 第一级
always @(posedge clk ...) case (sel_cnt) 0: sel <= 4'b0001; ... endcase // 第二级
```

同一 posedge 上：RHS 求值阶段两个块读到的都是**旧** `sel_cnt`；NBA 阶段 `sel_cnt` 写新值、`sel` 写入基于旧值算出的结果。下一个 posedge `sel` 才更新。

**结论：不是 bug。**

对 1kHz 数码管扫描完全无影响（每位保持 1ms = 50000 个 clk，慢得多）。

**想同步的改法（一般没必要）**
把两个 always 合并，用 `sel_cnt + 1` 的新值算 sel。但会引入额外组合逻辑，慢速显示场景建议保持原样。

---

### 11. `TURN_FREQ` 设置过高导致 595 数据撕裂

**现象**
`q_sel` 大部分时间正确，但在 `sel` 跳变边沿出现 `0000`（全灭）或双位同亮。

**根因**
位选切换间隔 < 595 一帧刷新周期：

- `sel` 切换间隔 = `CLOCK_FREQ / TURN_FREQ` 个 clk
- 595 级联移 16 bits 需要约 **64 个 clk**
- 若 `CLOCK_FREQ/TURN_FREQ < 64`，`sel` 在"正在被移入 595"时就跳变了 → 移入的 8 位新旧混合 → 撕裂

**解决**
`TURN_FREQ` 必须满足 `TURN_FREQ < CLOCK_FREQ / 64 ≈ 781250`。
默认 `TURN_FREQ = 1000`（每位停留 50000 clk ≫ 64 clk）非常安全。

```verilog
defparam hex8_HC595_test_inst.hex8_inst.TURN_FREQ = 1000;   // 别用 1000_000
```

**验证数据**

| TURN_FREQ | q_sel 干净一热码率 | 错值 |
|---|---|---|
| 1000_000 | 90.4% | 64 次 `0000` + 32 次双位同亮 |
| 1000 | 98.4% | 仅最初 16 帧（移位寄存器未填满，正常初始化） |

---

### 12. 仿真时长不足，看不到位选循环

**现象**
`q_sel` 一直是 `00000001`，不循环。

**根因**
仿真总时长 < `sel_cnt` 切换周期：

- 原 tb `#2000_00` = 200000 ns = **200 us**，4 段共 **800 us**
- `sel_cnt` 切换间隔 = 50000 clk = **1 ms**
- 800 us < 1 ms → `sel_cnt` 全程 = 0，`sel` 全程 = `0001`

**解决**
把 tb 延时改大（`#20000_00` = 2 ms/段，4 段 = 8 ms），让 `sel_cnt` 能走完多个周期。

**验证**
改为 8ms 后 `q_sel` 正确循环 `0x01 → 0x02 → 0x04 → 0x08` ✓

---

### 13. ★ HC595 级联错位：`qh_o` 写成寄存器导致每级丢 1 bit

**现象**
`q_seg` 输出的值**根本不是合法的段码**（如 `0x58 0xD8 0xDC 0xFC 0xC1 0xC7`），看着像段码被"扭曲"了。

**根因（核心）**
真实 74HC595 的 **QH' 是组合输出**，而原模型写成了**寄存器**：

```verilog
output reg qh_o;                    // ← 错：应该是 wire
always @(posedge clk ...) begin
  qh_o <= diff[7];                  // ← 错：在 posedge clk 更新
  diff <= {diff[6:0], dio};
end
```

级联时（`inst1.dio = inst0.qh_o`）：
- **真实器件**：下一级在 SRCLK 上升沿采到"本级**移位前**"的 Q7（靠 QH' 传播延迟保证）
- **寄存器版**：下一级在**同一个 `posedge clk`** 读 `qh_o`，读到的是**上一次**移位的值

→ **每级联一级丢 1 bit**。16 位移完后 `inst1` 只收到 `{0, seg[7..1]}`，期望值整体右移 1 位，`seg[0]` 永久丢失。

**附带问题**：模型还用 `posedge clk` 去**采样** SRCLK（`assign posedge_srclk = ~r_srclk && srclk`），这要求系统时钟至少比 SRCLK 快 2 倍。真实 595 没有系统时钟，SRCLK 上升沿直接触发。

**解决（方案 A，最小改动）**
```verilog
output wire qh_o;        // reg → wire
assign qh_o = diff[7];   // 组合输出
// 删掉：复位里的 qh_o <= 0;  和移位里的 qh_o <= diff[7];
```

**解决（方案 B，更贴近真实器件）**
去掉系统时钟采样，用真正的边沿触发：
```verilog
always @(posedge srclk or negedge rstn) begin
  if(!rstn) diff <= 0;
  else      diff <= {diff[6:0], dio};
end
always @(posedge rclk or negedge rstn) begin
  if(!rstn) q <= 0;
  else      q <= diff;
end
assign qh_o = diff[7];
```
（两个方案仿真结果完全一致；`clk` 端口保留但不使用，兼容现有例化）

**验证数据（8ms 仿真）**

| | 修复前 | 修复后 |
|---|---|---|
| `q_seg` | `0x58 0xD8 0xDC 0xFC 0xC1 0xC7` — **全非法段码** | `0xB0`(3) `0xA4`(2) `0x92`(5) `0x99`(4) `0x83`(B) `0x88`(A) `0xA1`(D) `0xC6`(C) — **全合法段码**（`0xB4` 为切换边界正常撕裂） |
| `q_sel` | 只有 `0x01` | `0x01→0x02→0x04→0x08` ✓ |

**衍生：`q_sel` 与 `sel` 位宽不匹配**
`hex8.sel` 是 4 位，`hex8_HC595_test.v` 里 `wire [7:0] sel` 是 8 位，编译告警：
```
Port 4 (sel) of module hex8 expects 4 bit(s), given 8. Padding 4 high bits.
```
高 4 位无人驱动（VCD 里显示 `b0xxxx`）。4 位数码管下不影响功能，但建议统一位宽消除隐患。

---

## 四、调试技巧 / 工具经验

### 14. 用 `fst2vcd` + Python 分析波形

**流程**
```bash
FST2VCD="C:/iverilog/bin/fst2vcd.exe"
$FST2VCD wave.fst > wave.vcd       # 注意：输出到 stdout，要重定向
```

然后用 Python 解析 VCD，在关键边沿（如 rclk 上升沿）采样信号值做统计比对。

**注意**
- `fst2vcd` 会**忽略第二个参数**，必须重定向 stdout
- **vvp 直接生成的 `.fst` 往往打不开**（格式问题）→ 见下条

---

### 15. VCD 解析陷阱：iverilog 去前导零 vs fst2vcd 零填充

**⚠️ 这是最容易踩的坑，会直接导致分析结论错误。**

| 来源 | 位宽表示 | 例子 |
|---|---|---|
| **iverilog 直接生成**的 VCD | **去掉前导零** | `b1 #` 表示 8'b0000_0001 |
| **fst2vcd 转换**出来的 VCD | **零填充到完整位宽** | `b00000001 #` |

**补位宽必须补 `'0'`**：
```python
val = "0" * (w - len(val)) + val      # ✅ 正确
```

**千万不要用 `val[0]` 补**：
```python
val = val[0] * (w - len(val)) + val   # ❌ 错误！
```
否则：
- `b1`（2bit 的 `01`）会被补成 `11`
- `b1011000`（0x58）会被补成 `0xD8`

**实际教训**：第一版分析脚本踩了这个坑，把 `q_sel` 读成 `0xFF/0xFE`、把 `q_seg` 读成 `0xD8`，一度得出错误结论。

**另外**：`vvp` 直接生成的 `.fst` 用 `fst2vcd` 常常打不开。绕开办法是让 tb 直接输出 VCD：
```verilog
$dumpfile("wave.vcd");   // 而不是 wave.fst
```

---

### 16. 最小复现法：写独立 tb 验证单个模块

**做法**
遇到可疑模块，单独写一个最小 tb，只实例化它，用最简单的激励验证行为。

**实例**（验证 HC595 移位方向）
```verilog
// 复位后依次移入 1, 0, 1 观察 diff
// 若 LSHIFT：0x00 → 0x01 → 0x02 → 0x05
// 若 RSHIFT：0x00 → 0x01 → 0x00 → 0x01
```
实测确认为 **LSHIFT**：`diff <= {diff[6:0], dio}` 等价于 `(diff << 1) | dio`，新数据进 LSB。

**价值**
比在大工程里加探针、翻波形快得多，结论也更可靠。

---

## 五、硬件对接 / 模块选型

### 17. 16_AD_DA_TEST 的 `da_data[4]=F20` 不在 J14 上

**现象**

想把 16_AD_DA_TEST 的 8 位 AD/DA 接口直接复用到 J14（30pin），再扩成 10 位接微相 ADA107。按例程 `.cst` 核对 J14 引脚时，发现 `da_data[4]` 被分配到了 **F20**，但 J14 上所有 30 个引脚都没有 F20。

**根因**

`基石板-扩展板原理图v1.0.pdf` 中，J14 只引出了以下 FPGA 管脚：

- 右侧：AA18、W15、V17、R19、F19、E19、V18、E22、C18、C20、B16、A15
- 左侧：P14、R16、P15、N14、U18、N15、P17、T18、R17、N17、R18、Y18、P19

F20（`IOT124B/LVDS/DQ2`）**没有被路由到 J14**（在扩展板原理图中完全搜索不到）。16_AD_DA_TEST 的 `.cst` 很可能是按另一种接法/另一种板子写的，不能直接照搬到 J14。

**解决**

把 `da_data[4]` 从 F20 改到 J14 上任意一个空闲 FPGA I/O，例如：

| 原例程信号 | 原球号 | 建议改到 J14 引脚 | 新球号 |
|---|---|---|---|
| `da_data[4]` | F20 | **Pin 16** | N15 |

然后再新增 4 根线扩到 10 位（推荐尽量左右对称，方便画转接板）：

| ADA107 信号 | 建议 J14 引脚 | 球号 | 说明 |
|---|---|---|---|
| `ADC_D[8]` | Pin 23 | C20 | 新增 ADC 高位 |
| `ADC_D[9]` | Pin 25 | B16 | 新增 ADC 高位 |
| `DAC_D[8]` | Pin 26 | R18 | 新增 DAC 高位 |
| `DAC_D[9]` | Pin 28 | Y18 | 新增 DAC 高位 |

**避坑**

- 不要直接照搬例程 `.cst`，必须逐根核对原理图：例程管脚 ≠ 当前板子接插件管脚。
- J14 上只有 **Pin 3 一根 GND**，转接板上要把 ADA107 的 Pin12/Pin30 都连到这一根地，并就近铺地平面，不要只压接一根细线。
- J14 的 Pin1 通过 R164/R165（4.7K）上拉到 +3.3V，不是普通 I/O，不建议用作数据/时钟。
- 画转接板前先用万用表/测试工程确认 J14 空闲引脚确实能作为普通 I/O 使用。

---

### 18. ADA107 接 J14 的引脚特殊功能核查与最优布线分配

**现象**

已确认 F20 不在 J14 上，需要重新给 ADA107 10 位 AD/DA 模块分配 J14 引脚。担心某些 J14 脚是专用时钟/配置/JTAG 脚，导致无法布线或 .cst 报错。

**根因核查**

逐根核对 `基石板-扩展板原理图v1.0.pdf` 和用户标注的 J14 原理图后，结论如下：

| 检查项 | 结论 |
|---|---|
| J14 Pin 1~4 | 电源/地，不能当 I/O（Pin 1/3 还有 4.7K 上拉，更不适合数据/时钟） |
| J14 Pin 5~30 | 全部为普通 FPGA I/O 或时钟增强脚，**无 JTAG/配置专用脚** |
| 时钟增强脚 | AA18(IOB77A, PLL clock)、Y18(IOB87A, GCLKT_10) 给 ADC_CLK/DAC_CLK 用更佳 |
| 数据/时钟线 | 扩展板上**无串联电阻/上下拉**，直连 FPGA |
| Bank 供电 | 全部支持 LVCMOS33 / BANK_VCCIO=3.3 |

**结论**：没有"无法布线"的特殊引脚。

**最优分配（最终版：ADC=J14 5~15，DAC=J14 16~30）**

你板上 J14 的 pin1 在**下方**，编号由下往上 1→30。按你的要求：**下方 Pin5~15 给 ADC，上方 Pin16~30 给 DAC**，与 ADA107 CON40A「上半 DAC / 下半 ADC」物理分区一致（转接板上把 ADA107 的 ADC 端朝 J14 下方、DAC 端朝 J14 上方，上↔上、下↔下，几乎不交叉）。

| J14 脚 | 球 | ADA107 引脚 | 信号 |
|---|---|---|---|
| 5 | AA18 | 39 | ADC_CLK |
| 6 | P14 | 25 | ADC_D1 |
| 7 | W15 | 26 | ADC_D0 |
| 8 | R16 | 27 | ADC_D3 |
| 9 | V17 | 28 | ADC_D2 |
| 10 | P15 | 31 | ADC_D5 |
| 11 | R19 | 32 | ADC_D4 |
| 12 | N14 | 33 | ADC_D7 |
| 13 | F19 | 34 | ADC_D6 |
| 14 | U18 | 35 | ADC_D9 |
| 15 | E19 | 36 | ADC_D8 |
| 16 | N15 | 3 | DAC_D9 |
| 17 | V18 | 4 | DAC_D8 |
| 18 | P17 | 5 | DAC_D7 |
| 19 | E22 | 6 | DAC_D6 |
| 20 | T18 | 7 | DAC_D5 |
| 21 | C18 | 1 | DAC_CLK |
| 22 | R17 | 8 | DAC_D4 |
| 23 | C20 | 9 | DAC_D3 |
| 24 | N17 | 10 | DAC_D2 |
| 25 | B16 | 13 | DAC_D1 |
| 26 | R18 | 14 | DAC_D0 |

未用/备用：Pin27（未标球号，NC）、Pin28(Y18, 时钟备用)、Pin29(A15, 可接 ad_otr)、Pin30(P19)。

**关键改动（相对例程）**

1. `da_data[4]` 从 **F20（不在 J14）** 改到 **R17(Pin22)** —— 这是必须改的唯一一根。
2. `ad_clk` 沿用 **AA18(Pin5)**；`da_clk` 沿用 **C18(Pin21)**，二者均为例程已验证时钟脚（125MHz 可跑），未用未验证的 Y18。
3. ADC/DAC 各扩到 10 位；`ADC_OE`(ADA107 Pin40) 转接板上**直接接地**，不占 I/O；`ADC_OVR`(Pin38) 可选，建议引到 Pin29/A15。

**避坑**

- ADA107 的 NC 脚共 12 个（Pin2、15~24、37），转接板上全部悬空；**切勿把 NC 当信号接**。
- 差分对（R16/P15、T18/R18、R19/P19 等）拆单端用，每脚单独 `IO_TYPE=LVCMOS33` 即可，2MHz 下无影响。
- 画板前用万用表/测试工程确认 J14 空闲脚能翻转，再批量布线。
- **最终结论：连接无错误**——22 个信号脚各用一次、无重复、无信号误接电源/地、NC 未接、时钟脚均为已验证脚、10 位每位唯一。

完整 `.cst` 片段和转接板建议见：  
`C:\Users\hokuu\WorkBuddy\2026-08-30-16-59-32\ADA107_J14_optimized_pinout.md`

---

### 21. ★★★ ADA107 模块排针插错位 → DAC 出平线（RTL 全对也白搭）

**现象**
P9（top_dds_dac）之前真机出平滑正弦；某次物理操作（割 R19 飞线等）后，**DAC OUT 示波器变平线**。
排查链：串口链路 500k 全通、命令链路仿真 4 项全 PASS、cst/顶层/版本逐一核对无异常、RTL 与"能用版本"逐字节一致——代码层完全排除。
**最终根因：ADA107 模块的排针插错位置**（整体偏位/未对齐 J14），重插到位后 P9 立即恢复正弦。

**教训迁移（重中之重）**
① 动过**物理接线/模块插拔/飞线焊接**后若波形异常，**第一反应先查模块排针是否插对位、插到位**（数针脚、对缺口），再动代码；
② 症状"RTL 全对 + 真机平线"时，**代码排除成本远高于物理检查**——先做 30 秒的模块重插再怀疑软件；
③ 示波器用鳄鱼夹测 50MHz 时钟**不可靠**（夹子电容/地线电感会把方波压平），这种测量结果不能当判据；
④ 排针插错不会报任何错误，是"静默故障"，只能靠对位目检/重插排除。

### 22. ★ 核心板与扩展板没插紧 → Gowin Programmer "Device not found"

**现象**
某次烧录时报：
```
Info: Cable found: Gowin USB Cable(FT2CH)...
Info: Target Device: GW5AT-60B(0x0001481B)
Info: Operation "SRAM Program" for device#1...
Error: Gowin Device not found.
```
**解读**：`Cable found` = USB 下载器侧正常（USB 枚举 OK）；`Device not found` = **JTAG 链路（板端）断**（TDI/TDO/TCK/TMS 某一根没通）。
**最终根因**：FPGA 核心板和扩展板（底板）**没有插紧**（当时 ADA107/扩展板重新插拔过），重新插紧后恢复正常。

**排查优先级（成本从低到高）**
① 重插下载线两端（尤其板端 JTAG 口，接触不良最常见）；
② 检查板卡间是否插紧（核心板/扩展板排针、下载排针）；
③ 彻底断电 10s 再上电（SRAM 下载是临时配置，断电即失，重上电应可重新下载）；
④ 换 USB 口（排除 USB 供电/枚举）；
⑤ 检查板子下载模式拨码开关（SRAM/Flash）是否被动过。

**教训迁移**
① "Cable found + Device not found" 是**板端 JTAG 链路断**的标志，优先查物理接触，不是 Programmer/工程问题；
② 动过板卡/模块插拔后再下载失败，**第一反应检查插紧**（与 21 条同理：物理优先于软件）；
③ JTAG 链路问题不会改代码解决，别浪费时间重综合。

---

### 23. ★★ 全设计改用 PLL 输出时钟 → 综合通过但板子完全不工作（无串口输出）

**现象**：把顶层所有逻辑的时钟从板载 `clk50` 换成 PLL 输出 `pll_clk1`（单时钟域重构），
综合/布局布线**全部成功、无 error**，但烧录后**串口一行都不发**，看起来板子"死了"。

**根因链（Gowin GW5AT / 其他高云器件同理）**：
```
① 逻辑全搬走后，clk50 只剩 mdclk 计数器在用
   → 工具把它降级到"通用布线"（不是全局时钟网络）：
     WARN (PR1014) : Generic routing resource will be used to clock signal 'clk50_d'
                     ... may lead to the excessive delay or skew
② 而 clk50 同时是 PLL 的 clkin + PLL_INIT 的 mdclk 来源
③ Gowin PLL 的 PLL_INIT（pll_init.v）必须等到 I_LOCK 才进 STEP_9、才释放 PLL 的 reset
④ 资源报告里"Global Clock Signals"表只剩 clk50_d/da_clk_d/mdclk_cnt[7]...
   ★ 看不到任何 PLL 输出被当成设计主时钟
⇒ PLL 可能一直没被释放 → 全设计没有时钟 → 连 UART 一起死
```

**怎么查（三个必看的构建报告证据）**：
1. `impl/pnr/*.log` → 找 **WARN PR1014**（clock 被降级到 generic routing）
2. `impl/pnr/*.rpt.txt` → **"Global Clock Signals"** 表：确认你的主时钟**在不在**上面
3. `impl/gwsynthesis/*.log` → 确认 PLL 相关模块（`Gowin_PLL` / `PLL_INIT`）**确实被编译进去了**

**结论 / 纪律**：
- ⚠️ **不要把整个设计的时钟从"板载输入时钟"换成"PLL 输出"**。
  留板载时钟域做系统时钟，PLL 只用来产生**相位偏移的专用时钟**（例如给 ADC 的相移采样时钟）
  —— 这样即使 PLL 出问题，UART/灯/心跳仍然活着，**故障可观测**。
- 若要单时钟域 + 相移采样，用"**板载时钟 + 外设时钟相移**"：
  把相移加在**给外设的时钟输出**上（改 IP 里 clkout0 的 phase），逻辑仍跑板载时钟。详见
  `FPGA招新题/docs/架构总览与优化方案_2026-09-10.md` 的 **方案 C**。
- 排查启示：**"综合无 error" ≠ "能跑"**。高云的这类问题只以 WARN 出现，必须主动看报告。

**关联**：TROUBLESHOOTING 阶段 26；逻辑经验 L31。

---

### 24. ★★★ IP 向导里的"输入频率"填错 → 所有输出**静默减半**（不报任何错）

**现象（2026-09-10）**：设计"看起来一切正常"——频率计读数对、FFT bin 对、DDS 输出正常，
但 **ADC 偶尔采到坏码**（vpp 毛刺），排查一整天无果。

**真因**：
```
src/gowin_pll/gowin_pll.ipc
   ClkinClockFrequency=100        ← 向导里填的是 100 MHz
   defparam PLLA_inst.FCLKIN = "100";  IDIV_SEL=2; MDIV_SEL=14; ODIV0_SEL=ODIV1_SEL=14

向导假设：100/2 × 14 = 700MHz VCO → /14 = 50MHz  ✓（Clkout0ExpectedFrequency=50）
板载实际： 50/2 × 14 = 350MHz VCO → /14 = 25MHz  ✗  ← **板载 sys_clk 是 50MHz**
```
⇒ 给 ADC 的时钟只有 25MHz（设计意图 50MHz）。**综合、布线、下载全部零 error / 零 warning。**

**怎么发现的（无需示波器）**：抓一段**原始采样序列**，看样本是否成对重复
- `v[2k]==v[2k+1]` 占 **99.8%**；相同值**游程长度全为偶数**（2/4/6/8/10…）
- ⇒ 数据每 2 个系统时钟才更新 ⇒ **采集时钟 = 缓冲区写速率 / 2 = 25MHz**
- 对照：频率计正确（100kHz → period=500）说明 clk50 确实是 50MHz → 排除"系统时钟也不对"

**危害**：不止时钟频率——任何依赖"绝对时间"的东西都会算错：
本次据此推出的"ADC 数据建立裕量 10ns、270° 相位最优"，实际是"5ns、270° 最差"，**结论正好反转**。

**预防清单**：
1. 用 IP 向导时，**输入频率必须与板载晶振/时钟树实测值一致**；不要"按目标频率"填
2. 生成后**打开 `.ipc` 核对** `ClkinClockFrequency` / `FCLKIN`，并与 `.cst` 里的时钟引脚对照
3. 任何**依赖绝对时间**的推导（采样相位、建立保持、延时匹配）之前，**先确认时钟频率**（实测或从数据特征反推）
4. 高速外设（ADC/DAC）如果"能工作但偶发异常"，把"采样率对不对"列入前三个必查项

**关联**：TROUBLESHOOTING 46 号；逻辑经验 L38/L39；工具经验 U23（配置类事实查源文件）。

---

### 25. ★★★ ADC 偶发坏码：先判"是不是采在数据跳变过程里"

**现象**：ADC 数据流里偶发坏点（约 0.3~1%），坏值幅度**恰好是位权重**（±32、±17、±340），
vpp（max−min）读数跳变，但**频率/FFT 读数完全正常**。

**判据（用一帧原始序列，三条同时成立就是"建立时间型"）**：
1. 坏点**只**出现在"多位同时翻转"的码边界（如中码 511↔512 需要 10 位同翻）
2. 偏差幅度 **∝ 同时翻转位数**：10 位 → ±340；4~6 位 → ±20；2~3 位 → ±10~16
3. 坏值是**逐位混合的整齐值**（如 `170 = 0b10101010`），不是连续分布的模拟噪声
4. 方向与穿越方向相关（MSB 最后稳定：上升穿越偏低、下降穿越偏高）

**⇒ 这三条成立就**不要**去查耦合/接触不良** —— 本次为此白做了：
重焊飞线、双绞、加电容、冻 DAC 总线、逐位屏蔽、换引脚，**全部无效**（都不是原因）。

**修法**：把采样相位挪到"距上次数据出现尽量远"的位置。
```
安全相位区间（mod T）= [tOD + d, T + tOD − t_su]     d=输出建立时间、t_su=FPGA 建立时间
本次：T=40ns、tOD=25ns、原相位 270°=+30ns（只等 5ns ✗）→ 改 135°=+15ns（等 30ns ✓）
```
**改完必须重新验证**：抓一帧，看 `|Δ|>16` 的点数是否降到 0~1。

**关联**：TROUBLESHOOTING 46 号；逻辑经验 L38；工具经验 U28（`raw_dump` 的两项结构诊断）。

---

## 附录：常用命令速查

```bash
# iverilog 工具链路径
IVERILOG="C:/iverilog/bin"
  iverilog.exe       # 编译
  vvp.exe            # 运行仿真
  gtkwave.exe        # 波形查看
  fst2vcd.exe        # fst → vcd 转换

# Python（用于波形分析脚本）
PY="C:/Users/hokuu/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# 编译 + 运行（iverilog）
$IVERILOG/iverilog.exe -g2012 -o sim.vvp file1.v file2.v tb.v
$IVERILOG/vvp.exe sim.vvp

# fst 转 vcd（注意重定向 stdout）
$IVERILOG/fst2vcd.exe wave.fst > wave.vcd

# 结束卡住的仿真进程
taskkill /F /IM vvp.exe

# TerosHDL 默认构建目录
C:\Users\hokuu\.teroshdl\build\wave.fst

# VSCode 生效配置目录
C:\Users\hokuu\AppData\Roaming\Code\User\profiles\-59357ddf\
```

---

*最后更新：2026-09-10（新增 23 全设计改用 PLL 输出时钟会死机 / 24 IP 向导输入频率填错导致输出静默减半 / 25 ADC 偶发坏码的“建立时间型”判据）*
