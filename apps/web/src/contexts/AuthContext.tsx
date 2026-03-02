import {
  createContext,
  PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  AuthMeResult,
  SessionResult,
  getAuthMe,
  loginUser,
  logoutSession,
  refreshSession,
} from '../services/api';

interface AuthContextValue {
  bootstrapping: boolean;
  accessToken: string | null;
  user: AuthMeResult | null;
  login: (email: string, password: string) => Promise<void>;
  tryRefresh: () => Promise<boolean>;
  logout: () => Promise<void>;
  reloadMe: () => Promise<void>;
  hasPermission: (permissionCode: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function resolveAuthMe(result: SessionResult): Promise<AuthMeResult> {
  const me = await getAuthMe(result.access_token);
  return {
    ...me,
    roles: result.user.roles,
    email: result.user.email,
    user_id: result.user.user_id,
  };
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [bootstrapping, setBootstrapping] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthMeResult | null>(null);

  const applySession = useCallback(async (result: SessionResult) => {
    const me = await resolveAuthMe(result);
    setAccessToken(result.access_token);
    setUser(me);
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
  }, []);

  const tryRefresh = useCallback(async (): Promise<boolean> => {
    try {
      const refreshed = await refreshSession();
      await applySession(refreshed);
      return true;
    } catch {
      clearSession();
      return false;
    }
  }, [applySession, clearSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await loginUser(email, password);
      await applySession(result);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    try {
      await logoutSession();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const reloadMe = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    const me = await getAuthMe(accessToken);
    setUser(me);
  }, [accessToken]);

  const hasPermission = useCallback(
    (permissionCode: string) => {
      if (!user) {
        return false;
      }
      return user.permissions.includes(permissionCode);
    },
    [user],
  );

  useEffect(() => {
    let active = true;

    (async () => {
      await tryRefresh();
      if (active) {
        setBootstrapping(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [tryRefresh]);

  const value = useMemo<AuthContextValue>(
    () => ({
      bootstrapping,
      accessToken,
      user,
      login,
      tryRefresh,
      logout,
      reloadMe,
      hasPermission,
    }),
    [accessToken, bootstrapping, hasPermission, login, logout, reloadMe, tryRefresh, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
