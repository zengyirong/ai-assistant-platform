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
const editVisible = ref(false);
const editId = ref('');

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
  status: 'ACTIVE',
  redirect: '',
});

const editForm = reactive({
  name: '',
  parent_id: '' as string | '',
  path: '',
  component: '',
  icon: '',
  sort_order: 0,
  visible: true,
  status: 'ACTIVE',
  redirect: '',
});

function resetCreateForm() {
  form.code = '';
  form.name = '';
  form.type = 'MENU';
  form.parent_id = '';
  form.path = '';
  form.component = '';
  form.icon = '';
  form.sort_order = 0;
  form.visible = true;
  form.status = 'ACTIVE';
  form.redirect = '';
}

async function load() {
  loading.value = true;
  try {
    const data = await listPermissionsApi();
    items.value = data.items ?? [];
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  resetCreateForm();
  createVisible.value = true;
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
    status: form.status,
    redirect: form.redirect || undefined,
  });
  ElMessage.success('已创建');
  createVisible.value = false;
  await load();
}

function openEdit(row: SystemPermission) {
  editId.value = row.id;
  editForm.name = row.name;
  editForm.parent_id = row.parent_id || '';
  editForm.path = row.path || '';
  editForm.component = row.component || '';
  editForm.icon = row.icon || '';
  editForm.sort_order = row.sort_order ?? 0;
  editForm.visible = !!row.visible;
  editForm.status = row.status || 'ACTIVE';
  editForm.redirect = row.redirect || '';
  editVisible.value = true;
}

async function onSaveEdit() {
  const clearParent = !editForm.parent_id;
  await updatePermissionApi(editId.value, {
    name: editForm.name,
    parent_id: editForm.parent_id || undefined,
    clear_parent: clearParent,
    path: editForm.path,
    component: editForm.component,
    icon: editForm.icon,
    sort_order: editForm.sort_order,
    visible: editForm.visible,
    status: editForm.status,
    redirect: editForm.redirect,
  });
  ElMessage.success('已更新（菜单变更需重新登录后生效）');
  editVisible.value = false;
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

function parentOptions(excludeId?: string) {
  return items.value.filter((p) => p.id !== excludeId);
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
      <ElButton type="primary" @click="openCreate">新增权限</ElButton>
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
          <ElSwitch :model-value="row.visible" @change="toggleVisible(row)" />
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <ElButton link type="primary" @click="openEdit(row)">编辑</ElButton>
          <ElButton
            link
            type="danger"
            :disabled="
              row.type === 'MENU' &&
              ['menu:dashboard', 'menu:system'].includes(row.code)
            "
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
          <ElInput
            v-model="form.code"
            placeholder="menu:xxx 或 knowledge:list"
          />
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
        <ElFormItem label="redirect">
          <ElInput v-model="form.redirect" />
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

    <ElDialog v-model="editVisible" title="编辑权限节点" width="520px">
      <ElForm label-width="88px">
        <ElFormItem label="编码">
          <ElInput
            :model-value="items.find((i) => i.id === editId)?.code"
            disabled
          />
        </ElFormItem>
        <ElFormItem label="类型">
          <ElInput
            :model-value="items.find((i) => i.id === editId)?.type"
            disabled
          />
        </ElFormItem>
        <ElFormItem label="名称" required>
          <ElInput v-model="editForm.name" />
        </ElFormItem>
        <ElFormItem label="父节点">
          <ElSelect
            v-model="editForm.parent_id"
            clearable
            filterable
            class="w-full"
          >
            <ElOption
              v-for="p in parentOptions(editId)"
              :key="p.id"
              :label="`${p.name} (${p.code})`"
              :value="p.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="path">
          <ElInput v-model="editForm.path" />
        </ElFormItem>
        <ElFormItem label="component">
          <ElInput v-model="editForm.component" />
        </ElFormItem>
        <ElFormItem label="icon">
          <ElInput v-model="editForm.icon" />
        </ElFormItem>
        <ElFormItem label="redirect">
          <ElInput v-model="editForm.redirect" />
        </ElFormItem>
        <ElFormItem label="排序">
          <ElInputNumber v-model="editForm.sort_order" />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="editForm.status" class="w-full">
            <ElOption label="ACTIVE" value="ACTIVE" />
            <ElOption label="DISABLED" value="DISABLED" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="侧栏可见">
          <ElSwitch v-model="editForm.visible" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editVisible = false">取消</ElButton>
        <ElButton type="primary" @click="onSaveEdit">保存</ElButton>
      </template>
    </ElDialog>
  </Page>
</template>
