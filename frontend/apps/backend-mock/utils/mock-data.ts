export interface UserInfo {
  id: number;
  password: string;
  realName: string;
  roles: string[];
  username: string;
  homePath?: string;
}

export interface TimezoneOption {
  offset: number;
  timezone: string;
}

export const MOCK_USERS: UserInfo[] = [
  {
    id: 0,
    password: '123456',
    realName: 'Admin',
    roles: ['super'],
    username: 'vben',
    homePath: '/dashboard/home',
  },
  {
    id: 1,
    password: '123456',
    realName: 'Admin',
    roles: ['admin'],
    username: 'admin',
    homePath: '/dashboard/home',
  },
  {
    id: 2,
    password: '123456',
    realName: 'User',
    roles: ['user'],
    username: 'jack',
    homePath: '/dashboard/home',
  },
];

export const MOCK_CODES = [
  {
    codes: ['AC_100100', 'AC_100110', 'AC_100120', 'AC_100010'],
    username: 'vben',
  },
  {
    codes: ['AC_100010', 'AC_100020', 'AC_100030'],
    username: 'admin',
  },
  {
    codes: ['AC_1000001', 'AC_1000002'],
    username: 'jack',
  },
];

const dashboardMenus = [
  {
    meta: {
      order: -1,
      title: 'page.dashboard.title',
    },
    name: 'Dashboard',
    path: '/dashboard',
    redirect: '/dashboard/home',
    children: [
      {
        name: 'DashboardHome',
        path: 'home',
        component: '/dashboard/index',
        meta: {
          affixTab: true,
          title: 'page.dashboard.home',
        },
      },
    ],
  },
];

export const MOCK_MENUS = [
  {
    menus: [...dashboardMenus],
    username: 'vben',
  },
  {
    menus: [...dashboardMenus],
    username: 'admin',
  },
  {
    menus: [...dashboardMenus],
    username: 'jack',
  },
];

export const MOCK_MENU_LIST = [
  {
    id: 1,
    name: 'Dashboard',
    status: 1,
    type: 'catalog',
    icon: 'lucide:layout-dashboard',
    path: '/dashboard',
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: 'page.dashboard.title',
    },
    children: [
      {
        id: 101,
        pid: 1,
        status: 1,
        type: 'menu',
        name: 'DashboardHome',
        path: 'home',
        component: '/dashboard/index',
        meta: {
          affixTab: true,
          icon: 'lucide:home',
          title: 'page.dashboard.home',
          keepAlive: true,
        },
      },
    ],
  },
];

export function getMenuIds(menus: any[]) {
  const ids: number[] = [];
  menus.forEach((item) => {
    ids.push(item.id);
    if (item.children && item.children.length > 0) {
      ids.push(...getMenuIds(item.children));
    }
  });
  return ids;
}

/**
 * 时区选项
 */
export const TIME_ZONE_OPTIONS: TimezoneOption[] = [
  {
    offset: -5,
    timezone: 'America/New_York',
  },
  {
    offset: 0,
    timezone: 'Europe/London',
  },
  {
    offset: 8,
    timezone: 'Asia/Shanghai',
  },
  {
    offset: 9,
    timezone: 'Asia/Tokyo',
  },
  {
    offset: 10,
    timezone: 'Australia/Sydney',
  },
];
