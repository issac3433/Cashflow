import React, { createContext, useContext, useEffect, useState } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../services/supabase';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';
import * as LocalAuthentication from 'expo-local-authentication';
import Constants from 'expo-constants';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  biometricAvailable: boolean;
  biometricType: string | null;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string }>;
  signInWithBiometric: () => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  saveBiometricCredentials: (email: string, password: string) => Promise<void>;
  hasBiometricCredentials: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricType, setBiometricType] = useState<string | null>(null);

  console.log('🔐 AuthProvider rendering, loading:', loading, 'user:', user?.email || 'none');

  // Check biometric availability on mount
  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  useEffect(() => {
    // Check for existing session with timeout
    const sessionPromise = supabase.auth.getSession();
    const timeoutPromise = new Promise((resolve) => {
      setTimeout(() => resolve(null), 5000); // 5 second timeout
    });

    Promise.race([sessionPromise, timeoutPromise])
      .then((result: any) => {
        if (result && result.data) {
          const { session } = result.data;
          setSession(session);
          setUser(session?.user ?? null);
          if (session) {
            AsyncStorage.setItem('supabase_token', session.access_token);
            AsyncStorage.setItem('supabase_user', JSON.stringify(session.user));
            // Initialize user in backend (don't wait for it - fire and forget)
            initializeUserInBackend(session.access_token).catch((err) => {
              console.error('Backend init failed on session check:', err);
            });
          }
        }
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error getting session:', error);
        setLoading(false);
      });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      
      if (session) {
        await AsyncStorage.setItem('supabase_token', session.access_token);
        await AsyncStorage.setItem('supabase_user', JSON.stringify(session.user));
        initializeUserInBackend(session.access_token);
      } else {
        await AsyncStorage.removeItem('supabase_token');
        await AsyncStorage.removeItem('supabase_user');
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const initializeUserInBackend = async (token: string) => {
    try {
      // Store token first so API client can use it
      await AsyncStorage.setItem('supabase_token', token);
      console.log('🔧 Initializing user in backend database...');
      console.log('🌐 API Base URL:', process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000');
      const result = await api.post('/me/init-supabase', {});
      console.log('✅ Backend initialization result:', result);
      return result;
    } catch (error: any) {
      console.error('❌ Backend initialization error:', error);
      console.error('Error details:', error.message);
      console.error('Response:', error.response?.data);
      console.error('Status:', error.response?.status);
      // Don't throw - this is not critical for sign in, but log it
      // Return null instead of throwing to prevent blocking
      return null;
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('Sign in error:', error);
        return { error: error.message };
      }

      if (data.session) {
        console.log('✅ Sign in successful!');
        console.log('User ID:', data.session.user.id);
        console.log('Initializing backend...');
        try {
          const initResult = await initializeUserInBackend(data.session.access_token);
          console.log('✅ Backend initialization result:', initResult);
        } catch (initError: any) {
          console.error('⚠️ Backend initialization failed, but sign in succeeded');
          console.error('Init error:', initError.message);
          // Don't fail sign in if backend init fails - user can retry later
        }
      } else {
        console.warn('Sign in successful but no session returned');
        return { error: 'Sign in successful but no session was created' };
      }

      return {};
    } catch (error: any) {
      console.error('Sign in exception:', error);
      return { error: error.message || 'Sign in failed' };
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        return { error: error.message };
      }

      // If sign up automatically creates a session (some Supabase configs do this)
      if (data.session) {
        setSession(data.session);
        setUser(data.session.user);
        await AsyncStorage.setItem('supabase_token', data.session.access_token);
        await AsyncStorage.setItem('supabase_user', JSON.stringify(data.session.user));
        // Return success with session info so LoginScreen can prompt for biometric
        return { session: data.session };
      }

      return {};
    } catch (error: any) {
      return { error: error.message || 'Sign up failed' };
    }
  };

  const checkBiometricAvailability = async () => {
    try {
      // Check if we're in Expo Go (which has limited FaceID support)
      const isExpoGo = Constants?.executionEnvironment === 'storeClient';
      
      const compatible = await LocalAuthentication.hasHardwareAsync();
      if (!compatible) {
        console.log('⚠️ Biometric hardware not available');
        setBiometricAvailable(false);
        return;
      }

      const enrolled = await LocalAuthentication.isEnrolledAsync();
      if (!enrolled) {
        console.log('⚠️ No biometrics enrolled on device');
        setBiometricAvailable(false);
        return;
      }

      // In Expo Go, biometrics may not work properly
      if (isExpoGo) {
        console.log('⚠️ Running in Expo Go - FaceID/TouchID has limited support');
        console.log('💡 For full FaceID support, use a development build: npx expo run:ios');
      }

      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        setBiometricType('Face ID');
      } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        setBiometricType('Touch ID');
      } else {
        setBiometricType('Biometric');
      }

      setBiometricAvailable(true);
    } catch (error) {
      console.error('❌ Error checking biometric availability:', error);
      setBiometricAvailable(false);
    }
  };

  const signInWithBiometric = async () => {
    try {
      // First authenticate with biometric (FaceID/TouchID only, no password fallback)
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: `Use ${biometricType || 'Face ID'} to sign in`,
        cancelLabel: 'Cancel',
        disableDeviceFallback: true, // Force FaceID/TouchID only, no password fallback
        fallbackLabel: 'Use Password', // This won't show if disableDeviceFallback is true
      });

      if (!result.success) {
        return { error: result.error === 'user_cancel' ? 'Authentication cancelled' : 'Biometric authentication failed' };
      }

      // Get saved credentials
      const savedEmail = await AsyncStorage.getItem('biometric_email');
      const savedPassword = await AsyncStorage.getItem('biometric_password');

      console.log('🔍 Retrieving saved credentials:', { 
        hasEmail: !!savedEmail, 
        hasPassword: !!savedPassword 
      });

      if (!savedEmail || !savedPassword) {
        console.error('❌ No saved credentials found');
        return { error: 'No saved credentials found. Please sign in with email and password first, then enable biometric login.' };
      }

      // Sign in with saved credentials
      return await signIn(savedEmail, savedPassword);
    } catch (error: any) {
      console.error('Biometric sign in error:', error);
      return { error: error.message || 'Biometric authentication failed' };
    }
  };

  const saveBiometricCredentials = async (email: string, password: string) => {
    try {
      await AsyncStorage.setItem('biometric_email', email);
      await AsyncStorage.setItem('biometric_password', password);
      console.log('✅ Biometric credentials saved successfully');
      // Verify they were saved
      const savedEmail = await AsyncStorage.getItem('biometric_email');
      const savedPassword = await AsyncStorage.getItem('biometric_password');
      console.log('🔍 Verification - Email saved:', !!savedEmail, 'Password saved:', !!savedPassword);
    } catch (error) {
      console.error('❌ Error saving biometric credentials:', error);
    }
  };

  const hasBiometricCredentials = async (): Promise<boolean> => {
    try {
      const email = await AsyncStorage.getItem('biometric_email');
      const password = await AsyncStorage.getItem('biometric_password');
      const hasCredentials = !!(email && password);
      console.log('🔍 Checking biometric credentials:', { 
        hasEmail: !!email, 
        hasPassword: !!password, 
        hasCredentials 
      });
      return hasCredentials;
    } catch (error) {
      console.error('❌ Error checking biometric credentials:', error);
      return false;
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    await AsyncStorage.removeItem('supabase_token');
    await AsyncStorage.removeItem('supabase_user');
    // Keep biometric credentials so user can use FaceID next time
    // They can manually clear them from settings if needed
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      session, 
      loading, 
      biometricAvailable,
      biometricType,
      signIn, 
      signUp, 
      signInWithBiometric,
      signOut,
      saveBiometricCredentials,
      hasBiometricCredentials,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

