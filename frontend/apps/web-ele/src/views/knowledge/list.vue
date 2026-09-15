<script lang="ts" setup>
import type { FormInstance, FormRules } from 'element-plus';

import type { KnowledgeBase, KbVisibility } from '#/types/knowledge';
import type { SpaceItem } from '#/api/space';

import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDrawer,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElRadio,
  ElRadioGroup,
  ElSelect,
  ElSpace,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  createKnowledgeBaseApi,
  deleteKnowledgeBaseApi,
  listKnowledgeBasesApi,
} from '#/api/knowledge';
import { listSpacesApi } from '#/api/space';

defineOptions({ name: 'KnowledgeList' });

const router = useRouter();
const loading = ref(false);
const items = ref<KnowledgeBase[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);

const keyword = ref('');
const filterVisibility = ref<'' | KbVisibility>('');
const filterStatus = ref<'' | 'ACTIVE' | 'ARCHIVED'>('');

const drawerVisible = ref(false);
const creating = ref(false);
const formRef = ref<FormInstance>();
const spaces = ref<SpaceItem[]>([]);

const form = reactive({
  name: '',
  description: '',
  visibility: 'PRIVATE' as KbVisibility,
  space_id: '' as string,
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  visibility: [{ required: true, message: '请选择可见范围', trigger: 'change' }],
};

const filteredItems = computed(() => {
  return items.value.filter((row) => {
    if (keyword.value && !row.name.includes(keyword.value.trim())) {
      return false;
    }
    if (filterVisibility.value && row.visibility !== filterVisibility.value) {
      return false;
    }
    if (filterStatus.value && row.status !== filterStatus.value) {
      return false;
    }
    return true;
  });
});

function visibilityLabel(v: string) {
  return v === 'SPACE' ? '空间' : '私有';
}

function statusLabel(s: string) {
  return s === 'ACTIVE' ? '正常' : '已归档';
}

async function loadList() {
  loading.value = true;
  try {
    const data = await listKnowledgeBasesApi({
      page: page.value,
      page_size: pageSize.value,
    });
    items.value = data.items ?? [];
    total.value = data.total ?? 0;
  } catch {
    // interceptor toast
  } finally {
    loading.value = false;
  }
}

async function loadSpaces() {
  try {
    const data = await listSpacesApi();
    spaces.value = data.items ?? [];
    const def = spaces.value.find((s) => s.is_default === 1) || spaces.value[0];
    if (def) {
      form.space_id = def.id;
    }
  } catch {
    spaces.value = [];
  }
}

function openCreate() {
  form.name = '';
  form.description = '';
  form.visibility = 'PRIVATE';
  drawerVisible.value = true;
  void loadSpaces();
}

async function submitCreate() {
  if (!formRef.value) return;
  await formRef.value.validate(async (ok) => {
    if (!ok) return;
    if (form.visibility === 'SPACE' && !form.space_id) {
      ElMessage.warning('空间可见性必须选择所属空间');
      return;
    }
    creating.value = true;
    try {
      const created = await createKnowledgeBaseApi({
        name: form.name.trim(),
        description: form.description.trim() || null,
        visibility: form.visibility,
        space_id: form.visibility === 'SPACE' ? form.space_id : null,
      });
      ElMessage.success('知识库已创建');
      drawerVisible.value = false;
      await router.push(`/knowledge/detail/${created.id}`);
    } catch {
      // interceptor
    } finally {
      creating.value = false;
    }
  });
}

function goDetail(row: KnowledgeBase) {
  void router.push(`/knowledge/detail/${row.id}`);
}

async function onDelete(row: KnowledgeBase) {
  try {
    await ElMessageBox.confirm(
      `删除知识库「${row.name}」？\n\n删除后：\n- 知识库无法继续访问\n- 关联文档将被删除\n- 关联向量索引将被清理\n\n该操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    );
  } catch {
    return;
  }
  try {
    await deleteKnowledgeBaseApi(row.id);
    ElMessage.success('已删除');
    await loadList();
  } catch {
    // interceptor
  }
}

onMounted(() => {
  void loadList();
});
</script>

<template>
  <Page title="知识库管理" description="管理知识库，上传文档后即可用于智能问答。">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <ElSpace wrap>
        <ElInput
          v-model="keyword"
          clearable
          placeholder="名称搜索"
          style="width: 220px"
        />
        <ElSelect
          v-model="filterVisibility"
          clearable
          placeholder="可见范围"
          style="width: 140px"
        >
          <ElOption label="私有" value="PRIVATE" />
          <ElOption label="空间" value="SPACE" />
        </ElSelect>
        <ElSelect
          v-model="filterStatus"
          clearable
          placeholder="状态"
          style="width: 120px"
        >
          <ElOption label="正常" value="ACTIVE" />
          <ElOption label="已归档" value="ARCHIVED" />
        </ElSelect>
        <ElButton @click="loadList">刷新</ElButton>
      </ElSpace>
      <ElButton
        v-access:code="'btn:knowledge:create'"
        type="primary"
        @click="openCreate"
      >
        新建知识库
      </ElButton>
    </div>

    <ElTable v-loading="loading" :data="filteredItems" stripe>
      <ElTableColumn prop="name" label="名称" min-width="180" />
      <ElTableColumn label="可见范围" width="100">
        <template #default="{ row }">
          {{ visibilityLabel(row.visibility) }}
        </template>
      </ElTableColumn>
      <ElTableColumn label="文档数" width="90">
        <template #default="{ row }">
          {{ row.document_count ?? 0 }}
        </template>
      </ElTableColumn>
      <ElTableColumn label="状态" width="100">
        <template #default="{ row }">
          <ElTag :type="row.status === 'ACTIVE' ? 'success' : 'info'" size="small">
            {{ statusLabel(row.status) }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn prop="updated_at" label="更新时间" min-width="180" />
      <ElTableColumn label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <ElButton link type="primary" @click="goDetail(row)">详情</ElButton>
          <ElButton link type="danger" @click="onDelete(row)">删除</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <div
      v-if="!loading && filteredItems.length === 0"
      class="text-muted-foreground py-16 text-center text-sm"
    >
      暂无知识库。创建第一个知识库，上传文档后即可开始智能问答。
    </div>

    <ElDrawer v-model="drawerVisible" title="新建知识库" size="420px">
      <ElForm ref="formRef" :model="form" :rules="rules" label-position="top">
        <ElFormItem label="名称" prop="name">
          <ElInput v-model="form.name" maxlength="128" show-word-limit />
        </ElFormItem>
        <ElFormItem label="描述">
          <ElInput
            v-model="form.description"
            type="textarea"
            :rows="3"
            maxlength="1024"
            show-word-limit
          />
        </ElFormItem>
        <ElFormItem label="可见范围" prop="visibility">
          <ElRadioGroup v-model="form.visibility">
            <ElRadio value="PRIVATE">私有</ElRadio>
            <ElRadio value="SPACE">空间</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem v-if="form.visibility === 'SPACE'" label="所属空间">
          <ElSelect v-model="form.space_id" placeholder="选择空间" class="w-full">
            <ElOption
              v-for="s in spaces"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </ElSelect>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElSpace>
          <ElButton @click="drawerVisible = false">取消</ElButton>
          <ElButton type="primary" :loading="creating" @click="submitCreate">
            创建
          </ElButton>
        </ElSpace>
      </template>
    </ElDrawer>
  </Page>
</template>
