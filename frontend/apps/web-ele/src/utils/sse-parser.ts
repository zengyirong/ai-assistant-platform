import type { SseEnvelope } from '#/types/sse';

/** Accumulates SSE text chunks and emits JSON envelopes from `data:` lines. */
export function createSseLineParser(
  onEvent: (envelope: SseEnvelope) => void,
) {
  let buffer = '';

  function consumeLine(line: string) {
    const trimmed = line.trimEnd();
    if (!trimmed.startsWith('data:')) return;
    const payload = trimmed.slice(5).trim();
    if (!payload || payload === '[DONE]') return;
    try {
      onEvent(JSON.parse(payload) as SseEnvelope);
    } catch {
      // ignore malformed chunk
    }
  }

  return {
    push(chunk: string) {
      buffer += chunk;
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        consumeLine(line);
      }
    },
    flush() {
      if (buffer.trim()) {
        consumeLine(buffer);
        buffer = '';
      }
    },
  };
}
