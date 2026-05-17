var trade_date = '20260515';
var newQuotes = [
  {ts_code:'601012.SH', trade_date:trade_date, close:8.52, pct_change:3.21, amount:52340000, vol:6140000},
  {ts_code:'601166.SH', trade_date:trade_date, close:6.78, pct_change:1.85, amount:41200000, vol:6080000},
  {ts_code:'600276.SH', trade_date:trade_date, close:42.35, pct_change:-1.23, amount:38900000, vol:920000},
  {ts_code:'000568.SZ', trade_date:trade_date, close:28.67, pct_change:2.15, amount:31200000, vol:1090000},
  {ts_code:'002415.SZ', trade_date:trade_date, close:35.42, pct_change:-0.87, amount:89000000, vol:2510000},
  {ts_code:'600031.SH', trade_date:trade_date, close:16.89, pct_change:1.56, amount:67800000, vol:4010000},
  {ts_code:'601857.SH', trade_date:trade_date, close:8.23, pct_change:0.49, amount:34500000, vol:4200000},
  {ts_code:'600887.SH', trade_date:trade_date, close:28.15, pct_change:-2.34, amount:45600000, vol:1620000},
  {ts_code:'000725.SZ', trade_date:trade_date, close:4.56, pct_change:1.79, amount:98700000, vol:21650000},
  {ts_code:'002475.SZ', trade_date:trade_date, close:32.18, pct_change:-1.45, amount:56700000, vol:1760000},
  {ts_code:'600030.SH', trade_date:trade_date, close:22.34, pct_change:0.67, amount:78900000, vol:3530000},
  {ts_code:'601988.SH', trade_date:trade_date, close:4.12, pct_change:-0.48, amount:23400000, vol:5680000},
  {ts_code:'600809.SH', trade_date:trade_date, close:215.6, pct_change:1.89, amount:67800000, vol:314000},
  {ts_code:'002230.SZ', trade_date:trade_date, close:52.34, pct_change:4.56, amount:234000000, vol:4470000},
  {ts_code:'300059.SZ', trade_date:trade_date, close:18.92, pct_change:-3.12, amount:89000000, vol:4700000},
  {ts_code:'600690.SH', trade_date:trade_date, close:28.45, pct_change:0.92, amount:34500000, vol:1210000},
  {ts_code:'002714.SZ', trade_date:trade_date, close:38.67, pct_change:-1.78, amount:23400000, vol:605000},
  {ts_code:'603259.SH', trade_date:trade_date, close:62.15, pct_change:2.34, amount:15600000, vol:251000},
  {ts_code:'000661.SZ', trade_date:trade_date, close:18.23, pct_change:-0.56, amount:12300000, vol:675000},
  {ts_code:'600309.SH', trade_date:trade_date, close:85.34, pct_change:1.23, amount:45600000, vol:534000},
  {ts_code:'002032.SZ', trade_date:trade_date, close:15.67, pct_change:-2.89, amount:23400000, vol:1490000},
  {ts_code:'601633.SH', trade_date:trade_date, close:28.92, pct_change:3.45, amount:56700000, vol:1960000},
  {ts_code:'000625.SZ', trade_date:trade_date, close:12.34, pct_change:-1.67, amount:34500000, vol:2800000},
  {ts_code:'600104.SH', trade_date:trade_date, close:14.56, pct_change:0.78, amount:67800000, vol:4650000},
  {ts_code:'002049.SZ', trade_date:trade_date, close:108.5, pct_change:5.23, amount:345000000, vol:3180000},
  {ts_code:'300124.SZ', trade_date:trade_date, close:42.18, pct_change:-4.56, amount:123000000, vol:2910000},
  {ts_code:'601138.SH', trade_date:trade_date, close:22.67, pct_change:1.12, amount:89000000, vol:3920000},
  {ts_code:'000100.SZ', trade_date:trade_date, close:3.89, pct_change:-0.26, amount:56700000, vol:14570000},
  {ts_code:'600585.SH', trade_date:trade_date, close:22.34, pct_change:0.45, amount:23400000, vol:1050000},
  {ts_code:'601919.SH', trade_date:trade_date, close:12.89, pct_change:1.67, amount:89000000, vol:6900000},
  {ts_code:'600588.SH', trade_date:trade_date, close:15.23, pct_change:-3.45, amount:34500000, vol:2260000},
  {ts_code:'300015.SZ', trade_date:trade_date, close:28.67, pct_change:2.89, amount:56700000, vol:1980000},
  {ts_code:'000538.SZ', trade_date:trade_date, close:62.34, pct_change:-0.34, amount:23400000, vol:376000},
  {ts_code:'600436.SH', trade_date:trade_date, close:48.92, pct_change:1.56, amount:12300000, vol:252000},
  {ts_code:'002304.SZ', trade_date:trade_date, close:82.15, pct_change:-1.23, amount:34500000, vol:420000},
  {ts_code:'000895.SZ', trade_date:trade_date, close:18.45, pct_change:0.89, amount:23400000, vol:1270000},
  {ts_code:'601088.SH', trade_date:trade_date, close:32.56, pct_change:-0.67, amount:56700000, vol:1740000},
  {ts_code:'600028.SH', trade_date:trade_date, close:5.67, pct_change:0.35, amount:89000000, vol:15690000},
  {ts_code:'002241.SZ', trade_date:trade_date, close:32.18, pct_change:3.78, amount:234000000, vol:7270000},
  {ts_code:'600660.SH', trade_date:trade_date, close:52.34, pct_change:1.45, amount:23400000, vol:448000},
  {ts_code:'601225.SH', trade_date:trade_date, close:22.89, pct_change:-1.89, amount:34500000, vol:1510000},
  {ts_code:'000963.SZ', trade_date:trade_date, close:28.56, pct_change:2.34, amount:45600000, vol:1600000},
  {ts_code:'002129.SZ', trade_date:trade_date, close:12.34, pct_change:4.89, amount:89000000, vol:7210000},
  {ts_code:'600085.SH', trade_date:trade_date, close:42.67, pct_change:-0.45, amount:23400000, vol:548000},
  {ts_code:'300760.SZ', trade_date:trade_date, close:285.6, pct_change:-2.67, amount:345000000, vol:1210000},
  {ts_code:'601899.SH', trade_date:trade_date, close:15.78, pct_change:1.23, amount:56700000, vol:3590000},
];

