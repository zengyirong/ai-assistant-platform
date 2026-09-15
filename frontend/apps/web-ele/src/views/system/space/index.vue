<script lang="ts" setup>
import type { SpaceItem, SpaceMember } from '#/api/system/space';
import type { SystemUser } from '#/api/system/user';

import { onMounted, ref } from 'vue';

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

import {
  createSpaceApi,
  listSpaceMembersApi,
  listSpacesApi,
  removeSpaceMemberApi,
  updateSpaceApi,
  upsertSpaceMemberApi,
} from '#/api/system/space';
import { listSystemUsersApi } from '#/api/system/user';

defineOptions({ name: 'SystemSpace' });

const loading = ref(false);
const items = ref<SpaceItem[]>([]);
const createVisible = ref(false);
const name = ref('');
const description = ref('');

const memberVisible = ref(false);
const current = ref<SpaceItem | null>(null);
const members = ref<SpaceMember[]>([]);
const users = ref<SystemUser[]>([]);
const memberUserId = ref('');
const memberRole = ref('MEMBER');

async function load() {
  loading.value = true;
  try {
    const data = await listSpacesApi();
    items.value = data.items ?? [];
  } finally {
    loading.value = false;
  }
}

async function onCreate() {
  await createSpaceApi({ name: name.value, description: description.value || undefined });
  ElMessage.success('空间已创建');
  createVisible.value = false;
  name.value = '';
  description.value = '';
  await load();
}

async function openMembers(row: SpaceItem) {
  current.value = row;
  const [m, u] = await Promise.all([
    listSpaceMembersApi(row.id),
    listSystemUsersApi({ page_size: 100, include_disabled: false }),
  ]);
  members.value = m.items ?? [];
  users.value = u.items ?? [];
  memberVisible.value = true;
}

async function addMember() {
  if (!current.value || !memberUserId.value) return;
  await upsertSpaceMemberApi(current.value.id, {
    user_id: memberUserId.value,
    role: memberRole.value,
  });
  ElMessage.success('成员已更新');
  await openMembers(current.value);
}

async function removeMember(userId: string) {
  if (!current.value) return;
  await removeSpaceMemberApi(current.value.id, userId);
  ElMessage.success('已移除');
  await openMembers(current.value);
}

async function rename(row: SpaceItem) {
  const next = window.prompt('新名称', row.name);
  if (!next || next === row.name) return;
  await updateSpaceApi(row.id, { name: next });
  ElMessage.success('已更新');
  await load();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <Page title="空间管理" description="协作空间（非行政组织部门）">
    <div class="mb-4">
      <ElButton type="primary" @click="createVisible = true">新建空间</ElButton>
    </div>
    <ElTable v-loading="loading" :data="items" stripe>
      <ElTableColumn prop="name" label="名称" min-width="160" />
      <ElTableColumn prop="description" label="描述" min-width="200" />
      <ElTableColumn label="默认" width="90">
        <template #default="{ row }">
          <ElTag v-if="row.is_default" type="success">是</ElTag>
          <span v-else>—</span>
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <ElButton link type="primary" @click="openMembers(row)">成员</ElButton>
          <ElButton link type="primary" @click="rename(row)">改名</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <ElDialog v-model="createVisible" title="新建空间" width="420px">
      <ElForm label-width="72px">
        <ElFormItem label="名称" required>
          <ElInput v-model="name" />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput v-model="description" type="textarea" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="createVisible = false">取消</ElButton>
        <ElButton type="primary" @click="onCreate">确定</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="memberVisible" title="空间成员" width="640px">
      <div class="mb-3 flex gap-2">
        <ElSelect
          v-model="memberUserId"
          filterable
          class="flex-1"
          placeholder="选择用户"
        >
          <ElOption
            v-for="u in users"
            :key="u.id"
            :label="`${u.nickname || u.username} (${u.username})`"
            :value="u.id"
          />
        </ElSelect>
        <ElSelect v-model="memberRole" class="w-28">
          <ElOption label="OWNER" value="OWNER" />
          <ElOption label="MEMBER" value="MEMBER" />
        </ElSelect>
        <ElButton type="primary" @click="addMember">添加</ElButton>
      </div>
      <ElTable :data="members" size="small">
        <ElTableColumn prop="username" label="用户" />
        <ElTableColumn prop="nickname" label="昵称" />
        <ElTableColumn prop="role" label="角色" width="100" />
        <ElTableColumn label="操作" width="90">
          <template #default="{ row }">
            <ElButton link type="danger" @click="removeMember(row.user_id)">
              移除
            </ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </ElDialog>
  </Page>
</template>
