var trade_date = '20260515';

// 插入大盘指数数据
var indices = [
  {ts_code:'000001.SH', name:'上证指数', close:3345.67, pct_change:0.56, open:3328.12, high:3358.90, low:3318.45, vol:3456789000, amount:456789000000},
  {ts_code:'399001.SZ', name:'深证成指', close:10856.34, pct_change:-0.23, open:10878.56, high:10912.34, low:10823.45, vol:4567890000, amount:567890000000},
  {ts_code:'399006.SZ', name:'创业板指', close:2156.78, pct_change:1.12, open:2134.56, high:2178.90, low:2128.34, vol:2345678000, amount:345678000000},
];

for (var i = 0; i < indices.length; i++) {
  var idx = indices[i];
  var existing = db.daily_quotes.findOne({ts_code: idx.ts_code, trade_date: trade_date});
  if (!existing) {
    db.daily_quotes.insertOne({
      ts_code: idx.ts_code,
      trade_date: trade_date,
      open: idx.open,
      high: idx.high,
      low: idx.low,
      close: idx.close,
      pct_change: idx.pct_change,
      vol: idx.vol,
      volume: idx.vol,
      amount: idx.amount
    });
  }
  // 也插入 stocks 集合
  db.stocks.updateOne(
    {ts_code: idx.ts_code},
    {$set: {name: idx.name, industry: '指数'}},
    {upsert: true}
  );
}

// 插入历史K线数据（最近60个交易日）
var baseDate = new Date('2026-03-02');
var shClose = 3200;
var szClose = 10500;
var cyClose = 2050;

for (var d = 0; d < 60; d++) {
  var date = new Date(baseDate);
  date.setDate(date.getDate() + d);
  // 跳过周末
  if (date.getDay() === 0 || date.getDay() === 6) continue;
  
  var td = date.getFullYear() + 
    ('0' + (date.getMonth()+1)).slice(-2) + 
    ('0' + date.getDate()).slice(-2);
  
  shClose = +(shClose * (1 + (Math.random()-0.48)*0.02)).toFixed(2);
  szClose = +(szClose * (1 + (Math.random()-0.48)*0.02)).toFixed(2);
  cyClose = +(cyClose * (1 + (Math.random()-0.48)*0.02)).toFixed(2);
  
  var shOpen = +(shClose * (1 + (Math.random()-0.5)*0.005)).toFixed(2);
  var szOpen = +(szClose * (1 + (Math.random()-0.5)*0.005)).toFixed(2);
  var cyOpen = +(cyClose * (1 + (Math.random()-0.5)*0.005)).toFixed(2);
  
  var shHigh = +(Math.max(shOpen, shClose) * (1 + Math.random()*0.005)).toFixed(2);
  var szHigh = +(Math.max(szOpen, szClose) * (1 + Math.random()*0.005)).toFixed(2);
  var cyHigh = +(Math.max(cyOpen, cyClose) * (1 + Math.random()*0.005)).toFixed(2);
  
  var shLow = +(Math.min(shOpen, shClose) * (1 - Math.random()*0.005)).toFixed(2);
  var szLow = +(Math.min(szOpen, szClose) * (1 - Math.random()*0.005)).toFixed(2);
  var cyLow = +(Math.min(cyOpen, cyClose) * (1 - Math.random()*0.005)).toFixed(2);
  
  var shPct = +((shClose - shOpen) / shOpen * 100).toFixed(2);
  var szPct = +((szClose - szOpen) / szOpen * 100).toFixed(2);
  var cyPct = +((cyClose - cyOpen) / cyOpen * 100).toFixed(2);
  
  var idxData = [
    {ts_code:'000001.SH', open:shOpen, high:shHigh, low:shLow, close:shClose, pct_change:shPct, vol:Math.round(Math.random()*5e9), amount:Math.round(Math.random()*6e11)},
    {ts_code:'399001.SZ', open:szOpen, high:szHigh, low:szLow, close:szClose, pct_change:szPct, vol:Math.round(Math.random()*6e9), amount:Math.round(Math.random()*7e11)},
    {ts_code:'399006.SZ', open:cyOpen, high:cyHigh, low:cyLow, close:cyClose, pct_change:cyPct, vol:Math.round(Math.random()*3e9), amount:Math.round(Math.random()*4e11)},
  ];
  
  for (var j = 0; j < idxData.length; j++) {
    var existing = db.daily_quotes.findOne({ts_code: idxData[j].ts_code, trade_date: td});
    if (!existing) {
      db.daily_quotes.insertOne(Object.assign({trade_date: td, volume: idxData[j].vol}, idxData[j]));
    }
  }
}

print('Inserted index data');

// 也给 600519.SH 补充历史K线数据
var maoClose = 1680;
for (var d = 0; d < 60; d++) {
  var date = new Date(baseDate);
  date.setDate(date.getDate() + d);
  if (date.getDay() === 0 || date.getDay() === 6) continue;
  
  var td = date.getFullYear() + 
    ('0' + (date.getMonth()+1)).slice(-2) + 
    ('0' + date.getDate()).slice(-2);
  
  maoClose = +(maoClose * (1 + (Math.random()-0.48)*0.015)).toFixed(2);
  var maoOpen = +(maoClose * (1 + (Math.random()-0.5)*0.008)).toFixed(2);
  var maoHigh = +(Math.max(maoOpen, maoClose) * (1 + Math.random()*0.008)).toFixed(2);
  var maoLow = +(Math.min(maoOpen, maoClose) * (1 - Math.random()*0.008)).toFixed(2);
  var maoPct = +((maoClose - maoOpen) / maoOpen * 100).toFixed(2);
  
  var existing = db.daily_quotes.findOne({ts_code: '600519.SH', trade_date: td});
  if (!existing) {
    db.daily_quotes.insertOne({
      ts_code: '600519.SH',
      trade_date: td,
      open: maoOpen,
      high: maoHigh,
      low: maoLow,
      close: maoClose,
      pct_change: maoPct,
      vol: Math.round(Math.random() * 1e8),
      volume: Math.round(Math.random() * 1e8),
      amount: Math.round(Math.random() * 2e10)
    });
  }
}

print('Inserted 600519.SH historical data');
print('Total 600519.SH quotes: ' + db.daily_quotes.count({ts_code: '600519.SH'}));
