import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/', label: 'Overview' },
  { to: '/analyzer', label: 'Text Analyzer' },
  { to: '/datasets', label: 'Datasets' },
  { to: '/annotation', label: 'Annotation' },
  { to: '/preprocessing', label: 'Preprocessing Lab' },
  { to: '/training', label: 'Training Lab' },
  { to: '/evaluation', label: 'Evaluation' },
  { to: '/models', label: 'Model Registry' },
  { to: '/experiments', label: 'Experiments' },
  { to: '/research', label: 'Research Center' },
  { to: '/about', label: 'About Project' },
  { to: '/settings', label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="h-dvh overflow-hidden lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="no-scrollbar bg-[var(--navy)] text-white px-5 py-6 max-h-[42vh] overflow-y-auto overscroll-contain lg:max-h-none lg:h-dvh">
        <div className="mb-8">
          <div className="text-xs uppercase tracking-[0.18em] text-blue-200/80">NLP Research</div>
          <h1 className="brand-serif text-2xl leading-tight mt-2">Code-Switching Analyzer</h1>
          <p className="text-sm text-blue-100/80 mt-2">Urdu · English · Local ML</p>
        </div>
        <nav className="no-scrollbar flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-x-visible lg:overflow-y-visible lg:pb-0">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-xl px-3 py-2 text-sm transition ${
                  isActive ? 'bg-[var(--royal)] text-white' : 'text-blue-100/85 hover:bg-white/10'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="no-scrollbar h-[calc(100dvh-42vh)] overflow-y-auto overscroll-contain px-4 py-6 sm:px-6 lg:h-dvh lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
