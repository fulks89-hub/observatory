import { createHash } from 'node:crypto';

function hash(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export function stableTopicId(trend) {
  const sources = (trend.signals || []).map((signal) => signal.url || '').filter(Boolean).sort();
  return `topic-${hash([trend.title || '', sources]).slice(0, 20)}`;
}

export function stableBookmarkId(bookmark) {
  return `bookmark-${hash(bookmark.id || bookmark.url || [bookmark.author_username, bookmark.created_at, bookmark.text]).slice(0, 20)}`;
}

export function attachEvaluations(report, evaluation) {
  const byId = new Map((evaluation?.topic_evaluations || []).map((item) => [item.id, item]));
  return {
    ...report,
    trends: (report?.trends || []).map((trend) => {
      const id = stableTopicId(trend);
      return { ...trend, ai_evaluation_id: id, ai_evaluation: byId.get(id) || null };
    }),
  };
}
