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
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api, Portfolio, Holding } from '../services/api';

export default function PortfolioScreen({ route, navigation }: any) {
  const { portfolioId } = route.params;
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);
  const [symbol, setSymbol] = useState('');
  const [shares, setShares] = useState('');
  const [sellShares, setSellShares] = useState('');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [symbolSuggestions, setSymbolSuggestions] = useState<Array<{symbol: string; name: string; price?: number}>>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const loadPortfolio = async () => {
    try {
      const data = await api.get<{
        portfolio: Portfolio;
        holdings: Holding[];
        total_value: number;
      }>(`/portfolios/${portfolioId}`);
      setPortfolio(data.portfolio);
      setHoldings(data.holdings);
    } catch (error) {
      // Silently handle errors - only show alert for critical failures
      Alert.alert('Error', 'Failed to load portfolio');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, [portfolioId]);

  // Search for symbol suggestions when typing
  useEffect(() => {
    const searchSymbols = async () => {
      if (symbol && symbol.length >= 2) {
        setSearchLoading(true);
        setShowSuggestions(true);
        try {
          const data = await api.get<{results: Array<{symbol: string; name: string; price?: number}>}>(
            `/symbols/suggest?q=${encodeURIComponent(symbol)}&limit=8`
          );
          setSymbolSuggestions(data.results || []);
        } catch (error) {
          // Silently handle errors - just show empty results
          setSymbolSuggestions([]);
        } finally {
          setSearchLoading(false);
        }
      } else {
        setSymbolSuggestions([]);
        setShowSuggestions(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(searchSymbols, 300);
    return () => clearTimeout(timeoutId);
  }, [symbol]);

  // Fetch current price when symbol changes (for buying)
  useEffect(() => {
    const fetchPrice = async () => {
      if (symbol && symbol.length >= 1 && !showSuggestions) {
        setPriceLoading(true);
        try {
          const priceData = await api.get<{ symbol: string; price: number | null }>(
            `/prices/latest/${symbol.toUpperCase()}`
          );
          setCurrentPrice(priceData.price);
        } catch (error) {
          // Silently handle errors - just set price to null
          setCurrentPrice(null);
        } finally {
          setPriceLoading(false);
        }
      } else {
        setCurrentPrice(null);
      }
    };

    // Debounce price fetching
    const timeoutId = setTimeout(fetchPrice, 500);
    return () => clearTimeout(timeoutId);
  }, [symbol, showSuggestions]);

  const onRefresh = () => {
    setRefreshing(true);
    loadPortfolio();
  };

  const handleAddHolding = async () => {
    if (!symbol || !shares || parseFloat(shares) <= 0) {
      Alert.alert('Error', 'Please enter valid symbol and shares');
      return;
    }

    try {
      await api.post('/holdings', {
        portfolio_id: portfolioId,
        symbol: symbol.toUpperCase(),
        shares: parseFloat(shares),
      });
      setShowAddModal(false);
      setSymbol('');
      setShares('');
      loadPortfolio();
      Alert.alert('Success', 'Holding added successfully');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to add holding');
    }
  };

  const handleSellHolding = async () => {
    if (!selectedHolding || !sellShares || parseFloat(sellShares) <= 0) {
      Alert.alert('Error', 'Please enter valid shares to sell');
      return;
    }

    if (parseFloat(sellShares) > selectedHolding.shares) {
      Alert.alert('Error', 'Cannot sell more shares than you own');
      return;
    }

    try {
      await api.post(`/holdings/${selectedHolding.id}/sell`, {
        shares: parseFloat(sellShares),
      } as any);
      setShowSellModal(false);
      setSelectedHolding(null);
      setSellShares('');
      loadPortfolio();
      Alert.alert('Success', 'Shares sold successfully');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to sell shares');
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  const totalValue = holdings.reduce(
    (sum, h) => sum + (h.current_value || h.shares * h.avg_price),
    0
  );

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {portfolio && (
          <>
            <View style={styles.header}>
              <Text style={styles.portfolioName}>{portfolio.name}</Text>
              <Text style={styles.portfolioType}>{portfolio.portfolio_type}</Text>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardLabel}>Cash Balance</Text>
              <Text style={styles.cardValue}>
                ${portfolio.cash_balance.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>

            <View style={styles.card}>
              <Text style={styles.cardLabel}>Total Portfolio Value</Text>
              <Text style={styles.cardValue}>
                ${totalValue.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Holdings</Text>
              {holdings.map((holding) => (
                <TouchableOpacity
                  key={holding.id}
                  style={styles.holdingCard}
                  onPress={() => {
                    setSelectedHolding(holding);
                    setShowSellModal(true);
                  }}
                >
                  <View style={styles.holdingHeader}>
                    <Text style={styles.holdingSymbol}>{holding.symbol}</Text>
                    <Text style={styles.holdingShares}>
                      {holding.shares.toFixed(2)} shares
                    </Text>
                  </View>
                  <View style={styles.holdingDetails}>
                    <View>
                      <Text style={styles.holdingLabel}>Avg Price</Text>
                      <Text style={styles.holdingValue}>
                        ${holding.avg_price.toFixed(2)}
                      </Text>
                    </View>
                    <View>
                      <Text style={styles.holdingLabel}>Current Price</Text>
                      <Text style={styles.holdingValue}>
                        ${(holding.current_price || holding.avg_price).toFixed(2)}
                      </Text>
                    </View>
                    <View>
                      <Text style={styles.holdingLabel}>Value</Text>
                      <Text style={styles.holdingValue}>
                        $
                        {(holding.current_value ||
                          holding.shares * holding.avg_price).toFixed(2)}
                      </Text>
                    </View>
                  </View>
                  {holding.gain_loss !== undefined && (
                    <View
                      style={[
                        styles.gainLoss,
                        holding.gain_loss >= 0 ? styles.gain : styles.loss,
                      ]}
                    >
                      <Text
                        style={[
                          styles.gainLossText,
                          holding.gain_loss >= 0 ? styles.gainText : styles.lossText,
                        ]}
                      >
                        {holding.gain_loss >= 0 ? '+' : ''}
                        ${holding.gain_loss.toFixed(2)} (
                        {holding.gain_loss_percent?.toFixed(2)}%)
                      </Text>
                    </View>
                  )}
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}
      </ScrollView>

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowAddModal(true)}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      {/* Add Holding Modal */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowAddModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        >
          <TouchableOpacity
            style={styles.modalOverlay}
            activeOpacity={1}
            onPress={() => setShowAddModal(false)}
          >
            <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Add Holding</Text>
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => {
                      setShowAddModal(false);
                      setSymbol('');
                      setShares('');
                      setSymbolSuggestions([]);
                      setShowSuggestions(false);
                      setCurrentPrice(null);
                    }}
                  >
                    <Ionicons name="close" size={24} color="#666" />
                  </TouchableOpacity>
                </View>
                <View style={styles.modalInputContainer}>
                  <View style={styles.symbolInputContainer}>
                    <TextInput
                      style={styles.modalInput}
                      placeholder="Search stock (e.g., Apple, AAPL)"
                      value={symbol}
                      onChangeText={(text) => {
                        setSymbol(text);
                        if (text.length >= 2) {
                          setShowSuggestions(true);
                        } else {
                          setShowSuggestions(false);
                        }
                      }}
                      onFocus={() => {
                        if (symbol.length >= 2) {
                          setShowSuggestions(true);
                        }
                      }}
                      autoCapitalize="none"
                      placeholderTextColor="#999"
                    />
                    {searchLoading && (
                      <ActivityIndicator size="small" color="#007AFF" style={styles.searchIndicator} />
                    )}
                  </View>
                  
                  {/* Symbol Suggestions */}
                  {showSuggestions && symbol.length >= 2 && symbolSuggestions.length > 0 && (
                    <View style={styles.suggestionsContainer}>
                      <FlatList
                        data={symbolSuggestions}
                        keyExtractor={(item) => item.symbol}
                        renderItem={({ item }) => (
                          <TouchableOpacity
                            style={styles.suggestionItem}
                            onPress={() => {
                              setSymbol(item.symbol);
                              setShowSuggestions(false);
                              setCurrentPrice(item.price || null);
                              setSymbolSuggestions([]); // Clear suggestions
                            }}
                          >
                            <View style={styles.suggestionContent}>
                              <Text style={styles.suggestionSymbol}>{item.symbol}</Text>
                              <Text style={styles.suggestionName} numberOfLines={1}>
                                {item.name}
                              </Text>
                            </View>
                            {item.price && (
                              <Text style={styles.suggestionPrice}>
                                ${item.price.toFixed(2)}
                              </Text>
                            )}
                          </TouchableOpacity>
                        )}
                        style={styles.suggestionsList}
                        keyboardShouldPersistTaps="handled"
                      />
                    </View>
                  )}
                  
                  {showSuggestions && symbol.length >= 2 && !searchLoading && symbolSuggestions.length === 0 && (
                    <View style={styles.noSuggestions}>
                      <Text style={styles.noSuggestionsText}>No stocks found</Text>
                    </View>
                  )}
                  
                  <TextInput
                    style={styles.modalInput}
                    placeholder="Shares"
                    value={shares}
                    onChangeText={setShares}
                    keyboardType="decimal-pad"
                    placeholderTextColor="#999"
                  />
                </View>
                
                {/* Real-time calculation for buying */}
                {symbol && (
                  <View style={styles.calculationContainer}>
                    {priceLoading ? (
                      <ActivityIndicator size="small" color="#007AFF" />
                    ) : currentPrice ? (
                      <>
                        <View style={styles.calculationRow}>
                          <Text style={styles.calculationLabel}>Current Price:</Text>
                          <Text style={styles.calculationValue}>
                            ${currentPrice.toFixed(2)}
                          </Text>
                        </View>
                        {shares && parseFloat(shares) > 0 && (
                          <>
                            <View style={styles.calculationRow}>
                              <Text style={styles.calculationLabel}>Total Cost:</Text>
                              <Text style={[styles.calculationValue, styles.totalCost]}>
                                ${(currentPrice * parseFloat(shares)).toFixed(2)}
                              </Text>
                            </View>
                            {portfolio && (
                              <>
                                <View style={styles.calculationRow}>
                                  <Text style={styles.calculationLabel}>Cash Balance:</Text>
                                  <Text style={styles.calculationValue}>
                                    ${portfolio.cash_balance.toFixed(2)}
                                  </Text>
                                </View>
                                {currentPrice * parseFloat(shares) > portfolio.cash_balance ? (
                                  <View style={styles.warningContainer}>
                                    <Ionicons name="warning" size={16} color="#FF3B30" />
                                    <Text style={styles.warningText}>
                                      Insufficient funds. Need ${((currentPrice * parseFloat(shares)) - portfolio.cash_balance).toFixed(2)} more.
                                    </Text>
                                  </View>
                                ) : (
                                  <View style={styles.successContainer}>
                                    <Ionicons name="checkmark-circle" size={16} color="#34C759" />
                                    <Text style={styles.successText}>
                                      You have sufficient funds
                                    </Text>
                                  </View>
                                )}
                              </>
                            )}
                          </>
                        )}
                      </>
                    ) : null}
                  </View>
                )}
                
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.cancelButton]}
                    onPress={() => {
                      setShowAddModal(false);
                      setSymbol('');
                      setShares('');
                      setSymbolSuggestions([]);
                      setShowSuggestions(false);
                      setCurrentPrice(null);
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.submitButton]}
                    onPress={handleAddHolding}
                  >
                    <Text style={styles.submitButtonText}>Add</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </TouchableOpacity>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </Modal>

      {/* Sell Holding Modal */}
      <Modal
        visible={showSellModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowSellModal(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        >
          <TouchableOpacity
            style={styles.modalOverlay}
            activeOpacity={1}
            onPress={() => setShowSellModal(false)}
          >
            <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()}>
              <View style={styles.modalContent}>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>
                    Sell {selectedHolding?.symbol}
                  </Text>
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => {
                      setShowSellModal(false);
                      setSelectedHolding(null);
                      setSellShares('');
                    }}
                  >
                    <Ionicons name="close" size={24} color="#666" />
                  </TouchableOpacity>
                </View>
                <Text style={styles.modalSubtitle}>
                  You own {selectedHolding?.shares.toFixed(2)} shares
                </Text>
                <View style={styles.modalInputContainer}>
                  <TextInput
                    style={styles.modalInput}
                    placeholder="Shares to sell"
                    value={sellShares}
                    onChangeText={setSellShares}
                    keyboardType="decimal-pad"
                    placeholderTextColor="#999"
                  />
                </View>
                
                {/* Real-time calculation for selling */}
                {selectedHolding && selectedHolding.current_price && (
                  <View style={styles.calculationContainer}>
                    <View style={styles.calculationRow}>
                      <Text style={styles.calculationLabel}>Current Price:</Text>
                      <Text style={styles.calculationValue}>
                        ${selectedHolding.current_price.toFixed(2)}
                      </Text>
                    </View>
                    {sellShares && parseFloat(sellShares) > 0 && (
                      <>
                        <View style={styles.calculationRow}>
                          <Text style={styles.calculationLabel}>Total Proceeds:</Text>
                          <Text style={[styles.calculationValue, styles.totalProceeds]}>
                            ${(selectedHolding.current_price * parseFloat(sellShares)).toFixed(2)}
                          </Text>
                        </View>
                        {parseFloat(sellShares) <= selectedHolding.shares ? (
                          <View style={styles.calculationRow}>
                            <Text style={styles.calculationLabel}>Remaining Shares:</Text>
                            <Text style={styles.calculationValue}>
                              {(selectedHolding.shares - parseFloat(sellShares)).toFixed(2)}
                            </Text>
                          </View>
                        ) : (
                          <View style={styles.warningContainer}>
                            <Ionicons name="warning" size={16} color="#FF3B30" />
                            <Text style={styles.warningText}>
                              Cannot sell more than {selectedHolding.shares.toFixed(2)} shares
                            </Text>
                          </View>
                        )}
                      </>
                    )}
                  </View>
                )}
                
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.cancelButton]}
                    onPress={() => {
                      setShowSellModal(false);
                      setSelectedHolding(null);
                      setSellShares('');
                    }}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.submitButton]}
                    onPress={handleSellHolding}
                  >
                    <Text style={styles.submitButtonText}>Sell</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </TouchableOpacity>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  portfolioName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  portfolioType: {
    fontSize: 16,
    color: '#666',
    textTransform: 'capitalize',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  cardValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  section: {
    marginTop: 8,
    marginBottom: 100,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginHorizontal: 16,
    marginBottom: 12,
  },
  holdingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  holdingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  holdingSymbol: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  holdingShares: {
    fontSize: 14,
    color: '#666',
  },
  holdingDetails: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  holdingLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  holdingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  gainLoss: {
    marginTop: 12,
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  gain: {
    backgroundColor: '#d4edda',
  },
  loss: {
    backgroundColor: '#f8d7da',
  },
  gainLossText: {
    fontSize: 14,
    fontWeight: '600',
  },
  gainText: {
    color: '#155724',
  },
  lossText: {
    color: '#721c24',
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 5,
  },
  fabText: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    flex: 1,
  },
  closeButton: {
    padding: 4,
    marginLeft: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  modalInputContainer: {
    marginTop: 8,
  },
  modalInput: {
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 12,
    color: '#1a1a1a',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  modalButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 8,
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007AFF',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  calculationContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  calculationRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  calculationLabel: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  calculationValue: {
    fontSize: 16,
    color: '#1a1a1a',
    fontWeight: '600',
  },
  totalCost: {
    fontSize: 18,
    color: '#007AFF',
    fontWeight: '700',
  },
  totalProceeds: {
    fontSize: 18,
    color: '#34C759',
    fontWeight: '700',
  },
  warningContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff3cd',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#856404',
    flex: 1,
    fontWeight: '500',
  },
  successContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#d4edda',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    gap: 8,
  },
  successText: {
    fontSize: 13,
    color: '#155724',
    flex: 1,
    fontWeight: '500',
  },
  symbolInputContainer: {
    position: 'relative',
  },
  searchIndicator: {
    position: 'absolute',
    right: 12,
    top: 16,
  },
  suggestionsContainer: {
    maxHeight: 200,
    backgroundColor: '#fff',
    borderRadius: 12,
    marginTop: 4,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  suggestionsList: {
    maxHeight: 200,
  },
  suggestionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  suggestionContent: {
    flex: 1,
    marginRight: 8,
  },
  suggestionSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 2,
  },
  suggestionName: {
    fontSize: 13,
    color: '#666',
  },
  suggestionPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  noSuggestions: {
    padding: 12,
    alignItems: 'center',
  },
  noSuggestionsText: {
    fontSize: 14,
    color: '#999',
  },
});

