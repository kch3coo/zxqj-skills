# 前端固定实现模板

## 定位

本文件只提供 Yudao 后台前端页面的固定实现模板和代码模式。硬规则正文以 `references/rule-registry.md` 为唯一来源。

本文件可以写示例代码、组件契约和落地点，但不得把示例写成新的规则口径。判断“必须、不得、验收不通过、无法证明”时，读取 `references/rule-registry.md` 中对应规则 ID。

使用本文件时先读取：

- `FE-PAGE-001` 前端页面固定结构
- `FE-TABLE-001` 表格可拖动框线
- `FE-ACTION-001` 操作列完整可点击
- `FE-COLUMN-001` 列显示操作
- `FE-FK-001` 外表 ID 可搜索分页下拉
- `SORT-001` 金额和时间列排序
- `FE-TZ-001` 前端北京时间固定
- `FE-DATE-001` 时间选择器移动端兼容
- `FE-MOBILE-001` 手机端可用性
- `FE-FORM-001` 弹窗和表单

## 适用范围

新增或修改以下前端内容时使用：

- 后台管理端 Vue 页面。
- 标准列表页。
- 弹窗选择表。
- 明细表、子表、展开行表格。
- 新增、编辑、详情弹窗。
- 查询区、工具栏、行操作按钮。
- 外表 ID 查询、筛选、回显和分页下拉。
- 业务时间筛选、展示、回显、提交。
- 金额列、单价列、总额列、税额列、货值列、日期列和时间列排序。

## 页面固定结构

标准列表页默认包含查询区、列表区、分页区，并落实规则 ID：

