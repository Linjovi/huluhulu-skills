---
name: draw-image
description: Use when the user asks to generate, draw, or create an image using AI. Triggers on requests like "帮我画", "生成图片", "draw an image", "generate image", "create a picture". Delegates all API logic to a Python script.
metadata:
  {
    "openclaw": {
      "requires": {
        "env": ["GRSAI_API_KEY"]
      }
    }
  }
---

# AI 画图

通过**自然语言提示词**调用 grsai.dakka.com.cn 接口生成图片，下载到本地后返回文件路径。

适用场景：
- 根据文字描述生成图片
- 指定风格、比例、质量的图片生成
- 提供参考图进行图生图

## 密钥来源与安全说明

- 本技能仅使用一个环境变量：`GRSAI_API_KEY`。
- 禁止在代码、提示词、日志或输出文件中硬编码/明文暴露密钥。

## 前提条件

配置环境变量：

```bash
# macOS 添加到 ~/.zshrc，Linux 添加到 ~/.bashrc
export GRSAI_API_KEY="your_api_key_here"
source ~/.zshrc   # 或 source ~/.bashrc
```

## 快速开始

```bash
python3 {baseDir}/scripts/draw_image.py --prompt "一只可爱的猫咪在草地上玩耍"
```

**参数说明：**

| 参数 | 说明 | 必填 |
|---|---|---|
| `--prompt` | 图片描述提示词 | ✅ |
| `--model` | 模型名称，默认 `gpt-image-2` | 否 |
| `--aspect-ratio` | 输出比例，见下方支持列表 | 否 |
| `--quality` | 质量：`auto` / `low` / `medium` / `high` | 否 |
| `--images` | 参考图片（空格分隔，支持 URL 或 base64） | 否 |
| `--output-dir` | 本地保存目录，默认 `./generated_images` | 否 |

**支持的 aspect-ratio 值：**
`auto` `1:1` `3:2` `2:3` `16:9` `9:16` `5:4` `4:5` `4:3` `3:4` `21:9` `9:21` `1:3` `3:1` `2:1` `1:2`
也支持像素值：`1024x1024`、`1920x1080` 等。

## 输出规范

成功时脚本向 stdout 输出 JSON：

```json
{
  "success": true,
  "local_path": "./generated_images/image_20260507_143022.png",
  "remote_url": "https://example.com/result.png"
}
```

进度信息输出到 stderr（在 Bash 工具输出中可见）。

**对用户的可见回复**：以本地文件路径为主，告知图片已保存位置；接口失败时说明原因，禁止编造图片内容。

## 示例

User: "帮我画一只赛博朋克风格的猫"

```bash
python3 {baseDir}/scripts/draw_image.py \
  --prompt "一只赛博朋克风格的猫，霓虹灯背景，未来感十足" \
  --aspect-ratio "1:1" \
  --quality "high"
```

## 常见错误

| 错误 | 处理方式 |
|---|---|
| `GRSAI_API_KEY is required` | 需先配置环境变量 |
| `HTTP Error 401` | API Key 无效，请检查 |
| `output_moderation` | 输出内容违规，积分已返还 |
| `input_moderation` | 输入内容违规，积分已返还，请修改提示词后重试 |
| `error` | 其他错误，积分已返还，建议重新提交任务 |
| `Timeout` | 任务超时，建议重试 |

## 合规说明

- 环境变量按敏感信息处理，不在日志或回复中泄露。
- 接口失败时不得编造图片路径或内容，应返回明确错误说明。
