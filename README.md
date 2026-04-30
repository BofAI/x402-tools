# `x402-cli`

x402 协议的 BankofAI 命令行客户端 —— 付款、收款、或本地一键自测整个流程。**不写代码**就能在链上转账。

## 1. 安装

```bash
pip install --pre bankofai-x402-cli
x402-cli --version
```

## 2. 设置钱包（一次性）

x402-cli 把签名委托给 [`bankofai-agent-wallet`](https://github.com/BofAI/agent-wallet)。最快的设置方式 —— 把你的 32 字节 hex 私钥导入：

```bash
agent-wallet start raw_secret \
  --wallet-id payer \
  --private-key 0x<你的-32字节-hex-私钥>
```

> 一把私钥同时派生 EVM 地址和 TRON 地址，**不需要为每条链单独配钱包**。
>
> 加密本地仓库、助记词、Privy 托管等其它选项：[agent-wallet — Getting Started](https://github.com/BofAI/agent-wallet/blob/main/doc/getting-started.md)。

## 3. 三个命令分别是干啥的

| 命令 | 谁用 | 干啥 |
|---|---|---|
| **`x402-cli pay <url>`** | 付款方 | 访问一个 URL，它返回 `402 Payment Required` 时，cli 帮你签名 + 付款 + 拿到响应 |
| **`x402-cli serve`** | 收款方 | 在本地起一个 `402` 收款端点，访问者付费才能拿到响应 |
| **`x402-cli roundtrip`** | 自测 / 一键转账 | 一条命令同时演两边：起 `serve` → 自己 `pay` → 关掉。**最常用于"装好之后做一笔最小转账验证一下"** |

## 4. 复制粘贴：一笔 GasFree 转账（TRON 主网）

把下面命令里的 `<收款方-TRON-地址>` 换成 `T...` 开头的真实地址，回车：

```bash
x402-cli roundtrip \
  --pay-to <收款方-TRON-地址> \
  --amount 1 \
  --token USDT \
  --network tron:mainnet
```

成功输出（节选）：

```json
{
  "ok": true,
  "result": {
    "scheme": "exact_gasfree",
    "amount": "1000000",
    "paid": true,
    "transaction": "<64-hex-tx-hash>"
  }
}
```

到 `https://tronscan.org/#/transaction/<tx-hash>` 看链上记录。

> **为什么这是 GasFree？** TRON 主网 USDT 默认走 `exact_gasfree` 协议 —— GasFree relayer 帮你付链上 TRX gas，**你的主钱包不需要任何 TRX 余额**。USDT 从你的 GasFree custodial 地址扣（地址由你的私钥确定性派生）。
>
> **第一次使用前**需要先给该 GasFree custodial 地址充值一些 USDT。详细步骤见 [docs/manual-test-guide.md → Walkthrough A](docs/manual-test-guide.md#4-walkthrough-a--tron-nile--exact_gasfree)。

### 其它网络的命令模板

| 网络 | 把 `--network` 换成 | 备注 |
|---|---|---|
| TRON 主网（默认 GasFree） | `tron:mainnet` | 主钱包不需要 TRX |
| BSC 主网（USDT permit） | `eip155:56` | 主钱包**需要 BNB 付 gas** |
| TRON Nile 测试网 | `tron:nile` | [水龙头](https://nileex.io/join/getJoinPage) |
| BSC Testnet | `eip155:97` | [水龙头](https://testnet.bnbchain.org/faucet-smart) |

想强制用某种 settlement 协议（不走默认）：在命令里加 `--scheme exact_gasfree | exact_permit | exact`。

## 5. 金额单位

```
rawAmount = amount × 10^decimals
```

| 你想说的 | 用哪个 flag |
|---|---|
| "1.25 USDT"（人类可读小数） | `--amount 1.25` |
| `1250000`（链上最小单位整数，USDT 是 6 decimals） | `--rawAmount 1250000` |

`pay` 命令的支付上限同理：`--max-amount` / `--max-rawAmount`。

## 6. 常见错误

| 报错 | 原因 + 解决 |
|---|---|
| `Insufficient GasFree balance` | GasFree custodial 地址余额不够，[充值步骤](docs/manual-test-guide.md#42-top-up-gasfreeaddress) |
| `cannot import name 'TokenRegistry' …` | 装的是 ≤0.1.0b10 旧版。升级：`pip install --pre --upgrade bankofai-x402-cli` |
| `resolve_wallet could not find a wallet source` | 还没设钱包，回到第 2 步 |
| 命令卡在 `Master Password:` | `local_secure` 钱包没持久化密码。重做时加 `--save-runtime-secrets` |
| `too many pending transfers` | GasFree relayer 限流，等 30~60s 再跑 |

更多排错：[docs/manual-test-guide.md → Troubleshooting](docs/manual-test-guide.md#7-troubleshooting)。

## 看更多

- [docs/manual-test-guide.md](docs/manual-test-guide.md) — 从安装到链上 tx 的完整 walkthrough，含 TRON GasFree、TRON permit、BSC permit 三种场景
- [FEATURES.md](FEATURES.md) — 完整 flag 矩阵和命令输出示例
- [agent-wallet 文档](https://github.com/BofAI/agent-wallet) — 钱包高级设置（Privy / 助记词 / 加密仓库）
- [bankofai-x402 SDK](https://pypi.org/project/bankofai-x402/) — 协议本身和编程接口（如果你想直接在代码里集成而不是用 cli）
