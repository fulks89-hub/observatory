import assert from 'node:assert/strict';
import test from 'node:test';
import { attachEvaluations, stableBookmarkId, stableTopicId } from '../scripts/ai-evaluation-contract.mjs';

test('stable identifiers ignore ordering noise and remain non-secret hashes', () => {
  const trend = { title: 'Example', signals: [{ url: 'https://b.test' }, { url: 'https://a.test' }] };
  assert.equal(stableTopicId(trend), stableTopicId({ ...trend, signals: [...trend.signals].reverse() }));
  assert.match(stableBookmarkId({ url: 'https://x.com/example/status/1' }), /^bookmark-[a-f0-9]{20}$/);
});

test('only exact matching evaluations attach to cards', () => {
  const trend = { title: 'Example', signals: [{ url: 'https://example.test' }] };
  const id = stableTopicId(trend);
  const report = attachEvaluations({ trends: [trend, { title: 'Other', signals: [] }] }, { topic_evaluations: [{ id, tldr: 'Evaluated' }] });
  assert.equal(report.trends[0].ai_evaluation.tldr, 'Evaluated');
  assert.equal(report.trends[1].ai_evaluation, null);
});
