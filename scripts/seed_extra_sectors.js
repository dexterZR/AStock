var trade_date = '20260515';
function rand(min, max) { return +(min + Math.random() * (max - min)).toFixed(2); }
function randPct() { return +((Math.random() - 0.45) * 10).toFixed(2); }

var extra = {
  '家用电器': [
    {ts_code:'000100.SZ', name:'TCL科技', close:4.56, pct_change:1.23},
    {ts_code:'002050.SZ', name:'三花智控', close:22.34, pct_change:2.15},
    {ts_code:'002032.SZ', name:'苏泊尔', close:56.78, pct_change:0.89},
    {ts_code:'002508.SZ', name:'老板电器', close:28.45, pct_change:-0.56},
    {ts_code:'002705.SZ', name:'新宝股份', close:15.67, pct_change:1.78},
    {ts_code:'603486.SH', name:'科沃斯', close:68.9, pct_change:3.12},
    {ts_code:'688169.SH', name:'石头科技', close:198.5, pct_change:1.45},
    {ts_code:'002959.SZ', name:'小熊电器', close:42.56, pct_change:-1.23},
  ],
  '消费电子': [
    {ts_code:'300433.SZ', name:'蓝思科技', close:12.34, pct_change:1.56},
    {ts_code:'002008.SZ', name:'大族激光', close:28.56, pct_change:-0.89},
    {ts_code:'300136.SZ', name:'信维通信', close:18.23, pct_change:2.34},
    {ts_code:'002236.SZ', name:'大华股份', close:15.67, pct_change:0.45},
    {ts_code:'300308.SZ', name:'中际旭创', close:88.9, pct_change:5.67},
    {ts_code:'300502.SZ', name:'新易盛', close:45.23, pct_change:3.45},
    {ts_code:'002446.SZ', name:'盛路通信', close:8.56, pct_change:-1.78},
    {ts_code:'688036.SH', name:'传音控股', close:68.34, pct_change:1.12},
  ],
  '轨道交通': [
    {ts_code:'601006.SH', name:'大秦铁路', close:7.89, pct_change:0.56},
    {ts_code:'600018.SH', name:'上港集团', close:5.23, pct_change:1.23},
    {ts_code:'601333.SH', name:'广深铁路', close:2.78, pct_change:-0.34},
    {ts_code:'600009.SH', name:'上海机场', close:38.56, pct_change:2.45},
    {ts_code:'601880.SH', name:'辽港股份', close:1.89, pct_change:0.67},
    {ts_code:'600017.SH', name:'日照港', close:3.45, pct_change:-0.89},
    {ts_code:'601000.SH', name:'唐山港', close:3.12, pct_change:0.23},
  ],
  '食品饮料': [
    {ts_code:'600779.SH', name:'水井坊', close:52.34, pct_change:1.23},
    {ts_code:'000848.SZ', name:'承德露露', close:8.56, pct_change:0.78},
    {ts_code:'002568.SZ', name:'百润股份', close:22.34, pct_change:-1.56},
    {ts_code:'002330.SZ', name:'得利斯', close:5.67, pct_change:0.45},
    {ts_code:'603345.SH', name:'安井食品', close:68.9, pct_change:2.12},
    {ts_code:'002847.SZ', name:'盐津铺子', close:52.34, pct_change:3.45},
    {ts_code:'603517.SH', name:'绝味食品', close:28.56, pct_change:-0.67},
  ],
  '医药': [
    {ts_code:'002007.SZ', name:'华兰生物', close:18.56, pct_change:1.23},
    {ts_code:'300347.SZ', name:'泰格医药', close:68.34, pct_change:2.56},
    {ts_code:'300017.SZ', name:'网宿科技', close:8.45, pct_change:-0.89},
    {ts_code:'300759.SZ', name:'康希诺', close:28.56, pct_change:1.78},
    {ts_code:'002432.SZ', name:'九安医疗', close:32.45, pct_change:3.12},
  ],
  '半导体': [
    {ts_code:'002371.SZ', name:'北方华创', close:288.5, pct_change:2.34},
    {ts_code:'688012.SH', name:'中微公司', close:128.56, pct_change:1.89},
    {ts_code:'603005.SH', name:'晶方科技', close:38.9, pct_change:-0.56},
    {ts_code:'300661.SZ', name:'圣邦股份', close:98.56, pct_change:3.45},
    {ts_code:'688256.SH', name:'寒武纪', close:168.9, pct_change:4.12},
    {ts_code:'688037.SH', name:'芯源微', close:88.34, pct_change:1.56},
  ],
  '化工': [
    {ts_code:'600426.SH', name:'华鲁恒升', close:28.56, pct_change:0.89},
    {ts_code:'002648.SZ', name:'卫星化学', close:18.34, pct_change:1.56},
    {ts_code:'600989.SH', name:'宝丰能源', close:15.67, pct_change:-0.45},
    {ts_code:'000301.SZ', name:'东方盛虹', close:6.78, pct_change:2.12},
    {ts_code:'600803.SH', name:'新奥股份', close:18.9, pct_change:0.67},
    {ts_code:'002470.SZ', name:'金正大', close:3.45, pct_change:-1.23},
  ],
  '互联网': [
    {ts_code:'002555.SZ', name:'三七互娱', close:22.34, pct_change:1.89},
    {ts_code:'300418.SZ', name:'昆仑万维', close:38.56, pct_change:2.34},
    {ts_code:'002602.SZ', name:'世纪华通', close:5.67, pct_change:-0.56},
    {ts_code:'002174.SZ', name:'游族网络', close:8.9, pct_change:1.12},
  ],
  '乳制品': [
    {ts_code:'600597.SH', name:'光明乳业', close:8.56, pct_change:0.78},
    {ts_code:'002570.SZ', name:'贝因美', close:4.23, pct_change:-1.23},
    {ts_code:'600873.SH', name:'梅花生物', close:8.9, pct_change:1.45},
    {ts_code:'002311.SZ', name:'海大集团', close:42.56, pct_change:2.12},
  ],
  '医疗器械': [
    {ts_code:'300003.SZ', name:'乐普医疗', close:12.34, pct_change:-0.89},
    {ts_code:'688060.SH', name:'联影医疗', close:108.56, pct_change:2.34},
    {ts_code:'300633.SZ', name:'开立医疗', close:38.9, pct_change:1.56},
    {ts_code:'002901.SZ', name:'大博医疗', close:28.56, pct_change:0.67},
  ],
  '石油化工': [
    {ts_code:'600157.SH', name:'永泰能源', close:1.56, pct_change:0.34},
    {ts_code:'002207.SZ', name:'准油股份', close:8.9, pct_change:1.23},
    {ts_code:'600546.SH', name:'山煤国际', close:12.34, pct_change:-0.67},
    {ts_code:'000554.SZ', name:'泰山石油', close:5.67, pct_change:0.89},
  ],
  '人工智能': [
    {ts_code:'300496.SZ', name:'中科创达', close:68.34, pct_change:2.56},
    {ts_code:'688037.SH', name:'芯源微', close:88.34, pct_change:1.89},
    {ts_code:'688083.SH', name:'中望软件', close:128.56, pct_change:3.12},
    {ts_code:'688111.SH', name:'金山办公', close:268.5, pct_change:2.45},
    {ts_code:'300033.SZ', name:'同花顺', close:108.9, pct_change:1.78},
  ],
  '新能源': [
    {ts_code:'002202.SZ', name:'金风科技', close:8.56, pct_change:-1.23},
    {ts_code:'600905.SH', name:'三峡能源', close:5.67, pct_change:0.89},
    {ts_code:'300274.SZ', name:'阳光电源', close:68.9, pct_change:2.34},
    {ts_code:'688599.SH', name:'天合光能', close:22.56, pct_change:1.56},
    {ts_code:'601865.SH', name:'福莱特', close:28.34, pct_change:-0.78},
    {ts_code:'002459.SZ', name:'晶澳科技', close:15.67, pct_change:0.45},
  ],
  '白酒': [
    {ts_code:'603369.SH', name:'今世缘', close:48.56, pct_change:1.23},
    {ts_code:'000557.SZ', name:'西部创业', close:5.67, pct_change:-0.89},
  ],
  '电力': [
    {ts_code:'600023.SH', name:'浙能电力', close:5.67, pct_change:0.78},
    {ts_code:'601985.SH', name:'中国核电', close:8.9, pct_change:1.34},
    {ts_code:'600795.SH', name:'国电电力', close:4.56, pct_change:-0.56},
    {ts_code:'003816.SH', name:'中国广核', close:3.45, pct_change:0.23},
    {ts_code:'600674.SH', name:'川投能源', close:15.78, pct_change:1.12},
    {ts_code:'601027.SH', name:'华能国际', close:7.89, pct_change:-0.45},
    {ts_code:'600884.SH', name:'杉杉股份', close:12.34, pct_change:2.56},
  ],
  '汽车': [
    {ts_code:'600685.SH', name:'广汽集团', close:10.56, pct_change:0.89},
    {ts_code:'601238.SH', name:'广汽集团H', close:8.9, pct_change:-0.34},
    {ts_code:'000980.SZ', name:'众泰汽车', close:3.45, pct_change:1.56},
    {ts_code:'600760.SH', name:'中航沈飞', close:42.34, pct_change:2.12},
  ],
  '煤炭': [
    {ts_code:'600188.SH', name:'兖矿能源', close:22.56, pct_change:-0.78},
    {ts_code:'601015.SH', name:'陕西黑猫', close:5.67, pct_change:1.23},
    {ts_code:'000983.SZ', name:'山西焦煤', close:8.9, pct_change:0.56},
  ],
  '保险': [
    {ts_code:'601628.SH', name:'中国人寿', close:32.56, pct_change:-0.45},
    {ts_code:'601988.SH', name:'中国人保', close:5.67, pct_change:0.89},
    {ts_code:'000627.SZ', name:'天茂集团', close:3.45, pct_change:1.12},
    {ts_code:'601319.SH', name:'中国人保H', close:4.56, pct_change:-0.67},
  ],
  '软件': [
    {ts_code:'600845.SH', name:'宝信软件', close:38.56, pct_change:1.89},
    {ts_code:'002410.SZ', name:'广联达', close:18.9, pct_change:2.34},
  ],
  '工程机械': [
    {ts_code:'600815.SH', name:'厦工股份', close:3.45, pct_change:0.78},
    {ts_code:'000425.SZ', name:'徐工机械', close:7.89, pct_change:1.56},
    {ts_code:'600710.SH', name:'常林股份', close:5.67, pct_change:-0.89},
  ],
  '安防': [
    {ts_code:'300364.SZ', name:'中文在线', close:18.56, pct_change:2.34},
    {ts_code:'002512.SZ', name:'达华智能', close:5.67, pct_change:-1.12},
    {ts_code:'300177.SZ', name:'中海达', close:8.9, pct_change:0.56},
  ],
  '面板': [
    {ts_code:'002387.SZ', name:'维信诺', close:8.56, pct_change:1.78},
    {ts_code:'300323.SZ', name:'华灿光电', close:6.78, pct_change:-0.45},
    {ts_code:'688303.SH', name:'大全能源', close:32.56, pct_change:2.12},
  ],
  '养殖': [
    {ts_code:'002157.SZ', name:'正邦科技', close:3.45, pct_change:-1.56},
    {ts_code:'002458.SZ', name:'益生股份', close:12.34, pct_change:0.89},
    {ts_code:'002299.SZ', name:'圣农发展', close:18.56, pct_change:1.23},
    {ts_code:'300498.SZ', name:'温氏股份', close:15.67, pct_change:-0.34},
  ],
  '石油': [
    {ts_code:'600157.SH', name:'永泰能源', close:1.56, pct_change:0.34},
    {ts_code:'600546.SH', name:'山煤国际', close:12.34, pct_change:-0.67},
  ],
  '包装': [
    {ts_code:'002599.SZ', name:'盛通股份', close:5.67, pct_change:0.89},
    {ts_code:'002812.SZ', name:'恩捷股份', close:42.56, pct_change:2.34},
    {ts_code:'300429.SZ', name:'强力新材', close:18.9, pct_change:-1.12},
  ],
  '通信设备': [
    {ts_code:'600050.SH', name:'中国联通', close:5.23, pct_change:0.67},
    {ts_code:'600487.SH', name:'亨通光电', close:15.67, pct_change:1.89},
    {ts_code:'002281.SZ', name:'光迅科技', close:28.56, pct_change:-0.45},
  ],
  '物流': [
    {ts_code:'600233.SH', name:'圆通速递', close:14.56, pct_change:0.78},
    {ts_code:'002120.SZ', name:'韵达股份', close:8.9, pct_change:-1.23},
    {ts_code:'603813.SH', name:'原尚股份', close:18.34, pct_change:1.56},
  ],
  '房地产': [
    {ts_code:'600340.SH', name:'华夏幸福', close:3.45, pct_change:-2.34},
    {ts_code:'000069.SZ', name:'华侨城A', close:4.56, pct_change:0.89},
  ],
  '建材': [
    {ts_code:'600720.SH', name:'祁连山', close:12.34, pct_change:0.56},
    {ts_code:'000786.SZ', name:'北新建材', close:28.56, pct_change:1.89},
    {ts_code:'002271.SZ', name:'东方雨虹', close:22.34, pct_change:-0.78},
  ],
  '黄金': [
    {ts_code:'600547.SH', name:'山东黄金', close:22.56, pct_change:1.89},
    {ts_code:'002155.SZ', name:'湖南黄金', close:15.67, pct_change:0.78},
    {ts_code:'600988.SH', name:'赤峰黄金', close:18.9, pct_change:2.34},
    {ts_code:'002237.SZ', name:'恒邦股份', close:12.34, pct_change:-0.56},
    {ts_code:'000975.SZ', name:'银泰黄金', close:15.67, pct_change:1.12},
    {ts_code:'601212.SH', name:'白银有色', close:3.45, pct_change:0.34},
    {ts_code:'002867.SZ', name:'周大生', close:12.56, pct_change:-0.89},
  ],
  '食品': [
    {ts_code:'603345.SH', name:'安井食品', close:68.9, pct_change:2.12},
    {ts_code:'002847.SZ', name:'盐津铺子', close:52.34, pct_change:3.45},
    {ts_code:'603517.SH', name:'绝味食品', close:28.56, pct_change:-0.67},
  ],
  '汽车零部件': [
    {ts_code:'002048.SZ', name:'宁波华翔', close:12.34, pct_change:0.89},
    {ts_code:'600741.SH', name:'华域汽车', close:15.67, pct_change:-0.56},
    {ts_code:'002703.SZ', name:'浙江世宝', close:8.9, pct_change:2.34},
    {ts_code:'603197.SH', name:'保隆科技', close:38.56, pct_change:1.12},
    {ts_code:'002920.SZ', name:'德赛西威', close:108.9, pct_change:3.45},
    {ts_code:'603799.SH', name:'华友钴业', close:22.34, pct_change:-1.78},
  ],
  '医疗服务': [
    {ts_code:'300017.SZ', name:'网宿科技', close:8.45, pct_change:-0.89},
    {ts_code:'300759.SZ', name:'康希诺', close:28.56, pct_change:1.78},
    {ts_code:'002432.SZ', name:'九安医疗', close:32.45, pct_change:3.12},
  ],
};

var insertCount = 0;
var updateCount = 0;

for (var industry in extra) {
  var stocks = extra[industry];
  for (var i = 0; i < stocks.length; i++) {
    var s = stocks[i];
    var existing = db.daily_quotes.findOne({ts_code: s.ts_code, trade_date: trade_date});
    if (!existing) {
      db.daily_quotes.insertOne({
        ts_code: s.ts_code,
        trade_date: trade_date,
        close: s.close,
        pct_change: s.pct_change,
        amount: Math.round(Math.random() * 200000000),
        vol: Math.round(Math.random() * 15000000)
      });
      insertCount++;
    }
    var res = db.stocks.updateOne(
      {ts_code: s.ts_code},
      {$set: {industry: industry, name: s.name}},
      {upsert: true}
    );
    if (res.modifiedCount > 0 || res.upsertedId) updateCount++;
  }
}

print('Inserted ' + insertCount + ' new quotes');
print('Updated ' + updateCount + ' stocks');

var pipeline = [
  {$match: {industry: {$ne: ''}}},
  {$group: {_id: '$industry', count: {$sum: 1}}},
  {$sort: {count: 1}}
];
db.stocks.aggregate(pipeline).forEach(function(d) {
  print(d._id + ': ' + d.count);
});
