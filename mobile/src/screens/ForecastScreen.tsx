import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { api, Portfolio } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

interface ForecastData {
  series: Array<{
    month: string;
    income: number;
    has_dividend: boolean;
  }>;
  scenarios: {
    conservative: number;
    moderate: number;
    optimistic: number;
    pessimistic: number;
  };
  assumptions: {
    growth_rate: number;
    reinvest: boolean;
  };
}

export default function ForecastScreen({ navigation }: any) {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null);
  const [months, setMonths] = useState(12);
  const [monthsText, setMonthsText] = useState('12'); // String state for input
  const [growthScenario, setGrowthScenario] = useState('moderate');
  const [reinvest, setReinvest] = useState(true);
  const [recurringDeposit, setRecurringDeposit] = useState('0');
  const [loading, setLoading] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const data = await api.get<Portfolio[]>('/portfolios');
      setPortfolios(data);
      if (data.length > 0) {
        setSelectedPortfolioId(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load portfolios:', error);
      Alert.alert('Error', 'Failed to load portfolios');
    }
  };

  const runForecast = async () => {
    if (!selectedPortfolioId) {
      Alert.alert('Error', 'Please select a portfolio');
      return;
    }

    setLoading(true);
    try {
      const data = await api.post<ForecastData>('/forecasts/monthly', {
        portfolio_id: selectedPortfolioId,
        months: months,
        assume_reinvest: reinvest,
        recurring_deposit: parseFloat(recurringDeposit) || 0,
        growth_scenario: growthScenario,
      });
      setForecastData(data);
    } catch (error: any) {
      console.error('Forecast failed:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to run forecast');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="trending-up" size={32} color={colors.primary} />
        <Text style={styles.title}>Cashflow Forecast</Text>
        <Text style={styles.subtitle}>Project your future dividend income</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Portfolio Selection</Text>
        {portfolios.length === 0 ? (
          <Text style={styles.emptyText}>No portfolios available</Text>
        ) : (
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={selectedPortfolioId}
              onValueChange={(value) => setSelectedPortfolioId(value)}
              style={styles.picker}
            >
              {portfolios.map((p) => (
                <Picker.Item key={p.id} label={p.name} value={p.id} />
              ))}
            </Picker>
          </View>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Forecast Parameters</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Forecast Period (months)</Text>
          <TextInput
            style={styles.input}
            value={monthsText}
            onChangeText={(text) => {
              // Allow empty string and numbers only
              if (text === '' || /^\d+$/.test(text)) {
                setMonthsText(text);
                const num = parseInt(text);
                if (!isNaN(num) && num > 0) {
                  setMonths(num);
                }
              }
            }}
            onBlur={() => {
              // Validate on blur - if empty or invalid, set to default
              const num = parseInt(monthsText);
              if (isNaN(num) || num <= 0) {
                setMonthsText('12');
                setMonths(12);
              } else {
                setMonthsText(num.toString());
              }
            }}
            keyboardType="numeric"
            placeholder="12"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Growth Scenario</Text>
          <View style={styles.pickerContainer}>
            <Picker
              selectedValue={growthScenario}
              onValueChange={setGrowthScenario}
              style={styles.picker}
            >
              <Picker.Item label="Conservative (0%)" value="conservative" />
              <Picker.Item label="Moderate (2%)" value="moderate" />
              <Picker.Item label="Optimistic (5%)" value="optimistic" />
              <Picker.Item label="Pessimistic (-5%)" value="pessimistic" />
            </Picker>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Recurring Deposit ($/month)</Text>
          <TextInput
            style={styles.input}
            value={recurringDeposit}
            onChangeText={setRecurringDeposit}
            keyboardType="numeric"
            placeholder="0"
          />
        </View>

        <TouchableOpacity
          style={[styles.checkboxContainer, styles.inputGroup]}
          onPress={() => setReinvest(!reinvest)}
        >
          <Ionicons
            name={reinvest ? 'checkbox' : 'checkbox-outline'}
            size={24}
            color={colors.primary}
          />
          <Text style={styles.checkboxLabel}>Reinvest Dividends (DRIP)</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={runForecast}
        disabled={loading || !selectedPortfolioId}
      >
        {loading ? (
          <ActivityIndicator color={colors.surface} />
        ) : (
          <>
            <Ionicons name="rocket" size={20} color={colors.surface} />
            <Text style={styles.buttonText}>Run Forecast</Text>
          </>
        )}
      </TouchableOpacity>

      {forecastData && forecastData.scenarios && (
        <View style={styles.resultsCard}>
          <Text style={styles.resultsTitle}>Forecast Results</Text>
          
          <View style={styles.scenariosContainer}>
            <Text style={styles.scenariosTitle}>Projected Total Income</Text>
            <View style={styles.scenarioRow}>
              <Text style={styles.scenarioLabel}>Conservative:</Text>
              <Text style={styles.scenarioValue}>
                ${((forecastData.scenarios?.conservative || 0)).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
            <View style={styles.scenarioRow}>
              <Text style={styles.scenarioLabel}>Moderate:</Text>
              <Text style={[styles.scenarioValue, styles.highlighted]}>
                ${((forecastData.scenarios?.moderate || 0)).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
            <View style={styles.scenarioRow}>
              <Text style={styles.scenarioLabel}>Optimistic:</Text>
              <Text style={styles.scenarioValue}>
                ${((forecastData.scenarios?.optimistic || 0)).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
            <View style={styles.scenarioRow}>
              <Text style={styles.scenarioLabel}>Pessimistic:</Text>
              <Text style={styles.scenarioValue}>
                ${((forecastData.scenarios?.pessimistic || 0)).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
          </View>

          {forecastData.series && forecastData.series.length > 0 && (
            <View style={styles.monthlyBreakdown}>
              <Text style={styles.breakdownTitle}>Monthly Breakdown</Text>
              {forecastData.series.slice(0, 6).map((item, index) => (
                <View key={index} style={styles.monthRow}>
                  <Text style={styles.monthLabel}>{item.month}</Text>
                  <Text style={styles.monthValue}>
                    ${(item.income || 0).toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </Text>
                </View>
              ))}
              {forecastData.series.length > 6 && (
                <Text style={styles.moreText}>
                  + {forecastData.series.length - 6} more months...
                </Text>
              )}
            </View>
          )}
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
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    margin: spacing.md,
    ...shadows.md,
  },
  cardTitle: {
    ...typography.h4,
    color: colors.text,
    marginBottom: spacing.md,
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
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  checkboxLabel: {
    ...typography.body,
    color: colors.text,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    margin: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    ...shadows.md,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    ...typography.body,
    color: colors.surface,
    fontWeight: '600',
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    padding: spacing.md,
  },
  resultsCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    margin: spacing.md,
    ...shadows.md,
  },
  resultsTitle: {
    ...typography.h3,
    color: colors.text,
    marginBottom: spacing.md,
  },
  scenariosContainer: {
    marginBottom: spacing.lg,
  },
  scenariosTitle: {
    ...typography.h4,
    color: colors.text,
    marginBottom: spacing.md,
  },
  scenarioRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  scenarioLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },
  scenarioValue: {
    ...typography.h4,
    color: colors.text,
  },
  highlighted: {
    color: colors.primary,
    fontWeight: '700',
  },
  monthlyBreakdown: {
    marginTop: spacing.md,
  },
  breakdownTitle: {
    ...typography.h4,
    color: colors.text,
    marginBottom: spacing.md,
  },
  monthRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  monthLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },
  monthValue: {
    ...typography.body,
    color: colors.text,
    fontWeight: '600',
  },
  moreText: {
    ...typography.caption,
    color: colors.textTertiary,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});

