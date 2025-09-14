import React, { useState } from 'react';
import { forgotPassword } from '../authApi';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await forgotPassword(email);
    if (res.msg) {
      setMessage(res.msg);
      setError('');
    } else {
      setError(res.detail || 'Error sending reset link');
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Forgot Password</h2>
      {message && <div style={{color:'green'}}>{message}</div>}
      {error && <div style={{color:'red'}}>{error}</div>}
      <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" required />
      <button type="submit">Send Reset Link</button>
    </form>
  );
}
