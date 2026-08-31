import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs'

const fixture = process.env.LINEAR_ALGEBRA_PDF || ''

test('実PDFからメタデータ・432ページ・アウトラインと遷移先を取得する', { skip: !existsSync(fixture) }, async () => {
  const data = new Uint8Array(readFileSync(fixture))
  const hash = createHash('sha256').update(data).digest('hex')
  const task = getDocument({ data, disableWorker: true })
  const pdf = await task.promise
  const metadata = await pdf.getMetadata()
  const outline = await pdf.getOutline()
  assert.equal(pdf.numPages, 432)
  assert.equal(metadata.info.Title, '線形代数学入門')
  assert.equal(metadata.info.Author, '黒田紘敏')
  assert.ok(outline.length > 0)
  const firstDestination = typeof outline[0].dest === 'string' ? await pdf.getDestination(outline[0].dest) : outline[0].dest
  assert.ok((await pdf.getPageIndex(firstDestination[0])) >= 0)
  assert.equal(hash, 'b73df53a7a4bcb9c255c3f7eabd6ea2594db9f734d3351b8dc21a6cb1689c073')
  await task.destroy()
})
