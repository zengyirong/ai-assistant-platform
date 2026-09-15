<script lang="ts" setup>
import type { SystemPermission } from '#/api/system/permission';

import { onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  createPermissionApi,
  deletePermissionApi,
  listPermissionsApi,
  updatePermissionApi,
} from '#/api/system/permission';

defineOptions({ name: 'SystemMenu' });

const loading = ref(false);
const items = ref<SystemPermission[]>([]);
const createVisible = ref(false);
const form = reactive({
  code: '',
  name: '',
  type: 'MENU',
  parent_id: '' as string | '',
  path: '',
  component: '',
  icon: '',
  sort_order: 0,
  visible: true,
});

async function load() {
  loading.value = true;
  try {
    const data = await listPermissionsApi();
    items.value = data.items ?? [];
  } finally {
    loading.value = false;
  }
}

async function onCreate() {
  await createPermissionApi({
    code: form.code,
    name: form.name,
    type: form.type,
    parent_id: form.parent_id || undefined,
    path: form.path || undefined,
    component: form.component || undefined,
    icon: form.icon || undefined,
    sort_order: form.sort_order,
    visible: form.visible,
  });
  ElMessage.success('已创建');
  createVisible.value = false;
  await load();
}

async function onDelete(row: SystemPermission) {
  await deletePermissionApi(row.id);
  ElMessage.success('已删除');
  await load();
}

async function toggleVisible(row: SystemPermission) {
  await updatePermissionApi(row.id, { visible: !row.visible });
  await load();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <Page
    title="菜单管理"
    description="sys_permission（MENU/BUTTON/API），非独立菜单表"
  >
    <div class="mb-4">
      <ElButton type="primary" @click="createVisible = true">新增权限</ElButton>
      <ElButton class="ml-2" @click="load">刷新</ElButton>
    </div>
    <ElTable v-loading="loading" :data="items" stripe row-key="id">
      <ElTableColumn prop="code" label="编码" min-width="180" />
      <ElTableColumn prop="name" label="名称" min-width="120" />
      <ElTableColumn prop="type" label="类型" width="90">
        <template #default="{ row }">
          <ElTag size="small">{{ row.type }}</ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn prop="path" label="路径" min-width="160" />
      <ElTableColumn prop="sort_order" label="排序" width="80" />
      <ElTableColumn label="可见" width="90">
        <template #default="{ row }">
          <ElSwitch
            :model-value="row.visible"
            @change="toggleVisible(row)"
          />
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <ElButton
            link
            type="danger"
            :disabled="row.code.startsWith('menu:') && row.type === 'MENU' && ['menu:dashboard','menu:system'].includes(row.code)"
            @click="onDelete(row)"
          >
            删除
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <ElDialog v-model="createVisible" title="新增权限节点" width="520px">
      <ElForm label-width="88px">
        <ElFormItem label="编码" required>
          <ElInput v-model="form.code" placeholder="menu:xxx 或 knowledge:list" />
        </ElFormItem>
        <ElFormItem label="名称" required>
          <ElInput v-model="form.name" />
        </ElFormItem>
        <ElFormItem label="类型" required>
          <ElSelect v-model="form.type" class="w-full">
            <ElOption label="MENU" value="MENU" />
            <ElOption label="BUTTON" value="BUTTON" />
            <ElOption label="API" value="API" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="父节点">
          <ElSelect v-model="form.parent_id" clearable filterable class="w-full">
            <ElOption
              v-for="p in items"
              :key="p.id"
              :label="`${p.name} (${p.code})`"
              :value="p.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="path">
          <ElInput v-model="form.path" />
        </ElFormItem>
        <ElFormItem label="component">
          <ElInput v-model="form.component" placeholder="/system/user/index" />
        </ElFormItem>
        <ElFormItem label="icon">
          <ElInput v-model="form.icon" placeholder="lucide:users" />
        </ElFormItem>
        <ElFormItem label="排序">
          <ElInputNumber v-model="form.sort_order" />
        </ElFormItem>
        <ElFormItem label="侧栏可见">
          <ElSwitch v-model="form.visible" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="createVisible = false">取消</ElButton>
        <ElButton type="primary" @click="onCreate">确定</ElButton>
      </template>
    </ElDialog>
  </Page>
</template>
