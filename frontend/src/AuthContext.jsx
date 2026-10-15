import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);
const KEY = "civic-eye-auth";

export function AuthProvider({ children }) {
  const [state, setState] = useState(() => {
    try { return JSON.parse(localStorage.getItem(KEY)) || { token: null, user: null }; }
    catch { return { token: null, user: null }; }
  });
  useEffect(() => { localStorage.setItem(KEY, JSON.stringify(state)); }, [state]);
  const value = useMemo(() => ({
    ...state,
    setAuth: (token, user) => setState({ token, user }),
    logout: () => setState({ token: null, user: null }),
    api: (path, opts = {}) => api(path, { ...opts, token: state.token }),
  }), [state]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { return useContext(AuthContext); }
