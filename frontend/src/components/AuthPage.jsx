import { useState } from 'react';
import { login, register } from '../api';

function parseApiError(err) {
  if (!err.body) return err.message || 'Something went wrong.';
  // Pydantic 422 validation errors come back as an array in detail
  if (Array.isArray(err.body.detail)) {
    return err.body.detail.map((d) => d.msg).join(' ');
  }
  if (typeof err.body.detail === 'string') return err.body.detail;
  return err.message || 'Something went wrong.';
}

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isRegister = mode === 'register';

  function switchMode(next) {
    setMode(next);
    setError('');
    setPassword('');
    setConfirmPassword('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (isRegister) {
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }

    setLoading(true);
    try {
      if (isRegister) {
        await register(username.trim(), password);
      } else {
        await login(username.trim(), password);
      }
      const me = await (await import('../api')).getMe();
      onAuthenticated(me);
    } catch (err) {
      if (err.status === 429) {
        setError('Too many attempts. Please wait a minute and try again.');
      } else {
        setError(parseApiError(err));
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-main-bg flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-accent-light/40 to-transparent opacity-60" />

      <div className="relative w-full max-w-md">
        {/* Logo & Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent shadow-lg shadow-accent/30 mb-4">
            <img
              src="../public/images/logo_white.png"
              alt="InteLex"
              className="w-10 h-10 object-contain"
            />
          </div>
          <h1 className="text-3xl font-serif font-bold text-content-primary tracking-tight">InteLex</h1>
          <p className="text-content-secondary text-sm mt-1">AI-Powered Legal Assistant</p>
        </div>

        {/* Card */}
        <div className="bg-surface rounded-2xl shadow-xl border border-border p-8">
          {/* Tab switcher */}
          <div className="flex rounded-xl bg-surface-hover p-1 mb-6">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                !isRegister
                  ? 'bg-surface shadow-sm text-content-primary'
                  : 'text-content-secondary hover:text-content-primary'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => switchMode('register')}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                isRegister
                  ? 'bg-surface shadow-sm text-content-primary'
                  : 'text-content-secondary hover:text-content-primary'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-2">
              <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={isRegister ? '3–32 characters, letters/numbers/_/-' : 'Enter your username'}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all duration-200 text-sm"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-content-primary mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegister ? 'At least 8 characters' : 'Enter your password'}
                className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all duration-200 text-sm"
              />
            </div>

            {/* Confirm Password (register only) */}
            {isRegister && (
              <div>
                <label className="block text-sm font-medium text-content-primary mb-1.5" htmlFor="confirm-password">
                  Confirm Password
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-content-primary placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent transition-all duration-200 text-sm"
                />
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-accent hover:bg-accent-hover disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg shadow-accent/20 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {isRegister ? 'Creating account…' : 'Signing in…'}
                </>
              ) : (
                isRegister ? 'Create Account' : 'Sign In'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-content-muted mt-6">
          InteLex &copy; {new Date().getFullYear()} &middot; Final Year Project
        </p>
      </div>
    </div>
  );
}
