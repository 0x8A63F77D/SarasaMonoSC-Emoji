# SarasaMonoSC-Emoji：部署指南

## 在本仓库首次发布

1. 将通过验证的 SC 改造 PR 合并到 `main`。
2. 确认仓库已启用 Actions，且策略允许工作流请求 `contents: write`。发布和保活任务需要该权限，构建任务只申请读取权限。
3. 合并相关代码会触发 **Auto-build Sarasa Mono SC Emoji**。也可在 Actions 页面选择该工作流，点击 **Run workflow**，选择 `main`。
4. 全部字体构建、测试和校验通过后，在 [Releases](https://github.com/0x8A63F77D/SarasaMonoSC-Emoji/releases) 下载四个 ZIP。

PR 构建不会发布 Release，只上传临时构建产物。发布上传中断时，再次运行会恢复草稿并补传附件；只有已公开且四个附件齐全的版本才跳过。

## 安装到另一个 TC Fork

从本仓库当前源码获取适配层，确保安装脚本和所需文件来自同一版本：

```bash
git clone https://github.com/0x8A63F77D/SarasaMonoSC-Emoji.git sc-overlay
python3 sc-overlay/sc/install_into_fork.py /path/to/your/tc-fork
```

`/path/to/your/tc-fork` 应是已克隆的 SarasaMonoTC-Emoji Fork。安装器保留目标仓库的 `README.md`、`LICENSE` 和合并引擎，将 SC 说明写入 `SC_README.md`。继承的 `Release` 和 `Check upstream` 工作流会归档至 `.github/upstream-workflows/`，移出 Actions 工作流目录；原文件内容不变，测试工作流继续保留。

在目标 Fork 中提交安装结果，包含工作流的移动和删除：

```bash
cd /path/to/your/tc-fork
git add -A .github sc/ tests/test_overlay.py LICENSE-AUTOMATION SC_README.md SETUP_SC_CN.md
git commit -m "feat: SC font variants with automated upstream rebuild"
git push origin main
```

随后启用 Actions，并在 `main` 手动运行 SC 工作流。此安装命令用于已经发布了 SC 改造的源码版本；如果改造仍在 PR 中，可先检出该 PR 的开发分支，再执行安装器。

本仓库保留的 TC 工作流已限制为仅在原 TC 上游仓库运行。安装器处理其他 Fork 时采用归档方式，避免覆盖它们的原始工作流。

## 自动追踪与发布

默认每天 UTC 03:23（北京时间 11:23）检查上游。只有字体来源、合并引擎或适配层变化才重建；四种变体、16 个字体必须全部构建及校验通过才能发布。

追踪对象包括：

- 原合并项目 `sspig0127/SarasaMonoTC-Emoji` 的 `main` 提交。
- Sarasa Gothic 最新 Release 中的 Sarasa Mono SC TTF。
- Noto Color Emoji / COLRv1 的 `2D/fonts/` 字体文件提交。
- Google Fonts 中单色 Noto Emoji 字体的提交。
- Nerd Fonts 最新 Release 的 Symbols Only 字体。
- SC 专用代码、测试及构建工作流。

每个 ZIP 包含字体、许可证和 `provenance.json`，记录实际来源版本、提交 SHA 及适配层内容哈希。文档和保活提交不改变构建指纹。超过 35 天无提交时，定时任务会按需提交保活记录；GitHub 的定时运行可能延迟。

## 验证与维护

首次真实构建已完成：200 项上游回归测试、16 个 SC 字体检查及四个 ZIP 打包均通过。适配层测试还覆盖草稿恢复、缺附件重试、附件大小检查和 TC 工作流归档。

上游不兼容时，构建会失败并保留调试产物，需调整适配层后重试。自动更新是在临时上游源码上构建，不会合并或重置本仓库的 Git 分支。

仓库根目录的合并引擎保留 TC 配置；SC 构建使用工作流中的临时源码和 `sc/adapt.py`。适配与流程测试可直接运行：

```bash
python3 tests/test_overlay.py
```

生成字体的许可证见 `LICENSE`；SC 自动化脚本的许可证见 `LICENSE-AUTOMATION`。使用和再发布时保留字体许可与署名。
