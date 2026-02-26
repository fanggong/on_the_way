# Docker 一键部署 v0.1.0

## 1. 准备

```bash
cp infra/docker/.env.example infra/docker/.env
```

如果你使用代理/VPN，可在 `infra/docker/.env` 中设置:

```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
ALL_PROXY=socks5://127.0.0.1:7890
```

如遇 Docker Hub 拉取失败，可切换镜像源:

```env
IMAGE_MIRROR_PREFIX=docker.1ms.run/
```

如需调整 OpenMetadata 登录账号（用于 ingestion/验收脚本自动取 JWT）:

```env
OM_ADMIN_EMAIL=admin@open-metadata.org
OM_ADMIN_PASSWORD=admin
```

## 2. 启动

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d
```

## 3. 查看状态

```bash
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env ps
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env logs -f api-service
```

## 4. 一键验收脚本

```bash
bash scripts/dev/verify_v0_1_0.sh
```

脚本检查:
- 容器运行状态
- P1/P2 写入链路
- dbt build
- Domain/Mart 产数
- 连接器健康接口
- OpenMetadata 可达与表搜索可见性

## 5. 导入 OpenMetadata 血缘（dbt + Postgres）

```bash
bash scripts/dev/run_openmetadata_ingestion.sh
```

该脚本会依次执行:
- 登录 OpenMetadata 并获取 JWT
- Postgres 元数据导入
- `dbt docs generate`
- dbt 元数据与血缘导入

## 6. 常见问题

- OpenMetadata 启动慢: 提升 Docker 内存后重启 metadata 相关容器。
- dbt 报连接失败: 确认 `postgres` 健康和 `.env` 中数据库配置。
- API 422: 检查 `value`、`occurred_at` 字段约束。
- `dbt-runner` 会生成 `data/dbt/target`、`data/dbt/logs`、`data/dbt/.user.yml` 运行产物；这些文件已在忽略规则中处理。

## 7. 关联文档

- 全交付物启动与验收（含 iOS 客户端）: `docs/run/交付物启动与验收说明_v0.1.0.md`
