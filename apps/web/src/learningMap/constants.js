export const LEARNING_MAP_STORAGE_KEY = 'math-reading-learning-map-v1'

export const NODE_TYPES = {
  concept: { label: '概念', icon: '◇' },
  definition: { label: '定義', icon: '≔' },
  example: { label: '例', icon: '◉' },
  counterexample: { label: '非例・反例', icon: '⊘' },
  theorem: { label: '定理', icon: '∴' },
  lemma: { label: '証明上の補題', icon: '⊢' },
  proofTechnique: { label: '証明技法', icon: '↝' },
  goal: { label: '目標', icon: '★' },
  section: { label: '章・節', icon: '§' },
}

export const LEARNING_STATUSES = {
  notStarted: { label: '未着手', symbol: '○' },
  learning: { label: '学習中', symbol: '▶' },
  needsCheck: { label: '要確認', symbol: '!' },
  understood: { label: '基本理解を確認', symbol: '✓' },
  review: { label: '要復習', symbol: '↺' },
}

export const UNDERSTANDING_LEVELS = ['概要を説明できる', '定義と標準例を扱える', '構成を自力で再現できる', '証明の要点を追える']

export const CONCEPT_CHECKS = [
  '自分の言葉で定義を説明できる',
  '対象となる集合・空間・構造を説明できる',
  '必要な仮定を説明できる',
  '記号の意味を説明できる',
  '具体例を挙げられる',
  '非例または反例を挙げられる',
  '目標概念に必要な理由を説明できる',
]
