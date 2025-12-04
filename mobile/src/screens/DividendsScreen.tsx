import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

interface DividendEvent {
  symbol: string;
  ex_date: string;
  pay_date: string;
  cash: number;
  shares: number;
}

interface CalendarData {
  events: DividendEvent[];
}

export default function DividendsScreen() {
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadCalendar();
  }, []);

  const loadCalendar = async () => {
    try {
      setLoading(true);
      const data = await api.get<CalendarData>('/calendar');
      setCalendarData(data);
    } catch (error: any) {
      console.error('Failed to load dividend calendar:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to load dividend calendar');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadCalendar();
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading dividend calendar...</Text>
      </View>
    );
  }

  if (!calendarData || !calendarData.events || calendarData.events.length === 0) {
    return (
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.header}>
          <Ionicons name="calendar" size={32} color={colors.primary} />
          <Text style={styles.title}>Dividend Calendar</Text>
          <Text style={styles.subtitle}>Track your upcoming dividend payments</Text>
        </View>
        <View style={styles.emptyContainer}>
          <Ionicons name="calendar-outline" size={64} color={colors.textTertiary} />
          <Text style={styles.emptyText}>No dividend events found</Text>
          <Text style={styles.emptySubtext}>
            Add some holdings to see upcoming dividends!
          </Text>
        </View>
      </ScrollView>
    );
  }

  const events = calendarData.events;
  const totalDividends = events.reduce((sum, e) => sum + e.cash, 0);
  const uniqueSymbols = new Set(events.map((e) => e.symbol)).size;
  const today = new Date();
  const upcomingEvents = events.filter(
    (e) => new Date(e.pay_date) >= today
  );
  const pastEvents = events.filter((e) => new Date(e.pay_date) < today);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Ionicons name="calendar" size={32} color={colors.primary} />
        <Text style={styles.title}>Dividend Calendar</Text>
        <Text style={styles.subtitle}>Track your upcoming dividend payments</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Ionicons name="cash" size={24} color={colors.dividend} />
          <Text style={styles.statValue}>
            ${totalDividends.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Text>
          <Text style={styles.statLabel}>Total Dividends</Text>
        </View>
        <View style={styles.statCard}>
          <Ionicons name="arrow-forward" size={24} color={colors.info} />
          <Text style={styles.statValue}>
            ${upcomingEvents.reduce((sum, e) => sum + e.cash, 0).toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Text>
          <Text style={styles.statLabel}>Upcoming</Text>
        </View>
        <View style={styles.statCard}>
          <Ionicons name="trending-up" size={24} color={colors.success} />
          <Text style={styles.statValue}>{uniqueSymbols}</Text>
          <Text style={styles.statLabel}>Paying Stocks</Text>
        </View>
      </View>

      {upcomingEvents.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="arrow-forward-circle" size={24} color={colors.info} />
            <Text style={styles.sectionTitle}>Upcoming Payments</Text>
          </View>
          {upcomingEvents
            .sort((a, b) => new Date(a.pay_date).getTime() - new Date(b.pay_date).getTime())
            .slice(0, 10)
            .map((event, index) => (
              <View key={index} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={styles.eventSymbol}>
                    <Text style={styles.symbolText}>{event.symbol}</Text>
                  </View>
                  <Text style={styles.eventAmount}>
                    ${event.cash.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.eventDetails}>
                  <View style={styles.eventDetail}>
                    <Ionicons name="calendar-outline" size={16} color={colors.textSecondary} />
                    <Text style={styles.eventDetailText}>
                      Pay: {new Date(event.pay_date).toLocaleDateString()}
                    </Text>
                  </View>
                  <View style={styles.eventDetail}>
                    <Ionicons name="layers-outline" size={16} color={colors.textSecondary} />
                    <Text style={styles.eventDetailText}>{event.shares} shares</Text>
                  </View>
                </View>
              </View>
            ))}
        </View>
      )}

      {pastEvents.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="checkmark-circle" size={24} color={colors.success} />
            <Text style={styles.sectionTitle}>Recent Payments</Text>
          </View>
          {pastEvents
            .sort((a, b) => new Date(b.pay_date).getTime() - new Date(a.pay_date).getTime())
            .slice(0, 5)
            .map((event, index) => (
              <View key={index} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={styles.eventSymbol}>
                    <Text style={styles.symbolText}>{event.symbol}</Text>
                  </View>
                  <Text style={styles.eventAmount}>
                    ${event.cash.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </Text>
                </View>
                <View style={styles.eventDetails}>
                  <Text style={styles.eventDetailText}>
                    Paid: {new Date(event.pay_date).toLocaleDateString()}
                  </Text>
                </View>
              </View>
            ))}
        </View>
      )}
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
  loadingText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },
  header: {
    padding: spacing.lg,
    backgroundColor: colors.surface,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    ...typography.h2,
    color: colors.text,
    marginTop: spacing.sm,
  },
  subtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  statsRow: {
    flexDirection: 'row',
    padding: spacing.md,
    gap: spacing.sm,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
    ...shadows.sm,
  },
  statValue: {
    ...typography.h4,
    color: colors.text,
    marginTop: spacing.xs,
    marginBottom: spacing.xs,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  section: {
    marginTop: spacing.md,
    marginBottom: spacing.lg,
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
  eventCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  eventSymbol: {
    backgroundColor: colors.primaryLight,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  symbolText: {
    ...typography.label,
    color: colors.primaryDark,
    fontWeight: '700',
  },
  eventAmount: {
    ...typography.h4,
    color: colors.text,
    fontWeight: '700',
  },
  eventDetails: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  eventDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  eventDetailText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
    minHeight: 400,
  },
  emptyText: {
    ...typography.h4,
    color: colors.text,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  emptySubtext: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

