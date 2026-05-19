#!/usr/bin/env python3
"""Portfolio data manager - read, update, and query portfolio holdings.

Data is stored in a workspace-isolated shared location:
  ~/.agents/portfolio-reader/data/<workspace_id>/portfolio.json

This ensures all agents in the same workspace share the same portfolio data,
while different workspaces remain completely isolated.

Usage:
  python portfolio.py read                    — Print current holdings as JSON
  python portfolio.py summary                 — Print formatted holdings table
  python portfolio.py buy <code> <name> <shares> <price>  — Buy / add position
  python portfolio.py sell <code> <shares> <price>        — Sell / reduce position
  python portfolio.py cash <amount>           — Set available cash
  python portfolio.py history                 — Print last 10 transactions
  python portfolio.py init-from-issue         — Initialize from existing Issue data
"""

import json
import os
import re
import sys
from datetime import datetime


def _get_workspace_id():
    """Determine the current workspace ID from the environment.

    Priority:
      1. MULTICA_WORKSPACE_ID env var (set by Multica platform)
      2. Infer from the current workdir path pattern:
         multica_workspaces_.../<workspace-uuid>/<task-prefix>/workdir
    """
    ws_id = os.environ.get("MULTICA_WORKSPACE_ID")
    if ws_id:
        return ws_id

    cwd = os.getcwd()
    # Pattern: .../multica_workspaces_<host>/<workspace-uuid>/<task-prefix>/workdir
    # or just running from within a workdir
    match = re.search(r"multica_workspaces[^/]+/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", cwd)
    if match:
        return match.group(1)

    # Fallback: try to find workspace ID from the script's own location
    script_path = os.path.abspath(__file__)
    match = re.search(r"multica_workspaces[^/]+/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", script_path)
    if match:
        return match.group(1)

    # Last resort: use a default workspace ID
    print("WARNING: Cannot determine workspace ID. Using 'default'.")
    print("         Set MULTICA_WORKSPACE_ID env var or run from a Multica workdir.")
    return "default"


WORKSPACE_ID = _get_workspace_id()
DATA_BASE_DIR = os.path.join(os.path.expanduser("~"), ".agents", "portfolio-reader", "data")
PORTFOLIO_DIR = os.path.join(DATA_BASE_DIR, WORKSPACE_ID)
PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, "portfolio.json")

DEFAULT_PORTFOLIO = {
    "last_updated": None,
    "cash": 0,
    "holdings": [],
    "transactions": []
}

MAX_TRANSACTIONS = 10


def ensure_dir():
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)


def load():
    ensure_dir()
    if not os.path.exists(PORTFOLIO_FILE):
        save(DEFAULT_PORTFOLIO)
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "transactions" not in data:
        data["transactions"] = []
    return data


def save(data):
    ensure_dir()
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_transaction(portfolio, tx_type, code, name, shares, price, amount):
    """追加一条交易记录，最多保留 MAX_TRANSACTIONS 条。"""
    tx = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": tx_type,
        "code": code,
        "name": name,
        "shares": shares,
        "price": price,
        "amount": round(amount, 2)
    }
    portfolio["transactions"].append(tx)
    if len(portfolio["transactions"]) > MAX_TRANSACTIONS:
        portfolio["transactions"] = portfolio["transactions"][-MAX_TRANSACTIONS:]


def find_holding(portfolio, code):
    code_clean = code.replace(".SZ", "").replace(".SH", "").replace(".US", "").replace(".OF", "")
    for h in portfolio["holdings"]:
        h_code = h["code"].replace(".SZ", "").replace(".SH", "").replace(".US", "").replace(".OF", "")
        if h_code == code_clean:
            return h
    return None


def cmd_read():
    data = load()
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_summary():
    data = load()
    if not data["holdings"] and data["cash"] == 0:
        print("暂无持仓数据。请先通过自然语言指令添加持仓，或运行 init-from-issue 从已有 Issue 导入。")
        return
    print("## 📋 当前持仓概览")
    print("")
    total_cost = 0
    if data["holdings"]:
        print("| 标的 | 代码 | 份额 | 成本价 | 成本金额 |")
        print("|------|------|------|--------|----------|")
        for h in data["holdings"]:
            cost_total = h["shares"] * h["cost_price"]
            total_cost += cost_total
            print(f"| {h['name']} | {h['code']} | {h['shares']:,} | {h['cost_price']:.4f} | {cost_total:,.2f} |")
        print(f"\n📈 持仓成本合计：{total_cost:,.2f} 元")
    print(f"\n💰 剩余可用资金：{data['cash']:,.2f} 元")
    print(f"📊 总资产估算：{total_cost + data['cash']:,.2f} 元（持仓成本 + 可用资金）")
    print(f"\n🕐 最后更新：{data['last_updated'] or '未知'}")
    print(f"\n🏢 工作组：{WORKSPACE_ID}")
    txs = data.get("transactions", [])
    if txs:
        print("\n## 🔄 最近交易记录")
        print("")
        print("| 时间 | 类型 | 标的 | 代码 | 份额 | 价格 | 金额 |")
        print("|------|------|------|------|------|------|------|")
        for tx in reversed(txs):
            type_label = "🟢 买入" if tx["type"] == "buy" else "🔴 卖出"
            print(f"| {tx['time']} | {type_label} | {tx['name']} | {tx['code']} | {tx['shares']:,} | {tx['price']:.4f} | {tx['amount']:,.2f} |")


