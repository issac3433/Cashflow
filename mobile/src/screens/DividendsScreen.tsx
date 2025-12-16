import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api, Portfolio } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

interface DividendEvent {
  symbol: string;
  ex_date: string | null;
  pay_date: string | null;
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
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadCalendar();
  }, []);

  const loadCalendar = async () => {
    try {
      setLoading(true);
      console.log('[Dividends] Loading calendar...');
      const data = await api.get<CalendarData>('/calendar');
      console.log('[Dividends] Calendar data received:', {
        eventCount: data?.events?.length || 0,
        events: data?.events?.slice(0, 3), // Log first 3 events for debugging
      });
      // Handle both successful empty responses and errors gracefully
      setCalendarData(data || { events: [] });
    } catch (error: any) {
      console.error('[Dividends] Error loading calendar:', error);
      // On error, set empty data instead of showing alert - graceful degradation
      setCalendarData({ events: [] });
      // Only show alert for non-500 errors (network issues, etc.)
      if (error.response?.status !== 500) {
        Alert.alert('Error', error.response?.data?.detail || 'Failed to load dividend calendar');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadCalendar();
  };

  const syncDividends = async () => {
    setSyncing(true);
    try {
      console.log('[Dividends] Starting sync...');
      // Get all portfolios for the user
      const portfolios = await api.get<Portfolio[]>('/portfolios');
      console.log('[Dividends] Found portfolios:', portfolios?.length || 0);
      
      if (!portfolios || portfolios.length === 0) {
        Alert.alert('No Portfolios', 'You need to create a portfolio first');
        setSyncing(false);
        return;
      }

      // Sync dividends for each portfolio
      let portfoliosSynced = 0;
      let totalSymbols = 0;
      let totalInserted = 0;
      const errors: string[] = [];

      for (const portfolio of portfolios) {
        try {
          console.log(`[Dividends] Syncing portfolio ${portfolio.id} (${portfolio.name})...`);
          const result = await api.post<{
            portfolio_id: number;
            symbols: string[];
            inserted: number;
            per_symbol: Record<string, number>;
          }>(`/dividends/sync/portfolio/${portfolio.id}`);
          
          console.log(`[Dividends] Portfolio ${portfolio.id} sync result:`, result);
          
          // Check if we got symbols (even if empty array)
          if (result && result.symbols) {
            if (result.symbols.length > 0) {
              portfoliosSynced++;
              totalSymbols += result.symbols.length;
              totalInserted += result.inserted || 0;
              console.log(`[Dividends] Portfolio ${portfolio.id}: ${result.symbols.length} symbols, ${result.inserted} events inserted`);
            } else {
              console.log(`[Dividends] Portfolio ${portfolio.id} has no holdings`);
            }
            // If symbols array is empty, portfolio has no holdings - that's okay
          }
        } catch (error: any) {
          // Log the error but continue with other portfolios
          console.error(`[Dividends] Error syncing portfolio ${portfolio.id}:`, error);
          const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
          errors.push(`${portfolio.name}: ${errorMessage}`);
        }
      }

      // Reload calendar after sync
      await loadCalendar();
      
      if (totalSymbols === 0 && portfolios.length > 0) {
        // Check if we have any holdings at all
        let hasHoldings = false;
        try {
          for (const portfolio of portfolios) {
            const portfolioData = await api.get<{ holdings?: any[] }>(`/portfolios/${portfolio.id}`);
            if (portfolioData?.holdings && portfolioData.holdings.length > 0) {
              hasHoldings = true;
              break;
            }
          }
        } catch (e) {
          // Ignore errors checking holdings
        }
        
        if (hasHoldings) {
          Alert.alert(
            'Sync Complete', 
            'Dividends synced, but no dividend events were found for your stocks. Some stocks may not pay dividends, or dividend data may not be available yet.'
          );
        } else {
          Alert.alert(
            'No Stocks Found', 
            'Add some stocks to your portfolios to sync dividends'
          );
        }
      } else if (errors.length > 0) {
        Alert.alert(
          'Partial Success',
          `Synced ${totalSymbols} stock${totalSymbols !== 1 ? 's' : ''} from ${portfoliosSynced} portfolio${portfoliosSynced !== 1 ? 's' : ''} (${totalInserted} events). Some errors occurred.`
        );
      } else {
        Alert.alert(
          'Success', 
          `Synced dividends for ${totalSymbols} stock${totalSymbols !== 1 ? 's' : ''} from ${portfoliosSynced} portfolio${portfoliosSynced !== 1 ? 's' : ''} (${totalInserted} events)`
        );
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to sync dividends';
      Alert.alert('Error', errorMessage);
    } finally {
      setSyncing(false);
    }
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
          <Text style={styles.emptyText}>No Dividends Yet</Text>
          <Text style={styles.emptySubtext}>
            {syncing 
              ? 'Syncing dividend data from your portfolios...'
              : 'Press "Sync Dividends" to fetch dividend information for your stocks. This may take a moment.'}
          </Text>
          <TouchableOpacity
            style={styles.syncButtonEmpty}
            onPress={syncDividends}
            disabled={syncing}
          >
            {syncing ? (
              <ActivityIndicator size="small" color={colors.surface} />
            ) : (
              <>
                <Ionicons name="refresh" size={18} color={colors.surface} />
                <Text style={styles.syncButtonTextEmpty}>Sync Dividends</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  const events = calendarData.events;
  const totalDividends = events.reduce((sum, e) => sum + (e.cash || 0), 0);
  const uniqueSymbols = new Set(events.map((e) => e.symbol)).size;
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Reset time to start of day for accurate comparison
  
  // Filter events by pay_date, falling back to ex_date if pay_date is null
  const upcomingEvents = events.filter((e) => {
    const dateStr = e.pay_date || e.ex_date;
    if (!dateStr) return false;
    const eventDate = new Date(dateStr);
    eventDate.setHours(0, 0, 0, 0);
    return eventDate >= today;
  });
  
  const pastEvents = events.filter((e) => {
    const dateStr = e.pay_date || e.ex_date;
    if (!dateStr) return false;
    const eventDate = new Date(dateStr);
    eventDate.setHours(0, 0, 0, 0);
    return eventDate < today;
  });

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Ionicons name="calendar" size={32} color={colors.primary} />
        <Text style={styles.title}>Dividend Calendar</Text>
        <Text style={styles.subtitle}>Track your upcoming dividend payments</Text>
        <TouchableOpacity
          style={styles.syncButton}
          onPress={syncDividends}
          disabled={syncing}
        >
          {syncing ? (
            <ActivityIndicator size="small" color={colors.primary} />
          ) : (
            <>
              <Ionicons name="refresh" size={16} color={colors.primary} />
              <Text style={styles.syncButtonText}>Sync Dividends</Text>
            </>
          )}
        </TouchableOpacity>
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
            ${upcomingEvents.reduce((sum, e) => sum + (e.cash || 0), 0).toLocaleString('en-US', {
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
            .sort((a, b) => {
              const dateA = new Date(a.pay_date || a.ex_date || '').getTime();
              const dateB = new Date(b.pay_date || b.ex_date || '').getTime();
              return dateA - dateB;
            })
            .slice(0, 10)
            .map((event, index) => {
              const displayDate = event.pay_date || event.ex_date;
              const dateLabel = event.pay_date ? 'Pay' : 'Ex-Date';
              return (
                <View key={index} style={styles.eventCard}>
                  <View style={styles.eventHeader}>
                    <View style={styles.eventSymbol}>
                      <Text style={styles.symbolText}>{event.symbol}</Text>
                    </View>
                    <Text style={styles.eventAmount}>
                      ${(event.cash || 0).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                  </View>
                  <View style={styles.eventDetails}>
                    {displayDate && (
                      <View style={styles.eventDetail}>
                        <Ionicons name="calendar-outline" size={16} color={colors.textSecondary} />
                        <Text style={styles.eventDetailText}>
                          {dateLabel}: {new Date(displayDate).toLocaleDateString()}
                        </Text>
                      </View>
                    )}
                    <View style={styles.eventDetail}>
                      <Ionicons name="layers-outline" size={16} color={colors.textSecondary} />
                      <Text style={styles.eventDetailText}>{event.shares || 0} shares</Text>
                    </View>
                  </View>
                </View>
              );
            })}
        </View>
      )}

      {pastEvents.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Ionicons name="checkmark-circle" size={24} color={colors.success} />
            <Text style={styles.sectionTitle}>Recent Payments</Text>
          </View>
          {pastEvents
            .sort((a, b) => {
              const dateA = new Date(a.pay_date || a.ex_date || '').getTime();
              const dateB = new Date(b.pay_date || b.ex_date || '').getTime();
              return dateB - dateA; // Reverse order for past events (newest first)
            })
            .slice(0, 5)
            .map((event, index) => {
              const displayDate = event.pay_date || event.ex_date;
              return (
                <View key={index} style={styles.eventCard}>
                  <View style={styles.eventHeader}>
                    <View style={styles.eventSymbol}>
                      <Text style={styles.symbolText}>{event.symbol}</Text>
                    </View>
                    <Text style={styles.eventAmount}>
                      ${(event.cash || 0).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                  </View>
                  <View style={styles.eventDetails}>
                    {displayDate && (
                      <Text style={styles.eventDetailText}>
                        Paid: {new Date(displayDate).toLocaleDateString()}
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
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
    marginBottom: spacing.lg,
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
    marginTop: spacing.md,
    gap: spacing.xs,
  },
  syncButtonText: {
    ...typography.label,
    color: colors.primary,
    fontWeight: '600',
  },
  syncButtonEmpty: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    marginTop: spacing.md,
    gap: spacing.sm,
    ...shadows.md,
  },
  syncButtonTextEmpty: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
  },
});

