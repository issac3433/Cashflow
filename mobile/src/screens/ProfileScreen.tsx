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
import { useAuth } from '../context/AuthContext';
import { api, UserProfile } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

export default function ProfileScreen({ navigation }: any) {
  const { user, signOut } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCashModal, setShowCashModal] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null);
  const [cashAction, setCashAction] = useState<'add' | 'withdraw' | null>(null);
  const [cashAmount, setCashAmount] = useState('');

  const loadProfile = async () => {
    try {
      const data = await api.get<UserProfile>('/profile');
      setProfile(data);
    } catch (error) {
      console.error('Failed to load profile:', error);
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
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

  const handleCashAction = async () => {
    if (!selectedPortfolio || !cashAction || !cashAmount || parseFloat(cashAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    try {
      const endpoint = cashAction === 'add' ? '/profile/cash/add' : '/profile/cash/withdraw';
      await api.post(endpoint, {
        amount: parseFloat(cashAmount),
        portfolio_id: selectedPortfolio,
      });
      setShowCashModal(false);
      setSelectedPortfolio(null);
      setCashAction(null);
      setCashAmount('');
      loadProfile();
      Alert.alert('Success', `Cash ${cashAction === 'add' ? 'added' : 'withdrawn'} successfully`);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || `Failed to ${cashAction} cash`);
    }
  };

  const handleLogout = async () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await signOut();
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.email}>{user?.email}</Text>
      </View>

      {profile && (
        <>
          <View style={styles.card}>
            <Text style={styles.cardLabel}>Total Net Worth</Text>
            <Text style={styles.cardValue}>
              ${profile.total_net_worth.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Portfolio Cash Management</Text>
            {profile.portfolios.map((portfolio) => (
              <View key={portfolio.id} style={styles.portfolioCard}>
                <View style={styles.portfolioHeader}>
                  <Text style={styles.portfolioName}>{portfolio.name}</Text>
                  <Text style={styles.portfolioType}>{portfolio.portfolio_type}</Text>
                </View>
                <Text style={styles.cashBalance}>
                  Cash: ${portfolio.cash_balance.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </Text>
                <View style={styles.cashButtons}>
                  <TouchableOpacity
                    style={[styles.cashButton, styles.addButton]}
                    onPress={() => {
                      setSelectedPortfolio(portfolio.id);
                      setCashAction('add');
                      setShowCashModal(true);
                    }}
                  >
                    <Text style={styles.cashButtonText}>Add Cash</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.cashButton, styles.withdrawButton]}
                    onPress={() => {
                      setSelectedPortfolio(portfolio.id);
                      setCashAction('withdraw');
                      setShowCashModal(true);
                    }}
                  >
                    <Text style={styles.cashButtonText}>Withdraw</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>

          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={20} color={colors.surface} />
            <Text style={styles.logoutButtonText}>Sign Out</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Cash Modal */}
      <Modal
        visible={showCashModal}
        animationType="slide"
        transparent
        onRequestClose={() => {
          setShowCashModal(false);
          setSelectedPortfolio(null);
          setCashAction(null);
          setCashAmount('');
        }}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 100}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              {cashAction === 'add' ? 'Add Cash' : 'Withdraw Cash'}
            </Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Amount"
              value={cashAmount}
              onChangeText={setCashAmount}
              keyboardType="decimal-pad"
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setShowCashModal(false);
                  setSelectedPortfolio(null);
                  setCashAction(null);
                  setCashAmount('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.submitButton]}
                onPress={handleCashAction}
              >
                <Text style={styles.submitButtonText}>
                  {cashAction === 'add' ? 'Add' : 'Withdraw'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
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
  },
  header: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    ...shadows.sm,
  },
  title: {
    ...typography.h2,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  email: {
    ...typography.body,
    color: colors.textSecondary,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    margin: spacing.md,
    ...shadows.md,
  },
  cardLabel: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  cardValue: {
    ...typography.h1,
    color: colors.text,
  },
  section: {
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.text,
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
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
    marginBottom: spacing.sm,
  },
  portfolioName: {
    ...typography.h4,
    color: colors.text,
  },
  portfolioType: {
    ...typography.caption,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  cashBalance: {
    ...typography.body,
    color: colors.text,
    marginBottom: spacing.md,
    fontWeight: '600',
  },
  cashButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  cashButton: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  addButton: {
    backgroundColor: colors.successLight,
  },
  withdrawButton: {
    backgroundColor: colors.errorLight,
  },
  cashButtonText: {
    ...typography.label,
    color: colors.text,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: colors.error,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    margin: spacing.md,
    marginTop: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    ...shadows.md,
  },
  logoutButtonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
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
    paddingBottom: spacing.xl,
  },
  modalTitle: {
    ...typography.h3,
    marginBottom: spacing.lg,
    color: colors.text,
  },
  modalInput: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    marginBottom: spacing.md,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  modalButton: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: colors.surfaceSecondary,
  },
  cancelButtonText: {
    ...typography.body,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: colors.primary,
    ...shadows.sm,
  },
  submitButtonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
  },
});

