var trade_date = '20260515';

// 1. 给部分股票设置涨停/跌停
var allQuotes = db.daily_quotes.find({trade_date: trade_date}, {ts_code:1, _id:1}).toArray();
var limitUpCount = 0;
var limitDownCount = 0;

for (var i = 0; i < allQuotes.length; i++) {
  var r = Math.random();
  if (r < 0.02) {
    // ~2% 涨停
    var pct = +(9.9 + Math.random() * 0.1).toFixed(2);
    db.daily_quotes.updateOne(
      {_id: allQuotes[i]._id},
      {$set: {pct_change: pct}}
    );
    limitUpCount++;
  } else if (r < 0.035) {
    // ~1.5% 跌停
    var pct = -((9.9 + Math.random() * 0.1).toFixed(2));
    db.daily_quotes.updateOne(
      {_id: allQuotes[i]._id},
      {$set: {pct_change: pct}}
    );
    limitDownCount++;
  }
}
print('Set limit up: ' + limitUpCount);
print('Set limit down: ' + limitDownCount);

// 2. 验证
var up = db.daily_quotes.count({trade_date: trade_date, pct_change: {$gt: 0}});
var down = db.daily_quotes.count({trade_date: trade_date, pct_change: {$lt: 0}});
var flat = db.daily_quotes.count({trade_date: trade_date, pct_change: 0});
var limitUp = db.daily_quotes.count({trade_date: trade_date, pct_change: {$gte: 9.9}});
var limitDown = db.daily_quotes.count({trade_date: trade_date, pct_change: {$lte: -9.9}});
var totalAmount = db.daily_quotes.aggregate([{$match: {trade_date: trade_date}}, {$group: {_id: null, total: {$sum: '$amount'}}}]).toArray()[0].total;

print('Up: ' + up + ' Down: ' + down + ' Flat: ' + flat);
print('Limit Up: ' + limitUp + ' Limit Down: ' + limitDown);
print('Total Amount: ' + (totalAmount / 1e8).toFixed(2) + ' 亿');
