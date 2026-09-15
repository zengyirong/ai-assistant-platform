import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:library',
      order: 10,
      title: $t('page.knowledge.title'),
    },
    name: 'Knowledge',
    path: '/knowledge',
    redirect: '/knowledge/list',
    children: [
      {
        name: 'KnowledgeList',
        path: 'list',
        component: () => import('#/views/knowledge/list.vue'),
        meta: {
          icon: 'lucide:folder-kanban',
          title: $t('page.knowledge.manage'),
        },
      },
      {
        name: 'KnowledgeDetail',
        path: 'detail/:kbId',
        component: () => import('#/views/knowledge/detail.vue'),
        meta: {
          hideInMenu: true,
          title: $t('page.knowledge.detail'),
        },
      },
    ],
  },
];

export default routes;
