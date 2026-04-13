# Frontend Auth Permission Skeleton Definition

## 1. 背景

当前 Trace Console 前端已具备基础页面、控制台路由、菜单、Trace / Task / Observability 页面，但此前登录页仍是静态表单与假跳转，前端请求也没有真正接入后端认证能力。

后端已经具备最小认证与 RBAC 能力，包括 `/auth/me`、`require_permission`、`sys_auth_role`、`sys_auth_permission`、`sys_auth_role_permission`、`sys_auth_subject_role` 等基础设施。因此，本阶段的目标不是重新设计完整权限平台，而是先让前端真正接入后端 auth profile，并形成后续页面重构可复用的认证与权限骨架。

本阶段同时为后续页面重构提供稳定基础，避免在页面组件、菜单、路由中继续散落临时权限判断。

## 2. 本轮目标

本轮只完成“认证与权限骨架”最小闭环。

本轮目标包括：

- 替换登录页假跳转，接入开发凭证登录。
- 接入后端 `/auth/me`，统一前端认证 profile。
- 让前端请求自动携带开发凭证。
- 增加控制台登录态守卫。
- 增加最小 permission code 判断工具。
- 让 Sidebar 和路由开始消费 permission codes。

本轮不做页面内部细粒度权限控制。Observability、Trace Detail、Task Detail 等页面内部 panel-level 权限先不接入，避免在页面最终形态尚未稳定前固化临时结构。

## 3. 已完成的认证能力

### AuthProvider

已新增最小 `AuthProvider`，负责维护前端认证状态：

- `status`
- `profile`
- `error`
- `refreshProfile()`
- `setCredential()`
- `logout()`

认证状态包括：

- `idle`
- `loading`
- `authenticated`
- `unauthenticated`
- `error`

当前恢复失败时会清理无效凭证，并进入 `unauthenticated`，同时保留错误信息。

### `/auth/me` 接入

已新增 `/auth/me` 调用封装，并将后端原始字段标准化为前端内部稳定结构：

```ts
{
  subject,
  roles,
  permissions,
  authType
}
```

前端其他模块不直接依赖后端原始字段 `auth_subject`、`auth_type`。

### 本地凭证管理

已新增 `authStorage.ts`，统一管理本地开发凭证。

当前存储策略固定为 `localStorage`，key 由 `authStorage.ts` 内部集中定义。除 `authStorage.ts` 外，其他业务代码不直接读写浏览器存储。

### HTTP 请求自动注入 `X-API-Key`

已在现有 `getJson` 基础上做最小改造。

业务请求会默认从 `authStorage.ts` 读取当前开发凭证，并在存在凭证时自动注入：

```http
X-API-Key: <credential>
```

`getJson` 的调用签名保持不变。

### 登录页开发凭证登录

登录页已从假登录跳转改为“开发凭证登录”。

用户输入 API Key 后，页面会调用 `setCredential()`，触发 `/auth/me` 校验。校验成功后跳转原始来源地址；没有来源地址时跳转 `/console/observability`。校验失败时停留在登录页并展示最小错误提示。

### RequireAuth 登录态守卫

已新增 `RequireAuth`，并用于保护当前控制台 App 根节点。

行为如下：

- `idle` / `loading`：展示最小 loading 占位。
- 未认证：跳转 `/login`，并保留 `state.from`。
- 已认证：继续渲染现有控制台结构。

### UserMenu 展示与退出

UserMenu 已接入当前认证信息。

当前展示：

- `profile.subject`
- `profile.roles`

点击退出后：

- 清理本地开发凭证。
- 清理当前 profile 与错误信息。
- 将认证状态置为 `unauthenticated`。
- 跳转 `/login`。

## 4. 已完成的权限能力

### AuthProfile.permissions

前端已统一从 `AuthProfile.permissions` 消费权限码。权限来源为后端 `/auth/me` 返回的 profile。

### PERMISSIONS 常量

已新增 `PERMISSIONS` 常量，集中定义当前最小 permission code：

```ts
trace.read
task.read
alert.read
```

