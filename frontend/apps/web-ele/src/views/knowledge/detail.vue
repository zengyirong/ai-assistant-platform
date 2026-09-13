<script lang="ts" setup>
import type { UploadUserFile } from 'element-plus';

import type { DocumentItem } from '#/types/document';
import type { KnowledgeBase, KbMember, RagConfig } from '#/types/knowledge';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDialog,
  ElMessage,
  ElMessageBox,
  ElSpace,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
  ElUpload,
} from 'element-plus';

import {
  deleteDocumentApi,
  listDocumentsApi,
  listDocumentJobsApi,
  retryDocumentApi,
  uploadDocumentApi,
} from '#/api/document';
import {
  getKnowledgeBaseApi,
  getRagConfigApi,
  listKbMembersApi,
} from '#/api/knowledge';
import { DOCUMENT_STATUS_MAP } from '#/types/document';

defineOptions({ name: 'KnowledgeDetail' });

const route = useRoute();
const router = useRouter();
const kbId = computed(() => String(route.params.id || ''));

const loading = ref(false);
const kb = ref<KnowledgeBase | null>(null);
const activeTab = ref('documents');

const docsLoading = ref(false);
const documents = ref<DocumentItem[]>([]);
const members = ref<KbMember[]>([]);
const rag = ref<RagConfig | null>(null);

const uploadVisible = ref(false);
const uploading = ref(false);
const fileList = ref<UploadUserFile[]>([]);
const pollTimer = ref<null | ReturnType<typeof setInterval>>(null);

const title = computed(() => kb.value?.name || '知识库详情');

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function statusMeta(status: string) {
  return (
    DOCUMENT_STATUS_MAP[status as keyof typeof DOCUMENT_STATUS_MAP] || {
      label: status,
      type: 'info' as const,
    }
  );
}

async function loadKb() {
  loading.value = true;
  try {
    kb.value = await getKnowledgeBaseApi(kbId.value);
  } catch {
    kb.value = null;
  } finally {
    loading.value = false;
  }
}

async function loadDocuments() {
  docsLoading.value = true;
  try {
    const data = await listDocumentsApi(kbId.value, { page: 1, page_size: 100 });
    documents.value = data.items ?? [];
  } catch {
    documents.value = [];
  } finally {
    docsLoading.value = false;
  }
}

async function loadMembers() {
  try {
    const data = await listKbMembersApi(kbId.value);
    members.value = data.items ?? [];
  } catch {
    members.value = [];
  }
}

async function loadRag() {
  try {
    rag.value = await getRagConfigApi(kbId.value);
  } catch {
    rag.value = null;
  }
}

function startPolling() {
  stopPolling();
  pollTimer.value = setInterval(() => {
    const busy = documents.value.some(
      (d) => d.status === 'PROCESSING' || d.status === 'UPLOADED',
    );
    if (busy) {
      void loadDocuments();
    }
  }, 2500);
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
}

async function onUpload() {
  const raw = fileList.value[0]?.raw;
  if (!raw) {
    ElMessage.warning('请选择文件');
    return;
  }
  uploading.value = true;
  try {
    await uploadDocumentApi(kbId.value, raw);
    ElMessage.success('上传成功，文档正在后台解析。');
    uploadVisible.value = false;
    fileList.value = [];
    await loadDocuments();
  } catch {
    // interceptor
  } finally {
    uploading.value = false;
  }
}

async function onRetry(row: DocumentItem) {
  try {
    await retryDocumentApi(row.id);
    ElMessage.success('已重新提交解析任务');
    await loadDocuments();
  } catch {
    // interceptor
  }
}

async function onDeleteDoc(row: DocumentItem) {
  try {
    await ElMessageBox.confirm(
      `删除「${row.file_name}」？\n删除后该文档将不再参与知识检索。`,
      '删除确认',
      { type: 'warning' },
    );
  } catch {
    return;
  }
  try {
    await deleteDocumentApi(row.id);
    ElMessage.success('已删除');
    await loadDocuments();
  } catch {
    // interceptor
  }
}

async function showFailReason(row: DocumentItem) {
  try {
    const data = await listDocumentJobsApi(row.id);
    const job = data.items?.[0];
    await ElMessageBox.alert(
      `错误类型：${job?.error_code || 'UNKNOWN'}\n\n原因：${
        job?.error_message || '暂无详情'
      }\n\n建议：请检查文件格式后重试，或联系管理员。`,
      '解析失败',
      { confirmButtonText: '知道了' },
    );
  } catch {
    // interceptor
  }
}

watch(
  activeTab,
  (tab) => {
    if (tab === 'documents') void loadDocuments();
    if (tab === 'members') void loadMembers();
    if (tab === 'rag') void loadRag();
  },
);

onMounted(async () => {
  await loadKb();
  await loadDocuments();
  startPolling();
});

onUnmounted(() => stopPolling());
</script>