var industryMap = {
  '601012.SH': '电力', '601166.SH': '银行', '600276.SH': '医药', '000568.SZ': '白酒',
  '002415.SZ': '安防', '600031.SH': '工程机械', '601857.SH': '石油', '600887.SH': '乳制品',
  '000725.SZ': '面板', '002475.SZ': '消费电子', '600030.SH': '券商', '601988.SH': '银行',
  '600809.SH': '白酒', '002230.SZ': '人工智能', '300059.SZ': '互联网', '600690.SH': '家用电器',
  '002714.SZ': '养殖', '603259.SH': '医药', '000661.SZ': '医药', '600309.SH': '化工',
  '002032.SZ': '包装', '601633.SH': '汽车', '000625.SZ': '汽车', '600104.SH': '汽车',
  '002049.SZ': '半导体', '300124.SZ': '机器人', '601138.SH': '电子制造', '000100.SZ': '面板',
  '600585.SH': '建材', '601919.SH': '航运', '600588.SH': '软件', '300015.SZ': '医疗服务',
  '000538.SZ': '中药', '600436.SH': '中药', '002304.SZ': '白酒', '000895.SZ': '食品',
  '601088.SH': '煤炭', '600028.SH': '石油化工', '002241.SZ': '消费电子', '600660.SH': '汽车零部件',
  '601225.SH': '煤炭', '000963.SZ': '医药', '002129.SZ': '半导体', '600085.SH': '医药',
  '300760.SZ': '医疗器械', '601899.SH': '黄金'
};

var insertCount = 0;
for (var i = 0; i < newQuotes.length; i++) {
  var q = newQuotes[i];
  var existing = db.daily_quotes.findOne({ts_code: q.ts_code, trade_date: q.trade_date});
  if (!existing) {
    db.daily_quotes.insertOne(q);
    insertCount++;
  }
}
print('Inserted ' + insertCount + ' new quotes');

var updateCount = 0;
for (var code in industryMap) {
  var res = db.stocks.updateOne(
    {ts_code: code},
    {$set: {industry: industryMap[code]}}
  );
  if (res.modifiedCount > 0) updateCount++;
}
print('Updated ' + updateCount + ' stock industries');

var total = db.daily_quotes.distinct('ts_code').length;
var industries = db.stocks.distinct('industry', {industry: {$ne: ''}});
print('Total stocks with quotes: ' + total);
print('Industries: ' + JSON.stringify(industries));
