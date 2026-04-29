# Codex Ralph Plugin

一个最小 Codex 插件：输入 `$autoc` 后，Codex 停下时自动继续。

默认不会生效。只有你在任务里写 `$autoc`，它才会对这一次任务生效。

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
$autoc
帮我修复这个 bug，并运行相关测试。
```

默认最多自动继续 `5` 次。

指定最多继续 `10` 次：

```text
$autoc 10
帮我重构这个模块，并更新测试。
```

写清楚验收文本：

```text
$autoc 10 acceptance: tests pass.
帮我重构这个模块，并更新测试。
```

## 规则

- 只识别 `$autoc`。
- 默认继续 `5` 次。
- `$autoc 10` 就最多继续 `10` 次。
- MVP 不做复杂完成判断，只按次数和你的验收文本提示 Codex 继续。

## License

MIT
