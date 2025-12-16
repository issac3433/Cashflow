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
  var_99?: number;
  concentration_risk: number;
  concentration?: {
    max_weight: number;
    top_holdings: Array<{ symbol: string; weight: number }>;
  };
  dividend_risks?: Record<string, {
    sustainability_score: number;
    risk_level: string;
    last_payment: string;
  }>;
  earnings_risks?: Record<string, {
    overall_risk_level: string;
    earnings_risk_score: number;
  }>;
  recommendations?: string[];
  portfolio_value?: number;
  num_holdings?: number;
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
      const data = await api.get<any>(endpoint);
      
      // Check if there's an error (no holdings)
      if (data.error || !data.has_holdings) {
        // Clear risk data to show empty state
        setRiskData(null);
        return;
      }
      
      setRiskData(data);
    } catch (error: any) {
      // On error, clear data to show empty state instead of alert
      setRiskData(null);
      // Only show alert for non-500 errors (network issues, etc.)
      if (error.response?.status !== 500) {
        console.error('Risk analysis failed:', error);
        Alert.alert('Error', error.response?.data?.detail || 'Failed to run risk analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    const normalizedLevel = level.toLowerCase().trim();
    switch (normalizedLevel) {
      case 'low':
      case 'very low':
        return colors.success; // Green for low risk
      case 'moderate':
      case 'medium':
        return colors.warning; // Yellow/Orange for moderate risk
      case 'high':
        return colors.error; // Red for high risk
      case 'very high':
      case 'extreme':
        return '#8B0000'; // Dark red for very high risk
      default:
        return colors.textSecondary; // Gray for unknown
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

      {!riskData && !loading && selectedPortfolioId && (
        <View style={styles.emptyContainer}>
          <Ionicons name="analytics-outline" size={64} color={colors.textTertiary} />
          <Text style={styles.emptyText}>No Stocks to Analyze</Text>
          <Text style={styles.emptySubtext}>
            Add stocks to your portfolio to see risk analysis here!
          </Text>
        </View>
      )}

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
            <Text style={[styles.riskScoreValue, { color: getRiskColor(riskData.overall_risk_level) }]}>
              Score: {riskData.risk_score.toFixed(1)}/100
            </Text>
            <View style={styles.scoreExplanation}>
              <Text style={styles.scoreExplanationText}>
                {riskData.risk_score >= 70 && '🟢 Low Risk (70-100): Stable, well-diversified portfolio'}
                {riskData.risk_score >= 50 && riskData.risk_score < 70 && '🟡 Medium Risk (50-69): Moderate volatility, some concentration'}
                {riskData.risk_score >= 30 && riskData.risk_score < 50 && '🟠 High Risk (30-49): High volatility, concentrated positions'}
                {riskData.risk_score < 30 && '🔴 Very High Risk (0-29): Extreme volatility, high concentration risk'}
              </Text>
            </View>
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

          {/* Comprehensive Analysis - Additional Metrics */}
          {analysisType === 'Comprehensive' && (
            <>
              {/* Portfolio Summary */}
              {(riskData.portfolio_value !== undefined || riskData.num_holdings !== undefined) && (
                <View style={styles.comprehensiveSection}>
                  <Text style={styles.sectionTitle}>Portfolio Summary</Text>
                  {riskData.portfolio_value !== undefined && (
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>Total Portfolio Value:</Text>
                      <Text style={styles.summaryValue}>
                        ${riskData.portfolio_value.toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </Text>
                    </View>
                  )}
                  {riskData.num_holdings !== undefined && (
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>Number of Holdings:</Text>
                      <Text style={styles.summaryValue}>{riskData.num_holdings}</Text>
                    </View>
                  )}
                  {riskData.var_99 !== undefined && (
                    <View style={styles.summaryRow}>
                      <Text style={styles.summaryLabel}>VaR (99%):</Text>
                      <Text style={styles.summaryValue}>
                        ${Math.abs(riskData.var_99).toLocaleString('en-US', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </Text>
                    </View>
                  )}
                </View>
              )}

              {/* Dividend Risk Analysis */}
              {riskData.dividend_risks && Object.keys(riskData.dividend_risks).length > 0 && (
                <View style={styles.comprehensiveSection}>
                  <Text style={styles.sectionTitle}>Dividend Risk Analysis</Text>
                  {Object.entries(riskData.dividend_risks).map(([symbol, risk]) => (
                    <View key={symbol} style={styles.riskItem}>
                      <View style={styles.riskItemHeader}>
                        <Text style={styles.riskSymbol}>{symbol}</Text>
                        <View style={[
                          styles.riskBadgeSmall,
                          { backgroundColor: getRiskColor(risk.risk_level) + '20' }
                        ]}>
                          <Text style={[styles.riskBadgeTextSmall, { color: getRiskColor(risk.risk_level) }]}>
                            {risk.risk_level}
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.riskDetail}>
                        Sustainability: {risk.sustainability_score.toFixed(1)}/100
                      </Text>
                      {risk.last_payment && (
                        <Text style={styles.riskDetail}>
                          Last Payment: {risk.last_payment}
                        </Text>
                      )}
                    </View>
                  ))}
                </View>
              )}

              {/* Earnings Risk Analysis */}
              {riskData.earnings_risks && Object.keys(riskData.earnings_risks).length > 0 && (
                <View style={styles.comprehensiveSection}>
                  <Text style={styles.sectionTitle}>Earnings Risk Analysis</Text>
                  {Object.entries(riskData.earnings_risks).map(([symbol, risk]) => (
                    <View key={symbol} style={styles.riskItem}>
                      <View style={styles.riskItemHeader}>
                        <Text style={styles.riskSymbol}>{symbol}</Text>
                        <View style={[
                          styles.riskBadgeSmall,
                          { backgroundColor: getRiskColor(risk.overall_risk_level) + '20' }
                        ]}>
                          <Text style={[styles.riskBadgeTextSmall, { color: getRiskColor(risk.overall_risk_level) }]}>
                            {risk.overall_risk_level}
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.riskDetail}>
                        Risk Score: {risk.earnings_risk_score.toFixed(1)}/100
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Risk Recommendations */}
              {riskData.recommendations && riskData.recommendations.length > 0 && (
                <View style={styles.comprehensiveSection}>
                  <Text style={styles.sectionTitle}>Risk Recommendations</Text>
                  {riskData.recommendations.map((recommendation, index) => (
                    <View key={index} style={styles.recommendationItem}>
                      <Ionicons name="bulb" size={16} color={colors.warning} style={styles.recommendationIcon} />
                      <Text style={styles.recommendationText}>{recommendation}</Text>
                    </View>
                  ))}
                </View>
              )}
            </>
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
    margin: spacing.lg,
    minHeight: 300,
  },
  emptyText: {
    ...typography.h4,
    color: colors.text,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  emptySubtext: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
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
  scoreExplanation: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: borderRadius.sm,
  },
  scoreExplanationText: {
    ...typography.caption,
    color: colors.textSecondary,
    textAlign: 'center',
    fontSize: 12,
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
  comprehensiveSection: {
    marginTop: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  summaryLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },
  summaryValue: {
    ...typography.body,
    color: colors.text,
    fontWeight: '600',
  },
  riskItem: {
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  riskItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  riskSymbol: {
    ...typography.body,
    color: colors.text,
    fontWeight: '600',
  },
  riskBadgeSmall: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: borderRadius.sm,
  },
  riskBadgeTextSmall: {
    ...typography.caption,
    fontWeight: '600',
    fontSize: 11,
  },
  riskDetail: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  recommendationIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  recommendationText: {
    ...typography.body,
    color: colors.text,
    flex: 1,
  },
});

