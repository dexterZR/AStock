export interface Holding {
  ts_code: string; name: string; total_shares: number; total_cost: number;
  buy_shares: number; avg_cost: number; latest_price: number; market_value: number;
  unrealized_pnl: number; unrealized_pnl_pct: number; risk_level: string; warning_events: string[];
}
export interface TradeRecord { ts_code: string; name: string; action: string; price: number; shares: number; trade_date: string; decision_logic: string; }
export interface StockEvent { _id?: string; ts_code: string; name: string; event_type: string; event_date: string; title: string; content: string; severity: string; is_resolved: boolean; }
export interface RiskAlert { _id?: string; ts_code: string; name: string; alert_level: string; title: string; description: string; triggered_at: string; is_acknowledged: boolean; }
