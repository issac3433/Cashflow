import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [biometricLoading, setBiometricLoading] = useState(false);
  const [hasSavedCredentials, setHasSavedCredentials] = useState(false);
  const [hasAutoPrompted, setHasAutoPrompted] = useState(false);
  const { 
    signIn, 
    signUp, 
    signInWithBiometric,
    biometricAvailable,
    biometricType,
    saveBiometricCredentials,
    hasBiometricCredentials,
  } = useAuth();
  const passwordInputRef = useRef<TextInput>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    // Check for saved biometric credentials
    checkBiometricCredentials();
    
    // Animate on mount
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  // Auto-prompt FaceID when credentials are available and user is on login (not sign up)
  useEffect(() => {
    if (
      hasSavedCredentials && 
      biometricAvailable && 
      !isSignUp && 
      !loading && 
      !biometricLoading &&
      !hasAutoPrompted
    ) {
      // Small delay to let the screen render and animations complete
      const timer = setTimeout(() => {
        setHasAutoPrompted(true);
        handleBiometricSignIn();
      }, 1000); // Wait for animations to complete

      return () => clearTimeout(timer);
    }
  }, [hasSavedCredentials, biometricAvailable, isSignUp, loading, biometricLoading, hasAutoPrompted]);

  // Reset auto-prompt flag when switching between sign in/sign up
  useEffect(() => {
    if (isSignUp) {
      setHasAutoPrompted(false);
    }
  }, [isSignUp]);

  const checkBiometricCredentials = async () => {
    const hasCredentials = await hasBiometricCredentials();
    console.log('🔍 LoginScreen - Has saved credentials:', hasCredentials);
    setHasSavedCredentials(hasCredentials);
  };

  const handleSubmit = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    const result = isSignUp ? await signUp(email, password) : await signIn(email, password);
    setLoading(false);

    if (result.error) {
      Alert.alert('Error', result.error);
    } else {
      // After successful sign in OR sign up (if auto-signed in), offer biometric
      // Check if biometric is available and credentials aren't already saved
      if (biometricAvailable && !hasSavedCredentials) {
        // Small delay to ensure navigation completes first
        setTimeout(() => {
          Alert.alert(
            `Enable ${biometricType}?`,
            `Would you like to use ${biometricType} for faster sign in? Your credentials will be securely stored on this device.`,
            [
              { 
                text: 'Not Now', 
                style: 'cancel',
                onPress: () => {
                  console.log('User declined biometric setup');
                }
              },
              {
                text: 'Enable',
                onPress: async () => {
                  try {
                    await saveBiometricCredentials(email, password);
                    setHasSavedCredentials(true);
                    Alert.alert(
                      'Biometric Login Enabled',
                      `You can now use ${biometricType} to sign in quickly!`,
                      [{ text: 'OK' }]
                    );
                  } catch (error) {
                    console.error('Failed to save biometric credentials:', error);
                    Alert.alert('Error', 'Failed to enable biometric login. Please try again later.');
                  }
                },
              },
            ]
          );
        }, 500);
      } else if (isSignUp && !result.session) {
        // Sign up without auto-login - show verification message
        Alert.alert(
          'Account Created!',
          'Please check your email for verification, then sign in.',
          [
            { 
              text: 'OK', 
              onPress: () => {
                setIsSignUp(false);
              }
            }
          ]
        );
      }
    }
  };

  const handleBiometricSignIn = async () => {
    setBiometricLoading(true);
    const result = await signInWithBiometric();
    setBiometricLoading(false);

    if (result.error) {
      Alert.alert('Authentication Failed', result.error);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 100}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        enableOnAndroid={true}
        enableAutomaticScroll={true}
      >
        <Animated.View 
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          <View style={styles.logoContainer}>
            <View style={styles.logoCircle}>
              <Text style={styles.logoEmoji}>💰</Text>
            </View>
            <Text style={styles.title}>Cashflow</Text>
            <Text style={styles.subtitle}>
              {isSignUp ? 'Create your account' : 'Welcome back'}
            </Text>
          </View>

          <View style={styles.form}>
            <View style={styles.inputContainer}>
              <Ionicons name="mail-outline" size={20} color={colors.textSecondary} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email"
                placeholderTextColor={colors.textTertiary}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                autoCorrect={false}
                editable={!loading && !biometricLoading}
                returnKeyType="next"
                onSubmitEditing={() => passwordInputRef.current?.focus()}
                blurOnSubmit={false}
                textContentType="emailAddress"
              />
            </View>

            <View style={styles.inputContainer}>
              <Ionicons name="lock-closed-outline" size={20} color={colors.textSecondary} style={styles.inputIcon} />
              <TextInput
                ref={passwordInputRef}
                style={styles.input}
                placeholder="Password"
                placeholderTextColor={colors.textTertiary}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoCapitalize="none"
                autoCorrect={false}
                editable={!loading && !biometricLoading}
                returnKeyType="done"
                onSubmitEditing={handleSubmit}
                textContentType={isSignUp ? "newPassword" : "password"}
              />
            </View>

            <TouchableOpacity
              style={[styles.button, (loading || biometricLoading) && styles.buttonDisabled]}
              onPress={handleSubmit}
              disabled={loading || biometricLoading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>
                  {isSignUp ? 'Sign Up' : 'Sign In'}
                </Text>
              )}
            </TouchableOpacity>

            {biometricAvailable && hasSavedCredentials && !isSignUp && (
              <View style={styles.biometricContainer}>
                <View style={styles.divider}>
                  <View style={styles.dividerLine} />
                  <Text style={styles.dividerText}>or</Text>
                  <View style={styles.dividerLine} />
                </View>
                <TouchableOpacity
                  style={styles.biometricButton}
                  onPress={handleBiometricSignIn}
                  disabled={loading || biometricLoading}
                  activeOpacity={0.8}
                >
                  {biometricLoading ? (
                    <ActivityIndicator color={colors.primary} />
                  ) : (
                    <>
                      <Ionicons 
                        name={biometricType === 'Face ID' ? 'face-recognition' : 'finger-print'} 
                        size={24} 
                        color={colors.primary} 
                      />
                      <Text style={styles.biometricButtonText}>
                        Sign in with {biometricType}
                      </Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            <TouchableOpacity
              style={styles.switchButton}
              onPress={() => setIsSignUp(!isSignUp)}
              disabled={loading || biometricLoading}
            >
              <Text style={styles.switchText}>
                {isSignUp
                  ? 'Already have an account? Sign in'
                  : "Don't have an account? Sign up"}
              </Text>
            </TouchableOpacity>
          </View>
        </Animated.View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.lg,
    paddingBottom: spacing.xxl, // Extra padding for keyboard
    minHeight: '100%',
  },
  content: {
    width: '100%',
    maxWidth: 400,
    alignSelf: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  logoCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
    ...shadows.lg,
  },
  logoEmoji: {
    fontSize: 48,
  },
  title: {
    ...typography.h1,
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  inputIcon: {
    marginLeft: spacing.md,
  },
  input: {
    flex: 1,
    ...typography.body,
    padding: spacing.md,
    color: colors.text,
    minHeight: 56,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.sm,
    ...shadows.md,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
    fontSize: 18,
  },
  biometricContainer: {
    marginTop: spacing.lg,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border,
  },
  dividerText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginHorizontal: spacing.md,
  },
  biometricButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 2,
    borderColor: colors.primary,
    gap: spacing.sm,
    ...shadows.sm,
  },
  biometricButtonText: {
    ...typography.body,
    color: colors.primary,
    fontWeight: '600',
  },
  switchButton: {
    marginTop: spacing.lg,
    alignItems: 'center',
    padding: spacing.sm,
  },
  switchText: {
    ...typography.body,
    color: colors.primary,
  },
});
