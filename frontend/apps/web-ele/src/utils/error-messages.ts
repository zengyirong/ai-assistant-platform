/** Stable API error code → Chinese copy (docs/api.md Error Matrix). */

export const API_ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: '参数校验失败，请检查填写内容',
  AUTH_UNAUTHORIZED: '未登录或登录已过期，请重新登录',
  PERMISSION_DENIED: '权限不足，无法执行此操作',
  KB_PERMISSION_DENIED: '无权访问该知识库',
  KB_NOT_FOUND: '知识库不存在或不可见',
  DOCUMENT_NOT_FOUND: '文档不存在',
  SPACE_NOT_FOUND: '空间不存在',
  CONVERSATION_NOT_FOUND: '会话不存在',
  DOCUMENT_DUPLICATED: '同知识库已存在相同文件，请勿重复上传',
  SPACE_NAME_CONFLICT: '空间名称冲突',
  USER_NAME_CONFLICT: '用户名已存在',
  ROLE_CODE_CONFLICT: '角色编码已存在',
  PERMISSION_CODE_CONFLICT: '权限码已存在',
  USER_NOT_FOUND: '用户不存在',
  ROLE_NOT_FOUND: '角色不存在',
  PERMISSION_NOT_FOUND: '权限或菜单不存在',
  DOCUMENT_FORMAT_INVALID: '不支持的文件格式，请上传 PDF / DOCX / TXT / MD',
  DOCUMENT_TOO_LARGE: '文件过大，超出上传限制',
  DOCUMENT_PARSE_FAILED: '文档解析失败，请检查文件后重试',
  LLM_RATE_LIMIT: '模型调用过于频繁，请稍后重试',
  VECTOR_STORE_UNAVAILABLE: '向量库暂时不可用，请稍后重试',
  SERVICE_UNAVAILABLE: '服务依赖未就绪，请稍后重试',
  LLM_TIMEOUT: '模型响应超时，请稍后重试',
  INTERNAL_ERROR: '服务异常，请稍后重试',
  SSE_CLIENT_ABORTED: '生成已取消',
};

const JOB_STAGE_LABELS: Record<string, string> = {
  PENDING: '等待处理',
  RUNNING: '处理中',
  PARSING: '解析中',
  CHUNKING: '切片中',
  EMBEDDING: '向量化中',
  INDEXING: '写入索引',
  SUCCESS: '已完成',
  FAILED: '失败',
  CANCELLED: '已取消',
};

const FIELD_LABELS: Record<string, string> = {
  username: '用户名',
  password: '密码',
  nickname: '昵称',
  email: '邮箱',
  code: '编码',
  name: '名称',
  role_ids: '角色',
  permission_ids: '权限',
};

type ValidationDetail = {
  type?: string;
  loc?: Array<string | number>;
  msg?: string;
  ctx?: Record<string, unknown>;
};

function fieldLabel(loc?: Array<string | number>): string {
  if (!loc?.length) return '参数';
  const parts = loc.filter((p) => p !== 'body' && p !== 'query' && p !== 'path');
  const key = String(parts[parts.length - 1] ?? '参数');
  return FIELD_LABELS[key] || key;
}

/** Turn FastAPI / Pydantic `details[]` into a short Chinese sentence. */
export function formatValidationDetails(details: unknown): string | null {
  if (!Array.isArray(details) || details.length === 0) {
    return null;
  }
  const lines = (details as ValidationDetail[]).slice(0, 3).map((item) => {
    const label = fieldLabel(item.loc);
    const type = item.type || '';
    const ctx = item.ctx || {};
    if (type === 'string_too_short' && ctx.min_length != null) {
      return `${label}至少 ${ctx.min_length} 个字符`;
    }
    if (type === 'string_too_long' && ctx.max_length != null) {
      return `${label}最多 ${ctx.max_length} 个字符`;
    }
    if (type === 'missing') {
      return `${label}不能为空`;
    }
    if (type === 'value_error' || type.includes('enum')) {
      return `${label}取值无效`;
    }
    if (item.msg) {
      return `${label}：${item.msg}`;
    }
    return `${label}校验失败`;
  });
  return lines.join('；');
}

export function resolveErrorMessage(
  code?: string | null,
  fallback?: string | null,
  details?: unknown,
): string {
  const fromDetails = formatValidationDetails(details);
  if (fromDetails) {
    return fromDetails;
  }
  // Prefer backend `message`: same code can mean different UX
  // (e.g. AUTH_UNAUTHORIZED = wrong password vs session expired).
  const text = fallback?.trim();
  if (text && text !== '参数校验失败') {
    return text;
  }
  if (code && API_ERROR_MESSAGES[code]) {
    return API_ERROR_MESSAGES[code];
  }
  if (text) {
    return text;
  }
  if (code) {
    return code;
  }
  return '操作失败，请稍后重试';
}

export function jobStageLabel(status?: string | null): string {
  if (!status) return '';
  return JOB_STAGE_LABELS[status] || status;
}
