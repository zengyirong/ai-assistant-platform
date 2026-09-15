<script lang="ts" setup>
import type { SystemPermission } from '#/api/system/permission';
import type { SystemRole } from '#/api/system/role';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTree,
} from 'element-plus';

import { listPermissionsApi } from '#/api/system/permission';
import {
  createRoleApi,
  listRolesApi,
  setRolePermissionsApi,
  updateRoleApi,
} from '#/api/system/role';

defineOptions({ name: 'SystemRole' });

const loading = ref(false);
const items = ref<SystemRole[]>([]);
const permFlat = ref<SystemPermission[]>([]);

const createVisible = ref(false);
const createCode = ref('');
const createName = ref('');

const permVisible = ref(false);
const permTarget = ref<SystemRole | null>(null);
const checkedKeys = ref<string[]>([]);
const treeRef = ref();

async function load() {
  loading.value = true;
  try {
    const [roles, perms] = await Promise.all([
      listRolesApi({ page_size: 100 }),
      listPermissionsApi(),
    ]);
    items.value = roles.items ?? [];
    permFlat.value = perms.items ?? [];
  } finally {
    loading.value = false;
  }
}

function treeData() {
  const byId = new Map(
    permFlat.value.map((p) => [p.id, { ...p, children: [] as any[] }]),
  );
  const roots: any[] = [];
  for (const node of byId.values()) {
    if (node.parent_id && byId.has(node.parent_id)) {
      byId.get(node.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

async function onCreate() {
  await createRoleApi({ code: createCode.value, name: createName.value });
  ElMessage.success('角色已创建');
  createVisible.value = false;
  createCode.value = '';
  createName.value = '';
  await load();
}

async function toggleStatus(row: SystemRole) {
  const next = row.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE';
  await updateRoleApi(row.id, { status: next });
  ElMessage.success('状态已更新');
  await load();
}

function openPerms(row: SystemRole) {
  permTarget.value = row;
  checkedKeys.value = [...(row.permission_ids ?? [])];
  permVisible.value = true;
}

async function savePerms() {
  if (!permTarget.value) return;
  const tree = treeRef.value;
  const keys = [
    ...(tree?.getCheckedKeys?.(false) ?? checkedKeys.value),
    ...(tree?.getHalfCheckedKeys?.() ?? []),
  ] as string[];
  await setRolePermissionsApi(permTarget.value.id, keys);
  ElMessage.success(
    '权限已保存（勾选菜单会自动补齐关联 API；重新登录后生效）',
  );
  permVisible.value = false;
  await load();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <Page title="角色管理" description="角色绑定 MENU / API 权限">
    <div class="mb-4">
      <ElButton type="primary" @click="createVisible = true">新建角色</ElButton>
    </div>
    <ElTable v-loading="loading" :data="items" stripe>
      <ElTableColumn prop="code" label="编码" width="140" />
      <ElTableColumn prop="name" label="名称" min-width="160" />
      <ElTableColumn label="状态" width="100">
        <template #default="{ row }">
          <ElTag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
            {{ row.status }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="权限数" width="100">
        <template #default="{ row }">
          {{ (row.permission_ids || []).length }}
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <ElButton link type="primary" @click="openPerms(row)">权限</ElButton>
          <ElButton
            link
            type="warning"
            :disabled="row.code === 'ADMIN' || row.code === 'USER'"
            @click="toggleStatus(row)"
          >
            {{ row.status === 'ACTIVE' ? '停用' : '启用' }}
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <ElDialog v-model="createVisible" title="新建角色" width="420px">
      <ElForm label-width="72px">
        <ElFormItem label="编码" required>
          <ElInput v-model="createCode" placeholder="如 EDITOR" />
        </ElFormItem>
        <ElFormItem label="名称" required>
          <ElInput v-model="createName" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="createVisible = false">取消</ElButton>
        <ElButton type="primary" @click="onCreate">确定</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="permVisible" title="分配权限" width="560px">
      <p class="text-muted-foreground mb-3 text-sm">
        请同时关注类型为 API 的节点；仅勾选 MENU
        会导致能看见菜单但接口 403。保存时会按菜单自动补齐常用 API。
      </p>
      <ElTree
        ref="treeRef"
        :data="treeData()"
        node-key="id"
        show-checkbox
        default-expand-all
        :default-checked-keys="checkedKeys"
        :props="{ label: 'name', children: 'children' }"
      >
        <template #default="{ data }">
          <span>{{ data.name }}</span>
          <ElTag size="small" class="ml-2">{{ data.type }}</ElTag>
          <span class="text-muted-foreground ml-2 text-xs">{{ data.code }}</span>
        </template>
      </ElTree>
      <template #footer>
        <ElButton @click="permVisible = false">取消</ElButton>
        <ElButton type="primary" @click="savePerms">保存</ElButton>
      </template>
    </ElDialog>
  </Page>
</template>
