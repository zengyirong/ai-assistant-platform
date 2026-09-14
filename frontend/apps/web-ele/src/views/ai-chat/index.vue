<script lang="ts" setup>
import type { KnowledgeBase } from '#/types/knowledge';
import type { ChatMessage, Conversation } from '#/types/conversation';
import type {
  SseCitationData,
  SseCitationItem,
  SseEnvelope,
  SseErrorData,
  SseTextData,
} from '#/types/sse';

import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  ElButton,
  ElDrawer,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElTag,
} from 'element-plus';

import {
  chatStreamApi,
  createConversationApi,
  deleteConversationApi,
  listConversationsApi,
  listMessagesApi,
} from '#/api/conversation';
import { listKnowledgeBasesApi } from '#/api/knowledge';

defineOptions({ name: 'AiChatWorkspace' });

type StreamState =
  | 'IDLE'
  | 'SENDING'
  | 'STREAMING'
  | 'COMPLETED'
  | 'ABORTED'
  | 'ERROR';

const conversations = ref<Conversation[]>([]);
const conversationsLoading = ref(false);
const activeConversationId = ref<string | null>(null);

const knowledgeBases = ref<KnowledgeBase[]>([]);
const selectedKbIds = ref<string[]>([]);

const messages = ref<ChatMessage[]>([]);
const messagesLoading = ref(false);
const citations = ref<SseCitationItem[]>([]);
const citationDrawerVisible = ref(false);

const question = ref('');
const streamState = ref<StreamState>('IDLE');
const streamError = ref('');
const abortController = ref<AbortController | null>(null);

const messageListRef = ref<HTMLElement | null>(null);

const isStreaming = computed(
  () => streamState.value === 'SENDING' || streamState.value === 'STREAMING',
);

const activeConversation = computed(() =>
  conversations.value.find((c) => c.id === activeConversationId.value),
);

const kbNameMap = computed(() => {
  const map = new Map<string, string>();
  for (const kb of knowledgeBases.value) {
    map.set(kb.id, kb.name);
  }
  return map;
});

