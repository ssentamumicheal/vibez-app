import React, { useState, useEffect } from 'react';
import { Transition, CSSTransition } from 'react-transition-group';

const API_BASE_URL = 'http://localhost:8000/api'; // Make sure this matches your Django server address

const App = () => {
  // State to hold the authentication token and user information
  const [token, setToken] = useState(localStorage.getItem('vibezToken') || null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

  // Fetch user data if a token exists
  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setUser(null);
    }
  }, [token]);

  const fetchUser = async () => {
    setLoading(true);
    setError(null);
    try {
      // Note: This endpoint is not yet defined in the backend, 
      // but it's a good practice to have one to get user details
      const response = await fetch(`${API_BASE_URL}/users/me/`, {
        headers: {
          'Authorization': `Token ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        throw new Error('Failed to fetch user data.');
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
      // If fetching user fails, the token might be invalid, so we clear it.
      setToken(null);
      localStorage.removeItem('vibezToken');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setToken(data.token);
        localStorage.setItem('vibezToken', data.token);
      } else {
        throw new Error(data.non_field_errors ? data.non_field_errors[0] : 'Login failed.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (username, email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setToken(data.token);
        localStorage.setItem('vibezToken', data.token);
      } else {
        const errorMessages = Object.values(data).flat().join(' ');
        throw new Error(errorMessages || 'Registration failed.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/logout/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        },
      });
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('vibezToken');
      // No need to handle success/error on logout, just clear local state.
    }
  };

  const transitionStyles = {
    entering: { opacity: 0 },
    entered: { opacity: 1 },
    exiting: { opacity: 0 },
    exited: { opacity: 0 },
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4 font-sans">
      <header className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-10">
        <h1 className="text-4xl font-extrabold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500">VIBEZ</h1>
        {token && (
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-pink-500 hover:bg-pink-600 text-white font-semibold rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105"
          >
            Logout
          </button>
        )}
      </header>
      
      <CSSTransition
        in={!token}
        timeout={500}
        classNames="fade"
        unmountOnExit
      >
        <AuthForm
          mode={authMode}
          onLogin={handleLogin}
          onRegister={handleRegister}
          onToggleMode={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
          loading={loading}
          error={error}
        />
      </CSSTransition>

      <CSSTransition
        in={!!token}
        timeout={500}
        classNames="fade"
        unmountOnExit
      >
        <Dashboard user={user} loading={loading} />
      </CSSTransition>

    </div>
  );
};

const AuthForm = ({ mode, onLogin, onRegister, onToggleMode, loading, error }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'login') {
      onLogin(email, password);
    } else {
      onRegister(username, email, password);
    }
  };

  return (
    <div className="w-full max-w-lg p-8 bg-gray-800 rounded-2xl shadow-2xl backdrop-filter backdrop-blur-lg bg-opacity-70 border border-gray-700 transition-all duration-500 ease-in-out transform scale-100">
      <h2 className="text-3xl font-bold text-center text-white mb-6">
        {mode === 'login' ? 'Welcome Back!' : 'Join Vibez'}
      </h2>
      <p className="text-center text-gray-400 mb-8">
        {mode === 'login' ? 'Log in to find the hottest parties in Uganda.' : 'Create an account to start exploring.'}
      </p>

      {error && (
        <div className="bg-red-500 text-white px-4 py-3 rounded-lg mb-6 text-sm text-center">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {mode === 'register' && (
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-5 py-3 bg-gray-700 text-white rounded-xl border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400 transition duration-300"
            required
          />
        )}
        <input
          type="email"
          placeholder="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-5 py-3 bg-gray-700 text-white rounded-xl border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400 transition duration-300"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-5 py-3 bg-gray-700 text-white rounded-xl border border-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-400 transition duration-300"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full px-5 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold rounded-xl shadow-lg hover:from-purple-700 hover:to-pink-700 transition duration-300 ease-in-out transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            mode === 'login' ? 'Login' : 'Register'
          )}
        </button>
      </form>

      <div className="text-center mt-8 text-gray-400">
        {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
        <button onClick={onToggleMode} className="text-purple-400 hover:text-purple-300 font-semibold ml-2 transition duration-300">
          {mode === 'login' ? 'Sign Up' : 'Log In'}
        </button>
      </div>
    </div>
  );
};

const Dashboard = ({ user, loading }) => {
  return (
    <div className="w-full max-w-2xl p-8 bg-gray-800 rounded-2xl shadow-2xl backdrop-filter backdrop-blur-lg bg-opacity-70 border border-gray-700 text-center">
      <h2 className="text-4xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
        Dashboard
      </h2>
      {loading ? (
        <p className="text-gray-400 animate-pulse">Fetching user data...</p>
      ) : (
        <>
          {user && (
            <p className="text-xl text-gray-200">
              Hello, <span className="font-extrabold text-purple-400">{user.username}</span>!
            </p>
          )}
          <p className="mt-4 text-lg text-gray-400">You're logged in. You can now access all of Vibez's features.</p>
        </>
      )}
      
      {/* TODO: Add more dashboard content here, e.g., party lists, maps, etc. */}
      <div className="mt-8 p-6 bg-gray-900 rounded-xl border border-gray-700">
        <h3 className="text-2xl font-bold mb-4 text-white">Your Vibez Awaits...</h3>
        <p className="text-gray-400">
          This is where you'll find a map of all the parties happening in Uganda, upcoming events, and the party chat.
        </p>
        <button className="mt-6 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-full transition duration-300 ease-in-out transform hover:scale-105">
          Find Parties Now
        </button>
      </div>
    </div>
  );
};

export default App;

