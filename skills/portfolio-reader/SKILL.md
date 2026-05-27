# Portfolio Reader — 持仓自动读取与更新

## 核心能力

1. **自动读取持仓** — 从共享 JSON 文件读取最新持仓，无需手动翻 Issue
2. **自然语言交易更新** — 用户只需说"我买了1000份半导体ETF，1.65元"，skill 自动更新持仓和现金
3. **数据共享与隔离** — 同一工作组内所有 agent 共享同一份持仓数据；不同工作组数据完全隔离
4. **交易记录追踪** — 自动记录最近10次买卖操作，随时可查

## 数据存储架构

持仓数据存储在 **工作组级别的共享路径**，而非每个 agent 的 workdir 内：

```
~/.agents/portfolio-reader/data/<workspace_id>/portfolio.json
```

- **同一工作组**：所有 agent 读写同一份 `portfolio.json`，数据实时共享，不会出现不一致
- **不同工作组**：每个 workspace_id 对应独立的数据目录，互不影响
- **workspace_id 自动推断**：脚本从环境变量 `MULTICA_WORKSPACE_ID` 或 workdir 路径自动识别当前工作组，无需手动配置

## 使用方式

### 1. 读取持仓（供分析报告使用）

调用脚本输出持仓摘要（含最近交易记录）：

```bash
python3 {baseDir}/scripts/portfolio.py summary
```

输出格式化的持仓表格和最近交易记录，可直接插入分析报告。

如需获取原始 JSON 数据（供程序处理）：

```bash
python3 {baseDir}/scripts/portfolio.py read
```

### 2. 买入/加仓

当用户说类似以下内容时：
- "我买了1000份半导体ETF，1.65元"
- "加仓510300，2000份，4.8元"

执行：

```bash
python3 {baseDir}/scripts/portfolio.py buy <代码> <名称> <份额> <价格>
```

- 如果已有该标的，自动**加权平均成本价**，份额累加
- 自动从可用资金中扣除买入金额
- 自动追加一条交易记录

### 3. 卖出/减仓

当用户说类似以下内容时：
- "卖了1000份纳指ETF，1.38元"
- "减仓510300，500份，4.75元"

执行：

```bash
python3 {baseDir}/scripts/portfolio.py sell <代码> <份额> <价格>
```

- 卖出金额自动加回可用资金
- 清仓时（份额卖完）自动移除该条目
- 自动追加一条交易记录

### 4. 查看最近交易记录

```bash
python3 {baseDir}/scripts/portfolio.py history
```

输出最近10条买卖记录（含时间、类型、标的、份额、价格、金额），按时间倒序显示。

### 5. 更新可用资金

```bash
python3 {baseDir}/scripts/portfolio.py cash <金额>
```