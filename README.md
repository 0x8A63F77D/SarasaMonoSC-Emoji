# SarasaMonoSC-Emoji

[![SC Build](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/actions/workflows/sc-autobuild.yml/badge.svg)](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/actions/workflows/sc-autobuild.yml)
[![Tests](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/actions/workflows/test.yml/badge.svg)](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/actions/workflows/test.yml)

**Sarasa Mono SC（更纱黑体简体中文等宽）+ Noto Emoji**，提供彩色、单色、彩色矢量和 Nerd Fonts 图标四种变体。

本项目基于 [sspig0127/SarasaMonoTC-Emoji](https://github.com/sspig0127/SarasaMonoTC-Emoji)，使用 SC 字体作为基底，通过 GitHub Actions 自动追踪上游、构建和发布。每种变体包含 Regular、Italic、Bold、BoldItalic，共 **16 个 TTF**。

[下载字体](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/releases) · [构建状态](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/actions/workflows/sc-autobuild.yml) · [English](SC_README.md)

## 下载与安装

1. 在本仓库的 [Releases](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/releases) 下载所需变体的 ZIP。
2. 解压后安装其中的 `.ttf` 文件，在编辑器或终端中选择对应字体族。
3. 四种变体使用不同字体族名称，可以同时安装。

如果尚无 Release，可查看 Actions 的构建结果。PR 构建仅提供临时 `sc-release` Artifact（保留 7 天），合并到 `main` 后才创建正式 Release。

| 变体 | 字体族名称 | Emoji 格式 | 用途 |
| --- | --- | --- | --- |
| Color | `SarasaMonoSCEmoji` | CBDT/CBLC 彩色位图 | 需要彩色 Emoji，且应用支持该格式 |
| Lite | `SarasaMonoSCEmojiLite` | 单色 TrueType 轮廓 | 单色显示、录屏或不支持彩色字体的应用 |
| COLRv1 | `SarasaMonoSCEmojiCOLRv1` | COLRv1 彩色矢量 | 应用支持 COLRv1，且需要可缩放的彩色 Emoji |
| Nerd Lite | `SarasaMonoSCEmojiLiteNerd` | 单色 Emoji + Nerd Fonts PUA 图标 | 终端提示符、开发图标和单字体配置 |

例如 Color 包包含 `SarasaMonoSCEmoji-Regular.ttf`、`SarasaMonoSCEmoji-Italic.ttf`、`SarasaMonoSCEmoji-Bold.ttf` 和 `SarasaMonoSCEmoji-BoldItalic.ttf`。其他变体使用各自的字体族名称作为文件名前缀。

## 自动更新

每天 **北京时间 11:23（UTC 03:23）** 检查以下来源，也支持手动运行：

| 来源 | 追踪内容 |
| --- | --- |
| SarasaMonoTC-Emoji | 上游 `main` 的合并引擎提交 |
| Sarasa Gothic | 最新 Release 中的 Sarasa Mono SC TTF |
| Noto Color Emoji / COLRv1 | `2D/fonts/` 中对应字体文件的最新提交 |
| Google Fonts Noto Emoji | 单色 `NotoEmoji[wght].ttf` 的最新提交 |
| Nerd Fonts | 最新 Release 的 Symbols Only 字体 |
| 本仓库 | SC 适配代码、测试及构建工作流的内容变化 |

发现变化后，按解析出的版本和 SHA 获取源码与字体，应用 SC 适配，构建四种变体，运行上游回归及 SC 字体校验，最后打包发布。仅在 **16 个字体全部构建并验证通过** 后发布，失败会保留调试产物。

Release 标签采用 `sc-auto-<来源指纹>`。每个 ZIP 都包含字体、许可证及 `provenance.json`，记录实际使用的来源版本、提交 SHA 和适配层内容哈希。文档或保活提交不会单独触发新版本构建。

上传中断时，下一次运行会恢复草稿并补传附件；只有已公开且四个 ZIP 齐全的 Release 才会跳过。超过 35 天无提交时，定时流程会按需提交一次保活记录。

**自动追踪发生在构建时。** 工作流会临时拉取上游合并引擎，不会自动合并或重置本仓库的 Git 分支。上游出现不兼容变化时，构建停止发布，需调整适配层。GitHub 的定时任务可能延迟执行。

## 构建与维护

本仓库的 SC 构建入口是 [`.github/workflows/sc-autobuild.yml`](.github/workflows/sc-autobuild.yml)。手动构建时，在 Actions 选择 **Auto-build Sarasa Mono SC Emoji → Run workflow**。

- PR：执行真实字体构建和验证，上传 ZIP，不发布 Release。
- `main` 的相关代码变更、定时检查或手动运行：根据来源指纹决定是否重建，并在验证后发布。
- 从上游继承的 TC 发布和检查工作流仅允许在原 TC 仓库执行。

仓库根目录的 `build.py`、`config.yaml` 和 `src/` 保留了继承的 TC 源码。SC 工作流会对临时获取的上游源码运行 [`sc/adapt.py`](sc/adapt.py)；直接在根目录运行 `build.py` 仍是 TC 配置。

不下载字体也可运行适配与发布流程测试：

```bash
python3 tests/test_overlay.py
```

安装到其他 Fork、Actions 权限设置和首次发布步骤见 [部署指南](SETUP_SC_CN.md)。安装脚本会保留目标 Fork 的 README、许可证及合并引擎，将继承的 TC 工作流归档到 `.github/upstream-workflows/`，避免与 SC 流程同时运行。

## 兼容性与取舍

- 字体按两列 Emoji 宽度构建并校验，但终端自身的 Unicode 列宽计算、字体回退和组合处理仍会影响最终显示。
- 彩色字体能否显示，取决于应用对 CBDT/CBLC 或 COLRv1 的支持；可选择 Lite 使用单色轮廓。
- COLRv1 受 TrueType 字形数量上限限制，只收录上游选择策略允许的 Emoji 子集，覆盖量会随源字体和版本变化。
- SC 适配保留了上游的 Emoji 合并逻辑，并修复 Color Emoji 内部字形名与 CJK 字形重名时丢失组合输出的问题。
- 仓库中的原有预览图片和 TC 技术文档来自上游，不能作为当前 SC Release 的覆盖率或渲染验证结果。

## 来源与许可证

感谢原项目作者及字体维护者：

- 合并引擎：[sspig0127/SarasaMonoTC-Emoji](https://github.com/sspig0127/SarasaMonoTC-Emoji)。原 README 与技术说明保留于 [UPSTREAM_README.md](UPSTREAM_README.md)。
- SC 基底：[be5invis/Sarasa-Gothic](https://github.com/be5invis/Sarasa-Gothic)。
- 彩色 Emoji：[googlefonts/noto-emoji](https://github.com/googlefonts/noto-emoji)。
- 单色 Emoji：[Google Fonts Noto Emoji](https://github.com/google/fonts/tree/main/ofl/notoemoji)。
- 开发图标：[ryanoasis/nerd-fonts](https://github.com/ryanoasis/nerd-fonts)。

生成的字体遵循 [SIL OFL 1.1](LICENSE)，发布包保留相应许可与署名；Nerd Lite 额外包含 Nerd Fonts 来源许可证。SC 自动化脚本使用 [MIT](LICENSE-AUTOMATION)，不改变生成字体的许可证。
