# Computer Lock

一个根据预设时间段自动锁定计算机的 Python 应用程序。

A Python application that locks your computer during configurable time periods.

## 功能特性 / Features

- **时段锁定** — 两种模式：指定时段内锁定 / 指定时段外锁定，每个模式支持两个时间段（支持跨天）
- **全屏锁定** — 多显示器全屏锁定窗口，显示实时时间、日期、星期
- **密码解锁 + 时段结束自动解锁** — 输入密码解锁；锁定时段结束（如 8:00→22:00 模式到 22:00）自动解除锁屏，无需密码，且继续监控
- **进程白名单** — 白名单程序在前台时自动隐藏锁屏，切换回非白名单程序时自动重新锁定
- **键盘屏蔽** — 可选拦截 Win/Alt/Tab/Esc/F4/Shift/Ctrl/Delete（需 `keyboard` 库）
- **白名单启动按钮** — 锁屏界面可直接启动白名单程序
- **配置自动迁移** — 旧版 `config.json` 自动迁移至新版配置文件

## 安装 / Installation

```bash
pip install keyboard  # 可选，键盘屏蔽需要
python src/ComputerLock.py
```

## 使用 / Usage

1. 运行 `python src/ComputerLock.py` 打开设置界面
2. 选择模式（"锁定时段内" / "锁定时段外"），配置时间段、密码
3. 添加进程白名单（支持 exe 名或完整路径）
4. 点击"开始监控"，程序最小化至托盘开始监控
5. 锁屏界面输入密码解锁，或等到锁定时段结束自动解锁

## 配置文件 / Configuration

两种模式各自独立配置文件：

- `config_lock_period.json` — 锁定时段内模式
- `config_unlock_period.json` — 锁定时段外模式

| 字段 | 说明 |
|------|------|
| `password` | 解锁密码 |
| `period1_start` / `period1_end` | 时段1起止（HH:MM，支持跨天） |
| `period2_start` / `period2_end` | 时段2起止（HH:MM，支持跨天） |

锁屏使用锁屏开始那一刻的时段快照：到达时段结束点即自动解锁（`0:00`→`24:00` 这类永不到期的配置除外）。

## 构建 / Build

```bash
pyinstaller ComputerLock.spec
```

生成 `dist/ComputerLock.exe`（无控制台窗口）。

## 注意事项 / Notes

- Windows 专用，依赖 `pywin32`（通过 `ctypes.windll`）
- 需管理员权限运行才能生效键盘屏蔽
- 白名单匹配不区分大小写，自动去除路径前缀和引号
- `lock_debug.log` 只记录状态变化与关键事件（另有 60 秒心跳），超过 5MB 时轮转为 `lock_debug.log.old`

## 许可证 / License

MIT License
