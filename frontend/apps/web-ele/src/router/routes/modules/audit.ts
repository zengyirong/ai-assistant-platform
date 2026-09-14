import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      authority: ['ADMIN'],
      icon: 'lucide:scroll-text',
      order: 40,
      title: '审计日志',
    },
    name: 'Audit',
    path: '/audit',
    redirect: '/audit/list',
    children: [
      {
        name: 'AuditLogList',
        path: 'list',
        component: () => import('#/views/audit/list.vue'),
        meta: {
          authority: ['ADMIN'],
          icon: 'lucide:list',
          title: '操作记录',
        },
      },
    ],
  },
];

export default routes;
