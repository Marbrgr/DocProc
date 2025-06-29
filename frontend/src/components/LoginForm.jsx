import { useState } from 'react'
import '../App.css'
import axios from 'axios'

function LoginForm({ onLoginSuccess}) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault() // prevent page refresh
        setIsLoading(true)
        setError('')

        try {
            const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
                username: username,
                password: password
            })

            const token = response.data.access_token
            localStorage.setItem('jwt_token', token)

            console.log('Login successful!', response.data)
            onLoginSuccess()
        } catch (error) {
            console.error('Login failed:', error)
            setError('Invalid username or password')
        } finally {
            setIsLoading(false)
        }
    }



    return (
        <div className="login-form">
            <h1>DocuMind AI</h1>
            {error && <div className="login-error">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        id="username"
                        type="text"
                        placeholder="Enter your username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" disabled={isLoading} className="login-btn">
                    {isLoading ? 'Signing in...' : 'Sign In'}
                </button>
            </form>
        </div>
    )

}

export default LoginForm