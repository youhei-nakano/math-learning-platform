import LearningMapPage from './pages/LearningMapPage'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav" aria-label="メインナビゲーション">
        <div className="app-nav__inner">
          <span className="app-nav__brand">Math Notes</span>
          <span className="app-nav__item active" aria-current="page">
            <span aria-hidden="true">⌘</span> 学習マップ
          </span>
        </div>
      </nav>
      <LearningMapPage />
    </div>
  )
}

export default App
