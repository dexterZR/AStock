var trade_date = '20260515';

var industryStocks = {
  '银行': [
    {ts_code:'601288.SH', name:'农业银行', close:4.56, pct_change:0.44},
    {ts_code:'600015.SH', name:'华夏银行', close:7.23, pct_change:-0.82},
    {ts_code:'601818.SH', name:'光大银行', close:3.89, pct_change:0.26},
    {ts_code:'600919.SH', name:'江苏银行', close:8.12, pct_change:1.24},
    {ts_code:'601169.SH', name:'北京银行', close:5.67, pct_change:-0.35},
  ],
  '白酒': [
    {ts_code:'000799.SZ', name:'酒鬼酒', close:22.34, pct_change:-1.56},
    {ts_code:'603589.SH', name:'口子窖', close:35.67, pct_change:0.89},
    {ts_code:'000596.SZ', name:'古井贡酒', close:198.5, pct_change:1.23},
  ],
  '医药': [
    {ts_code:'600196.SH', name:'复星医药', close:22.56, pct_change:-0.67},
    {ts_code:'000538.SZ', name:'云南白药', close:62.34, pct_change:-0.34},
    {ts_code:'600085.SH', name:'同仁堂', close:42.67, pct_change:-0.45},
    {ts_code:'000963.SZ', name:'华东医药', close:28.56, pct_change:2.34},
    {ts_code:'603259.SH', name:'药明康德', close:62.15, pct_change:2.34},
  ],
  '汽车': [
    {ts_code:'600733.SH', name:'北汽蓝谷', close:8.56, pct_change:-1.23},
    {ts_code:'000800.SZ', name:'一汽解放', close:7.89, pct_change:0.56},
    {ts_code:'600104.SH', name:'上汽集团', close:14.56, pct_change:0.78},
  ],
  '半导体': [
    {ts_code:'002049.SZ', name:'紫光国微', close:108.5, pct_change:5.23},
    {ts_code:'002129.SZ', name:'中环股份', close:12.34, pct_change:4.89},
    {ts_code:'603501.SH', name:'韦尔股份', close:88.56, pct_change:3.12},
    {ts_code:'688981.SH', name:'中芯国际', close:52.34, pct_change:2.45},
  ],
  '消费电子': [
    {ts_code:'002475.SZ', name:'立讯精密', close:32.18, pct_change:-1.45},
    {ts_code:'002241.SZ', name:'歌尔股份', close:32.18, pct_change:3.78},
    {ts_code:'002056.SZ', name:'横店东磁', close:15.67, pct_change:1.12},
  ],
  '石油': [
    {ts_code:'600028.SH', name:'中国石化', close:5.67, pct_change:0.35},
    {ts_code:'601857.SH', name:'中国石油', close:8.23, pct_change:0.49},
  ],
  '电力': [
    {ts_code:'601012.SH', name:'隆基绿能', close:8.52, pct_change:3.21},
    {ts_code:'600900.SH', name:'长江电力', close:28.45, pct_change:-1.47},
    {ts_code:'600886.SH', name:'国投电力', close:14.56, pct_change:0.89},
  ],
  '保险': [
    {ts_code:'601601.SH', name:'中国太保', close:25.34, pct_change:-1.56},
    {ts_code:'601336.SH', name:'新华保险', close:32.78, pct_change:-0.89},
  ],
  '食品饮料': [
    {ts_code:'000895.SZ', name:'双汇发展', close:18.45, pct_change:0.89},
    {ts_code:'603288.SH', name:'海天味业', close:35.67, pct_change:1.64},
    {ts_code:'600872.SH', name:'中炬高新', close:22.34, pct_change:-0.56},
  ],
  '人工智能': [
    {ts_code:'002230.SZ', name:'科大讯飞', close:52.34, pct_change:4.56},
    {ts_code:'688787.SH', name:'海天瑞声', close:45.67, pct_change:3.12},
    {ts_code:'688041.SH', name:'海光信息', close:78.9, pct_change:2.67},
  ],
  '医疗器械': [
    {ts_code:'300760.SZ', name:'迈瑞医疗', close:285.6, pct_change:-2.67},
    {ts_code:'688050.SH', name:'爱博医疗', close:68.34, pct_change:-1.23},
  ],
  '新能源': [
    {ts_code:'300750.SZ', name:'宁德时代', close:198.5, pct_change:-0.8},
    {ts_code:'601012.SH', name:'隆基绿能', close:8.52, pct_change:3.21},
    {ts_code:'600438.SH', name:'通威股份', close:22.56, pct_change:-1.34},
  ],
  '煤炭': [
    {ts_code:'601088.SH', name:'中国神华', close:32.56, pct_change:-0.67},
    {ts_code:'601225.SH', name:'陕西煤业', close:22.89, pct_change:-1.89},
    {ts_code:'601898.SH', name:'中煤能源', close:9.56, pct_change:-0.45},
  ],
  '券商': [
    {ts_code:'600030.SH', name:'中信证券', close:22.34, pct_change:0.67},
    {ts_code:'601211.SH', name:'国泰君安', close:15.78, pct_change:1.23},
    {ts_code:'600837.SH', name:'海通证券', close:10.23, pct_change:-0.56},
  ],
  '化工': [
    {ts_code:'600309.SH', name:'万华化学', close:85.34, pct_change:1.23},
    {ts_code:'002493.SZ', name:'荣盛石化', close:8.56, pct_change:-0.78},
  ],
  '中药': [
    {ts_code:'600436.SH', name:'片仔癀', close:48.92, pct_change:1.56},
    {ts_code:'000538.SZ', name:'云南白药', close:62.34, pct_change:-0.34},
    {ts_code:'600085.SH', name:'同仁堂', close:42.67, pct_change:-0.45},
  ],
  '工程机械': [
    {ts_code:'600031.SH', name:'三一重工', close:16.89, pct_change:1.56},
    {ts_code:'000157.SZ', name:'中联重科', close:8.45, pct_change:0.89},
  ],
  '通信设备': [
    {ts_code:'000063.SZ', name:'中兴通讯', close:28.56, pct_change:-0.73},
    {ts_code:'002396.SZ', name:'星网锐捷', close:22.34, pct_change:1.45},
  ],
  '物流': [
    {ts_code:'002352.SZ', name:'顺丰控股', close:38.56, pct_change:-2.11},
    {ts_code:'601156.SH', name:'圆通速递', close:14.23, pct_change:0.67},
  ],
  '房地产': [
    {ts_code:'000002.SZ', name:'万科A', close:7.12, pct_change:1.9},
    {ts_code:'600048.SH', name:'保利发展', close:10.56, pct_change:-0.45},
    {ts_code:'001979.SZ', name:'招商蛇口', close:8.89, pct_change:0.78},
  ],
  '轨道交通': [
    {ts_code:'601766.SH', name:'中国中车', close:6.78, pct_change:-0.34},
    {ts_code:'600845.SH', name:'中国通号', close:4.56, pct_change:1.12},
  ],
  '旅游': [
    {ts_code:'601888.SH', name:'中国中免', close:68.34, pct_change:1.99},
    {ts_code:'600054.SH', name:'黄山旅游', close:12.56, pct_change:0.45},
  ],
  '面板': [
    {ts_code:'000725.SZ', name:'京东方A', close:4.56, pct_change:1.79},
    {ts_code:'000100.SZ', name:'TCL科技', close:3.89, pct_change:-0.26},
  ],
  '安防': [
    {ts_code:'002415.SZ', name:'海康威视', close:35.42, pct_change:-0.87},
    {ts_code:'002236.SZ', name:'大华股份', close:18.56, pct_change:1.23},
  ],
  '乳制品': [
    {ts_code:'600887.SH', name:'伊利股份', close:28.15, pct_change:-2.34},
    {ts_code:'600429.SH', name:'三元股份', close:5.67, pct_change:0.56},
  ],
  '互联网': [
    {ts_code:'300059.SZ', name:'东方财富', close:18.92, pct_change:-3.12},
    {ts_code:'300454.SZ', name:'深信服', close:68.34, pct_change:1.56},
  ],
  '软件': [
    {ts_code:'600588.SH', name:'用友网络', close:15.23, pct_change:-3.45},
    {ts_code:'002368.SZ', name:'太极股份', close:28.56, pct_change:2.12},
  ],
  '机器人': [
    {ts_code:'300124.SZ', name:'汇川技术', close:42.18, pct_change:-4.56},
    {ts_code:'688169.SH', name:'石头科技', close:198.5, pct_change:1.89},
  ],
  '电子制造': [
    {ts_code:'601138.SH', name:'工业富联', close:22.67, pct_change:1.12},
    {ts_code:'002916.SZ', name:'深南电路', close:88.34, pct_change:2.56},
  ],
  '建材': [
    {ts_code:'600585.SH', name:'海螺水泥', close:22.34, pct_change:0.45},
    {ts_code:'600801.SH', name:'华新水泥', close:12.56, pct_change:-0.89},
  ],
  '航运': [
    {ts_code:'601919.SH', name:'中远海控', close:12.89, pct_change:1.67},
    {ts_code:'601872.SH', name:'招商轮船', close:6.78, pct_change:0.34},
  ],
  '石油化工': [
    {ts_code:'600028.SH', name:'中国石化', close:5.67, pct_change:0.35},
    {ts_code:'600688.SH', name:'上海石化', close:3.45, pct_change:-0.56},
  ],
  '汽车零部件': [
    {ts_code:'600660.SH', name:'福耀玻璃', close:52.34, pct_change:1.45},
    {ts_code:'002594.SZ', name:'比亚迪', close:268.5, pct_change:-2.46},
  ],
  '养殖': [
    {ts_code:'002714.SZ', name:'牧原股份', close:38.67, pct_change:-1.78},
    {ts_code:'000876.SZ', name:'新 希 望', close:8.56, pct_change:-0.45},
  ],
  '医疗服务': [
    {ts_code:'300015.SZ', name:'爱尔眼科', close:28.67, pct_change:2.89},
    {ts_code:'688111.SH', name:'金山办公', close:268.5, pct_change:3.45},
  ],
  '包装': [
    {ts_code:'002032.SZ', name:'苏泊尔', close:15.67, pct_change:-2.89},
    {ts_code:'002012.SZ', name:'凯恩股份', close:8.34, pct_change:0.56},
  ],
  '黄金': [
    {ts_code:'601899.SH', name:'紫金矿业', close:15.78, pct_change:1.23},
    {ts_code:'600489.SH', name:'中金黄金', close:12.34, pct_change:0.89},
  ],
  '食品': [
    {ts_code:'000895.SZ', name:'双汇发展', close:18.45, pct_change:0.89},
    {ts_code:'600872.SH', name:'中炬高新', close:22.34, pct_change:-0.56},
  ],
};

var insertCount = 0;
var updateCount = 0;

for (var industry in industryStocks) {
  var stocks = industryStocks[industry];
  for (var i = 0; i < stocks.length; i++) {
    var s = stocks[i];
    // Insert quote
    var existing = db.daily_quotes.findOne({ts_code: s.ts_code, trade_date: trade_date});
    if (!existing) {
      db.daily_quotes.insertOne({
        ts_code: s.ts_code,
        trade_date: trade_date,
        close: s.close,
        pct_change: s.pct_change,
        amount: Math.round(Math.random() * 100000000),
        vol: Math.round(Math.random() * 10000000)
      });
      insertCount++;
    }
    // Update industry
    var res = db.stocks.updateOne(
      {ts_code: s.ts_code},
      {$set: {industry: industry, name: s.name}}
    );
    if (res.modifiedCount > 0) updateCount++;
  }
}

print('Inserted ' + insertCount + ' new quotes');
print('Updated ' + updateCount + ' stock industries');

var total = db.daily_quotes.distinct('ts_code').length;
var industries = db.stocks.distinct('industry', {industry: {$ne: ''}});
print('Total stocks with quotes: ' + total);
print('Industry count: ' + industries.length);
