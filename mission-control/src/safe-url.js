export function safeExternalHref(value) {
  if (typeof value !== 'string' || !/^https?:\/\//i.test(value) || /[\u0000-\u001f\u007f]/.test(value)) return null;
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null;
    return url.href;
  } catch {
    return null;
  }
}
