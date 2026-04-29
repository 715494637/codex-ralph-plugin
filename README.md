# Codex Auto Continue

一个很小的 Codex 插件：当任务还没做完但 Codex 停下时，可以自动让它继续。

默认不会生效。只有你在任务里写 `/autoc`，它才会对这一次任务生效。

## 适合谁

- 你经常跑长任务，Codex 偶尔停在半路。
- 你不想每次手动发一句 `go on`。
- 你又不希望所有任务都自动继续。

## 安装

### 1. 下载这个仓库

```powershell
git clone <this-repo-url>
cd codex-auto-continue
```

### 2. 打开 Codex 配置

配置文件一般在：

```text
~/.codex/config.toml
```

Windows 示例：

```text
C:\Users\你的用户名\.codex\config.toml
```

### 3. 加入这段配置

把路径改成你自己下载后的仓库路径：

```toml
[features]
plugins = true
plugin_hooks = true

[marketplaces.codex-auto-continue]
source_type = "local"
source = "C:\\path\\to\\codex-auto-continue"
```

### 4. 重启 Codex

重启后输入：

```text
/plugins
```

找到 `Auto Continue`，安装并启用它。

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

## 插件位置

```text
plugins/auto-continue
```

## License

MIT
