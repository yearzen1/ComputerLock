## v2.1.1

### Fixed
- Whitelist entries now preserve the original user input (supports both `chrome.exe` and full paths like `D:\path\to\app.exe`); matching still uses basename comparison

## v2.1.0

### Refactor
- Split monolith into modular files (config.py, lock_screen.py, process_util.py)
- Migrate old config.json to new config files

### Features
- Two lock modes: lock during period / lock outside period
- Two configurable time periods per mode (overnight support)
- Process whitelist: auto-hide lock screen when whitelisted app is foreground
- Launch whitelisted apps directly from lock screen
- Keyboard block for Win/Alt/Tab/Esc/F4/Shift/Ctrl/Delete (optional)
- Multi-monitor fullscreen lock window

### Misc
- Removed outdated screenshots (lock.png, setting.png)
- Updated README to reflect actual functionality
