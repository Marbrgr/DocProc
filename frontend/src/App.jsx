import { useState, useEffect} from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import LoginForm from './components/LoginForm'
import Dashboard from './components/Dashboard'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('jwt_token')
    if (token) {
      setIsLoggedIn(true)
    }
  }, [])

  return (
    <div className={`App ${!isLoggedIn ? 'login-page' : ''}`}>
      {isLoggedIn ? (
        <Dashboard />
      ): (
        <LoginForm onLoginSuccess={() => setIsLoggedIn(true)} />
      )}
    </div>
  )
}

export default App