function scrollToBottom() {
  void nextTick(() => {
    const el = messageListRef.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
}

async function loadKnowledgeBases() {
  try {
    const data = await listKnowledgeBasesApi({ page: 1, page_size: 100 });
    knowledgeBases.value = (data.items ?? []).filter((k) => k.status === 'ACTIVE');
  } catch {
    knowledgeBases.value = [];
  }
}

async function loadConversations() {
  conversationsLoading.value = true;
  try {
    const data = await listConversationsApi({ page: 1, page_size: 50 });
    conversations.value = data.items ?? [];
  } catch {
    conversations.value = [];
  } finally {
    conversationsLoading.value = false;
  }
}

async function loadMessages(conversationId: string) {
  messagesLoading.value = true;
  streamError.value = '';
  try {
    const data = await listMessagesApi(conversationId, {
      page: 1,
      page_size: 100,
    });
    messages.value = data.items ?? [];
    const lastAssistant = [...messages.value]
      .reverse()
      .find((m) => m.role === 'ASSISTANT' && m.citations?.length);
    citations.value = lastAssistant?.citations ?? [];
    scrollToBottom();
  } catch {
    messages.value = [];
    citations.value = [];
  } finally {
    messagesLoading.value = false;
  }
}

async function selectConversation(id: string) {
  if (isStreaming.value) {
    ElMessage.warning('请先停止当前生成');
    return;
  }
  activeConversationId.value = id;
  const conv = conversations.value.find((c) => c.id === id);
  if (conv?.kb_scope?.length) {
    selectedKbIds.value = [...conv.kb_scope];
  }
  await loadMessages(id);
}

async function createConversation() {
  if (isStreaming.value) {
    ElMessage.warning('请先停止当前生成');
    return;
  }
  try {
    const conv = await createConversationApi({
      title: '新会话',
      kb_ids: selectedKbIds.value.length ? selectedKbIds.value : null,
    });
    conversations.value = [conv, ...conversations.value];
    activeConversationId.value = conv.id;
    messages.value = [];
    citations.value = [];
    streamState.value = 'IDLE';
    ElMessage.success('已创建新会话');
  } catch {
    // interceptor
  }
}

async function removeConversation(conv: Conversation, e: Event) {
  e.stopPropagation();
  try {
    await ElMessageBox.confirm(`删除会话「${conv.title}」？`, '删除确认', {
      type: 'warning',
    });
  } catch {
    return;
  }
  try {
    await deleteConversationApi(conv.id);
    conversations.value = conversations.value.filter((c) => c.id !== conv.id);
    if (activeConversationId.value === conv.id) {
      activeConversationId.value = null;
      messages.value = [];
      citations.value = [];
    }
  } catch {
    // interceptor
  }
}

function stopStreaming() {
  abortController.value?.abort();
  abortController.value = null;
  streamState.value = 'ABORTED';
  const last = messages.value[messages.value.length - 1];
  if (last?.role === 'ASSISTANT' && last.status === 'GENERATING') {
    last.status = 'ABORTED';
  }
}

async function sendQuestion() {
  const text = question.value.trim();
  if (!text) return;
  if (isStreaming.value) return;

  let conversationId = activeConversationId.value;
  if (!conversationId) {
    try {
      const conv = await createConversationApi({
        title: text.slice(0, 40),
        kb_ids: selectedKbIds.value.length ? selectedKbIds.value : null,
      });
      conversations.value = [conv, ...conversations.value];
      conversationId = conv.id;
      activeConversationId.value = conv.id;
      messages.value = [];
    } catch {
      return;
    }
  }

  const tempUserId = `local-user-${Date.now()}`;
  const tempAssistantId = `local-assistant-${Date.now()}`;

  messages.value.push({
    id: tempUserId,
    conversation_id: conversationId,
    role: 'USER',
    content: text,
    status: 'COMPLETED',
    request_id: null,
    citations: [],
    created_at: new Date().toISOString(),
  });
  messages.value.push({
    id: tempAssistantId,
    conversation_id: conversationId,
    role: 'ASSISTANT',
    content: '',
    status: 'GENERATING',
    request_id: null,
    citations: [],
    created_at: new Date().toISOString(),
  });
  question.value = '';
  citations.value = [];
  streamError.value = '';
  streamState.value = 'SENDING';
  scrollToBottom();

  const controller = new AbortController();
  abortController.value = controller;

  const assistant = () =>
    messages.value.find((m) => m.id === tempAssistantId) ||
    messages.value[messages.value.length - 1];

  try {
    await chatStreamApi(
      {
        conversation_id: conversationId,
        question: text,
        kb_ids: selectedKbIds.value.length ? selectedKbIds.value : null,
      },
      {
        signal: controller.signal,
        onEvent: (envelope: SseEnvelope) => {
          const msg = assistant();
          if (!msg || msg.role !== 'ASSISTANT') return;

          if (envelope.message_id && msg.id.startsWith('local-')) {
            msg.id = envelope.message_id;
          }
          msg.request_id = envelope.request_id;

          switch (envelope.event) {
            case 'start': {
              streamState.value = 'STREAMING';
              msg.status = 'GENERATING';
              break;
            }
            case 'citation': {
              const data = envelope.data as SseCitationData;
              const list = data?.citations ?? [];
              msg.citations = list;
              citations.value = list;
              break;
            }
            case 'text': {
              streamState.value = 'STREAMING';
              const data = envelope.data as SseTextData;
              msg.content += data?.content ?? '';
              scrollToBottom();
              break;
            }
            case 'done': {
              streamState.value = 'COMPLETED';
              msg.status = 'COMPLETED';
              break;
            }
            case 'error': {
              const data = envelope.data as SseErrorData;
              streamState.value = 'ERROR';
              streamError.value = data?.message || data?.code || '生成失败';
              msg.status = 'FAILED';
              if (!msg.content) {
                msg.content = streamError.value;
              }
              break;
            }
          }
        },
        onEnd: () => {
          if (streamState.value === 'STREAMING' || streamState.value === 'SENDING') {
            streamState.value = 'COMPLETED';
            const msg = assistant();
            if (msg && msg.status === 'GENERATING') {
              msg.status = 'COMPLETED';
            }
          }
          abortController.value = null;
          void loadConversations();
        },
      },
    );
  } catch (error: any) {
    if (controller.signal.aborted || error?.name === 'AbortError') {
      streamState.value = 'ABORTED';
    } else {
      streamState.value = 'ERROR';
      streamError.value = error?.message || '请求失败';
      const msg = assistant();
      if (msg && msg.role === 'ASSISTANT') {
        msg.status = 'FAILED';
        if (!msg.content) msg.content = streamError.value;
      }
      ElMessage.error(streamError.value);
    }
    abortController.value = null;
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    void sendQuestion();
  }
}

function focusCitations(msg: ChatMessage) {
  if (msg.role === 'ASSISTANT' && msg.citations?.length) {
    citations.value = msg.citations;
  }
}

onMounted(async () => {
  await Promise.all([loadKnowledgeBases(), loadConversations()]);
});

onUnmounted(() => {
  abortController.value?.abort();
});
</script>

<template>
  <Page title="智能问答" content-class="p-0">
    <div
      class="border-border grid min-h-[calc(100vh-180px)] grid-cols-1 overflow-hidden rounded border lg:grid-cols-[220px_1fr_280px]"
    >
      <!-- Sessions -->
      <aside class="border-border flex flex-col border-b lg:border-b-0 lg:border-r">
        <div class="border-border border-b p-3">
          <ElButton class="w-full" type="primary" @click="createConversation">
            + 新会话
          </ElButton>
        </div>
        <div v-loading="conversationsLoading" class="flex-1 overflow-y-auto p-2">
          <button
            v-for="conv in conversations"
            :key="conv.id"
            type="button"
            class="hover:bg-accent group mb-1 flex w-full items-start justify-between gap-2 rounded px-2 py-2 text-left text-sm"
            :class="
              activeConversationId === conv.id ? 'bg-accent font-medium' : ''
            "
            @click="selectConversation(conv.id)"
          >
            <span class="line-clamp-2 flex-1">{{ conv.title || '未命名会话' }}</span>
            <span
              class="text-muted-foreground hidden text-xs group-hover:inline"
              @click="removeConversation(conv, $event)"
            >
              删
            </span>
          </button>
          <div
            v-if="!conversationsLoading && conversations.length === 0"
            class="text-muted-foreground px-2 py-6 text-center text-xs"
          >
            暂无会话
          </div>
        </div>
      </aside>

      <!-- Chat -->
      <main class="flex min-h-[420px] flex-col">
        <div class="border-border flex flex-wrap items-center gap-2 border-b px-4 py-3">
          <span class="text-muted-foreground text-sm">知识库范围</span>
          <ElSelect
            v-model="selectedKbIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            clearable
            placeholder="不选则使用全部可访问知识库"
            style="min-width: 260px; max-width: 420px"
          >
            <ElOption
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </ElSelect>
          <div class="ml-auto flex gap-2 lg:hidden">
            <ElButton
              size="small"
              :disabled="citations.length === 0"
              @click="citationDrawerVisible = true"
            >
              引用来源 ({{ citations.length }})
            </ElButton>
          </div>
        </div>

        <div
          ref="messageListRef"
          v-loading="messagesLoading"
          class="flex-1 space-y-4 overflow-y-auto px-4 py-4"
        >
          <div
            v-if="messages.length === 0 && !messagesLoading"
            class="text-muted-foreground flex h-full min-h-[240px] items-center justify-center text-sm"
          >
            开始你的第一次知识问答。请先创建知识库并上传文档。
          </div>

          <div
            v-for="msg in messages"
            :key="msg.id"
            class="flex"
            :class="msg.role === 'USER' ? 'justify-end' : 'justify-start'"
            @click="focusCitations(msg)"
          >
            <div
              class="max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap"
              :class="
                msg.role === 'USER'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-accent'
              "
            >
              <div v-if="msg.role === 'ASSISTANT' && !msg.content && isStreaming">
                正在思考…
              </div>
              <div v-else>{{ msg.content }}</div>
              <div
                v-if="msg.role === 'ASSISTANT' && msg.status === 'FAILED'"
                class="mt-1 text-xs opacity-80"
              >
                生成失败，可重新提问。
              </div>
            </div>
          </div>
        </div>

        <div class="border-border border-t p-3">
          <div
            v-if="streamState === 'ERROR' && streamError"
            class="text-destructive mb-2 text-xs"
          >
            {{ streamError }}
          </div>
          <div class="flex gap-2">
            <textarea
              v-model="question"
              class="border-border bg-background min-h-[72px] flex-1 resize-none rounded border px-3 py-2 text-sm outline-none focus:ring-1"
              placeholder="输入问题，Enter 发送，Shift+Enter 换行"
              :disabled="isStreaming"
              @keydown="onKeydown"
            />
            <div class="flex flex-col gap-2">
              <ElButton
                v-if="!isStreaming"
                type="primary"
                :disabled="!question.trim()"
                @click="sendQuestion"
              >
                发送
              </ElButton>
              <ElButton v-else type="warning" @click="stopStreaming">停止</ElButton>
            </div>
          </div>
          <div class="text-muted-foreground mt-2 text-xs">
            当前会话：{{ activeConversation?.title || '未选择（发送时自动创建）' }}
            <template v-if="selectedKbIds.length">
              · 范围：
              <ElTag
                v-for="id in selectedKbIds"
                :key="id"
                size="small"
                class="ml-1"
              >
                {{ kbNameMap.get(id) || id.slice(0, 8) }}
              </ElTag>
            </template>
          </div>
        </div>
      </main>

      <!-- Citation panel (desktop) -->
      <aside
        class="border-border hidden flex-col border-l lg:flex"
      >
        <div class="border-border border-b px-4 py-3 text-sm font-medium">
          引用来源
          <span class="text-muted-foreground font-normal">
            ({{ citations.length }})
          </span>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3">
          <div
            v-if="citations.length === 0"
            class="text-muted-foreground py-8 text-center text-xs"
          >
            回答产生后在此展示 Citation
          </div>
          <div
            v-for="(c, idx) in citations"
            :key="`${c.chunk_id}-${idx}`"
            class="border-border rounded border p-3 text-xs"
          >
            <div class="mb-1 font-medium">
              [{{ idx + 1 }}]
              {{ c.document_name || `文档 ${c.document_id.slice(0, 8)}` }}
            </div>
            <div class="text-muted-foreground mb-2">
              <span v-if="c.page != null">第 {{ c.page }} 页</span>
              <span v-if="c.section"> · {{ c.section }}</span>
            </div>
            <div class="leading-relaxed whitespace-pre-wrap">
              {{ c.snippet || '无摘要' }}
            </div>
          </div>
        </div>
      </aside>
    </div>

    <ElDrawer
      v-model="citationDrawerVisible"
      title="引用来源"
      direction="rtl"
      size="85%"
    >
      <div class="space-y-3">
        <div
          v-for="(c, idx) in citations"
          :key="`m-${c.chunk_id}-${idx}`"
          class="border-border rounded border p-3 text-xs"
        >
          <div class="mb-1 font-medium">
            [{{ idx + 1 }}] {{ c.document_name || `文档 ${c.document_id.slice(0, 8)}` }}
          </div>
          <div class="text-muted-foreground mb-2">
            <span v-if="c.page != null">第 {{ c.page }} 页</span>
            <span v-if="c.section"> · {{ c.section }}</span>
          </div>
          <div class="whitespace-pre-wrap">{{ c.snippet || '无摘要' }}</div>
        </div>
      </div>
    </ElDrawer>
  </Page>
</template>
