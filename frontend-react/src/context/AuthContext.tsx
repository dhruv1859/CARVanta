import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../api/client';

interface UserData {
    id: number;
    email: string;
    username: string;
    full_name: string;
    role: string;
    avatar_url?: string;
    institution?: string;
    total_analyses: number;
    login_count: number;
}

interface AuthContextType {
    user: UserData | null;
    token: string | null;
    loading: boolean;
    login: (emailOrUsername: string, password: string) => Promise<void>;
    register: (email: string, username: string, password: string, fullName: string, role: string, institution?: string, country?: string) => Promise<any>;
    logout: () => void;
    updateProfile: (data: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<UserData | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('carvanta_token'));
    const [loading, setLoading] = useState(true);

    // On mount, check if token exists and validate it
    useEffect(() => {
        if (token) {
            api.get('/api/v5/auth/me', { headers: { Authorization: `Bearer ${token}` } })
                .then(res => {
                    if (res.data.error) {
                        localStorage.removeItem('carvanta_token');
                        setToken(null);
                        setUser(null);
                    } else {
                        setUser(res.data);
                    }
                })
                .catch(() => {
                    localStorage.removeItem('carvanta_token');
                    setToken(null);
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (emailOrUsername: string, password: string) => {
        const res = await api.post('/api/v5/auth/login', {
            email_or_username: emailOrUsername,
            password,
        });

        if (res.data.error) throw new Error(res.data.error);

        const { access_token, user: userData } = res.data;
        localStorage.setItem('carvanta_token', access_token);
        localStorage.setItem('carvanta_refresh', res.data.refresh_token);
        setToken(access_token);
        setUser(userData);
    };

    const register = async (
        email: string, username: string, password: string,
        fullName: string, role: string, institution?: string, country?: string
    ): Promise<any> => {
        const res = await api.post('/api/v5/auth/register', {
            email, username, password,
            full_name: fullName, role, institution, country,
        });

        if (res.data.error) throw new Error(res.data.error);

        // Return response — LoginPage handles verification step before login
        return res.data;
    };

    const logout = () => {
        if (token) {
            api.post('/api/v5/auth/logout', {}, { headers: { Authorization: `Bearer ${token}` } })
                .catch(() => {}); // fire-and-forget
        }
        localStorage.removeItem('carvanta_token');
        localStorage.removeItem('carvanta_refresh');
        setToken(null);
        setUser(null);
    };

    const updateProfile = async (data: any) => {
        const res = await api.put('/api/v5/auth/profile', data, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.data.error) throw new Error(res.data.error);
        setUser(prev => prev ? { ...prev, ...res.data } : prev);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateProfile }}>
            {children}
        </AuthContext.Provider>
    );
}
