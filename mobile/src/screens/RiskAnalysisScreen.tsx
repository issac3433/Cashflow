import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { api, Portfolio } from '../services/api';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { spacing, borderRadius, shadows } from '../theme/spacing';

interface RiskData {
  risk_score: number;
  overall_risk_level: string;
  volatility: number;
  beta: number;
  sharpe_ratio: number;
  max_drawdown: number;
  var_95: number;
  concentration_risk: number;
  concentration?: {
    max_weight: number;
    top_holdings: Array<{ symbol: string; weight: number }>;
  };
}

export default function RiskAnalysisScreen() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null);
  const [analysisType, setAnalysisType] = useState<'Comprehensive' | 'Quick Overview'>('Quick Overview');
  const [loading, setLoading] = useState(false);
  const [riskData, setRiskData] = useState<RiskData | null>(null);

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

  const runAnalysis = async () => {
    if (!selectedPortfolioId) {
      Alert.alert('Error', 'Please select a portfolio');
      return;
    }

    setLoading(true);
    try {
      const endpoint = analysisType === 'Comprehensive' 
        ? `/risk/analysis/${selectedPortfolioId}`
        : `/risk/metrics/${selectedPortfolioId}`;
      const data = await api.get<RiskData>(endpoint);
      setRiskData(data);
    } catch (error: any) {
      console.error('Risk analysis failed:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to run risk analysis');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low':
        return colors.success;
      case 'moderate':
        return colors.warning;
      case 'high':
        return colors.error;
      default:
        return colors.textSecondary;
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="warning" size={32} color={colors.warning} />
        <Text style={styles.title}>Risk Analysis</Text>
        <Text style={styles.subtitle}>Comprehensive portfolio risk assessment</Text>
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
        <Text style={styles.cardTitle}>Analysis Type</Text>
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={analysisType}
            onValueChange={(value) => setAnalysisType(value)}
            style={styles.picker}
          >
            <Picker.Item label="Quick Overview" value="Quick Overview" />
            <Picker.Item label="Comprehensive" value="Comprehensive" />
          </Picker>
        </View>
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={runAnalysis}
        disabled={loading || !selectedPortfolioId}
      >
        {loading ? (
          <ActivityIndicator color={colors.surface} />
        ) : (
          <>
            <Ionicons name="analytics" size={20} color={colors.surface} />
            <Text style={styles.buttonText}>Run Risk Analysis</Text>
          </>
        )}
      </TouchableOpacity>

      {riskData && (
        <View style={styles.resultsCard}>
          <Text style={styles.resultsTitle}>Risk Overview</Text>
          
          <View style={styles.riskScoreCard}>
            <Text style={styles.riskScoreLabel}>Overall Risk Level</Text>
            <View style={[styles.riskBadge, { backgroundColor: getRiskColor(riskData.overall_risk_level) + '20' }]}>
              <Text style={[styles.riskBadgeText, { color: getRiskColor(riskData.overall_risk_level) }]}>
                {riskData.overall_risk_level.toUpperCase()}
              </Text>
            </View>
            <Text style={styles.riskScoreValue}>Score: {riskData.risk_score.toFixed(1)}/100</Text>
          </View>

          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <Ionicons name="pulse" size={24} color={colors.info} />
              <Text style={styles.metricLabel}>Volatility</Text>
              <Text style={styles.metricValue}>{(riskData.volatility * 100).toFixed(2)}%</Text>
            </View>
            <View style={styles.metricCard}>
              <Ionicons name="trending-up" size={24} color={colors.primary} />
              <Text style={styles.metricLabel}>Beta</Text>
              <Text style={styles.metricValue}>{riskData.beta.toFixed(2)}</Text>
            </View>
            <View style={styles.metricCard}>
              <Ionicons name="stats-chart" size={24} color={colors.success} />
              <Text style={styles.metricLabel}>Sharpe Ratio</Text>
              <Text style={styles.metricValue}>{riskData.sharpe_ratio.toFixed(2)}</Text>
            </View>
            <View style={styles.metricCard}>
              <Ionicons name="arrow-down" size={24} color={colors.error} />
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={styles.metricValue}>{(riskData.max_drawdown * 100).toFixed(2)}%</Text>
            </View>
            <View style={styles.metricCard}>
              <Ionicons name="alert-circle" size={24} color={colors.warning} />
              <Text style={styles.metricLabel}>VaR (95%)</Text>
              <Text style={styles.metricValue}>
                ${Math.abs(riskData.var_95).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>
            <View style={styles.metricCard}>
              <Ionicons name="layers" size={24} color={colors.dividend} />
              <Text style={styles.metricLabel}>Concentration</Text>
              <Text style={styles.metricValue}>{(riskData.concentration_risk * 100).toFixed(1)}%</Text>
            </View>
          </View>

          {riskData.concentration?.top_holdings && riskData.concentration.top_holdings.length > 0 && (
            <View style={styles.concentrationSection}>
              <Text style={styles.sectionTitle}>Top Holdings by Weight</Text>
              {riskData.concentration.top_holdings.slice(0, 5).map((holding, index) => (
                <View key={index} style={styles.holdingRow}>
                  <Text style={styles.holdingSymbol}>{holding.symbol}</Text>
                  <Text style={styles.holdingWeight}>
                    {(holding.weight * 100).toFixed(1)}%
                  </Text>
                </View>
              ))}
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
  pickerContainer: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceSecondary,
  },
  picker: {
    color: colors.text,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    padding: spacing.md,
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
  riskScoreCard: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  riskScoreLabel: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  riskBadge: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
    marginBottom: spacing.sm,
  },
  riskBadgeText: {
    ...typography.label,
    fontWeight: '700',
  },
  riskScoreValue: {
    ...typography.h4,
    color: colors.text,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  metricCard: {
    width: '48%',
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  metricLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    marginBottom: spacing.xs,
  },
  metricValue: {
    ...typography.h4,
    color: colors.text,
    fontWeight: '700',
  },
  concentrationSection: {
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  sectionTitle: {
    ...typography.h4,
    color: colors.text,
    marginBottom: spacing.md,
  },
  holdingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  holdingSymbol: {
    ...typography.body,
    color: colors.text,
    fontWeight: '600',
  },
  holdingWeight: {
    ...typography.body,
    color: colors.textSecondary,
  },
});

