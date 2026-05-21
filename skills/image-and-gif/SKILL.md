---
name: image-and-gif
description: Use when the user asks to generate, draw, or create an image OR an animated GIF / 动图 / 动画 / 表情包. Calls the OpenAI-compatible /v1/images/generations endpoint (default https://api.openai.com, overridable via OPENAI_BASE_URL). Two modes - (a) single image from prompt with optional reference images, (b) animated GIF built from a generated 3x3 frame grid sliced and assembled with Pillow. Triggers on "帮我画", "生成图片", "做个动图", "生成 gif", "做表情包", "draw an image", "generate image", "make a gif", "animate this".
metadata:
  {
    "openclaw": {
      "requires": {
        "env": ["OPENAI_API_KEY"]
      }
    }
  }
---

# Image & GIF Generator

封装 OpenAI 兼容的 `/v1/images/generations` 接口，提供两种交付：

1. **单图生成** — 根据 prompt 生成图片，可带参考图。
2. **动图生成** — 先生成 3×3 九宫格图，再切成 9 帧合成 GIF。

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Bearer 鉴权 |
| `OPENAI_BASE_URL` | ❌ | 基地址，默认 `https://api.openai.com`。也可填兼容代理，如 `https://grsaiapi.com`、`https://grsai.dakka.com.cn` |

```bash
export OPENAI_API_KEY="sk-..."
```

## 依赖

- Python 3.8+
- **GIF 模式必需** [Pillow](https://pillow.readthedocs.io/)：`pip install Pillow`
- 单图模式无第三方依赖

## 脚本一览

```
scripts/
├── generate_image.py   # 单图入口
├── generate_grid.py    # 九宫格入口
├── grid_to_gif.py      # 切图+合成 GIF
└── animate.py          # 端到端：grid → GIF
```

---

## 1. 单图生成

```bash
python3 {baseDir}/scripts/generate_image.py \
  --prompt "一只柴犬坐在窗台上看日落，扁平插画风，暖色调" \
  --ratio 1:1
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--prompt` | — | 图片描述（必填） |
| `--ratio` | `1:1` | 比例，支持：`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `5:4`, `4:5`, `21:9`, `9:21`, `1:2`, `2:1` |
| `--references` | — | 参考图，可填本地路径 / URL / `data:` URL；多个用空格分隔 |
| `--output-dir` | `./generated_images` | 本地保存目录 |
| `--output-path` | — | 显式指定输出 PNG 路径，覆盖 `--output-dir` |
| `--no-download` | `false` | 不保存到本地，stdout 返回 `remote_url` |

### 输出

默认：

```json
{ "success": true, "local_path": "./generated_images/image_20260521_201520.png" }
```

`--no-download`：

```json
{ "success": true, "remote_url": "https://cdn.example.com/img_abc123.png" }
```

---

## 2. 动图生成

### 一行端到端

```bash
python3 {baseDir}/scripts/animate.py \
  --prompt "一只柯基坐着朝镜头挥右前爪打招呼，扁平卡通风格，白底" \
  --ratio 1:1 \
  --frame-size 256x256
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--prompt` | — | 动作描述（必填） |
| `--ratio` | `1:1` | 同单图 |
| `--references` | — | 参考图 |
| `--output-dir` | `./generated_gifs` | 输出目录 |
| `--duration` | `120` | 每帧时长（毫秒） |
| `--frame-size` | — | 输出帧最终尺寸，例如 `256x256` |

### 输出

```json
{
  "success": true,
  "grid_path": "./generated_gifs/grid_20260521_201600.png",
  "gif_path": "./generated_gifs/animation_20260521_201600.gif"
}
```

### 提示词建议

`generate_grid.py` 内置了强约束 prompt 模板（要求方格对齐、风格统一、**单向动作**且**末帧不得回到首帧姿态**、cell 内无文字水印），用户只需描述「主体 + 动作 + 风格」：

- ✅ `一只胖橘猫眨眼，扁平插画风`
- ✅ `加载圆环从 12 点转到 9 点位置，单色蓝 #1E90FF`（避免「转一圈」暗示首尾重合）
- ✅ `一杯啤酒从空到满，3D 渲染，浅灰背景`
- ❌ `画 9 张图然后拼起来` ← 不必，模板已经处理

---

## 输出与回复规范

- stderr：接口 URL、size、保存路径等进度信息
- stdout：单行 JSON
- **对用户的可见回复**：以本地文件路径为主；接口失败时如实说明原因，**禁止编造路径或图片内容**

## 常见错误

| 错误 | 处理 |
|---|---|
| `OPENAI_API_KEY environment variable is required` | `export OPENAI_API_KEY=...` |
| `HTTP 401 ... unauthorized` | Key 无效或欠费 |
| `HTTP 400 ... size` | 比例不在支持列表中 |
| `Pillow is required` | `pip install Pillow`（只在 GIF 模式触发） |
| GIF 9 帧不连贯 | 缩短动作描述、加 `--references` 参考图 |
| 末帧又回到首帧姿态 | prompt 里强调「动作结束停在末态、不要回到起始姿势」 |

## 合规说明

- 不在日志 / stdout / 用户回复中泄露 API Key。
- 接口失败时不得编造图片或路径；脚本以非 0 退出并返回 stderr 错误。