<template>
  <Page :title="title" content-class="p-0">
    <template #description>
      <span class="text-muted-foreground">{{ kb?.description || '—' }}</span>
    </template>
    <template #extra>
      <ElButton @click="router.push({ name: 'KnowledgeList' })">返回列表</ElButton>
    </template>

    <div v-loading="loading" class="px-4 pb-4">
      <div v-if="kb" class="mb-4 flex flex-wrap gap-2">
        <ElTag size="small">{{ kb.visibility === 'SPACE' ? '空间' : '私有' }}</ElTag>
        <ElTag size="small" :type="kb.status === 'ACTIVE' ? 'success' : 'info'">
          {{ kb.status === 'ACTIVE' ? '正常' : '已归档' }}
        </ElTag>
      </div>

      <ElTabs v-model="activeTab">
        <ElTabPane label="概览" name="overview">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div class="rounded border p-4">
              <div class="text-muted-foreground text-sm">文档数量</div>
              <div class="mt-2 text-2xl font-semibold">{{ documents.length }}</div>
            </div>
            <div class="rounded border p-4">
              <div class="text-muted-foreground text-sm">已就绪</div>
              <div class="mt-2 text-2xl font-semibold">
                {{ documents.filter((d) => d.status === 'READY').length }}
              </div>
            </div>
            <div class="rounded border p-4">
              <div class="text-muted-foreground text-sm">解析失败</div>
              <div class="mt-2 text-2xl font-semibold">
                {{ documents.filter((d) => d.status === 'FAILED').length }}
              </div>
            </div>
          </div>
          <div class="text-muted-foreground mt-6 text-sm">
            创建人：{{ kb?.created_by || '—' }} · 更新时间：{{ kb?.updated_at || '—' }}
          </div>
        </ElTabPane>

        <ElTabPane label="文档" name="documents">
          <div class="mb-3 flex items-center justify-between">
            <div class="text-muted-foreground text-sm">
              支持 PDF / DOCX / TXT / MD，单文件最大 20MB
            </div>
            <ElButton type="primary" @click="uploadVisible = true">上传文档</ElButton>
          </div>

          <ElTable v-loading="docsLoading" :data="documents" stripe>
            <ElTableColumn prop="file_name" label="文件名" min-width="200" />
            <ElTableColumn prop="file_type" label="类型" width="90" />
            <ElTableColumn label="大小" width="100">
              <template #default="{ row }">
                {{ formatSize(row.file_size) }}
              </template>
            </ElTableColumn>
            <ElTableColumn label="状态" width="120">
              <template #default="{ row }">
                <ElTag :type="statusMeta(row.status).type" size="small">
                  {{ statusMeta(row.status).label }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="updated_at" label="更新时间" min-width="180" />
            <ElTableColumn label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <ElSpace>
                  <ElButton
                    v-if="row.status === 'FAILED'"
                    link
                    type="warning"
                    @click="showFailReason(row)"
                  >
                    原因
                  </ElButton>
                  <ElButton
                    v-if="row.status === 'FAILED' || row.status === 'UPLOADED'"
                    link
                    type="primary"
                    @click="onRetry(row)"
                  >
                    重试
                  </ElButton>
                  <ElButton link type="danger" @click="onDeleteDoc(row)">
                    删除
                  </ElButton>
                </ElSpace>
              </template>
            </ElTableColumn>
          </ElTable>

          <div
            v-if="!docsLoading && documents.length === 0"
            class="text-muted-foreground py-12 text-center text-sm"
          >
            当前知识库还没有文档。支持 PDF / DOCX / TXT / MD。
          </div>
        </ElTabPane>

        <ElTabPane label="成员与权限" name="members">
          <ElTable :data="members" stripe>
            <ElTableColumn prop="user_id" label="用户 ID" min-width="260" />
            <ElTableColumn prop="role" label="权限" width="120" />
            <ElTableColumn prop="created_at" label="加入时间" min-width="180" />
          </ElTable>
        </ElTabPane>

        <ElTabPane label="RAG 配置" name="rag">
          <div v-if="rag" class="max-w-xl space-y-2 text-sm">
            <div>Chunk 策略：{{ rag.chunk_strategy }}</div>
            <div>Chunk Size：{{ rag.chunk_size }}</div>
            <div>Chunk Overlap：{{ rag.chunk_overlap }}</div>
            <div>Top K：{{ rag.top_k }}</div>
            <div>Temperature：{{ rag.temperature }}</div>
            <div class="text-muted-foreground pt-2">
              一期先只读展示；编辑表单后续迭代。
            </div>
          </div>
          <div v-else class="text-muted-foreground text-sm">暂无配置</div>
        </ElTabPane>
      </ElTabs>
    </div>

    <ElDialog v-model="uploadVisible" title="上传文档" width="480px">
      <ElUpload
        v-model:file-list="fileList"
        :auto-upload="false"
        :limit="1"
        drag
        accept=".pdf,.docx,.txt,.md,.markdown"
      >
        <div class="py-6 text-center">
          <div>拖拽文件到这里，或点击选择</div>
          <div class="text-muted-foreground mt-2 text-xs">
            PDF / DOCX / TXT / MD，单文件 ≤ 20MB
          </div>
        </div>
      </ElUpload>
      <template #footer>
        <ElSpace>
          <ElButton @click="uploadVisible = false">取消</ElButton>
          <ElButton type="primary" :loading="uploading" @click="onUpload">
            开始上传
          </ElButton>
        </ElSpace>
      </template>
    </ElDialog>
  </Page>
</template>
