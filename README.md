# courseware_html_kit — 课件 → 学习网页工具包

配合技能 **courseware-to-study-webpage** 使用（流程与规则见 `SKILL.md`）。

## 从 GitHub 使用

```bash
git clone https://github.com/dkvkvk/courseware-to-study-webpage.git
cd courseware-to-study-webpage
python3 tools/build_example.py
```

仓库根目录即下文的 `kit/`。将 `SKILL.md` 与配套目录放在支持技能的 Agent 环境中使用。
完整示例因上传大小限制保存在 `example/parts/`，上面的命令会无损还原
`example/iot_control_study.html`，并校验 SHA-256；之后可直接用浏览器打开。
`starter_preview.html` 无需构建即可预览。

## ZIP 工具包安装

```bash
mkdir -p /data/work && unzip -o courseware_html_kit.zip -d /data/work/   # 得到 /data/work/kit
```

依赖（沙盒已预装）：python3、poppler-utils（pdftotext/pdftoppm）、python-pptx、LibreOffice（soffice，PPT/PPTX 转 PDF 出图）、tesseract（仅 `--ocr`）、Pillow、node + playwright、chromium。

## 目录

```
kit/
├── SKILL.md                     技能全文（流程、忠实规则、拓展规则、质检清单）
├── README.md                    本文件
├── tools/
│   ├── extract.py               逐页抽取：文本 + 页面图 + inventory.md + summary.json
│   └── qa.js                    质检：桌面/展开/手机/深色截图分段 + JS 错误 + 横向溢出 + 残留 TeX + 占位符
├── starter/                     模板分块（按文件名排序拼接）
│   ├── 00_head.html             head + 全部 CSS（浅/深色变量、组件、手机适配）
│   ├── 10_body.html             页面骨架（{{占位符}}）：顶栏、目录、首屏、导学、章节示例、速查、自测、页脚
│   ├── 80_svgdefs.html          SVG 箭头 marker #ah 与线框类
│   ├── 90_core.js.html          通用脚本（必须最后）
│   └── build.sh                 拼接脚本
├── example/
│   └── iot_control_study.html   完整示例（《物联网控制》第 1/4/5 章）
└── starter_preview.html         模板直接拼出的预览页
```

## 命令

```bash
# 1) 抽取（可一次传多份；PPT/PPTX/KEY 会先转 PDF 出图）
python3 /data/work/kit/tools/extract.py /data/work/extract a.pdf b.pptx --dpi 70
python3 /data/work/kit/tools/extract.py /data/work/extract scan.pdf --ocr --dpi 150   # 扫描件
#   输出：extract/01_<短名>/pages/p001.txt、extract/01_<短名>/img/p-NN.png（位数随页数）、
#         extract/inventory.md、extract/summary.json

# 2) 构建
mkdir -p /data/work/site && cp -r /data/work/kit/starter/* /data/work/site/
#   把 10_body.html 按章拆成 10_intro.html / 20_ch1.html / 30_ch2.html …（编号 10–79）
bash /data/work/site/build.sh /data/work/site /data/work/out.html

# 3) 质检（选项：--no-mobile --no-dark --seg 1500）
node /data/work/kit/tools/qa.js /data/work/out.html /data/work/qa
#   若找不到 playwright：在有 node_modules 的目录运行，或 NODE_PATH=/path/to/node_modules
#   若找不到 chromium：CHROMIUM=/path/to/chromium node …
```

## 模板组件速览（详见 10_body.html）

| 组件 | 写法 | 用途 |
|---|---|---|
| 行内/块级公式 | `<span class="m">…</span>` / `<span class="mb">…</span>` | 轻量 TeX 子集，离线渲染 |
| 提示框 | `.callout.key / .add / .warn / .err` | 重点 / 补充（拓展）/ 注意 / 勘误 |
| 卡片与网格 | `.box`、`.grid2`、`.grid3` | 并列概念、速查 |
| 表格 | `.tablewrap > table`（宽表加 `.wide`） | 对比表，手机横滑 |
| 步骤/时间线/流程 | `.steps`、`.timeline`、`.flow` | 方法步骤、历史、流程 |
| 交互区 | `.lab`（滑块 + canvas + `.metrics`） | 参数演示，脚本见 `initDemo()` |
| 折叠 | `details.src` | 课件原文、课堂提问、例题详解 |
| 自测 | `#quiz` + `QUIZ` 数组 `[题干, [选项…], 正确序号, 解析]` | 即时反馈与计分 |

## 90_core.js 主要函数

- `tex(src)` / `renderMath(root)`：公式渲染；`esc`、`$`(id)、`cssv`(CSS 变量)、`fmt`。
- 复数：`C cadd csub cmul cdiv cabs cexp`，多项式 `polyEval`，求根 `roots(coeffs)`。
- 数值：`rk4(f, x, t, h)` 单步积分（`f(t, x)` 返回导数数组，循环调用得到轨迹）；绘图 `plot(canvas, cfg)`，`cfg = {series, bands, hlines, vlines, points, xmin, xmax, ymin, ymax, xlabel, zero}`，hlines 可设 label/pos/va/ly 防止标注重叠；主题切换调用 `redrawAll()`。
- 页面：`initToc`（目录高亮 + 移动端开关）、`initQuiz`、`initDemo`（示例交互）、`safe(fn, name)`（单模块报错不影响其他）。
