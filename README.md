# Codex Ralph Plugin

一个 Codex 插件：当任务还没做完但 Codex 停下时，可以自动让它继续。

默认不会生效。只有你在任务里写 ` /autoc`，它才会对这一次任务生效。

## 一分钟安装

### 1. 添加插件市场

在终端运行：

```powershell
codex plugin marketplace add 715494637/codex-ralph-plugin
```

### 2. 安装插件

启动 Codex：

```powershell
codex --enable plugin_hooks
```

然后输入：

```text
/plugins
```

找到 `Codex Ralph Plugin`，安装并启用。

> 只运行 `marketplace add` 还没有启用插件，必须进 `/plugins` 安装一次。

### 3. 永久启用 hooks

打开 Codex 配置文件：

```text
~/.codex/config.toml
```

确保里面有：

```toml
[features]
plugins = true
plugin_hooks = true
```

如果只是临时试用，可以不改配置，每次启动时用：

```powershell
codex --enable plugin_hooks
```

## 使用

最简单写法：

```text
 /autoc
帮我修复这个 bug，并运行相关测试。
```

注意：`/autoc` 前面有一个空格。这不是笔误。

Codex CLI 会把行首 `/xxx` 当成内置命令，所以直接输入 `/autoc` 会出现 `Unrecognized command`。前面加一个空格后，它会作为普通任务文本发送，插件仍然会识别 `/autoc`。

默认最多自动继续 `5` 次。

指定最多继续 `10` 次：

```text
 /autoc 10
帮我重构这个模块，并更新测试。
```

写清楚验收标准：

```text
 /autoc 10 acceptance: tests pass and final answer summarizes the change.
帮我重构这个模块，并更新测试。
```

## 规则

- 只有写了 ` /autoc` 的那一次任务会触发。
- 没写 `/autoc` 的任务不会触发。
- 数字是最多继续次数，不是必须继续次数。
- 如果任务提前完成，Codex 会正常结束。

## 仓库结构

```text
.codex-plugin/plugin.json
hooks/hooks.json
hooks/auto_continue.py
```

根目录就是插件目录，Codex 安装时不需要再进入子目录。

## License

MIT
