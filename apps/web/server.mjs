import { createReadStream, existsSync, statSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, resolve, sep } from 'node:path'

const root = resolve(import.meta.dirname, 'dist')
const port = Number(process.env.PORT || 4173)
const sandboxUrl = process.env.RESEARCH_API_URL || 'http://127.0.0.1:8765'
const types = { '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml' }

function sendJson(response, status, value) {
  const body = JSON.stringify(value)
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(body), 'Cache-Control': 'no-store' })
  response.end(body)
}

async function proxyResearch(request, response) {
  const chunks = []; let size = 0
  for await (const chunk of request) { size += chunk.length; if (size > 32 * 1024) return sendJson(response, 413, { error: { message: 'リクエストが大きすぎます。' } }); chunks.push(chunk) }
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 18_000)
  try {
    const upstream = await fetch(`${sandboxUrl}/v1/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: Buffer.concat(chunks), signal: controller.signal })
    const body = await upstream.text()
    response.writeHead(upstream.status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); response.end(body)
  } catch (error) {
    sendJson(response, error.name === 'AbortError' ? 504 : 502, { error: { code: error.name === 'AbortError' ? 'timeout' : 'upstream_unavailable', message: error.name === 'AbortError' ? '検索がタイムアウトしました。' : '検索サービスへ接続できません。' } })
  } finally { clearTimeout(timer) }
}

createServer(async (request, response) => {
  const url = new URL(request.url, 'http://local')
  if (url.pathname === '/api/research/query' && request.method === 'POST') return proxyResearch(request, response)
  if (!['GET', 'HEAD'].includes(request.method)) return sendJson(response, 405, { error: { message: 'Method not allowed' } })
  let path = resolve(root, `.${decodeURIComponent(url.pathname)}`)
  if (!path.startsWith(root + sep) && path !== root) return sendJson(response, 400, { error: { message: 'Invalid path' } })
  if (!existsSync(path) || statSync(path).isDirectory()) path = resolve(root, 'index.html')
  response.writeHead(200, { 'Content-Type': types[extname(path)] || 'application/octet-stream', 'X-Content-Type-Options': 'nosniff' })
  if (request.method === 'HEAD') response.end(); else createReadStream(path).pipe(response)
}).listen(port, '127.0.0.1', () => console.log(`my-app listening on http://127.0.0.1:${port}`))
