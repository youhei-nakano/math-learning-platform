const base = (node) => ({
  status: 'notStarted',
  notes: '',
  references: '',
  checklist: {},
  proofSteps: [],
  resolvedReviewIds: [],
  ...node,
})

export const DEMO_NODES = [
  base({ id: 'symplectic', title: 'シンプレクティック多様体', type: 'definition', reason: 'Floer理論の舞台となる幾何構造を定めるため。', relation: 'ラグランジュ部分多様体と擬正則曲線を記述する周囲空間。', level: '定義と標準例を扱える', completion: '閉じた非退化2形式の条件を説明し、標準例を1つ挙げられる。', prerequisiteIds: [], x: 60, y: 70, minimal: true, status: 'understood' }),
  base({ id: 'lagrangian', title: 'ラグランジュ部分多様体', type: 'definition', reason: 'Floer複体を定める2つの幾何学的対象だから。', relation: '交点が複体の生成元になる。', level: '定義と標準例を扱える', completion: '次元条件と形式の制限条件を説明できる。', prerequisiteIds: ['symplectic'], x: 300, y: 55, minimal: true, status: 'understood' }),
  base({ id: 'cotangent', title: '余接束の零切断', type: 'example', reason: 'ラグランジュ部分多様体の基本例で直感を得るため。', relation: '抽象的な定義を具体化する補助例。', level: '概要を説明できる', completion: '零切断がラグランジュになる理由を概説できる。', prerequisiteIds: ['lagrangian'], x: 545, y: 30, minimal: false }),
  base({ id: 'intersection', title: '横断的交点', type: 'concept', reason: '生成元を離散的に扱う基本状況を理解するため。', relation: 'L₀∩L₁ の各交点を鎖群の基底として用いる。', level: '定義と標準例を扱える', completion: '接空間による横断性を説明できる。', prerequisiteIds: ['lagrangian'], x: 545, y: 125, minimal: true, status: 'learning' }),
  base({ id: 'almost-complex', title: '適合する概複素構造', type: 'definition', reason: 'Floer方程式とエネルギーを定式化するため。', relation: 'ストリップを数える解析的構造を与える。', level: '概要を説明できる', completion: 'ωとの適合条件と誘導計量の役割を説明できる。', prerequisiteIds: ['symplectic'], x: 300, y: 190, minimal: true, status: 'needsCheck' }),
  base({ id: 'strip', title: '擬正則ストリップ', type: 'concept', reason: '微分の係数を与える曲線を理解するため。', relation: '交点間を結ぶ解のモジュライ空間を考える。', level: '定義と標準例を扱える', completion: '境界条件つきFloer方程式の各項を説明できる。', prerequisiteIds: ['intersection', 'almost-complex'], x: 790, y: 175, minimal: true }),
  base({ id: 'maslov', title: 'Maslov指数（役割）', type: 'concept', reason: '生成元の次数とモジュライ空間の次元を追うため。', relation: '微分で数える指数1の解を選別する。', level: '概要を説明できる', completion: '指数が次数差・期待次元に関係することを説明できる。', prerequisiteIds: ['lagrangian', 'strip'], x: 790, y: 285, minimal: false }),
  base({ id: 'compactness', title: 'コンパクト性の入力', type: 'theorem', reason: '曲線の数え上げが有限になる条件を把握するため。', relation: '微分の定義可能性と境界解析を支える。', level: '証明の要点を追える', completion: 'バブリング等を除く仮定が必要な理由を説明できる。', prerequisiteIds: ['strip'], x: 1035, y: 115, minimal: true, proofSteps: [
    { id: 'compact-1', claim: 'エネルギーが一様に抑えられた解列を取る。', grounds: 'エネルギー恒等式', explanation: '固定した端点を持つストリップを考える。' },
    { id: 'compact-2', claim: '部分列はFloer解へ収束する。', grounds: 'Gromovコンパクト性', explanation: '破れやバブリングの扱いを省略している。' },
  ] }),
  base({ id: 'chain-group', title: 'Floer鎖群 CF(L₀,L₁)', type: 'definition', reason: '複体の台となる代数的対象を定めるため。', relation: '横断的交点で生成される加群。', level: '構成を自力で再現できる', completion: '係数環を明示して交点から鎖群を書ける。', prerequisiteIds: ['intersection'], x: 790, y: 50, minimal: true }),
  base({ id: 'differential', title: 'Floer微分', type: 'definition', reason: '交点間の幾何を代数化する中心操作だから。', relation: '指数1のストリップを数え、生成元に作用させる。', level: '構成を自力で再現できる', completion: '入力・出力・数え上げ対象・係数を区別して式を説明できる。', prerequisiteIds: ['chain-group', 'strip', 'compactness'], x: 1280, y: 95, minimal: true }),
  base({ id: 'boundary-lemma', title: '1次元モジュライ空間の境界', type: 'lemma', reason: '微分を2回適用した項の相殺を理解するため。', relation: '壊れたストリップが境界点として現れる。', level: '証明の要点を追える', completion: '境界と2段階の軌道の対応を概説できる。', prerequisiteIds: ['compactness', 'differential', 'maslov'], x: 1280, y: 260, minimal: false, proofSteps: [
    { id: 'boundary-1', claim: '1次元モジュライ空間をコンパクト化する。', grounds: 'コンパクト性・貼り合わせ', explanation: '端点は壊れたストリップに対応する。' },
  ] }),
  base({ id: 'd-squared', title: '∂² = 0', type: 'theorem', reason: '定義した微分が鎖複体を与えることを確認するため。', relation: 'Lagrangian Floer複体の成立を保証する核心。', level: '証明の要点を追える', completion: '1次元モジュライ空間の境界の数え上げから説明できる。', prerequisiteIds: ['differential', 'boundary-lemma'], x: 1525, y: 210, minimal: false, proofSteps: [
    { id: 'square-1', claim: '∂²の係数は2段階のストリップの数である。', grounds: 'Floer微分の定義', explanation: '中間の交点について和を取る。' },
    { id: 'square-2', claim: '境界点は対になって相殺する。', grounds: '1次元コンパクト多様体の境界', explanation: '向きまたは mod 2 の係数を選ぶ必要がある。' },
  ] }),
  base({ id: 'goal', title: 'Lagrangian Floer複体の基本構成', type: 'goal', reason: '交点と擬正則曲線から鎖複体を組み立てる全体像を得るため。', relation: '今回のデモ学習目標。', level: '構成を自力で再現できる', completion: '仮定を明示し、CF・微分・∂²=0の役割を一続きで説明できる。', prerequisiteIds: ['differential', 'd-squared'], x: 1770, y: 135, minimal: true }),
]

