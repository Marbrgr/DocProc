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
        <div>
            <h1>Login</h1>
            {error && <p style={{color: 'red'}}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <div>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>
                <div>
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <br></br>
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Logging in...' : 'Login'}
                </button>
            </form>
        </div>
    )

}

export default LoginForm