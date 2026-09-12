import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: $t('page.dashboard.title'),
    },
    name: 'Dashboard',
    path: '/dashboard',
    redirect: '/dashboard/home',
    children: [
      {
        name: 'DashboardHome',
        path: 'home',
        component: () => import('#/views/dashboard/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:home',
          title: $t('page.dashboard.home'),
        },
      },
    ],
  },
];

export default routes;
