# docker-mirrors

Rainbond builder 使用的 docker.io 动态镜像代理候选源。

- `mirrors.json` — 候选 mirror 列表（schema v1），通过 jsDelivr CDN 分发：
  `https://cdn.jsdelivr.net/gh/goodrain/docker-mirrors@main/mirrors.json`
- builder 侧只把它当**候选清单**：每次刷新会对每个地址做 `/v2/` 探活 + 测速，
  只采用真实可用的前 N 个，所以列表里出现暂时失效的地址不影响构建。

## 维护

- 自动：每周 GitHub Action（`.github/workflows/sync.yml`）抓取
  [dongyubin/DockerHub](https://github.com/dongyubin/DockerHub) README、探活后提 PR。
- 人工：直接改 `mirrors.json` 提 PR。

**安全须知**：mirror 处于中间人位置，可以篡改镜像内容。自动同步只提 PR，
必须人工审核域名可信后再 merge，禁止配置自动合并。

## mirrors.json schema (v1)

```json
{
  "version": 1,
  "updated_at": "2026-06-12T00:00:00Z",
  "mirrors": [
    { "url": "https://docker.1ms.run", "note": "毫秒镜像" }
  ]
}
```

- `url` 必填，保留 scheme（`http://` 开头表示纯 HTTP 端点）
- `version` 当前固定为 `1`，builder 端不识别其他版本
