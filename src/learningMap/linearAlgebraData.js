const source = (page, section) => ({
  pdfTitle: '線形代数学入門', pdfPage: page, section,
  extractionSource: 'PDF内部アウトライン＋対象ページの目視確認', confidence: 'high',
  confirmationStatus: 'unconfirmed',
})

const node = (id, title, type, page, section, prerequisiteIds, options = {}) => ({
  id, title, canonicalName: options.canonicalName ?? title, aliases: options.aliases ?? [], type, prerequisiteIds, status: 'notStarted', notes: '', references: '', checklist: {}, proofSteps: [], resolvedReviewIds: [],
  reason: options.reason ?? `${title}を後続概念の前提として用いるため。`,
  relation: options.relation ?? '実対称行列の直交対角化を構成するための前提。',
  level: options.level ?? '定義と標準例を扱える',
  completion: options.completion ?? `${title}の定義または役割を説明できる。`,
  importance: options.importance ?? 'required', included: true, generationRationale: options.rationale ?? `${section}がPDFアウトラインに掲載されているため。`,
  sourcePages: [page], sourceSections: [section], ...source(page, section),
})

export const LINEAR_ALGEBRA_PDF = {
  fileName: 'text_linear_algebra.pdf', title: '線形代数学入門', author: '黒田紘敏', pageCount: 432,
  outlineAvailable: true, fileSize: 1715219,
  warnings: ['本文の通常テキスト抽出では日本語の文字化けを確認しました。概念名は本文の壊れた文字列から確定せず、内部アウトラインと対象ページを使用しています。'],
  outline: [
    { title: '第2章 行列の定義とその演算', page: 25, children: ['3 行列の積 (p.32)', '4 正則行列 (p.48)'] },
    { title: '第8章 ベクトル空間に関する基本的概念', page: 190, children: ['2 ベクトル空間 (p.195)', '3 ベクトルの1次独立性 (p.208)', '4 基底と次元 (p.216)'] },
    { title: '第9章 線形写像', page: 254, children: ['2 線形写像の定義と性質 (p.258)', '5 線形写像の表現行列 (p.280)'] },
    { title: '第10章 行列の対角化', page: 299, children: ['1 固有値と固有ベクトル (p.299)', '2 行列の対角化 (p.313)'] },
    { title: '第11章 ベクトル空間と内積', page: 351, children: ['1 実計量ベクトル空間 (p.351)', '4 正規直交基底・グラム・シュミット (p.375)', '5 直交行列 (p.392)'] },
    { title: '第12章 実対称行列の対角化と2次形式', page: 404, children: ['1.1 実対称行列の固有値・固有ベクトル (p.404)', '1.2 直交行列による対角化の計算例 (p.407)'] },
  ],
}

