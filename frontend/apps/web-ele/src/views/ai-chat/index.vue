<script lang="ts" setup>
import { Page } from '@vben/common-ui';

import { ElButton } from 'element-plus';
import { useRouter } from 'vue-router';

defineOptions({ name: 'AiChatWorkspace' });

const router = useRouter();
</script>

<template>
  <Page
    title="智能问答"
    description="三栏布局（会话 / Chat / Citation）将按 Phase 0.5 实现；当前为占位。"
  >
    <div
      class="border-border grid min-h-[480px] grid-cols-1 overflow-hidden rounded border lg:grid-cols-[220px_1fr_260px]"
    >
      <aside class="border-border border-b p-4 lg:border-b-0 lg:border-r">
        <div class="mb-3 text-sm font-medium">会话</div>
        <ElButton class="w-full" type="primary" plain>+ 新会话</ElButton>
        <div class="text-muted-foreground mt-6 text-xs">会话列表即将接入</div>
      </aside>
      <main class="flex flex-col p-4">
        <div class="mb-3 text-sm">
          当前知识库：
          <ElButton
            link
            type="primary"
            @click="router.push({ name: 'KnowledgeList' })"
          >
            去选择知识库
          </ElButton>
        </div>
        <div
          class="text-muted-foreground flex flex-1 items-center justify-center text-sm"
        >
          开始你的第一次知识问答。请先创建知识库并上传文档。
        </div>
      </main>
      <aside class="border-border border-t p-4 lg:border-l lg:border-t-0">
        <div class="mb-3 text-sm font-medium">引用来源</div>
        <div class="text-muted-foreground text-xs">回答产生后在此展示 Citation</div>
      </aside>
    </div>
  </Page>
</template>
