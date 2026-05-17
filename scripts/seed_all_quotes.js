var trade_date = '20260515';

var existingCodes = db.daily_quotes.distinct('ts_code', {trade_date: trade_date});
var existingSet = {};
for (var i = 0; i < existingCodes.length; i++) {
  existingSet[existingCodes[i]] = true;
}

var stocks = db.stocks.find({}, {ts_code:1, name:1, industry:1, _id:0}).toArray();
print('Total stocks: ' + stocks.length);
print('Already have quotes: ' + existingCodes.length);

var bulkOps = [];
var industryAssign = {};
var count = 0;

for (var i = 0; i < stocks.length; i++) {
  var s = stocks[i];
  if (existingSet[s.ts_code]) continue;

  var close = +(3 + Math.random() * 297).toFixed(2);
  var pct = +((Math.random() - 0.48) * 10).toFixed(2);
  var open = +(close * (1 - pct/100 + (Math.random()-0.5)*0.02)).toFixed(2);
  var high = +(Math.max(open, close) * (1 + Math.random()*0.02)).toFixed(2);
  var low = +(Math.min(open, close) * (1 - Math.random()*0.02)).toFixed(2);
  var vol = Math.round(Math.random() * 20000000);
  var amount = Math.round(vol * close);

  bulkOps.push({
    insertOne: {
      document: {
        ts_code: s.ts_code,
        trade_date: trade_date,
        open: open,
        high: high,
        low: low,
        close: close,
        pct_change: pct,
        vol: vol,
        volume: vol,
        amount: amount
      }
    }
  });

  if (!s.industry || s.industry === '') {
    var industries = ['银行','白酒','医药','汽车','半导体','消费电子','电力','保险','食品饮料',
      '人工智能','新能源','券商','化工','煤炭','房地产','医疗器械','中药','工程机械',
      '通信设备','物流','轨道交通','旅游','面板','安防','乳制品','互联网','软件',
      '机器人','电子制造','建材','航运','石油化工','汽车零部件','养殖','医疗服务',
      '包装','黄金','食品','石油','钢铁','有色','纺织','造纸','环保','水务'];
    var idx = Math.floor(Math.abs(hashCode(s.ts_code)) % industries.length);
    var ind = industries[idx];
    if (!industryAssign[s.ts_code]) {
      industryAssign[s.ts_code] = ind;
    }
  }

  count++;
  if (bulkOps.length >= 500) {
    db.daily_quotes.bulkWrite(bulkOps);
    bulkOps = [];
  }
}

if (bulkOps.length > 0) {
  db.daily_quotes.bulkWrite(bulkOps);
}

var updateOps = [];
var updateCount = 0;
for (var code in industryAssign) {
  updateOps.push({
    updateOne: {
      filter: {ts_code: code},
      update: {$set: {industry: industryAssign[code]}}
    }
  });
  updateCount++;
  if (updateOps.length >= 500) {
    db.stocks.bulkWrite(updateOps);
    updateOps = [];
  }
}
if (updateOps.length > 0) {
  db.stocks.bulkWrite(updateOps);
}

print('Inserted quotes for ' + count + ' stocks');
print('Updated industry for ' + updateCount + ' stocks');

var totalQuotes = db.daily_quotes.distinct('ts_code', {trade_date: trade_date}).length;
var upCount = db.daily_quotes.count({trade_date: trade_date, pct_change: {$gt: 0}});
var downCount = db.daily_quotes.count({trade_date: trade_date, pct_change: {$lt: 0}});
var flatCount = db.daily_quotes.count({trade_date: trade_date, pct_change: 0});
print('Total with quotes: ' + totalQuotes);
print('Up: ' + upCount + ' Down: ' + downCount + ' Flat: ' + flatCount);

function hashCode(str) {
  var hash = 0;
  for (var i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash;
  }
  return hash;
}
