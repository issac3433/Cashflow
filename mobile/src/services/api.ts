import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// API base URL - adjust for your environment
// For web, use localhost. For mobile device, use your computer's IP address
const getApiBaseUrl = () => {
  // Your Mac's IP address - update this if your IP changes
  // Check with: ifconfig | grep "inet " | grep -v 127.0.0.1
  const macIP = '10.0.0.128';
  
  // Android emulator uses special IP to reach host machine
  const androidEmulatorIP = '10.0.2.2';
  
  // Check environment variable first
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;
    // If it's localhost and we're on Android emulator, use emulator IP
    if (envUrl.includes('localhost') && Platform.OS === 'android' && __DEV__) {
      return envUrl.replace('localhost', androidEmulatorIP);
    }
    // If it's localhost and we're on a physical device (iOS/Android), replace with IP
    if (envUrl.includes('localhost') && Platform.OS !== 'web') {
      return envUrl.replace('localhost', macIP);
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
  
  // For iOS simulator or physical device, use Mac's IP address
  return __DEV__ ? `http://${macIP}:8000` : 'https://your-api-domain.com';
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

  constructor() {
    console.log('🔧 Creating API client with base URL:', API_BASE_URL);
    this.client = axios.create({
      baseURL: API_BASE_URL,
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

    // Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        console.error('❌ API Error:', {
          message: error.message,
          code: error.code,
          response: error.response?.data,
          status: error.response?.status,
          config: {
            url: error.config?.url,
            baseURL: error.config?.baseURL,
            method: error.config?.method,
          },
        });
        
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