### usePermission

已新增 `usePermission()`，提供最小权限判断能力：

```ts
permissions
hasPermission(code)
hasAnyPermission(codes)
hasAllPermissions(codes)
```

该 hook 不判断角色，不做 ABAC，不处理资源级权限。

### ROUTE_PERMISSION_MAP

已新增最小路由权限映射：

```ts
/console/observability -> task.read
/console/traces -> trace.read
/console/tasks -> task.read
```

当前路由权限采用单核心 permission 判断。

### Sidebar 菜单权限过滤

`NavigationItem` 已支持可选字段：

```ts
permissionCodes?: string[]
```

Sidebar 在渲染菜单前会根据当前用户权限过滤菜单项。

规则：

- 没有 `permissionCodes` 的菜单项默认可见。
- 配置了 `permissionCodes` 的菜单项使用 `hasAnyPermission(permissionCodes)` 判断是否可见。
- section 过滤后为空时不渲染该 section。

### RequireAuth 路由权限控制

`RequireAuth` 已在登录态基础上增加最小路由权限控制。

规则：

- 未登录仍跳转 `/login`。
- 已登录后，根据当前 `location.pathname` 查询 `ROUTE_PERMISSION_MAP`。
- 命中映射后使用 `hasPermission(permission)` 判断是否允许访问。
- 未命中映射的路径默认允许访问。
- 无权限时返回最小文本占位，不跳转，不引入完整 403 页面。

### “同一路由同一核心权限”规则

当前已明确采用“同一路由同一核心权限”规则。

例如：

- `Observability` 菜单指向 `/console/observability`，使用 `task.read`。
- `Task Management` 菜单指向 `/console/observability`，使用 `task.read`。
- `Alert Center` 当前也指向 `/console/observability`，因此本轮同样使用 `task.read`，不使用 `alert.read`。

这样可以避免菜单可见性与路由可访问性不一致。

## 5. 权限模型说明

当前前端权限模型采用 permission code 驱动。

当前已接入的 permission code：

```ts
trace.read
task.read
alert.read
```

`"*"` 被视为超级权限。只要 `profile.permissions` 包含 `"*"`，以下判断均返回 `true`：

```ts
hasPermission(code)
hasAnyPermission(codes)
hasAllPermissions(codes)
```

菜单级权限使用：

```ts
hasAnyPermission(permissionCodes)
```

原因是菜单是入口展示，不应在 MVP 阶段因为缺少某个面板权限而隐藏整个入口。

路由级权限使用：

```ts
hasPermission(permission)
```

原因是当前 `ROUTE_PERMISSION_MAP` 采用单核心 permission 设计，每个路由优先只绑定一个核心权限。

当前不基于角色名做前端判断。角色只作为权限集合来源，前端消费的是 permission codes。

## 6. 当前系统边界

前端权限仅用于体验控制，包括：

- 控制菜单是否展示。
- 控制路由是否允许进入。
- 避免用户误入明显无权限页面。

前端权限不是安全边界。

真实安全边界仍然后端接口中的 `require_permission`。任何涉及数据读取、写入、执行、配置变更的能力，都必须以后端权限校验为准。

前端隐藏菜单或拦截路由不能替代后端鉴权。

## 7. 已明确不做的内容

本轮明确不做以下能力：

- panel-level 权限。
- 按钮级权限。
- 页面内局部权限控制。
- ABAC。
- 资源级权限。
- 租户、组织、空间权限。
- SSO。
- OAuth2 / OIDC / CAS / SAML。
- refresh token。
- token rotation。
- httpOnly cookie session。
- 后端动态菜单。
- 后端菜单下发。
- 完整 403 页面。
- 正式用户名密码登录接口。
- 后端 auth 接口改造。

## 8. 可复用骨架能力

以下能力是后续页面重构必须优先复用的基础设施：

### useAuth

用于读取当前认证状态、profile、错误信息，并执行刷新 profile、设置开发凭证和退出登录。

后续页面不应直接读取 localStorage，也不应绕过 AuthProvider 管理登录态。

### usePermission

