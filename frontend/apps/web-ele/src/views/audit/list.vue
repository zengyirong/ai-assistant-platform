<script lang="ts" setup>
import type { AuditLogItem } from '#/types/audit';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { listAuditLogsApi } from '#/api/audit';

defineOptions({ name: 'AuditLogList' });

const loading = ref(false);
const items = ref<AuditLogItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);
const actionFilter = ref('');

const ACTION_OPTIONS = [
  { label: '全部', value: '' },
  { label: '登录', value: 'auth.login' },
  { label: '登出', value: 'auth.logout' },
  { label: '上传文档', value: 'document.upload' },
  { label: '删除文档', value: 'document.delete' },
  { label: '重试解析', value: 'document.retry' },
  { label: '成员变更', value: 'kb.member.upsert' },
  { label: '移除成员', value: 'kb.member.remove' },
];

function resultType(result: string) {
  if (result === 'SUCCESS') return 'success';
  if (result === 'DENIED') return 'warning';
  return 'danger';
}

function formatDetail(detail: AuditLogItem['detail']) {
  if (!detail) return '—';
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

async function load() {
  loading.value = true;
  try {
    const data = await listAuditLogsApi({
      page: page.value,
      page_size: pageSize.value,
      action: actionFilter.value || undefined,
    });
    items.value = data.items ?? [];
    total.value = data.total ?? 0;
  } catch {
    items.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function onPageChange(p: number) {
  page.value = p;
  void load();
}

function onSizeChange(size: number) {
  pageSize.value = size;
  page.value = 1;
  void load();
}

function onSearch() {
  page.value = 1;
  void load();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <Page title="审计日志" description="组织内关键写操作记录（仅管理员）">
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <ElSelect
        v-model="actionFilter"
        clearable
        placeholder="按操作筛选"
        style="width: 200px"
        @change="onSearch"
      >
        <ElOption
          v-for="opt in ACTION_OPTIONS"
          :key="opt.value || 'all'"
          :label="opt.label"
          :value="opt.value"
        />
      </ElSelect>
      <ElButton type="primary" @click="onSearch">刷新</ElButton>
    </div>

    <ElTable v-loading="loading" :data="items" stripe>
      <ElTableColumn prop="created_at" label="时间" min-width="180" />
      <ElTableColumn prop="action" label="操作" min-width="150" />
      <ElTableColumn label="结果" width="100">
        <template #default="{ row }">
          <ElTag :type="resultType(row.result)" size="small">
            {{ row.result }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn prop="user_id" label="用户 ID" min-width="200" />
      <ElTableColumn prop="resource_type" label="资源类型" width="120" />
      <ElTableColumn prop="resource_id" label="资源 ID" min-width="200" />
      <ElTableColumn label="详情" min-width="220" show-overflow-tooltip>
        <template #default="{ row }">
          {{ formatDetail(row.detail) }}
        </template>
      </ElTableColumn>
      <ElTableColumn prop="ip" label="IP" width="120" />
    </ElTable>

    <div class="mt-4 flex justify-end">
      <ElPagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :page-sizes="[10, 20, 50]"
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>
  </Page>
</template>
