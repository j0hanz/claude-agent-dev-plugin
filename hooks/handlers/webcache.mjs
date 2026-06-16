import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getProjectDir, debug } from '../io.mjs';

const CACHE_DIR = () => path.join(getProjectDir(), '.claude', 'webcache');

function hashUrl(url) {
  return crypto.createHash('sha256').update(url).digest('hex').slice(0, 32);
}

async function getCacheFile(url) {
  const hash = hashUrl(url);
  const filePath = path.join(CACHE_DIR(), `${hash}.json`);
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

async function writeCacheFile(url, data) {
  const hash = hashUrl(url);
  const cacheDir = CACHE_DIR();
  try {
    await fs.mkdir(cacheDir, { recursive: true });
    await fs.writeFile(path.join(cacheDir, `${hash}.json`), JSON.stringify(data, null, 2));
  } catch (err) {
    debug(`webcache: failed to write cache for ${url}: ${err.message}`);
  }
}

export async function check(input) {
  const url = input?.tool_input?.url;
  if (!url) return null;

  const cached = await getCacheFile(url);
  if (!cached) return null;

  const { etag, last_modified } = cached;
  if (!etag && !last_modified) return null;

  const headers = {};
  if (etag) headers['If-None-Match'] = etag;
  if (last_modified) headers['If-Modified-Since'] = last_modified;

  try {
    const response = await fetch(url, {
      method: 'HEAD',
      headers,
      signal: AbortSignal.timeout(4000),
    });

    if (response.status === 304) {
      const fetchedAt = new Date(cached.fetched_at).toISOString();
      return {
        decision: 'block',
        reason: `[webcache] Cache hit for ${url}\n\nRevalidated via HTTP 304; content unchanged since ${fetchedAt}.\n\n${cached.content}`,
      };
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      debug(`webcache check: timeout fetching ${url}`);
    } else {
      debug(`webcache check: error fetching ${url}: ${err.message}`);
    }
  }

  return null;
}

export async function store(input) {
  const url = input?.tool_input?.url;
  if (!url) return null;

  const content = input?.tool_response?.result ?? input?.tool_response;
  if (!content) return null;

  try {
    const response = await fetch(url, {
      method: 'HEAD',
      signal: AbortSignal.timeout(5000),
    });

    const etag = response.headers.get('ETag');
    const last_modified = response.headers.get('Last-Modified');

    if (!etag && !last_modified) {
      return null;
    }

    await writeCacheFile(url, {
      url,
      etag: etag || null,
      last_modified: last_modified || null,
      content: String(content),
      fetched_at: Date.now(),
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      debug(`webcache store: timeout fetching ${url}`);
    } else {
      debug(`webcache store: error storing cache for ${url}: ${err.message}`);
    }
  }

  return null;
}