用于判断当前用户是否具备指定 permission code。

后续页面如需要权限判断，应优先使用 `usePermission()`，不要直接散落 `profile.permissions.includes(...)`。

### PERMISSIONS

用于集中维护 permission code 字符串。

后续新增页面或菜单权限时，应优先扩展 `PERMISSIONS`，避免在页面组件中硬编码权限字符串。

### ROUTE_PERMISSION_MAP

用于维护最小路由级权限映射。

后续新增控制台路由时，应同步补充对应核心 permission。

### permissionCodes

用于菜单项权限声明。

后续新增菜单项时，应优先通过 `permissionCodes` 声明入口可见性，而不是在 Sidebar 内写特殊判断。

### RequireAuth

用于控制台路由认证和路由级权限判断。

后续页面重构时，应继续让页面挂在现有受保护控制台结构下，而不是在每个页面单独重复登录态判断。

## 9. 已知限制

### API Key + localStorage

当前认证仍是开发凭证模式，凭证存储在 `localStorage`。这是 MVP 过渡方案，不是长期安全方案。

后续正式认证应评估 token、cookie、refresh token 或 SSO 接入方式。

### `/auth/me` header 注入未统一

当前 `/auth/me` 在 `authApi.ts` 内单独注入 `X-API-Key`。

业务请求在 `client.ts` 的 `getJson` 内统一注入 `X-API-Key`。

两者当前不会在同一个请求中重复注入，但后续可以收口为统一 header 构建能力。

### route 前缀匹配简单实现

当前路由权限匹配使用简单前缀命中：

```ts
location.pathname.startsWith(pathPrefix)
```

目前映射较少，尚不存在复杂重叠路径。

如果未来出现更复杂路由，例如 `/console/traces/admin`、`/console/traces/settings`，需要升级为更长前缀优先或 route metadata。

### 无 403 页面

当前无权限时只返回最小文本占位：

```text
当前账号没有访问该页面的权限。
```

后续需要补正式 403 页面或统一 `PageStateView` 风格。

### overview 接口权限耦合问题

当前 `/console/observability` 路由核心权限为 `task.read`。

但 Observability 页面内部仍会请求：

- `/operations/overview`
- `/traces/stats`
- `/alerts/stats`

其中 `/operations/overview` 后端当前需要 `task.read` 和 `alert.read`。这意味着仅有 `task.read` 的用户即使通过了路由级权限，也可能在页面数据请求阶段遇到接口 403。

本轮暂不处理该问题。后续如果要支持 panel-level 权限，需要进一步拆分请求策略，按权限有条件请求对应接口，或推动后端聚合接口降级返回可见数据。

## 10. 后续演进方向

### 1. 页面重构（优先）

下一阶段应优先重构页面结构，稳定 Observability、Trace Detail、Task Detail 的最终页面形态。

页面重构时应复用当前骨架能力：

- `useAuth`
- `usePermission`
- `PERMISSIONS`
- `ROUTE_PERMISSION_MAP`
- `permissionCodes`
- `RequireAuth`

不要在页面中新增临时角色判断或绕过现有认证上下文。

### 2. panel-level 权限（后置）

页面结构稳定后，再做 panel-level 权限。

建议优先从 Observability 页面开始：

- task 相关面板使用 `task.read`
- trace 相关面板使用 `trace.read`
- alert 相关面板使用 `alert.read`

同时需要调整数据请求策略，避免无权限接口导致整个页面失败。

### 3. 403 页面

后续可以新增正式 403 页面或统一无权限状态组件，用于替换当前 `RequireAuth` 的最小文本占位。

该阶段仍不应改变后端安全边界。

### 4. 正式认证体系

在认证骨架稳定后，再推进正式认证体系：

- 正式用户名密码登录。
- token / refresh token。
- httpOnly cookie session。
- OAuth2 / OIDC / CAS / SAML。
- SSO 登录入口、callback、logout 联动。

正式认证接入时，应尽量复用当前 AuthProvider、useAuth、authApi 的边界，不应把登录状态散落到页面组件中。
