---
name: skillhub-upload
description: 当用户要求按照 upload.md 将本地 Skill 上传到小红书 SkillHub 时使用。通过 Red Skill Upload CLI 完成授权、打包、上传和提交确认。
---

# skillhub-upload

## 触发

当用户说“按照 https://redskill.xiaohongshu.net/upload.md 把 <skill-name-or-path> 上传到小红书 SkillHub”或提出等价上传请求时，读取 upload.md 指令，并使用本 skill 驱动 `skillhub-upload` CLI。

## 目标流程

1. 回复用户：收到。我会在电脑上读取 upload.md 说明，检查 Red Skill CLI 和本地授权状态。
2. 确认 CLI 可用：优先使用当前仓库的 `tools/skillhub-upload`，或确认 `skillhub-upload` 已在 PATH 中。不可用时先说明缺少 CLI。
3. 查找用户给出的本地 Skill 目录或 `.zip` 源包。用户只给名称时，先在当前工作区和常见目录查找唯一匹配目录；找不到或多匹配时询问用户绝对路径。zip 只能作为 CLI 输入源包，不能由 agent 解压或代替 CLI 重新打包。
4. 执行 `skillhub-upload whoami` 检查授权状态。
5. 未授权时执行 `skillhub-upload login --agent`，读取 CLI 输出的 `PROMPT`，把授权链接和 `XXXX-XXXX` 用户授权码转成聊天消息发给用户。
6. 授权消息必须照抄下面模板，只替换 `<AUTH_URL>`、`<USER_CODE>`、`<MINUTES>` 三个占位符，不增删措辞。`<AUTH_URL>` 来自 `prompt.authorizeUrl`，`<USER_CODE>` 来自 `prompt.userCode`，`<MINUTES>` 用 `prompt.expiresInSeconds` 换算分钟。

````markdown
请用手机自带浏览器打开下面的授权链接，打开后会自动跳转到小红书 App 完成授权：

```
<AUTH_URL>
```

授权码：<USER_CODE>
有效期：<MINUTES> 分钟

我会继续等待 CLI 自动完成授权。如果你已经在手机上完成授权但我没有自动响应，你再回复「好了」。
````

7. 正常情况下等待 CLI 轮询完成后自动继续。用户回复”好了”只是兜底唤醒：仅当 CLI 轮询已完成但 agent 没有恢复时使用；进程中断或状态丢失时，重新执行 `skillhub-upload login --agent`，CLI 会自动从磁盘恢复未完成的授权状态，无需用户重新打开授权链接。
8. 授权完成后按下面的「publish 子流程」固定四步执行，所有字段值取自用户当前会话答复，不要从 SKILL.md / 目录名 / 文件结构 / 上下文对话推断。
9. publish 子流程结束后，把 `RESULT_JSON` 的成功结果、失败原因或取消状态如实转述给用户。

## publish 子流程

固定 4 步，按顺序执行；步骤 1 用 AskUserQuestion 一次性收齐参数，步骤 2-3 把参数全部以 CLI flag 传入，避开 stdin piping。

### Step 1 — 一次性收齐 publish 参数

(a) 先拉一次实时标签列表，命令：

```bash
node -e "import('./cli/tags.mjs').then(({loadContentTags}) => loadContentTags().then(t => console.log(JSON.stringify(t.map(x => x.name)))))"
```

（如果跑的是 PATH 上的 `skillhub-upload` 而非仓库源码，没有 tags.mjs 入口，就直接 curl `https://edith-skillhub.sl.beta.xiaohongshu.com/api/sns/v1/activity_platform/config/query_config?material_id=750&module_id=811` 取 `data[].tagName`。两条路只能挑一条，**不要硬编码标签清单**。）

(b) 用 AskUserQuestion 一次发两题：

- 「source：原创 / 转载」二选一
- 「tag：&lt;上一步拉到的中文名数组&gt;」多选，用户可选一个或多个

(c) 用户 source 选 `转载` 才追问 `repost_source`（自由文本，最多 15 字符）；选 `原创` 直接跳过。

### Step 2 — dry-run 出待提交载荷给用户审阅

```bash
skillhub-upload publish <absolute-path> --dry-run --agent \
  --source <original|repost> --tag <中文标签名[,中文标签名...]> [--repost-source <来源名>]
```

读 `RESULT_JSON.payload`，把关键字段摘出来给用户看：`name`、Skill ID（payload 字段 `skill_identifier`）、`version`、`description`、`original`、`repost_source`、`content_tag_ids`。标签字段展示**中文名列表**，不要只甩 `tagId`。

**Skill ID 派生失败的兜底**：如果 dry-run 抛 `Skill ID 为空，无法从名称...或目录名...自动生成，请输入 Skill ID` 错误（名称和目录名都派生不出合法 kebab-case），按以下顺序处理：

1. 基于 skill 的 `name` / `description` 语义推一个 kebab-case Skill ID（如「微信读书」→ `weread`，「飞书文档助手」→ `feishu-docs`）
2. 用 `AskUserQuestion` 给用户「采纳推荐 `<推荐值>` / 自定义其他名字」两个选项
3. 必须告知用户：**Skill ID 是平台上的 skill 主键，提交后跨版本不可改名**，请慎重
4. 拿到最终 Skill ID 后追加 `--identifier <值>` 重跑 Step 2

### Step 3 — 用户明确说「提交 / 确认 / submit」后真实提交

```bash
printf 'submit\n' | skillhub-upload publish <absolute-path> --agent \
  --source <original|repost> --tag <中文标签名[,中文标签名...]> [--repost-source <来源名>]
```

不要带 `--yes`，让 CLI 进 confirm 阶段；`submit\n` 从 stdin 推给它即可。用户说「取消 / cancel」就把第二条命令换成 `printf 'cancel\n' | ...`。用户回复「好了」不能当成提交触发词。

### Step 4 — 转述结果

把最终 `RESULT_JSON` 的 `status`（submitted / cancelled / error）+ 关键回执（`skillId` 或错误码 + 文案）发给用户。

## CLI 调用约定

本 skill 只负责把聊天请求翻译成 CLI 调用，不复制打包、上传、提交逻辑。
上传入口接受本地 skill 目录或 `.zip` 源包；zip 必须由 CLI 在本地解包、过滤、校验并重新生成上传包，不能由 agent 直接上传或改包。

```bash
skillhub-upload whoami
skillhub-upload login --agent
skillhub-upload publish /absolute/path/to/skill --agent
skillhub-upload publish /absolute/path/to/skill.zip --agent
```

本地验证可使用 dry-run。标签可直接传一个或多个中文名（CLI 内部完成 name→id 映射，多个用逗号分隔），也允许调试时传数字 id：

```bash
node cli/index.mjs publish test/fixtures/minimal-skill --dry-run --agent --source original --tag 效率工具,内容创作 --yes
# 或调试用：--tag-id 1001,1002
```

## 禁止事项

- 不自行拼授权链接。
- 不要求用户复制 token、cookie 或 authorization code。
- 不展示 access token / refresh token。
- 不代替用户或 CLI 解压、过滤、zip/tar 打包；只把本地 skill 目录或 `.zip` 源包交给 CLI。
- 不使用浏览器自动化或 `/tmp/skillhub-*` 信号文件。
