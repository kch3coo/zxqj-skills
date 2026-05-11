# DB Compare API Reference

本 skill 只依赖这三个接口。

## `POST /api/compare`

用途：根据 compare 配置执行一次对比。

请求体直接使用 `CompareRequest` JSON，字段与项目 compare yaml 一致：

```json
{
  "source": {
    "host": "localhost",
    "port": 3306,
    "username": "root",
    "password": "Huawei@123",
    "database": "source-db"
  },
  "target": {
    "host": "localhost",
    "port": 3307,
    "username": "root",
    "password": "Huawei@123",
    "database": "target-db"
  }
}
```

响应：

- 无差异：`{"success":true}`
- 有差异：`{"success":true,"id":"<compare-id>"}`
- 失败：`{"error":"..."}`

## `GET /api/compare/{id}/sql/download?type=upgrade`

用途：下载指定 compare 结果的全量 upgrade SQL。

成功时返回纯 SQL 文本。

## `GET /api/compare/{id}/tables`

用途：当 recompare 仍有差异时，保存残余表级摘要。

响应形如：

```json
{
  "tables": [
    {
      "tableName": "system_menu",
      "hasStructDiff": false,
      "hasDataDiff": true
    }
  ]
}
```

## Backend Availability

后端默认基地址：`http://127.0.0.1:8080`

脚本优先探活 `GET /api/config/list`。如果接口不可用，会尝试在本地 `db-compare/backend` 执行：

```bash
./gradlew bootRun
```