export const DEMO_REVIEWS = {
  compactness: [
    { id: 'review-compact-1', stepId: 'compact-2', type: '定理の適用条件不足', description: 'Gromovコンパクト性を使うための幾何学的仮定が明示されていません。', check: 'バブリングを除外・制御する仮定と、どの収束概念を使うか確認してください。', severity: '重要' },
    { id: 'review-compact-2', stepId: 'compact-2', type: 'AIでは確認不能', description: '解析的な詳細はこのデモレビューでは検証できません。', check: '専門文献の正確な定理と仮定を照合してください。', severity: '注意' },
  ],
  'd-squared': [
    { id: 'review-square-1', stepId: 'square-2', type: '仮定の不足', description: '符号つきで数えるか mod 2 で数えるかが未指定です。', check: '係数環と向き付けに必要な仮定を明示してください。', severity: '重要' },
    { id: 'review-square-2', stepId: 'square-2', type: '論理の飛躍', description: 'コンパクト化された境界と壊れたストリップの対応が省略されています。', check: 'コンパクト性と貼り合わせの入力をステップとして追加してください。', severity: '重要' },
  ],
  'boundary-lemma': [
    { id: 'review-boundary-1', stepId: 'boundary-1', type: '根拠不足', description: '貼り合わせ定理の役割が名前だけで、適用対象が不明です。', check: 'どの解の近傍を貼り合わせるか記述してください。', severity: '注意' },
  ],
}
