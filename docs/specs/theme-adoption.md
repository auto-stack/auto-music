# 主题采纳合同（theme-adoption）

> 来源：auto-os/PLAN-058（2026-11-04 work 候选 T-02）。宿主主合同：
> auto-os `docs/specs/shell/host-theme-policy-and-delivery.md`；
> 本批登记页：auto-os `docs/specs/apps/product-theme-batch-058.md`。

## 消费形态

- **固定快照**：`vendor/themes` = UI 管理渠道发布的官方主题包快照
  （`themes` 0.2.0，内容 digest
  `9fa07742dc68aa5377ae06cb2d966386002063f184c515b6c5dddf8a6bef838e`，
  per-file sha256 与源包校验同律：pac.at `2e66212b…`、themes.at
  `329c2d56…`）。快照不可二次编辑、非第二权威源；升级 = UI 发新快照
  替换 + 本仓重验。
- **pac 声明**：`dep themes { path: "vendor/themes" }`；原显式
  `theme: "dark"` 键**退役** = **follow 宿主**（宿主策略完整快照 >
  本 design 默认 > legacy 回退；显式值会以 pac 优先级压过宿主跟随，
  两族×明暗需求下不声明）。品牌 accent（emerald）保留豁免。
- **源内导入**：`use themes.themes: Auto`——缺此行包主题不入收集链，
  design/follow 候选按 C-11 未注册整帧拒绝（031 合同）。
- **design 默认**：`theme: "Auto"` + dark_mode 位派生 mode（默认 true=
  暗色，与原 pac theme:"dark" 的独立默认一致）；`dark_mode` 模型位语义
  沿 Plan 458 机制（AUTO_UI_THEME env 链 CLI > os-config > pac.at 播种，
  env 未解析时按 PLAN-615 T-04 回退 OS 系统主题；family 链激活时由已
  提交策略派生 mode 驱动）。本产品现 UI 无明暗切换按钮（637/638 重设计
  后 ToggleDarkMode 无 UI 触发，运行时位由 env/宿主链驱动），dark_mode/
  accent_color 声明保留（变量名勿改契约）。

## 豁免与不变量

- 品牌 accent（emerald）为 App 命名空间固定值豁免（pac `accent` 键与
  播控台封面渐变/播放徽章的 emerald 语义着色不随主题映射）。
- 内容域豁免：专辑封面渐变、媒体像素、波形/歌词内容色不被主题重染；
  rose（红心）与 emerald（播放徽章）为语义状态与装饰渐变豁免（637
  Phase B 映射表既列）。
- 原完整适用业务门在采纳前后保持：真实 scan（`AUTO_MEDIA_ROOT` →
  `/api/media/scan`）、真实播放/暂停/队列/点赞链路不变；空曲库诚实态
  （`library_error`/`root_missing`）不变。

## 验证与测试设施（os-058 冻结工具链：auto-man 2bbd954 / auto-lang 2f558fc93 / auto-ui 3c46104b / auto-web 3de5524 / auto-down 7c4d5cbb）

- `tests/test_058_theme.py`（本批新增反控，两腿×单 boot 序）：
  - **腿 A 显式覆盖轨**：`AUTO_UI_THEME=dark` → 主区像素逐位
    `#09090b`（Auto dark background 官方包值）、dark_mode 状态 true、
    受管夹具真实 scan（3 首）/播放哨兵保持。
  - **腿 B OS 跟随轨**：`AUTO_UI_THEME` 未设 → OS 系统主题播种
    （本机浅色 → light）；主区像素 `#ffffff`（Auto light 值）。
  - 像素采样点=主区 (700,24)（侧栏为 bg-card/60 合成面，合成值 #0d0d0f
    另证）；证据目录 `plan-artifacts/plan-058/auto-os/music/`。
- `tests/test_020_vm.py` 原样保留（原 walkthrough 门）。已知：其中
  Settings/明暗切换腿按 637/638 重设计前的 UI 文案定位，现 UI 无该
  按钮（walkthrough 容错跳过，不产生假红）；播放/队列文案腿同理按现
  UI 图标面判定。原门文件不动，由本批反控补真 oracle。
- 运行 env：`AUTO_LANG_ROOT`=os-058 组树（links 冲突规避——生成工作区
  auto-lang 路径须与 auto-web 同源）、`AUTO_BIN`=组树 auto.exe；
  受管媒体根 `AUTO_MEDIA_ROOT`=plan-artifacts 夹具（不触用户 E 盘）。
