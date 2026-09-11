import React, { createContext, useContext, useState, useEffect } from 'react'

const UserCtx = createContext(null)

export function UserProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tpa_user')) } catch { return null }
  })

  const login = (u) => { setUser(u); localStorage.setItem('tpa_user', JSON.stringify(u)) }
  const logout = () => { setUser(null); localStorage.removeItem('tpa_user') }

  return <UserCtx.Provider value={{ user, login, logout }}>{children}</UserCtx.Provider>
}

export const useUser = () => useContext(UserCtx)
