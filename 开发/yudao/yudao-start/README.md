# Yudao Start Skill

`yudao-start` 用于本地启动 / 重启 Yudao、若依、ruoyi-vue-pro 风格的全栈项目。

它当前封装的是 skill 自带脚本：

```bash
scripts/dev-start.sh
```

脚本默认项目根目录是 `$HOME/code`，可通过 `CODE_ROOT=/path/to/code` 覆盖。

核心能力：

- Effy / CheckNM / Ruoqi / Shanghai Yian 项目别名
- `启动项目`：只启动前端和后端
- `完整启动项目`：先重置 MySQL volume 重新跑初始化 SQL，再启动前端和后端
- 前端端口从 `3000` 自动递增
- 后端端口从 `48080` 自动递增
- 前端 `VITE_BASE_URL` 自动指向本次后端端口
- 数据库依赖启动
- MySQL volume 显式重置后重新跑初始化 SQL

本 skill 只处理本地开发环境启动和重置，不处理业务代码分析。业务代码分析继续使用 `yudao`。
