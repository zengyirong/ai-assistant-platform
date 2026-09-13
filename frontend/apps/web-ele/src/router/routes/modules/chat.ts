import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:message-square-text',
      order: 5,
      title: $t('page.chat.title'),
    },
    name: 'AiChat',
    path: '/chat',
    redirect: '/chat/workspace',
    children: [
      {
        name: 'AiChatWorkspace',
        path: 'workspace',
        component: () => import('#/views/ai-chat/index.vue'),
        meta: {
          affixTab: false,
          icon: 'lucide:bot',
          title: $t('page.chat.workspace'),
        },
      },
    ],
  },
];

export default routes;