def cmd_history():
    data = load()
    txs = data.get("transactions", [])
    if not txs:
        print("暂无交易记录。")
        return
    print("## 🔄 最近交易记录（最多10条）")
    print("")
    print("| 时间 | 类型 | 标的 | 代码 | 份额 | 价格 | 金额 |")
    print("|------|------|------|------|------|------|------|")
    for tx in reversed(txs):
        type_label = "🟢 买入" if tx["type"] == "buy" else "🔴 卖出"
        print(f"| {tx['time']} | {type_label} | {tx['name']} | {tx['code']} | {tx['shares']:,} | {tx['price']:.4f} | {tx['amount']:,.2f} |")


def cmd_buy(code, name, shares, price):
    portfolio = load()
    existing = find_holding(portfolio, code)
    if existing:
        total_cost = existing["shares"] * existing["cost_price"] + shares * price
        existing["shares"] += shares
        existing["cost_price"] = round(total_cost / existing["shares"], 4)
        existing["name"] = name or existing["name"]
    else:
        portfolio["holdings"].append({
            "code": code,
            "name": name,
            "shares": shares,
            "cost_price": price
        })
    amount = shares * price
    portfolio["cash"] = round(portfolio["cash"] - amount, 2)
    add_transaction(portfolio, "buy", code, name, shares, price, amount)
    save(portfolio)
    print(f"✅ 买入 {name}（{code}）{shares}份 @ {price}元，花费 {amount:,.2f} 元")


def cmd_sell(code, shares, price):
    portfolio = load()
    existing = find_holding(portfolio, code)
    if not existing:
        print(f"❌ 未找到 {code} 的持仓记录")
        sys.exit(1)
    if existing["shares"] < shares:
        print(f"❌ 持仓不足：{existing['name']}（{code}）仅有 {existing['shares']}份，尝试卖出 {shares}份")
        sys.exit(1)
    name = existing["name"]
    amount = shares * price
    existing["shares"] -= shares
    portfolio["cash"] = round(portfolio["cash"] + amount, 2)
    if existing["shares"] == 0:
        portfolio["holdings"].remove(existing)
        print(f"✅ 清仓 {name}（{code}），回笼 {amount:,.2f} 元")
    else:
        print(f"✅ 卖出 {name}（{code}）{shares}份 @ {price}元，回笼 {amount:,.2f} 元")
    add_transaction(portfolio, "sell", code, name, shares, price, amount)
    save(portfolio)


def cmd_cash(amount):
    portfolio = load()
    portfolio["cash"] = amount
    save(portfolio)
    print(f"✅ 可用资金已更新为 {amount:,.2f} 元")


def cmd_init_from_issue():
    portfolio = load()
    if portfolio["holdings"]:
        print("⚠️ 已有持仓数据。如需覆盖，请先删除 ~/.agents/portfolio-reader/data/<workspace_id>/portfolio.json")
        sys.exit(1)
    print("请将 Issue 中的持仓数据粘贴到 stdin，按 Ctrl-D 结束：")
    content = sys.stdin.read()
    pattern = r'(.+?)[（(](\d{6})[）)]\s*\|\s*([\d,]+)份\s*\|\s*成本([\d.]+)元'
    for m in re.finditer(pattern, content):
        name = m.group(1).strip()
        code = m.group(2)
        shares = int(m.group(3).replace(",", ""))
        price = float(m.group(4))
        portfolio["holdings"].append({
            "code": code,
            "name": name,
            "shares": shares,
            "cost_price": price
        })
    cash_match = re.search(r'剩余可用资金共([\d,]+)元', content)
    if cash_match:
        portfolio["cash"] = float(cash_match.group(1).replace(",", ""))
    save(portfolio)
    print(f"✅ 已导入 {len(portfolio['holdings'])} 条持仓记录，可用资金 {portfolio['cash']:,.2f} 元")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "read":
        cmd_read()
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "history":
        cmd_history()
    elif cmd == "buy":
        if len(sys.argv) < 6:
            print("用法: portfolio.py buy <code> <name> <shares> <price>")
            sys.exit(1)
        cmd_buy(sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5]))
    elif cmd == "sell":
        if len(sys.argv) < 5:
            print("用法: portfolio.py sell <code> <shares> <price>")
            sys.exit(1)
        cmd_sell(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]))
    elif cmd == "cash":
        if len(sys.argv) < 3:
            print("用法: portfolio.py cash <amount>")
            sys.exit(1)
        cmd_cash(float(sys.argv[2]))
    elif cmd == "init-from-issue":
        cmd_init_from_issue()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)