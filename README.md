# Codex Ralph Plugin

一个 Codex 插件：当任务还没做完但 Codex 停下时，可以自动让它继续。

默认不会生效。只有你在任务里写 `/autoc`，它才会对这一次任务生效。

## 一分钟安装

### 1. 添加插件市场

在终端运行：

```powershell
codex plugin marketplace add 715494637/codex-ralph-plugin
```

### 2. 启用 hooks

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

### 3. 安装插件

重启 Codex，然后输入：

```text
/plugins
```

找到 `Codex Ralph Plugin`，安装并启用。

## 使用

最简单写法：

```text
/autoc
帮我修复这个 bug，并运行相关测试。
```

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

- 只有写了 `/autoc` 的那一次任务会触发。
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