```vue
<template>
  <ContentWrap>
    <el-form
      class="-mb-15px mobile-safe-query-form"
      :model="queryParams"
      ref="queryFormRef"
      :inline="true"
      label-width="100px"
    >
      <!-- 查询条件：执行 CONTRACT-001、FE-FK-001、FE-TZ-001、FE-DATE-001、FE-MOBILE-001 -->
      <el-form-item label="关联对象" prop="relationId">
        <el-select
          v-model="queryParams.relationId"
          placeholder="请选择关联对象"
          clearable
          filterable
          remote
          :remote-method="remoteSearchRelation"
          :loading="relationLoading"
          class="!w-240px"
        >
          <el-option
            v-for="item in relationOptions"
            :key="item.id"
            :label="formatRelationLabel(item)"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item>
        <div class="mobile-safe-actions">
          <el-button @click="handleQuery"><Icon icon="ep:search" class="mr-5px" /> 搜索</el-button>
          <el-button @click="resetQuery"><Icon icon="ep:refresh" class="mr-5px" /> 重置</el-button>
        </div>
        <el-popover placement="bottom-start" trigger="click" width="280">
          <template #reference>
            <el-button class="ml-8px"><Icon icon="ep:setting" class="mr-5px" /> 列显示</el-button>
          </template>
          <div class="column-visibility-content">
            <el-checkbox-group v-model="visibleColumnKeys" @change="persistColumnVisibility">
              <el-checkbox
                v-for="column in toggleableColumns"
                :key="column.key"
                :label="column.key"
                :disabled="column.locked === true"
                class="!block !mb-6px"
              >
                {{ column.label }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </el-popover>
      </el-form-item>
    </el-form>
  </ContentWrap>

  <ContentWrap>
    <el-table
      row-key="id"
      v-loading="loading"
      :data="list"
      :stripe="true"
      border
      @sort-change="handleSortChange"
    >
      <!-- 普通业务列：执行 FE-TABLE-001、FE-COLUMN-001 -->
      <el-table-column
        v-if="colVisible('id')"
        label="ID"
        align="center"
        prop="id"
        min-width="90"
      />

      <el-table-column
        v-if="colVisible('fieldName')"
        label="业务字段"
        align="center"
        prop="fieldName"
        min-width="140"
        show-overflow-tooltip
      />

      <!-- 金额和时间列：执行 SORT-001，prop 使用后端 DO 的 camelCase 字段名 -->
      <el-table-column
        v-if="colVisible('amountField')"
        label="金额字段"
        align="center"
        prop="amountField"
        min-width="140"
        sortable="custom"
      />

      <!-- 操作列：执行 FE-ACTION-001 -->
      <el-table-column
        label="操作"
        align="center"
        min-width="240"
        :resizable="false"
        class-name="table-action-column"
      >
        <template #default="scope">
          <div class="table-actions">
            <!-- 执行 FE-ACTION-001：操作列禁止固定右侧；按钮直接可见可点；按钮多时加宽、换行、分组直接展示或移动端动作区 -->
          </div>
        </template>
      </el-table-column>
    </el-table>

    <Pagination
      :total="total"
      v-model:page="queryParams.pageNo"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />
  </ContentWrap>
</template>

<script setup lang="ts">
import { buildSortingField } from '@/utils'

type SortingField = { field: string; order: 'asc' | 'desc' }
type ToggleColumn = { key: string; label: string; locked?: boolean; defaultVisible?: boolean }
type ColumnVisibilityCache = { visibleKeys: string[]; allKeys: string[] }

const BEIJING_TIME_ZONE = 'Asia/Shanghai'
const COLUMN_VIS_KEY = '模块名_页面名_主表_columns_visible'

const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  relationId: undefined as number | undefined,
  sortingFields: [] as SortingField[]
})

const toggleableColumns: ToggleColumn[] = [
  { key: 'id', label: 'ID', defaultVisible: false },
  { key: 'fieldName', label: '业务字段' },
  { key: 'amountField', label: '金额字段' },
  { key: 'status', label: '状态' },
  { key: 'remark', label: '备注' },
  { key: 'operation', label: '操作', locked: true }
]

const defaultVisibleColumnKeys = toggleableColumns
  .filter((column) => column.defaultVisible !== false)
  .map((column) => column.key)
const visibleColumnKeys = ref<string[]>(loadVisibleColumnKeys())

function loadVisibleColumnKeys() {
  const saved = localStorage.getItem(COLUMN_VIS_KEY)
  if (!saved) return defaultVisibleColumnKeys
  try {
    const cache = JSON.parse(saved) as ColumnVisibilityCache
    const savedVisibleKeys = cache.visibleKeys
    const savedAllKeys = cache.allKeys
    if (!Array.isArray(savedVisibleKeys) || !Array.isArray(savedAllKeys)) return defaultVisibleColumnKeys
    const currentKeys = new Set(toggleableColumns.map((column) => column.key))
    const lockedKeys = toggleableColumns.filter((column) => column.locked).map((column) => column.key)
    const oldKeys = new Set(savedAllKeys)
    const visibleKeys = new Set(savedVisibleKeys.filter((key) => currentKeys.has(key)))
    toggleableColumns.forEach((column) => {
      if (!oldKeys.has(column.key) && column.defaultVisible !== false) visibleKeys.add(column.key)
    })
    lockedKeys.forEach((key) => visibleKeys.add(key))
    return Array.from(visibleKeys)
  } catch {
    return defaultVisibleColumnKeys
  }
}

function colVisible(key: string) {
  const column = toggleableColumns.find((item) => item.key === key)
  if (column?.locked) return true
  return visibleColumnKeys.value.includes(key)
}

type RelationOption = { id: number; name?: string; code?: string; no?: string }
const relationOptions = ref<RelationOption[]>([])
const relationLoading = ref(false)

function formatRelationLabel(item: RelationOption) {
  return [item.no || item.code, item.name].filter(Boolean).join(' - ') || '-'
}

async function remoteSearchRelation(keyword?: string) {
  relationLoading.value = true
  try {
    // 替换为当前业务 API；执行 FE-FK-001：默认候选分页下限为 20，label 不能显示裸 ID。
    const data = await RelationApi.getRelationPage({
      pageNo: 1,
      pageSize: 20,
      keyword: keyword || undefined
    })
    relationOptions.value = data.list || []
  } finally {
    relationLoading.value = false
  }
}

function persistColumnVisibility() {
  localStorage.setItem(
    COLUMN_VIS_KEY,
    JSON.stringify({ visibleKeys: visibleColumnKeys.value, allKeys: toggleableColumns.map((column) => column.key) })
  )
}

function handleSortChange(params: { prop?: string; order?: 'ascending' | 'descending' | null }) {
  queryParams.pageNo = 1
  if (!params.prop || !params.order) {
    queryParams.sortingFields = []
    getList()
    return
  }
  queryParams.sortingFields = [buildSortingField(params) as SortingField]
  getList()
}

function resetSort(tableRef?: { clearSort?: () => void }) {
  queryParams.sortingFields = []
  tableRef?.clearSort?.()
}
</script>

<style scoped>
.table-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px 8px;
  overflow: visible;
}

:deep(.table-action-column .cell) {
  overflow: visible;
  white-space: normal;
}

@media (max-width: 768px) {
  :deep(.mobile-safe-query-form) {
    display: block;
  }

  :deep(.mobile-safe-query-form .el-form-item) {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }

  :deep(.mobile-safe-query-form .el-form-item__label) {
    display: block;
    width: 100% !important;
    text-align: left;
    line-height: 24px;
  }

  :deep(.mobile-safe-query-form .el-form-item__content),
  :deep(.mobile-safe-query-form .el-input),
  :deep(.mobile-safe-query-form .el-select),
  :deep(.mobile-safe-query-form .el-date-editor) {
    width: 100% !important;
    max-width: 100%;
  }

  .mobile-safe-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    width: 100%;
  }

  .mobile-safe-actions .el-button {
    flex: 1 1 calc(50% - 8px);
    min-width: 112px;
    margin-left: 0;
  }

  :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
    max-width: calc(100vw - 24px);
    margin: 12px auto !important;
  }

  :deep(.el-dialog__body) {
    max-height: calc(100dvh - 168px);
    overflow: auto;
  }

  :deep(.el-dialog__footer) {
    position: sticky;
    bottom: 0;
    z-index: 1;
    background: var(--el-bg-color);
  }
}
</style>
```

