<script lang="ts" setup>
import type { FormInstance, FormRules, UploadUserFile } from 'element-plus';

import type { DocumentItem } from '#/types/document';
import type {
  KnowledgeBase,
  KbMember,
  KbMemberRole,
  RagConfig,
} from '#/types/knowledge';

import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
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
  addKbMemberApi,
  getKnowledgeBaseApi,
  getRagConfigApi,
  listKbMembersApi,
  removeKbMemberApi,
  updateRagConfigApi,
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

const memberDialogVisible = ref(false);
const memberSaving = ref(false);
const memberFormRef = ref<FormInstance>();
const memberForm = reactive({
  user_id: '',
  role: 'VIEWER' as KbMemberRole,
});
const memberRules: FormRules = {
  user_id: [{ required: true, message: '请输入用户 ID', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
};

const ragFormRef = ref<FormInstance>();
const ragSaving = ref(false);
const ragForm = reactive({
  chunk_strategy: 'recursive',
  chunk_size: 800,
  chunk_overlap: 120,
  top_k: 5,
  score_threshold: null as null | number,
  llm_model: '' as string,
  temperature: 0.2,
  system_prompt: '' as string,
});
const ragRules: FormRules = {
  chunk_size: [{ required: true, message: '必填', trigger: 'blur' }],
  chunk_overlap: [{ required: true, message: '必填', trigger: 'blur' }],
  top_k: [{ required: true, message: '必填', trigger: 'blur' }],
  temperature: [{ required: true, message: '必填', trigger: 'blur' }],
};

const title = computed(() => kb.value?.name || '知识库详情');

const roleLabel: Record<KbMemberRole, string> = {
  OWNER: '所有者',
  EDITOR: '编辑者',
  VIEWER: '查看者',
};

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

function applyRagToForm(config: RagConfig) {
  ragForm.chunk_strategy = config.chunk_strategy || 'recursive';
  ragForm.chunk_size = config.chunk_size;
  ragForm.chunk_overlap = config.chunk_overlap;
  ragForm.top_k = config.top_k;
  ragForm.score_threshold = config.score_threshold;
  ragForm.llm_model = config.llm_model || '';
  ragForm.temperature = config.temperature;
  ragForm.system_prompt = config.system_prompt || '';
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
    if (rag.value) applyRagToForm(rag.value);
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

function openAddMember() {
  memberForm.user_id = '';
  memberForm.role = 'VIEWER';
  memberDialogVisible.value = true;
}

async function submitAddMember() {
  const valid = await memberFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  memberSaving.value = true;
  try {
    await addKbMemberApi(kbId.value, {
      user_id: memberForm.user_id.trim(),
      role: memberForm.role,
    });
    ElMessage.success('成员已添加');
    memberDialogVisible.value = false;
    await loadMembers();
  } catch {
    // interceptor
  } finally {
    memberSaving.value = false;
  }
}

async function onRemoveMember(row: KbMember) {
  try {
    await ElMessageBox.confirm(
      `移除成员「${row.user_id}」？\n移除后对方将无法访问此知识库。`,
      '移除确认',
      { type: 'warning' },
    );
  } catch {
    return;
  }
  try {
    await removeKbMemberApi(kbId.value, row.user_id);
    ElMessage.success('已移除');
    await loadMembers();
  } catch {
    // interceptor
  }
}

async function saveRag() {
  const valid = await ragFormRef.value?.validate().catch(() => false);
  if (!valid) return;
  ragSaving.value = true;
  try {
    rag.value = await updateRagConfigApi(kbId.value, {
      chunk_strategy: ragForm.chunk_strategy,
      chunk_size: ragForm.chunk_size,
      chunk_overlap: ragForm.chunk_overlap,
      top_k: ragForm.top_k,
      score_threshold: ragForm.score_threshold,
      llm_model: ragForm.llm_model || null,
      temperature: ragForm.temperature,
      system_prompt: ragForm.system_prompt || null,
    });
    if (rag.value) applyRagToForm(rag.value);
    ElMessage.success('RAG 配置已保存');
  } catch {
    // interceptor
  } finally {
    ragSaving.value = false;
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
          <div class="mb-3 flex items-center justify-between gap-3">
            <div class="text-muted-foreground text-sm">
              OWNER 可管理成员；EDITOR 可编辑；VIEWER 只读。一期暂无用户搜索，请填写用户
              UUID。
            </div>
            <ElButton type="primary" @click="openAddMember">添加成员</ElButton>
          </div>
          <ElTable :data="members" stripe>
            <ElTableColumn prop="user_id" label="用户 ID" min-width="260" />
            <ElTableColumn label="权限" width="120">
              <template #default="{ row }">
                {{ roleLabel[row.role as KbMemberRole] || row.role }}
              </template>
            </ElTableColumn>
            <ElTableColumn prop="created_at" label="加入时间" min-width="180" />
            <ElTableColumn label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <ElButton link type="danger" @click="onRemoveMember(row)">
                  移除
                </ElButton>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElTabPane>

        <ElTabPane label="RAG 配置" name="rag">
          <ElForm
            v-if="rag"
            ref="ragFormRef"
            :model="ragForm"
            :rules="ragRules"
            label-position="top"
            class="max-w-xl"
          >
            <ElFormItem label="Chunk 策略" prop="chunk_strategy">
              <ElInput v-model="ragForm.chunk_strategy" />
            </ElFormItem>
            <div class="grid grid-cols-1 gap-2 md:grid-cols-2">
              <ElFormItem label="Chunk Size (100–8000)" prop="chunk_size">
                <ElInputNumber
                  v-model="ragForm.chunk_size"
                  :min="100"
                  :max="8000"
                  class="w-full"
                />
              </ElFormItem>
              <ElFormItem label="Chunk Overlap (0–4000)" prop="chunk_overlap">
                <ElInputNumber
                  v-model="ragForm.chunk_overlap"
                  :min="0"
                  :max="4000"
                  class="w-full"
                />
              </ElFormItem>
              <ElFormItem label="Top K (1–50)" prop="top_k">
                <ElInputNumber
                  v-model="ragForm.top_k"
                  :min="1"
                  :max="50"
                  class="w-full"
                />
              </ElFormItem>
              <ElFormItem label="Temperature (0–2)" prop="temperature">
                <ElInputNumber
                  v-model="ragForm.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  class="w-full"
                />
              </ElFormItem>
            </div>
            <ElFormItem label="Score Threshold（可选）">
              <ElInputNumber
                v-model="ragForm.score_threshold"
                :min="0"
                :max="1"
                :step="0.05"
                clearable
                class="w-full"
              />
            </ElFormItem>
            <ElFormItem label="LLM Model（可选）">
              <ElInput v-model="ragForm.llm_model" placeholder="留空使用系统默认" />
            </ElFormItem>
            <ElFormItem label="System Prompt（可选）">
              <ElInput
                v-model="ragForm.system_prompt"
                type="textarea"
                :rows="4"
                placeholder="可选系统提示词"
              />
            </ElFormItem>
            <ElButton type="primary" :loading="ragSaving" @click="saveRag">
              保存配置
            </ElButton>
          </ElForm>
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

    <ElDialog v-model="memberDialogVisible" title="添加成员" width="440px">
      <ElForm
        ref="memberFormRef"
        :model="memberForm"
        :rules="memberRules"
        label-position="top"
      >
        <ElFormItem label="用户 ID（UUID）" prop="user_id">
          <ElInput
            v-model="memberForm.user_id"
            placeholder="例如从 /auth/me 获取的 id"
          />
        </ElFormItem>
        <ElFormItem label="角色" prop="role">
          <ElSelect v-model="memberForm.role" class="w-full">
            <ElOption label="所有者 OWNER" value="OWNER" />
            <ElOption label="编辑者 EDITOR" value="EDITOR" />
            <ElOption label="查看者 VIEWER" value="VIEWER" />
          </ElSelect>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElSpace>
          <ElButton @click="memberDialogVisible = false">取消</ElButton>
          <ElButton
            type="primary"
            :loading="memberSaving"
            @click="submitAddMember"
          >
            添加
          </ElButton>
        </ElSpace>
      </template>
    </ElDialog>
  </Page>
</template>
