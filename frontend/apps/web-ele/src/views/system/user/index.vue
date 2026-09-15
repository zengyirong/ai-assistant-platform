<script lang="ts" setup>
import type { SystemRole } from '#/api/system/role';
import type { SystemUser } from '#/api/system/user';

import { onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElOption,
    ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { listRolesApi } from '#/api/system/role';
import {
  createSystemUserApi,
  listSystemUsersApi,
  resetSystemUserPasswordApi,
  setSystemUserRolesApi,
  updateSystemUserApi,
} from '#/api/system/user';

defineOptions({ name: 'SystemUser' });

const loading = ref(false);
const items = ref<SystemUser[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const keyword = ref('');
const roles = ref<SystemRole[]>([]);

const createVisible = ref(false);
const createForm = reactive({
  username: '',
  password: '',
  nickname: '',
  role_ids: [] as string[],
});

const roleVisible = ref(false);
const roleTarget = ref<SystemUser | null>(null);
const roleIds = ref<string[]>([]);

const pwdVisible = ref(false);
const pwdTarget = ref<SystemUser | null>(null);
const newPassword = ref('');

const editVisible = ref(false);
const editTarget = ref<SystemUser | null>(null);
const editForm = reactive({
  nickname: '',
  email: '',
  status: 'ACTIVE',
});

async function loadRoles() {
  const data = await listRolesApi({ page_size: 100 });
  roles.value = data.items ?? [];
}

async function load() {
  loading.value = true;
  try {
    const data = await listSystemUsersApi({
      q: keyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
      include_disabled: true,
    });
    items.value = data.items ?? [];
    total.value = data.total ?? 0;
  } finally {
    loading.value = false;
  }
}

async function onCreate() {
  await createSystemUserApi({
    username: createForm.username,
    password: createForm.password,
    nickname: createForm.nickname || undefined,
    role_ids: createForm.role_ids.length ? createForm.role_ids : undefined,
  });
  ElMessage.success('用户已创建');
  createVisible.value = false;
  createForm.username = '';
  createForm.password = '';
  createForm.nickname = '';
  createForm.role_ids = [];
  await load();
}

async function toggleStatus(row: SystemUser) {
  const next = row.status === 'ACTIVE' ? 'DISABLED' : 'ACTIVE';
  await updateSystemUserApi(row.id, { status: next });
  ElMessage.success(next === 'ACTIVE' ? '已启用' : '已停用');
  await load();
}

function openRoles(row: SystemUser) {
  roleTarget.value = row;
  roleIds.value = [...(row.role_ids ?? [])];
  roleVisible.value = true;
}

async function saveRoles() {
  if (!roleTarget.value) return;
  await setSystemUserRolesApi(roleTarget.value.id, roleIds.value);
  ElMessage.success('角色已更新');
  roleVisible.value = false;
  await load();
}

function openPwd(row: SystemUser) {
  pwdTarget.value = row;
  newPassword.value = '';
  pwdVisible.value = true;
}

async function savePwd() {
  if (!pwdTarget.value) return;
  await resetSystemUserPasswordApi(pwdTarget.value.id, newPassword.value);
  ElMessage.success('密码已重置');
  pwdVisible.value = false;
}

function openEdit(row: SystemUser) {
  editTarget.value = row;
  editForm.nickname = row.nickname || '';
  editForm.email = row.email || '';
  editForm.status = row.status || 'ACTIVE';
  editVisible.value = true;
}

async function saveEdit() {
  if (!editTarget.value) return;
  await updateSystemUserApi(editTarget.value.id, {
    nickname: editForm.nickname,
    email: editForm.email,
    status: editForm.status,
  });
  ElMessage.success('用户已更新');
  editVisible.value = false;
  await load();
}

onMounted(async () => {
  await loadRoles();
  await load();
});
</script>

<template>
  <Page title="用户管理" description="本组织用户（无部门）">
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <ElInput
        v-model="keyword"
        clearable
        class="w-56"
        placeholder="用户名 / 昵称"
        @keyup.enter="load"
      />
      <ElButton type="primary" @click="load">查询</ElButton>
      <ElButton type="primary" @click="createVisible = true">新增用户</ElButton>
    </div>

    <ElTable v-loading="loading" :data="items" stripe>
      <ElTableColumn prop="username" label="用户名" min-width="120" />
      <ElTableColumn prop="nickname" label="昵称" min-width="120" />
      <ElTableColumn prop="email" label="邮箱" min-width="160" />
      <ElTableColumn label="角色" min-width="140">
        <template #default="{ row }">
          <ElTag
            v-for="code in row.roles || []"
            :key="code"
            class="mr-1"
            size="small"
          >
            {{ code }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="状态" width="100">
        <template #default="{ row }">
          <ElTag :type="row.status === 'ACTIVE' ? 'success' : 'info'">
            {{ row.status === 'ACTIVE' ? '启用' : '停用' }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <ElButton link type="primary" @click="openEdit(row)">编辑</ElButton>
          <ElButton link type="primary" @click="openRoles(row)">角色</ElButton>
          <ElButton link type="primary" @click="openPwd(row)">重置密码</ElButton>
          <ElButton link type="warning" @click="toggleStatus(row)">
            {{ row.status === 'ACTIVE' ? '停用' : '启用' }}
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <ElDialog v-model="createVisible" title="新增用户" width="480px">
      <ElForm label-width="88px">
        <ElFormItem label="用户名" required>
          <ElInput
            v-model="createForm.username"
            placeholder="至少 3 位字母/数字/下划线"
            maxlength="32"
          />
        </ElFormItem>
        <ElFormItem label="密码" required>
          <ElInput
            v-model="createForm.password"
            type="password"
            show-password
            placeholder="至少 8 位"
          />
        </ElFormItem>
        <ElFormItem label="昵称">
          <ElInput v-model="createForm.nickname" />
        </ElFormItem>
        <ElFormItem label="角色">
          <ElSelect
            v-model="createForm.role_ids"
            multiple
            class="w-full"
            placeholder="默认 USER"
          >
            <ElOption
              v-for="r in roles"
              :key="r.id"
              :label="`${r.name} (${r.code})`"
              :value="r.id"
            />
          </ElSelect>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="createVisible = false">取消</ElButton>
        <ElButton type="primary" @click="onCreate">确定</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="editVisible" title="编辑用户" width="480px">
      <ElForm label-width="88px">
        <ElFormItem label="用户名">
          <ElInput :model-value="editTarget?.username" disabled />
        </ElFormItem>
        <ElFormItem label="昵称">
          <ElInput v-model="editForm.nickname" maxlength="128" />
        </ElFormItem>
        <ElFormItem label="邮箱">
          <ElInput v-model="editForm.email" maxlength="255" />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="editForm.status" class="w-full">
            <ElOption label="启用" value="ACTIVE" />
            <ElOption label="停用" value="DISABLED" />
          </ElSelect>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editVisible = false">取消</ElButton>
        <ElButton type="primary" @click="saveEdit">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="roleVisible" title="分配角色" width="420px">
      <ElSelect v-model="roleIds" multiple class="w-full">
        <ElOption
          v-for="r in roles"
          :key="r.id"
          :label="`${r.name} (${r.code})`"
          :value="r.id"
        />
      </ElSelect>
      <template #footer>
        <ElButton @click="roleVisible = false">取消</ElButton>
        <ElButton type="primary" @click="saveRoles">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="pwdVisible" title="重置密码" width="420px">
      <ElInput
        v-model="newPassword"
        type="password"
        show-password
        placeholder="至少 8 位"
      />
      <template #footer>
        <ElButton @click="pwdVisible = false">取消</ElButton>
        <ElButton type="primary" @click="savePwd">确定</ElButton>
      </template>
    </ElDialog>
  </Page>
</template>
