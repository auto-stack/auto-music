# auto-music

音乐播放器，使用 AutoLang / AutoUI 开发的独立应用。

本仓是首批产品源码基线；当前能力以导入版本为准，仓库描述中的产品方向不表示全部已实现。

## 运行

安装对应版本的 `auto` CLI 后，从本仓根执行：

```sh
auto run
auto run -r vm
```

前端端口：`17830`。后端端口：`17831`。

共享 StyleKit 已固定在 `vendor/stylekit`，无需相邻 auto-lang 示例目录。

配置 `AUTO_MEDIA_ROOT` 指向自己的媒体目录；原始开发机路径已移除。真实视频播放还需要对应媒体运行库。

## 来源与组合

来源提交、路径与文件 hash 见 `SOURCE-IMPORT.json`。首次导入提交保留在 `source-sync` 分支；完整 v0.5 恢复后从该基线导入差异，再与产品开发线合并。

AutoOS 通过 [`apps/020-music-player`](https://github.com/auto-stack/auto-os/tree/v0.6-dev/apps/020-music-player) submodule 固定本仓版本；教学 Demo 保留在来源仓。

已有测试随源导入；端口与平台相关测试需要按本仓配置准备运行环境。安装/启动与双端完整功能验收是不同检查项。

## 主题采纳（auto-os/PLAN-058）

- `vendor/themes` 为 UI 管理渠道发布的固定版本快照（`themes` 0.2.0，内容
  digest `9fa07742dc68aa5377ae06cb2d966386002063f184c515b6c5dddf8a6bef838e`），
  经 `pac.at` `dep themes` 消费；快照不可二次编辑、非第二权威源。
- 主合同（宿主策略/跟随/拒绝语义）在 **auto-os/PLAN-058**
  （`auto-os` 仓 `docs/plans/058-media-products-theme-adoption.md`
  与其 canonical specs）：本产品原显式 `theme: "dark"` 键已退役 =
  **follow 宿主**（宿主策略完整快照 > 本 `design` 默认 > legacy 回退）；
  `src/front/app.at` `design { theme: "Auto", mode: dark_mode 派生 }`
  为独立/无宿主环境的默认腿（默认暗色语义沿 AUTO_UI_THEME env 链与
  OS 回退，Plan 458/615 机制；`use themes.themes: Auto` 注册收集链——
  C-11 合同）。合同细则见 `docs/specs/theme-adoption.md`。
- 品牌 accent（emerald）为 App 命名空间固定值豁免，不随主题映射；
  `dark_mode`/`accent_color` 契约变量名原样（Plan 458）。
