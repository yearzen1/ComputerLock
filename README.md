# Computer Lock

一个根据预设时间段自动锁定计算机的 Python 应用程序。

A Python application that locks your computer during configurable time periods.

## 功能特性 / Features

- **时段锁定** — 两种模式：指定时段内锁定 / 指定时段外锁定，每个模式支持两个时间段（支持跨天）
- **全屏锁定** — 多显示器全屏锁定窗口，显示实时时间、日期、星期
- **密码解锁** — 密码保护，支持自动倒计时解锁
- **Daily Tasks** — 锁屏界面显示每日任务清单，全部完成 + 密码正确才可解锁；每日自动重置
- **进程白名单** — 白名单程序在前台时自动隐藏锁屏，切换回非白名单程序时自动重新锁定；锁屏界面可直接启动白名单程序
- **键盘屏蔽** — 可选拦截 Win/Alt/Tab/Esc/F4/Shift/Ctrl/Delete（需 `keyboard` 库）
- **配置共享** — whitelist 和 daily tasks 两个模式共享统一配置文件
- **现代化界面** — 基于 ttkbootstrap 主题（设置页 light 主题，锁屏 dark 主题）

## 安装 / Installation

```bash
pip install keyboard ttkbootstrap  # keyboard 可选，ttkbootstrap 用于主题
python ComputerLock.py
```

## 使用 / Usage

1. 运行 `python ComputerLock.py` 打开设置界面
2. 选择模式（"锁定时段内" / "锁定时段外"），配置时间段、锁定时长、密码
3. 添加进程白名单（支持 exe 名或完整路径）
4. 配置 Daily Tasks（可选），打勾标记完成
5. 点击"开始监控"，程序最小化至托盘开始监控
6. 锁屏界面可勾选 Daily Tasks，全部完成方可输入密码解锁

## 配置文件 / Configuration

模式独立配置：

| 文件 | 说明 |
|------|------|
| `config_lock_period.json` | 锁定时段内模式的时段和密码 |
| `config_unlock_period.json` | 锁定时段外模式的时段和密码 |
| `config_shared.json` | whitelist 和 daily tasks（两模式共享） |

### 模式配置字段

| 字段 | 说明 |
|------|------|
| `lock_duration` | 锁定持续时间（分钟） |
| `password` | 解锁密码 |
| `period1_start` / `period1_end` | 时段1起止（HH:MM） |
| `period2_start` / `period2_end` | 时段2起止（HH:MM） |

### 共享配置字段

| 字段 | 说明 |
|------|------|
| `whitelist` | 白名单进程名列表（共享） |
| `daily_tasks` | 每日任务列表 `[{text, done}]` |
| `daily_tasks_date` | 上次重置日期（自动每日重置） |

## 构建 / Build

```bash
pip install ttkbootstrap
$env:TCL_LIBRARY = "D:\python\tcl\tcl8.6"
$env:TK_LIBRARY = "D:\python\tcl\tk8.6"
pyinstaller ComputerLock.spec
```

生成 `dist/ComputerLock.exe`（无控制台窗口），输出到 `final/`。

## 注意事项 / Notes

- Windows 专用，依赖 `pywin32`（通过 `ctypes.windll`）
- 需管理员权限运行才能生效键盘屏蔽
- 白名单匹配不区分大小写，自动去除路径前缀和引号
- ttkbootstrap "flatly" 主题用于设置界面，锁屏界面为自定义黑色主题

## 许可证 / License

MIT License
