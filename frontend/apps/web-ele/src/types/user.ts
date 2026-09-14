/** Org user brief for member pickers */

export interface OrgUser {
  id: string;
  username: string;
  nickname: string | null;
  status: string;
}

export interface OrgUserPage {
  items: OrgUser[];
  total: number;
  page: number;
  page_size: number;
}
