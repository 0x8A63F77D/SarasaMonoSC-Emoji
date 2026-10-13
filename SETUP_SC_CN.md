# SarasaMonoSC-Emoji：部署指南

## 推荐方式：在原项目 Fork 中安装适配层

1. 打开 <https://github.com/sspig0127/SarasaMonoTC-Emoji>，点击 **Fork**，将 Fork 创建到自己的账号。GitHub 仓库设置中可以将仓库重命名为 `SarasaMonoSC-Emoji`。
2. 把 Fork `git clone` 到本地，例如 `git clone https://github.com/<你的用户名>/SarasaMonoSC-Emoji.git`。
3. 解压提供的 `SarasaMonoSC-Emoji-repository.zip`。执行：

   ```bash
   python SarasaMonoSC-Emoji/sc/install_into_fork.py /path/to/your/fork
   ```

   该脚本**只复制 SC 专用文件**，不会覆盖 Fork 原有的 `README.md`、`LICENSE` 或合并引擎源码。
4. 进入 Fork 工作目录，提交并推送：

   ```bash
   git add -A .github sc/ tests/test_overlay.py LICENSE-AUTOMATION SC_README.md SETUP_SC_CN.md
   git commit -m "feat: SC font variants with automated upstream rebuild"
   git push origin main
   ```

5. 在 GitHub 的 **Settings → Actions → General → Workflow permissions** 中启用 **Read and write permissions**。若组织级策略禁止该权限，需要由仓库管理员处理。
6. 在 **Actions** 页面启用新工作流 **Auto-build Sarasa Mono SC Emoji**（公开 Fork 的定时工作流通常默认关闭）。安装脚本会将继承的 `Release` 和 `Check upstream` 工作流归档至 `.github/upstream-workflows/`，避免 TC 流程继续执行；本仓库保留的 TC 工作流也已限制为仅在 TC 上游运行。
7. 运行 **Actions → Auto-build Sarasa Mono SC Emoji → Run workflow**。验证成功后，在仓库 **Releases** 下载四个 ZIP。若发布上传中断，再次运行会恢复草稿并补传附件；仅公开且四个附件齐全的版本才跳过。

默认每天 UTC 03:23 检查上游。只有源文件或者适配层发生变化才构建并发布。四种变体、16 个字体文件必须全部构建及校验通过，才能发布 Release；失败不会发布半成品。

## 或者新建一个干净仓库

如果不要求 GitHub 的正式 Fork 关系，也可以在 GitHub 新建空的 `SarasaMonoSC-Emoji` 仓库，把 ZIP 内的全部文件提交到 `main`。它会在构建时自动拉取原 TC 项目的源码，功能相同，而且不用额外关闭 TC 工作流。推荐长期维护时采用这种方式。

## 自动追踪对象

- 原合并项目 `sspig0127/SarasaMonoTC-Emoji` 主分支提交；
- Sarasa Gothic 最新 Release 版本，下载对应 `SarasaMonoSC-TTF`；
- Noto Color Emoji / Noto COLRv1 的 2D 字体文件最近一次提交；
- Google Fonts 中单色 Noto Emoji 字体最近一次提交；
- Nerd Fonts 最新 Release；
- SC 专用代码及 Action 配置内容。

每个 ZIP 都包含字体文件、许可证、`provenance.json`（精确记录实际使用的上游版本与提交 SHA）。公开仓库 60 天无活动时 GitHub 可能停用 cron，因此工作流在超过 35 天无提交时会自动进行轻量保活，不会触发重复 Release。

## 注意事项

1. **首次真实构建已通过**：PR #1 的 GitHub Actions 已完成全部 16 个字体构建、200 项上游回归测试和 16 个 SC 字体检查，并生成四个 ZIP。PR 运行仅上传构建产物；合并到 main 后才创建 Release。
2. **上游不兼容时暂停发布**：自动使用最新源码不等于新版本一定能合并成功；原项目合并算法和 COLRv1 字形预算变化时，CI 会失败并保留日志，需调整适配层。
3. **不强推覆盖 Git 仓库**：不会自动 `git merge` 或 `git reset` 原 Fork；新版上游合并引擎按特定 SHA 构建时临时获取，不会修改仓库中的 Fork 原文件。
4. **许可证**：使用 SIL OFL 字体时保留原仓库 `LICENSE`；新加的 CI 脚本许可参见 `LICENSE-AUTOMATION`。生成的 ZIP 内会包含字体许可证。
