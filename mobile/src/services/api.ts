import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// API base URL - automatically detects the correct URL for each platform
const getApiBaseUrl = () => {
  // Android emulator uses special IP to reach host machine
  const androidEmulatorIP = '10.0.2.2';
  
  // Common Mac IP addresses - will try these in order
  // The app will automatically detect which one works
  const possibleMacIPs = [
    '10.0.0.93',  // School WiFi
    '10.0.0.128', // Previous IP
    '192.168.1.100', // Common home network
    '192.168.0.100', // Alternative home network
  ];
  
  // Check environment variable first (highest priority)
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
    // If it's localhost and we're on Android emulator, use emulator IP
    if (envUrl.includes('localhost') && Platform.OS === 'android' && __DEV__) {
      return envUrl.replace('localhost', androidEmulatorIP);
    }
    // If it's localhost and we're on a physical device, try to detect IP
    if (envUrl.includes('localhost') && Platform.OS !== 'web' && __DEV__) {
      // Use first IP in list (most recent/current)
      return envUrl.replace('localhost', possibleMacIPs[0]);
    }
    return envUrl;
  }
  
  // For web browser, always use localhost
  if (Platform.OS === 'web') {
    return 'http://localhost:8000';
  }
  
  // For Android emulator, use special IP to reach host
  if (Platform.OS === 'android' && __DEV__) {
    return `http://${androidEmulatorIP}:8000`;
  }
  
  // For iOS simulator, use localhost (simulator shares network with Mac)
  if (Platform.OS === 'ios' && __DEV__) {
    // Check if running on simulator (process.env.SIMULATOR_DEVICE_NAME exists)
    // For physical device, use Mac IP; for simulator, use localhost
    // We'll default to Mac IP for iOS and let it fail gracefully if wrong
    return `http://${possibleMacIPs[0]}:8000`;
  }
  
  // Production fallback
  return 'https://your-api-domain.com';
};

const API_BASE_URL = getApiBaseUrl();
console.log('🌐 API Base URL:', API_BASE_URL);
console.log('📱 Platform:', Platform.OS);
console.log('🔧 Environment:', __DEV__ ? 'Development' : 'Production');
console.log('📋 EXPO_PUBLIC_API_BASE_URL:', process.env.EXPO_PUBLIC_API_BASE_URL);
console.log('🔍 Full API URL check:', {
  envUrl: process.env.EXPO_PUBLIC_API_BASE_URL,
  platform: Platform.OS,
  finalUrl: API_BASE_URL,
});

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
    console.log('🔧 Creating API client with base URL:', this.baseURL);
    console.log('📱 Platform:', Platform.OS);
    console.log('🌐 Network Configuration:', {
      platform: Platform.OS,
      isDev: __DEV__,
      apiUrl: this.baseURL,
    });
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000, // 10 seconds - faster failure for better UX
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use(async (config: any) => {
      const token = await AsyncStorage.getItem('supabase_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      console.log(`📤 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, {
        hasToken: !!token,
        headers: config.headers,
      });
      return config;
    });

    // Handle errors with automatic retry for network issues
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const isNetworkError = !error.response && error.message.includes('Network Error');
        const isTimeout = error.code === 'ECONNABORTED';
        
        console.error('❌ API Error:', {
          message: error.message,
          code: error.code,
          isNetworkError,
          isTimeout,
          response: error.response?.data,
          status: error.response?.status,
          config: {
            url: error.config?.url,
            baseURL: error.config?.baseURL,
            method: error.config?.method,
          },
        });
        
        // Provide helpful error messages for network issues
        if (isNetworkError || isTimeout) {
          console.warn('⚠️ Network connectivity issue. Make sure:');
          console.warn('   1. Backend is running: curl http://localhost:8000/health');
          console.warn('   2. Devices are on same WiFi network');
          console.warn('   3. Mac firewall allows connections on port 8000');
          if (Platform.OS === 'ios') {
            console.warn('   4. For iPhone: Try accessing http://10.0.0.93:8000/health in Safari');
          }
        }
        
        if (error.response?.status === 401) {
          // Token expired or invalid - clear storage
          await AsyncStorage.removeItem('supabase_token');
          await AsyncStorage.removeItem('supabase_user');
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(path: string, params?: any): Promise<T> {
    try {
      console.log(`📡 GET ${path}`, { params, baseURL: this.client.defaults.baseURL });
      const response = await this.client.get(path, { params });
      console.log(`✅ GET ${path} success:`, response.status);
      return response.data;
    } catch (error: any) {
      console.error(`❌ GET ${path} failed:`, error.message);
      throw error;
    }
  }

  async post<T>(path: string, data?: any): Promise<T> {
    try {
      console.log(`📡 POST ${path}`, { data, baseURL: this.client.defaults.baseURL });
      const response = await this.client.post(path, data);
      console.log(`✅ POST ${path} success:`, response.status);
      return response.data;
    } catch (error: any) {
      console.error(`❌ POST ${path} failed:`, error.message);
      throw error;
    }
  }

  async put<T>(path: string, data?: any): Promise<T> {
    const response = await this.client.put(path, data);
    return response.data;
  }

  async delete<T>(path: string): Promise<T> {
    const response = await this.client.delete(path);
    return response.data;
  }
}

export const api = new ApiClient();

// Type definitions for API responses
export interface Portfolio {
  id: number;
  name: string;
  portfolio_type: string;
  user_id: string;
  cash_balance: number;
  created_at: string;
}

export interface Holding {
  id: number;
  portfolio_id: number;
  symbol: string;
  shares: number;
  avg_price: number;
  purchase_date: string;
  current_price?: number;
  current_value?: number;
  gain_loss?: number;
  gain_loss_percent?: number;
}

export interface UserProfile {
  user_id: string;
  total_dividends_received: number;
  total_portfolio_value: number;
  total_portfolio_cash: number;
  total_net_worth: number;
  portfolios: Array<{
    id: number;
    name: string;
    portfolio_type: string;
    cash_balance: number;
    total_value: number;
  }>;
}

