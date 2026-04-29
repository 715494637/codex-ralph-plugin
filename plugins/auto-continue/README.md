# Auto Continue

这个插件只做一件事：你写 `/autoc` 时，它会在 Codex 停下后检查这次任务是否还需要继续。

## 使用

默认最多继续 `5` 次：

```text
/autoc
帮我修复 bug，并运行相关测试。
```

最多继续 `10` 次：

```text
/autoc 10
帮我重构这个模块，并更新测试。
```

带验收标准：

```text
/autoc 10 acceptance: tests pass and final answer summarizes the change.
帮我重构这个模块，并更新测试。
```

## 说明

- 不写 `/autoc` 就不会触发。
- `/autoc` 只影响当前这一次任务。
- 数字是最多继续次数。
- 默认最多继续 `5` 次。
