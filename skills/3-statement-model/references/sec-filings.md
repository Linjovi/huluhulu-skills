# 数据需求清单

本文件列出构建三报表模型所需的全部数据项及数据提取映射关系。数据由用户提前准备。

---

## 1. 所需数据项总览

### 核心数据要求

| 数据类型 | 最少要求 | 建议 |
|---------|---------|------|
| 利润表数据 | 至少3个完整财年 | 5年最佳 |
| 资产负债表数据 | 至少3个完整财年末余额 | 5年最佳 |
| 现金流量表数据 | 至少3个完整财年 | 5年最佳 |

### 数据来源优先级

1. 年度报告 / 经审计的财务报表（最可靠）
2. 业绩发布会 / 投资者推介材料（管理层表述）
3. 券商研报（分析师估算）
4. 行业报告（市场规模、趋势参考）
5. 新闻（仅用于最新动态，需交叉验证）

---

## 2. 利润表数据提取映射

| 模型行项目 | 常见来源名称 | 说明 |
|----------|-------------|------|
| 营业收入 | "Net Revenue" / "Total Revenue" / "营业收入" | 直接提取 |
| 营业成本 | "Cost of Revenue" / "Cost of Sales" / "营业成本" | 直接提取；若无则需推算 |
| 毛利润 | "Gross Profit" / "毛利润" | 直接提取或计算(收入-COGS) |
| 销售费用 | "Selling" / "Marketing" / "Sales" / "销售费用" | 直接提取 |
| 研发费用 | "Research and Development" / "研发费用" | 直接提取 |
| 管理费用 | "General and Administrative" / "管理费用" | 直接提取 |
| 折旧摊销 | 利润表(如单独列出) 或 现金流量表经营活动 | 从CF加回项提取 |
| 股份报酬 | 利润表(如单独列出) 或 CF经营活动 或 报表附注 | 多来源交叉验证 |
| 利息支出 | "Interest Expense" / "利息支出" | 直接提取或附注推算 |
| 利息收入 | "Interest Income" / "利息收入" | 直接提取 |
| 其他收入/支出 | "Other income (expense), net" / "其他收支" | 直接提取 |
| 税费 | "Income Tax Expense" / "所得税费用" | 直接提取；与附注税率交叉验证 |
| 净利润 | "Net Income" / "净利润" | 直接提取 |

---

## 3. 资产负债表数据提取映射

| 模型行项目 | 常见来源名称 | 说明 |
|----------|-------------|------|
| 现金及等价物 | "Cash and Cash Equivalents" / "货币资金" | 直接提取 |
| 短期投资 | "Short-term investments" / "交易性金融资产" | 直接提取 |
| 应收账款 | "Accounts Receivable, net" / "应收账款" | 直接提取（扣除坏账准备后净值） |
| 存货 | "Inventories" / "存货" | 直接提取 |
| 其他流动资产 | "Other current assets" / "其他流动资产" | 直接提取 |
| PP&E(净值) | "Property, Plant and Equipment, net" / "固定资产净值" | 直接提取 |
| 无形资产(净值) | "Intangible Assets, net" / "Goodwill" / "无形资产" | 直接提取 |
| 递延税资产 | "Deferred Tax Assets" / "递延所得税资产" | 直接提取 |
| 其他非流动资产 | "Other non-current assets" / "其他非流动资产" | 汇总提取 |
| 应付账款 | "Accounts Payable" / "应付账款" | 直接提取 |
| 短期债务 | "Current portion of long-term debt" / "短期借款" | 直接提取 |
| 其他流动负债 | "Accrued liabilities" / "Other current liabilities" / "其他流动负债" | 汇总提取 |
| 长期债务 | "Long-term debt" (非流动部分) / "长期借款" | 直接提取 |
| 递延税负债 | "Deferred Tax Liabilities" / "递延所得税负债" | 直接提取 |
| 其他非流动负债 | "Other non-current liabilities" / "其他非流动负债" | 汇总提取 |
| 普通股/资本溢价 | "Common stock" + "Additional paid-in capital" / "股本+资本公积" | 合并提取 |
| 留存收益 | "Retained Earnings" / "Accumulated deficit" / "未分配利润" | 直接提取 |
| 其他权益项 | "Other comprehensive income" / "Treasury stock" / "其他权益" | 汇总提取 |

---

## 4. 现金流量表数据提取映射