export const LINEAR_ALGEBRA_NODES = [
  node('matrix-product', '行列の積', 'definition', 32, '第2章 3.1 行列の積の定義', [], { importance: 'supporting', relation: '基底変換式と P⁻¹AP の計算に使用する。' }),
  node('invertible', '正則行列と逆行列', 'definition', 48, '第2章 4.1 正則性と逆行列', ['matrix-product'], { importance: 'recommended', relation: '対角化を P⁻¹AP と表すために必要。' }),
  node('vector-space', 'ベクトル空間', 'definition', 195, '第8章 2.1 ベクトル空間の定義', [], { relation: '固有空間と内積空間を扱う基礎。' }),
  node('subspace', '部分空間', 'definition', 202, '第8章 2.3 部分空間', ['vector-space'], { relation: '固有空間が部分空間であることを理解する。' }),
  node('independence', '一次独立', 'definition', 208, '第8章 3.1 1次独立と1次従属', ['vector-space'], { relation: '固有ベクトルから基底を作れる条件。' }),
  node('basis-dimension', '基底と次元', 'definition', 216, '第8章 4.1 基底の定義と性質', ['independence', 'subspace'], { relation: '固有空間ごとの基底を全空間の基底へ組み立てる。' }),
  node('linear-map', '線形写像', 'definition', 258, '第9章 2.1 線形写像の定義と例', ['vector-space'], { importance: 'recommended', relation: '行列を線形変換として捉える。' }),
  node('representation', '表現行列', 'definition', 280, '第9章 5.1 表現行列の定義と計算例', ['basis-dimension', 'linear-map'], { importance: 'recommended', relation: '基底の選択と行列表示の関係を理解する。' }),
  node('basis-change', '基底変換と表現行列', 'concept', 293, '第9章 5.4 基底の変換行列', ['representation', 'invertible'], { relation: '固有ベクトル基底への変換が対角化を与える。' }),
  node('eigenvalue-vector', '固有値と固有ベクトル', 'definition', 299, '第10章 1.1 固有値と固有ベクトルの定義', ['matrix-product', 'linear-map'], { relation: '対角成分と変換行列の列を構成する。' }),
  node('eigenspace', '固有空間', 'definition', 306, '第10章 1.2 固有空間', ['eigenvalue-vector', 'subspace'], { relation: '重複固有値に対して必要な基底を選ぶ。' }),
  node('diagonalization', '行列の対角化', 'definition', 313, '第10章 2.1 対角化の定義', ['basis-change', 'eigenvalue-vector', 'eigenspace'], { relation: '目標の「直交」対角化の基礎となる構成。' }),
  node('diagonalizable-condition', '対角化可能性の条件', 'theorem', 314, '第10章 2.2 対角化可能であるための必要十分条件', ['diagonalization', 'basis-dimension'], { relation: '固有ベクトル基底の存在と対角化を結ぶ。', level: '証明の要点を追える' }),
  node('inner-product', '実ベクトル空間の内積', 'definition', 351, '第11章 1.1 実ベクトル空間の内積', ['vector-space'], { relation: '直交性と長さを定義する。' }),
  node('orthogonality', 'ベクトルの直交性', 'definition', 358, '第11章 1.2 ベクトルの直交性', ['inner-product'], { relation: '異なる固有値の固有ベクトル間の関係を記述する。' }),
  node('orthonormal-basis', '正規直交基底', 'definition', 375, '第11章 4.1 正規直交基底', ['orthogonality', 'basis-dimension'], { relation: '直交行列の列となる固有ベクトル基底。' }),
  node('gram-schmidt', 'グラム・シュミットの直交化法', 'theorem', 378, '第11章 4.2 グラム・シュミットの直交化法', ['orthonormal-basis', 'independence'], { importance: 'recommended', relation: '同一固有空間内で正規直交基底を作る。', level: '構成を自力で再現できる' }),
  node('orthogonal-matrix', '直交行列', 'definition', 392, '第11章 5.1 直交行列', ['matrix-product', 'orthonormal-basis'], { relation: '正規直交固有ベクトルを列に並べた変換行列。' }),
  node('symmetric-matrix', '実対称行列', 'definition', 404, '第12章 1.1 実対称行列の固有値・固有ベクトル', ['matrix-product'], { relation: '直交対角化定理の対象となる行列。' }),
  node('real-eigenvalues', '実対称行列の固有値は実数', 'theorem', 404, '第12章 定理1.2 固有値', ['symmetric-matrix', 'eigenvalue-vector', 'inner-product'], { relation: '実数空間内で固有ベクトル基底を構成できることを支える。', level: '証明の要点を追える' }),
  node('orthogonal-eigenvectors', '異なる固有値の固有ベクトルは直交', 'theorem', 405, '第12章 定理1.4 直交性', ['symmetric-matrix', 'orthogonality', 'eigenvalue-vector'], { relation: '異なる固有空間から選んだ基底が相互に直交する。', level: '証明の要点を追える' }),
  node('orthogonal-diagonalization', '実対称行列の直交対角化', 'goal', 406, '第12章 定理1.6 対角化可能性', ['real-eigenvalues', 'orthogonal-eigenvectors', 'gram-schmidt', 'orthogonal-matrix', 'diagonalizable-condition'], { relation: '今回の到達目標。', level: '構成を自力で再現できる', completion: '実対称行列について直交行列 P により P⁻¹AP が対角行列になる構成と根拠を説明できる。', rationale: '第12章 定理1.6とp.407以降の計算例を到達点として確認したため。' }),
]

export const EDGE_TYPES = ['定義の理解に必要', '定理の主張に必要', '証明で使用', '計算に必要', '理解を助ける補助', '今回の目標では省略可能', '文書構造上の親子']

function inferEdgeType(fromId, toNode) {
  if (['matrix-product', 'invertible', 'basis-change'].includes(fromId)) return '計算に必要'
  if (toNode.type === 'theorem' || toNode.type === 'goal') return '証明で使用'
  return '定義の理解に必要'
}

export const LINEAR_ALGEBRA_EDGES = LINEAR_ALGEBRA_NODES.flatMap((target) => target.prerequisiteIds.map((sourceId) => ({
  id: `${sourceId}--${target.id}`, sourceId, targetId: target.id, type: inferEdgeType(sourceId, target),
  rationale: `${target.title}の学習に${LINEAR_ALGEBRA_NODES.find((n) => n.id === sourceId)?.title}を使用する候補。`, confirmationStatus: 'unconfirmed',
})))

export function createLinearAlgebraCandidateMap(now = new Date().toISOString()) {
  return {
    id: `linear-algebra-${Date.now()}`, name: '実対称行列の直交対角化', goal: '実対称行列の直交対角化を理解する',
    sourceType: 'pdf-reviewed-candidate', sourceLabel: 'PDF抽出候補（レビュー済み初期データ）', pdf: structuredClone(LINEAR_ALGEBRA_PDF),
    nodes: structuredClone(LINEAR_ALGEBRA_NODES), edges: structuredClone(LINEAR_ALGEBRA_EDGES), createdAt: now, updatedAt: now, candidateStatus: 'review',
  }
}
