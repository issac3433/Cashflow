import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { useAuth } from '../context/AuthContext';
import { api, UserProfile } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

export default function HomeScreen({ navigation }: any) {
  const { user, signOut } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioType, setNewPortfolioType] = useState<'individual' | 'retirement'>('individual');
  const [creating, setCreating] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [hasError, setHasError] = useState(false);

  const loadProfile = async (isRetry = false) => {
    try {
      console.log('Loading profile...');
      console.log('🌐 API Base URL should be logged in api.ts');
      const data = await api.get<UserProfile>('/profile');
      console.log('Profile loaded:', data);
      setProfile(data);
      setHasError(false);
      setRetryCount(0);
      setLoading(false);
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      console.error('Error details:', error.message);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      // Auto-retry on initial load if it's a network error (backend might be starting)
      if (loading && retryCount < 2 && !isRetry) {
        const delay = 1000; // 1 second delay
        console.log(`Retrying in ${delay}ms... (attempt ${retryCount + 1}/2)`);
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadProfile(true);
        }, delay);
        return; // Don't set loading to false yet
      }
      
      // Stop loading and show error after retries exhausted
      setLoading(false);
      setHasError(true);
      if (!isRetry) {
        Alert.alert(
          'Failed to Load Profile',
          error.response?.data?.detail || error.message || 'Network error. Make sure backend is running.'
        );
      }
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadProfile();
  };

  const createPortfolio = async () => {
    if (!newPortfolioName.trim()) {
      Alert.alert('Error', 'Please enter a portfolio name');
      return;
    }

    setCreating(true);
    try {
      await api.post('/portfolios', {
        name: newPortfolioName.trim(),
        portfolio_type: newPortfolioType,
      });
      Alert.alert('Success', 'Portfolio created successfully!');
      setShowCreateModal(false);
      setNewPortfolioName('');
      setNewPortfolioType('individual');
      loadProfile();
    } catch (error: any) {
      console.error('Failed to create portfolio:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create portfolio');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={{ marginTop: 16, color: '#666' }}>Loading...</Text>
      </View>
    );
  }

  if (!profile && !loading) {
    return (
      <View style={styles.centerContainer}>
        {hasError ? (
          <>
            <Ionicons name="alert-circle" size={48} color={colors.warning} style={{ marginBottom: spacing.md }} />
            <Text style={{ color: '#666', marginBottom: 8, fontSize: 16 }}>Unable to load profile</Text>
            <Text style={{ color: '#999', marginBottom: 16, fontSize: 14, textAlign: 'center', paddingHorizontal: 20 }}>
              {retryCount >= 3 
                ? 'Please check your connection and make sure the backend is running.'
                : 'This might be your first time signing in. Your profile will be created automatically.'}
            </Text>
            <TouchableOpacity
              style={styles.button}
              onPress={() => {
                setRetryCount(0);
                setHasError(false);
                setLoading(true);
                loadProfile();
              }}
            >
              <Text style={styles.buttonText}>Retry</Text>
            </TouchableOpacity>
          </>
        ) : (
          <>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={{ color: '#666', marginTop: spacing.md, fontSize: 16 }}>Loading profile...</Text>
          </>
        )}
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.greeting}>Welcome back!</Text>
            <Text style={styles.email}>{user?.email}</Text>
          </View>
          <TouchableOpacity
            style={styles.signOutButton}
            onPress={async () => {
              Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Sign Out',
                  style: 'destructive',
                  onPress: async () => {
                    try {
                      await signOut();
                      // Navigation will happen automatically via AuthContext state change
                    } catch (error) {
                      console.error('Sign out error:', error);
                      Alert.alert('Error', 'Failed to sign out. Please try again.');
                    }
                  },
                },
              ]);
            }}
            activeOpacity={0.7}
          >
            <Ionicons name="log-out-outline" size={32} color={colors.error} />
          </TouchableOpacity>
        </View>
      </View>

      {profile && (
        <>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="trending-up" size={24} color={colors.primary} />
              <Text style={styles.cardLabel}>Total Net Worth</Text>
            </View>
            <Text style={styles.cardValue}>
              ${(profile.total_net_worth || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
          </View>

          <View style={styles.statsRow}>
            <View style={[styles.card, styles.halfCard]}>
              <View style={styles.cardHeader}>
                <Ionicons name="pie-chart" size={20} color={colors.info} />
                <Text style={styles.cardLabel}>Portfolio Value</Text>
              </View>
              <Text style={styles.cardValue}>
                ${(profile.total_portfolio_value || 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>

            <View style={[styles.card, styles.halfCard]}>
              <View style={styles.cardHeader}>
                <Ionicons name="cash" size={20} color={colors.success} />
                <Text style={styles.cardLabel}>Cash Balance</Text>
              </View>
              <Text style={styles.cardValue}>
                ${(profile.total_portfolio_cash || 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
          </View>

          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="calendar" size={24} color={colors.dividend} />
              <Text style={styles.cardLabel}>Total Dividends Received</Text>
            </View>
            <Text style={styles.cardValue}>
              ${(profile.total_dividends_received || 0).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
          </View>

          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Ionicons name="folder" size={24} color={colors.text} />
              <Text style={styles.sectionTitle}>Portfolios</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => setShowCreateModal(true)}
              >
                <Ionicons name="add-circle" size={24} color={colors.primary} />
              </TouchableOpacity>
            </View>
            {profile.portfolios.map((portfolio) => (
              <TouchableOpacity
                key={portfolio.id}
                style={styles.portfolioCard}
                onPress={() =>
                  navigation.navigate('Portfolio', { portfolioId: portfolio.id })
                }
              >
                <View style={styles.portfolioHeader}>
                  <View style={styles.portfolioHeaderLeft}>
                    <Ionicons 
                      name={portfolio.portfolio_type === 'retirement' ? 'shield' : 'briefcase'} 
                      size={24} 
                      color={colors.primary} 
                    />
                    <View style={styles.portfolioInfo}>
                      <Text style={styles.portfolioName}>{portfolio.name}</Text>
                      <Text style={styles.portfolioType}>{portfolio.portfolio_type}</Text>
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
                </View>
                <View style={styles.portfolioStats}>
                  <View style={styles.portfolioStat}>
                    <Text style={styles.portfolioLabel}>Value</Text>
                    <Text style={styles.portfolioValue}>
                      ${(portfolio.total_value || 0).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                  </View>
                  <View style={styles.portfolioStat}>
                    <Text style={styles.portfolioLabel}>Cash</Text>
                    <Text style={styles.portfolioValue}>
                      ${(portfolio.cash_balance || 0).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </>
      )}

      <Modal
        visible={showCreateModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowCreateModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 100}
        >
          <TouchableOpacity
            style={styles.modalOverlay}
            activeOpacity={1}
            onPress={() => setShowCreateModal(false)}
          >
            <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()}>
              <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Create New Portfolio</Text>
                <TouchableOpacity
                  style={styles.closeButton}
                  onPress={() => {
                    setShowCreateModal(false);
                    setNewPortfolioName('');
                    setNewPortfolioType('individual');
                  }}
                >
                  <Ionicons name="close" size={24} color={colors.text} />
                </TouchableOpacity>
              </View>

            <View style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Portfolio Name</Text>
                <TextInput
                  style={styles.input}
                  value={newPortfolioName}
                  onChangeText={setNewPortfolioName}
                  placeholder="My Portfolio"
                  placeholderTextColor={colors.textTertiary}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Portfolio Type</Text>
                <View style={styles.pickerContainer}>
                  <Picker
                    selectedValue={newPortfolioType}
                    onValueChange={(value) => setNewPortfolioType(value)}
                    style={styles.picker}
                  >
                    <Picker.Item label="Individual" value="individual" />
                    <Picker.Item label="Retirement" value="retirement" />
                  </Picker>
                </View>
              </View>

              <TouchableOpacity
                style={[styles.createButton, creating && styles.buttonDisabled]}
                onPress={createPortfolio}
                disabled={creating}
              >
                {creating ? (
                  <ActivityIndicator color={colors.surface} />
                ) : (
                  <>
                    <Ionicons name="checkmark-circle" size={20} color={colors.surface} />
                    <Text style={styles.createButtonText}>Create Portfolio</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
            </View>
          </TouchableOpacity>
        </TouchableOpacity>
        </KeyboardAvoidingView>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  header: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  signOutButton: {
    padding: spacing.md,
    backgroundColor: colors.errorLight,
    borderRadius: borderRadius.md,
    ...shadows.sm,
  },
  greeting: {
    ...typography.h2,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  email: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    margin: spacing.md,
    ...shadows.md,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    gap: spacing.sm,
  },
  halfCard: {
    flex: 1,
    marginHorizontal: spacing.sm,
  },
  statsRow: {
    flexDirection: 'row',
    marginHorizontal: spacing.md,
  },
  cardLabel: {
    ...typography.label,
    color: colors.textSecondary,
  },
  cardValue: {
    ...typography.h1,
    color: colors.text,
    marginTop: spacing.xs,
  },
  section: {
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.text,
  },
  portfolioCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    ...shadows.md,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  portfolioHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  portfolioInfo: {
    flex: 1,
  },
  portfolioName: {
    ...typography.h4,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  portfolioType: {
    ...typography.caption,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  portfolioStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  portfolioStat: {
    alignItems: 'center',
  },
  portfolioLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  portfolioValue: {
    ...typography.h4,
    color: colors.text,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
  },
  buttonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
  },
  addButton: {
    marginLeft: 'auto',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.lg,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  modalTitle: {
    ...typography.h3,
    color: colors.text,
    flex: 1,
  },
  closeButton: {
    padding: 4,
    marginLeft: spacing.sm,
  },
  modalBody: {
    gap: spacing.md,
  },
  inputGroup: {
    marginBottom: spacing.md,
  },
  label: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  input: {
    ...typography.body,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceSecondary,
    color: colors.text,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceSecondary,
  },
  picker: {
    color: colors.text,
  },
  createButton: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  createButtonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});