## 列显示状态模式

本节只说明 `FE-COLUMN-001` 的代码落点。列显示只用于页面主表或主列表，使用页面唯一、主表唯一的 key。展开表、明细表、子表、弹窗表、表单内编辑表和嵌套表默认不加列显示。

```ts
const COLUMN_VIS_KEY = '模块名_页面名_主表_columns_visible'
```

新增、删除、改名普通业务列时，必须同步更新：

- `toggleableColumns`
- 表格列的 `v-if`
- 默认可见列
- 验收记录中的 `FE-COLUMN-001`

列显示实现要点：

- `id` 列在配置中存在，但 `defaultVisible: false`。
- 除操作列外，主表业务数据列都可隐藏。
- 操作列固定可见、不可隐藏，但不得使用 `fixed="right"`。
- 选择列、展开列、序号列等功能列不作为普通业务列管理。

## 外表 ID 分页下拉模式

本节只说明 `FE-FK-001` 的代码模式。外表 ID 查询、筛选或表单选择提交值使用 ID，用户界面显示名称、编号、单号、编码或组合字段。

```vue
<el-select
  v-model="queryParams.supplierId"
  placeholder="请选择供应商"
  clearable
  filterable
  remote
  :remote-method="remoteSearchSupplier"
  :loading="supplierLoading"
  class="!w-240px"
>
  <el-option
    v-for="item in supplierOptions"
    :key="item.id"
    :label="item.code ? `${item.code} - ${item.name}` : item.name"
    :value="item.id"
  />
</el-select>
```

