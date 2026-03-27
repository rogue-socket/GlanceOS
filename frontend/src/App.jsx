import { ThemeProvider } from './context/ThemeContext'
import Dashboard from './components/Dashboard'

function App() {
  return (
    <ThemeProvider>
      <Dashboard />
    </ThemeProvider>
  )
}

export default App