| 模型行项目 | 常见来源名称 | 说明 |
|----------|-------------|------|
| 净利润 | 经营活动现金流顶部 - "Net income" / "净利润" | 直接提取 |
| 折旧摊销 | 经营活动现金流 - "Depreciation" + "Amortization" / "折旧摊销" | 直接提取或合并项拆分 |
| 股份报酬 | 经营活动现金流 - "Stock-based compensation" / "股份支付" | 直接提取 |
| 营运资金变动 | 经营活动现金流各项变动 | 按项目逐一提取 |
| 资本支出 | 投资活动现金流 - "Purchase of PP&E" / "购建固定资产" | 直接提取（负值） |
| 资产处置 | 投资活动现金流 - "Sale of PP&E" / "处置固定资产" | 直接提取（正值） |
| 债务发行 | 筹资活动现金流 - "Proceeds from issuance of debt" / "借款收到现金" | 直接提取 |
| 债务偿还 | 筹资活动现金流 - "Repayments of debt" / "偿还债务" | 直接提取（负值） |
| 权益发行 | 筹资活动现金流 - "Proceeds from issuance of stock" / "吸收投资收到现金" | 直接提取 |
| 股利支付 | 筹资活动现金流 - "Dividends paid" / "分配股利" | 直接提取（负值） |

---

## 5. 辅助数据需求

### 折旧摊销明细
- 折旧方法（直线法、双倍余额递减法等）
- 各类资产的使用年限
- 摊销类别和年限
- PP&E滚存明细（如有）

### 债务明细
- 各笔债务的利率、到期日、面值
- 可转换债务条款
- 债务契约条件
- 未来到期时间表

### 所得税/NOL信息
- 适用税率
- NOL（净营业亏损）余额和到期时间
- 递延税资产和负债明细
- 有效税率与法定税率的差异原因
- 估值准备

### 权益信息
- 股份报酬计划细节（期权、RSU数量和归属时间表）
- 普通股和优先股信息
- 股利政策声明
- 库藏股活动

### 承诺和或有事项
- 租赁承诺（经营租赁和融资租赁）
- 重大法律诉讼
- 未完工购买承诺

---

## 6. 数据质量检查

### 数据一致性检查
- 同一来源中的利润表和资产负债表期间必须对齐
- LTM（最近十二个月）数据需从季度数据滚存计算
- 逐年比较时注意报告单位是否变化

### LTM滚存计算
```
LTM收入 = 最近完整财年收入 + 当前Q累计 - 对应去年Q累计
```

例如，如最近数据为Q3 FY2025：
```
LTM收入 = FY2024全年收入 + Q1-Q3 FY2025收入 - Q1-Q3 FY2024收入
```

---

## 7. 常见数据差异处理

### 不同公司命名差异

| 标准名称 | 常见替代名称 |
|---------|------------|
| Revenue | Net Sales, Net Revenue, Total Revenue, Turnover, 营业收入 |
| COGS | Cost of Revenue, Cost of Sales, Cost of Products Sold, 营业成本 |
| SG&A | Operating Expenses, Selling, General & Administrative, 销售管理费用 |
| Net Income | Net Earnings, Profit, 净利润 |
| PP&E | Property and Equipment, Fixed Assets, Tangible Assets, 固定资产 |
| Retained Earnings | Accumulated Earnings, Accumulated Deficit (如为负), 未分配利润 |
| APIC | Additional Paid-in Capital, Capital in Excess of Par Value, 资本公积 |
| Short-term Debt | Current Portion of Long-term Debt, Short-term Borrowings, 短期借款 |

### 折旧摊销单独列示 vs 合并列示
- **单独列示**：利润表中直接看到"折旧摊销"行 → 直接提取
- **合并列示**：利润表中COGS或SG&A内含折旧摊销 → 需从现金流量表经营活动加回项提取总额，再从附注拆分折旧和摊销

### 股份报酬(SBC)的位置
- 利润表单独行项（最理想）
- 嵌入在SG&A各费用项中（需从附注或CF提取总额）
- 仅在现金流量表中作为加回项出现

### 重组/一次性项目
- 识别并记录所有一次性项目（重组费用、资产减值、诉讼和解等）
- 标注哪些项目应从"正常化"利润率中排除
- 保留原始报告数字，在单独行项标注调整项

### 前期调整
- 如报表中包含对前期数据的追溯调整，优先使用调整后数字
- 记录调整原因和金额
- 如不同年度报表数据不一致，优先使用最近年度中的调整后数据

### 非标准财年
- 如公司财年不截止于12月31日，注意期间标签标注正确
- 例如：FY2024A可能指截至3月31日的财年
- 统一使用"FY"标注，并在假设部分注明实际截止日期

### 外币折算
- 如公司以非本币报告，记录折算汇率和折算方法
- 确认使用的是平均汇率（利润表）还是期末汇率（资产负债表）
- 统一折算为模型基准货币