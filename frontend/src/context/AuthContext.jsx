import React, { createContext, useContext, useState, useEffect } from 'react';
import API from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('access_token')));

  useEffect(() => {
    let active = true;
    if (!token) {
      setUser(null);
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    API.get('/auth/me')
      .then((response) => {
        if (active) setUser(response.data);
      })
      .catch((error) => {
        if (active) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setToken(null);
          setUser(null);
          console.error('Failed to load current user', error);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [token]);

  const login = async (email, password) => {
    const res = await API.post('/auth/login', { email, password });
    const { access_token, refresh_token } = res.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    setToken(access_token);
    const currentUser = await API.get('/auth/me');
    setUser(currentUser.data);
    return res.data;
  };

  const refreshUser = async () => {
    const currentUser = await API.get('/auth/me');
    setUser(currentUser.data);
    return currentUser.data;
  };

  const registerPatient = async (data) => {
    const res = await API.post('/auth/register/patient', data);
    return res.data;
  };

  const registerDoctor = async (data) => {
    const res = await API.post('/auth/register/doctor', data);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, token, role: user?.role, loading, login, refreshUser, registerPatient, registerDoctor, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
