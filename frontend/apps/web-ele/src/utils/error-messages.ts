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

export function resolveErrorMessage(
  code?: string | null,
  fallback?: string | null,
): string {
  // Prefer backend `message`: same code can mean different UX
  // (e.g. AUTH_UNAUTHORIZED = wrong password vs session expired).
  const text = fallback?.trim();
  if (text) {
    return text;
  }
  if (code && API_ERROR_MESSAGES[code]) {
    return API_ERROR_MESSAGES[code];
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
