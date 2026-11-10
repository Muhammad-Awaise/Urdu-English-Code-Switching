import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import AboutProject from './pages/AboutProject'
import Analyzer from './pages/Analyzer'
import Annotation from './pages/Annotation'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import Evaluation from './pages/Evaluation'
import Experiments from './pages/Experiments'
import Models from './pages/Models'
import Preprocessing from './pages/Preprocessing'
import Research from './pages/Research'
import Settings from './pages/Settings'
import Training from './pages/Training'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/about" element={<AboutProject />} />
          <Route path="/analyzer" element={<Analyzer />} />

          <Route path="/datasets" element={<Datasets />} />
          <Route path="/annotation" element={<Annotation />} />
          <Route path="/preprocessing" element={<Preprocessing />} />
          <Route path="/training" element={<Training />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/models" element={<Models />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/research" element={<Research />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
