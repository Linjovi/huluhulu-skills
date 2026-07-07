---
name: animate-gif
description: Use when the user asks to create an animated GIF / 动图 / 动画 / 表情包 from a text prompt. Two-step pipeline — (1) generate a 3×3 frame grid via nanobanana / gpt-image / seedream, (2) slice the grid into 9 frames and assemble an animated GIF. Triggers on "做个动图", "生成 gif", "做表情包", "make a gif", "animate this", "生成动图".
---

# Animate GIF Generator

通过**自然语言提示词**生成动图 GIF。

## 工作流程

```
用户提示词 → [Step 1] 生成九宫格图 → [Step 2] 裁切九宫格 → 动图 GIF
```

---

## 第一步：生成九宫格图

### 支持的模型

内置支持三种图像生成模型的官方接口，用户通过环境变量配置 API Key 和选择 provider。

| Provider | 模型 | 环境变量 | 默认 Base URL |
|---|---|---|---|
| `gpt-image` | `gpt-image-1` (OpenAI) | `OPENAI_API_KEY` | `https://api.openai.com` |
| `nanobanana` | `gemini-2.5-flash-image` (Google Gemini) | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com` |
| `seedream` | `seedream-4.0` (火山方舟) | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com` |

**可选环境变量：**

| 变量 | 说明 |
|---|---|
| `OPENAI_BASE_URL` | 覆盖 gpt-image 的基地址（兼容代理） |
| `GEMINI_BASE_URL` | 覆盖 nanobanana 的基地址 |
| `GEMINI_IMAGE_MODEL` | 覆盖 Gemini 模型名（默认 `gemini-2.5-flash-image`，可选 `gemini-3.1-flash-image` 等） |
| `ARK_BASE_URL` | 覆盖 seedream 的基地址 |
| `ARK_IMAGE_MODEL` | 覆盖方舟模型名（默认 `seedream-4.0`） |

### 配置 API Key

根据你使用的 provider，配置对应的 API Key：

```bash
# gpt-image (OpenAI)
export OPENAI_API_KEY="sk-..."

# nanobanana (Google Gemini)
export GEMINI_API_KEY="..."

# seedream (火山方舟)
export ARK_API_KEY="..."
```

### 调用方式

```bash
python3 {baseDir}/scripts/generate_grid.py \
  --prompt "一只柯基坐着朝镜头挥右前爪打招呼，扁平卡通风格，白底" \
  --provider gpt-image
```

**参数：**

| 参数 | 默认 | 说明 |
|---|---|---|
| `--prompt` | — | 动作描述（必填）：主体 + 动作 + 风格 |
| `--provider` | `gpt-image` | 图像生成模型：`gpt-image` / `nanobanana` / `seedream` |
| `--references` | — | 参考图（本地路径 / URL / `data:` URL），多个用空格分隔 |
| `--output-dir` | `./generated_gifs` | 输出目录 |
| `--output-path` | — | 显式指定输出 PNG 路径 |

**输出：**

```json
{ "success": true, "grid_path": "./generated_gifs/grid_20260707_120000.png" }
```

### 模型选择决策

1. **用户明确指定了 provider** → 使用该 provider，需检查对应环境变量是否已配置。
2. **用户未指定 provider，但已配置了某个 API Key** → 自动使用已配置 Key 对应的 provider。
3. **用户未指定 provider，且未配置任何上述 API Key** → 检查是否具备其他图像生成能力（如已有的 image-and-gif skill、grsai-gpt-image skill、MCP 图片生成工具等）。如果有，用这些能力生成九宫格图；如果没有，告知用户需要配置至少一个 provider 的 API Key。

### 提示词建议

脚本内置了强约束 prompt 模板（要求方格对齐、风格统一、**单向动作**且**末帧不得回到首帧姿态**、cell 内无文字水印），用户只需描述「主体 + 动作 + 风格」：

- ✅ `一只胖橘猫眨眼，扁平插画风`
- ✅ `加载圆环从 12 点转到 9 点位置，单色蓝 #1E90FF`（避免「转一圈」暗示首尾重合）
- ✅ `一杯啤酒从空到满，3D 渲染，浅灰背景`
- ❌ `画 9 张图然后拼起来` ← 不必，模板已经处理

---

## 第二步：裁切九宫格 → 动图 GIF

### 前置依赖

```bash
pip install Pillow
```

### 调用方式

```bash
python3 {baseDir}/scripts/grid_to_gif.py \
  --grid "./generated_gifs/grid_20260707_120000.png" \
  --duration 120 \
  --frame-size 256x256
```

**参数：**

| 参数 | 默认 | 说明 |
|---|---|---|
| `--grid` | — | 九宫格 PNG 路径（必填） |
| `--output-dir` | `./generated_gifs` | 输出目录 |
| `--gif-path` | — | 显式指定输出 GIF 路径 |
| `--duration` | `120` | 每帧时长（毫秒） |
| `--frame-size` | — | 输出帧最终尺寸，例如 `256x256` |

**输出：**

```json
{ "success": true, "gif_path": "./generated_gifs/animation_20260707_120005.gif" }
```

### 裁切原理

1. 将九宫格图按 1/3 等分裁切成 9 帧。
2. 自动检测主体位置并对齐（消除帧间抖动）。
3. 白底使用颜色掩码，非白底使用边缘检测 + 参考帧填充。
4. 合成循环播放的 GIF（`loop=0` 无限循环）。

---

## 端到端示例

```bash
# Step 1: 生成九宫格图
python3 {baseDir}/scripts/generate_grid.py \
  --prompt "一只柴犬摇尾巴，扁平插画风，白色背景" \
  --provider nanobanana \
  --output-dir ./generated_gifs

# Step 2: 裁切并合成 GIF
python3 {baseDir}/scripts/grid_to_gif.py \
  --grid ./generated_gifs/grid_20260707_120000.png \
  --duration 100 \
  --frame-size 256x256
```

---

## 输出与回复规范

- stderr：接口 URL、provider、模型、保存路径等进度信息
- stdout：单行 JSON
- **对用户的可见回复**：以本地文件路径为主；接口失败时如实说明原因，**禁止编造路径或图片内容**

## 常见错误

| 错误 | 处理 |
|---|---|
| `OPENAI_API_KEY environment variable is required` | `export OPENAI_API_KEY=...` |
| `GEMINI_API_KEY environment variable is required` | `export GEMINI_API_KEY=...` |
| `ARK_API_KEY environment variable is required` | `export ARK_API_KEY=...` |
| `HTTP 401 ... unauthorized` | Key 无效或欠费 |
| `Pillow is required` | `pip install Pillow`（第二步依赖） |
| GIF 9 帧不连贯 | 缩短动作描述、加 `--references` 参考图 |
| 末帧又回到首帧姿态 | prompt 里强调「动作结束停在末态、不要回到起始姿势」 |

## 合规说明

- 不在日志 / stdout / 用户回复中泄露 API Key。
- 接口失败时不得编造图片或路径；脚本以非 0 退出并返回 stderr 错误。
