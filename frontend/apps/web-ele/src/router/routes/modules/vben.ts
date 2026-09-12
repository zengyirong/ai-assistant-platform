import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

/** Keep profile only — remove Vben promo / about / other UI previews. */
const routes: RouteRecordRaw[] = [
  {
    name: 'Profile',
    path: '/profile',
    component: () => import('#/views/_core/profile/index.vue'),
    meta: {
      icon: 'lucide:user',
      hideInMenu: true,
      title: $t('page.auth.profile'),
    },
  },
];

export default routes;