```ts
const supplierOptions = ref<Array<{ id: number; name: string; code?: string }>>([])
const supplierLoading = ref(false)

const remoteSearchSupplier = async (keyword?: string) => {
  supplierLoading.value = true
  try {
    const data = await SupplierApi.getSupplierPage({
      pageNo: 1,
      pageSize: 20,
      name: keyword || undefined
    })
    supplierOptions.value = data.list || []
  } finally {
    supplierLoading.value = false
  }
}
```

回显实现要点：

- 默认列表没有当前 ID 时，调用详情接口或可返回业务字段的分页接口补齐选项。
- 回显文本仍显示名称、编号、单号或编码，不显示裸 ID。
- 如果接口只返回 ID，先补接口或换接口，不交付显示 ID 的下拉。
- 默认候选分页小于 20 时提升到 20；已有业务理由使用大于 20 或全量加载时保留原意图，不强行改小。

## 金额和时间排序模式

本节只说明 `SORT-001` 的接入模式。前端负责把列 `prop` 通过公共 `buildSortingField` 发到 `queryParams.sortingFields`；`prop` 使用后端 DO 的 camelCase 字段名。

前端接入要点：

```vue
<el-table ref="tableRef" :data="list" border @sort-change="handleSortChange">
  <el-table-column prop="orderDate" label="订货日期" sortable="custom" />
  <el-table-column prop="totalPreTaxAmount" label="不含税金额" sortable="custom" />
</el-table>
```

```ts
import { buildSortingField } from '@/utils'

const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  sortingFields: [] as Array<{ field: string; order: 'asc' | 'desc' }>
})

const handleSortChange = (params: { prop?: string; order?: 'ascending' | 'descending' | null }) => {
  queryParams.pageNo = 1
  if (!params.prop || !params.order) {
    queryParams.sortingFields = []
    getList()
    return
  }
  queryParams.sortingFields = [
    buildSortingField(params) as { field: string; order: 'asc' | 'desc' }
  ]
  getList()
}

const resetQuery = () => {
  queryParams.sortingFields = []
  tableRef.value?.clearSort?.()
  handleQuery()
}
```

后端接入要点：

- 非 join：PageReqVO 继承 `SortablePageParam`，Mapper 保持 `selectPage(reqVO, wrapper)`，复用系统底层排序。
- join：PageReqVO 继承 `SortablePageParam`，Mapper 按销售模块等价写法使用 `MyBatisUtils.buildPage(reqVO, reqVO.getSortingFields())` 后再 `selectJoinPage(page, DO.class, wrapper)`。

## 北京时间桥接模式

本节只说明 `FE-TZ-001` 的代码接入方式。具体转换工具优先复用项目已有时间工具；没有现成工具时，在当前切片内补最小公共工具或页面内桥接函数。

日期控件必须成对处理：

```ts
// 接口值 -> 控件值
const formTime = toBeijingPickerValue(apiTime)

// 控件值 -> 接口值
const submitTime = fromBeijingPickerValue(formTime)
```

不要只依靠 `format` 或 `value-format` 判断时区已经正确。验收执行 `FE-TZ-001` 和 `FE-DATE-001`。

## 响应式日期范围组件模式

本节只说明 `FE-DATE-001` 的代码模式。日期范围筛选、导出区间、报表区间优先使用项目统一响应式日期范围组件；没有现成组件时，在当前切片先封装一个通用组件，再接入页面。

页面使用模式：

```vue
<ResponsiveDateRangePicker
  v-model="queryParams.createTime"
  value-format="YYYY-MM-DD HH:mm:ss"
  placeholder="请选择创建时间"
  start-placeholder="开始日期"
  end-placeholder="结束日期"
  class="!w-220px"
/>

<ResponsiveDateRangePicker
  v-model="exportRange"
  value-format="YYYY-MM-DD"
  placeholder="请选择导出区间"
  class="!w-360px"
/>
```

