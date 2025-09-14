import React, { createContext, useState, useEffect } from 'react';
import { getMe } from './authApi';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      if (token) {
        const res = await getMe(token);
        if (res.username) setUser(res);
        else setUser(null);
      }
      setLoading(false);
    }
    fetchUser();
  }, [token]);

  const login = (token) => {
    setToken(token);
    localStorage.setItem('token', token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