组件契约：

- 对外只暴露一个范围值 `v-model`，页面不维护移动端开始/结束临时状态。
- 桌面端分支使用 `el-date-picker type="daterange"` 或项目等价控件。
- 替换已有桌面日期控件时，先沿用原控件宽度和查询区位置；不要默认放大宽度。需要变宽时，只改到解决重叠问题的最小值，并说明浏览器证据。
- 外层 wrapper 不得改变桌面查询区排版。使用 `inheritAttrs: false` 或项目等价方式，把外部 `class`、`style`、透传属性转发给桌面端真实日期控件，或保证 wrapper 与真实控件同宽。
- 手机端分支使用只读输入框作为入口，打开底部抽屉、全屏或单列弹层。
- 手机端内部使用 `selectingStep`、`draftStart`、`draftEnd` 等组件内状态，先选开始日期，再选结束日期。
- 手机端弹层提供开始/结束回显、月份切换、清空、取消、确认。
- 输出范围走项目北京时间工具，按 `FE-TZ-001` 生成日初、日末或业务要求的北京时间日期格式。
- 替换页面旧写法时删除 `mobileStart`、`mobileEnd`、`syncMobileRange`、`isMobileViewport` 等页面级日期范围临时逻辑。

桌面保真写法示例：

```vue
<template>
  <div class="responsive-date-range-picker">
    <el-date-picker
      v-if="!isMobileViewport"
      v-bind="controlAttrs"
      :model-value="modelValue"
      type="daterange"
      :class="['responsive-date-range-picker__desktop', attrs.class]"
      :style="attrs.style"
      @update:model-value="handleDesktopChange"
    />
    <el-input
      v-else
      v-bind="controlAttrs"
      :model-value="mobileDisplayValue"
      readonly
      class="responsive-date-range-picker__mobile"
      @click="openMobilePicker"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ inheritAttrs: false })

const attrs = useAttrs()
const controlAttrs = computed(() => {
  const { class: _className, style: _style, ...rest } = attrs
  return rest
})
</script>
```

桌面查询区验收要点：

- 原页面是 `!w-220px` 就先保持 `!w-220px`，不要直接改成 `!w-360px`。
- 浏览器测量 wrapper 和真实控件宽度应等于页面声明宽度。
- 搜索、重置、新增、导出、列显示按钮不得被日期控件压住或发生不可接受位移。
- 手机端仍按 `FE-MOBILE-001` 全宽显示，不受桌面固定宽度影响。

## 手机端实现模式

本节只说明 `FE-MOBILE-001` 的常见实现顺序。手机端最小按 `375px` 取证：

1. 查询区单列或折叠。
2. 工具按钮换行或分组直接展示。
3. 表格在表格容器内横向滚动。
4. 操作列不固定右侧，随表格横向滚动到最后一列，按钮换行直出或使用移动端动作区。
5. 弹窗接近全宽，内容滚动，底部按钮可到达。
6. 日期范围使用响应式日期范围组件，手机端走抽屉、全屏或单列弹层，不直接交付默认双面板 `daterange`。

验收执行 `FE-MOBILE-001` 和 `FE-DATE-001`。

## 分页模式

标准列表页必须使用项目分页组件：

```vue
<Pagination
  :total="total"
  v-model:page="queryParams.pageNo"
  v-model:limit="queryParams.pageSize"
  @pagination="getList"
/>
```

不使用分页时，必须说明该列表不是分页列表，或后端接口不是分页接口。

## 前端交付记录

交付时按 `references/acceptance.md` 输出触发规则 ID 的结论。前端页面一般至少写：

```text
前端验收：
- FE-PAGE-001：
- FE-TABLE-001：
- FE-ACTION-001：
- FE-COLUMN-001：
- FE-FK-001：
- FE-TZ-001：
- FE-DATE-001：
- FE-MOBILE-001：
- FE-FORM-001：
- 无法证明：
```
