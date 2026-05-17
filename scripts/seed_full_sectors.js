var trade_date = '20260515';

function rand(min, max) { return +(min + Math.random() * (max - min)).toFixed(2); }
function randPct() { return +((Math.random() - 0.45) * 10).toFixed(2); }

var sectors = {
  '银行': [
    {ts_code:'601288.SH', name:'农业银行'}, {ts_code:'600015.SH', name:'华夏银行'},
    {ts_code:'601818.SH', name:'光大银行'}, {ts_code:'600919.SH', name:'江苏银行'},
    {ts_code:'601169.SH', name:'北京银行'}, {ts_code:'600016.SH', name:'民生银行'},
    {ts_code:'601398.SH', name:'工商银行'}, {ts_code:'600036.SH', name:'招商银行'},
    {ts_code:'000001.SZ', name:'平安银行'}, {ts_code:'601166.SH', name:'兴业银行'},
  ],
  '白酒': [
    {ts_code:'000799.SZ', name:'酒鬼酒'}, {ts_code:'603589.SH', name:'口子窖'},
    {ts_code:'000596.SZ', name:'古井贡酒'}, {ts_code:'000858.SZ', name:'五粮液'},
    {ts_code:'600519.SH', name:'贵州茅台'}, {ts_code:'600809.SH', name:'山西汾酒'},
    {ts_code:'002304.SZ', name:'洋河股份'}, {ts_code:'000568.SZ', name:'泸州老窖'},
    {ts_code:'603369.SH', name:'今世缘'}, {ts_code:'000557.SZ', name:'西部创业'},
  ],
  '医药': [
    {ts_code:'600196.SH', name:'复星医药'}, {ts_code:'000538.SZ', name:'云南白药'},
    {ts_code:'600085.SH', name:'同仁堂'}, {ts_code:'000963.SZ', name:'华东医药'},
    {ts_code:'603259.SH', name:'药明康德'}, {ts_code:'600276.SH', name:'恒瑞医药'},
    {ts_code:'002007.SZ', name:'华兰生物'}, {ts_code:'000661.SZ', name:'长春高新'},
    {ts_code:'300015.SZ', name:'爱尔眼科'}, {ts_code:'300347.SZ', name:'泰格医药'},
  ],
  '汽车': [
    {ts_code:'600733.SH', name:'北汽蓝谷'}, {ts_code:'000800.SZ', name:'一汽解放'},
    {ts_code:'600104.SH', name:'上汽集团'}, {ts_code:'002594.SZ', name:'比亚迪'},
    {ts_code:'601633.SH', name:'长城汽车'}, {ts_code:'000625.SZ', name:'长安汽车'},
    {ts_code:'600685.SH', name:'广汽集团'}, {ts_code:'601238.SH', name:'广汽集团'},
    {ts_code:'000980.SZ', name:'众泰汽车'}, {ts_code:'600760.SH', name:'中航沈飞'},
  ],
  '半导体': [
    {ts_code:'002049.SZ', name:'紫光国微'}, {ts_code:'002129.SZ', name:'中环股份'},
    {ts_code:'603501.SH', name:'韦尔股份'}, {ts_code:'688981.SH', name:'中芯国际'},
    {ts_code:'600703.SH', name:'三安光电'}, {ts_code:'002371.SZ', name:'北方华创'},
    {ts_code:'688012.SH', name:'中微公司'}, {ts_code:'603005.SH', name:'晶方科技'},
    {ts_code:'300661.SZ', name:'圣邦股份'}, {ts_code:'688256.SH', name:'寒武纪'},
  ],
  '消费电子': [
    {ts_code:'002475.SZ', name:'立讯精密'}, {ts_code:'002241.SZ', name:'歌尔股份'},
    {ts_code:'002056.SZ', name:'横店东磁'}, {ts_code:'002415.SZ', name:'海康威视'},
    {ts_code:'300433.SZ', name:'蓝思科技'}, {ts_code:'002008.SZ', name:'大族激光'},
    {ts_code:'300136.SZ', name:'信维通信'}, {ts_code:'002236.SZ', name:'大华股份'},
    {ts_code:'601138.SH', name:'工业富联'}, {ts_code:'002916.SZ', name:'深南电路'},
  ],
  '电力': [
    {ts_code:'601012.SH', name:'隆基绿能'}, {ts_code:'600900.SH', name:'长江电力'},
    {ts_code:'600886.SH', name:'国投电力'}, {ts_code:'600023.SH', name:'浙能电力'},
    {ts_code:'601985.SH', name:'中国核电'}, {ts_code:'600795.SH', name:'国电电力'},
    {ts_code:'003816.SH', name:'中国广核'}, {ts_code:'600674.SH', name:'川投能源'},
    {ts_code:'601027.SH', name:'华能国际'}, {ts_code:'600884.SH', name:'杉杉股份'},
  ],
  '保险': [
    {ts_code:'601601.SH', name:'中国太保'}, {ts_code:'601336.SH', name:'新华保险'},
    {ts_code:'601318.SH', name:'中国平安'}, {ts_code:'601628.SH', name:'中国人寿'},
    {ts_code:'601988.SH', name:'中国人保'}, {ts_code:'002141.SZ', name:'贤丰控股'},
    {ts_code:'601609.SH', name:'金地集团'}, {ts_code:'600292.SH', name:'远达环保'},
    {ts_code:'000627.SZ', name:'天茂集团'}, {ts_code:'601319.SH', name:'中国人保'},
  ],
  '食品饮料': [
    {ts_code:'000895.SZ', name:'双汇发展'}, {ts_code:'603288.SH', name:'海天味业'},
    {ts_code:'600872.SH', name:'中炬高新'}, {ts_code:'600779.SH', name:'水井坊'},
    {ts_code:'000848.SZ', name:'承德露露'}, {ts_code:'002568.SZ', name:'百润股份'},
    {ts_code:'603288.SH', name:'海天味业'}, {ts_code:'600690.SH', name:'海尔智家'},
    {ts_code:'000568.SZ', name:'泸州老窖'}, {ts_code:'002330.SZ', name:'得利斯'},
  ],
  '人工智能': [
    {ts_code:'002230.SZ', name:'科大讯飞'}, {ts_code:'688787.SH', name:'海天瑞声'},
    {ts_code:'688041.SH', name:'海光信息'}, {ts_code:'688256.SH', name:'寒武纪'},
    {ts_code:'300496.SZ', name:'中科创达'}, {ts_code:'688037.SH', name:'芯源微'},
    {ts_code:'300454.SZ', name:'深信服'}, {ts_code:'688111.SH', name:'金山办公'},
    {ts_code:'688083.SH', name:'中望软件'}, {ts_code:'300033.SZ', name:'同花顺'},
  ],
  '新能源': [
    {ts_code:'300750.SZ', name:'宁德时代'}, {ts_code:'600438.SH', name:'通威股份'},
    {ts_code:'601012.SH', name:'隆基绿能'}, {ts_code:'002202.SZ', name:'金风科技'},
    {ts_code:'600905.SH', name:'三峡能源'}, {ts_code:'002129.SZ', name:'中环股份'},
    {ts_code:'300274.SZ', name:'阳光电源'}, {ts_code:'688599.SH', name:'天合光能'},
    {ts_code:'601865.SH', name:'福莱特'}, {ts_code:'002459.SZ', name:'晶澳科技'},
  ],
  '券商': [
    {ts_code:'600030.SH', name:'中信证券'}, {ts_code:'601211.SH', name:'国泰君安'},
    {ts_code:'600837.SH', name:'海通证券'}, {ts_code:'601688.SH', name:'华泰证券'},
    {ts_code:'000776.SZ', name:'广发证券'}, {ts_code:'601788.SH', name:'光大证券'},
    {ts_code:'600109.SH', name:'国金证券'}, {ts_code:'601198.SH', name:'东兴证券'},
    {ts_code:'000166.SZ', name:'申万宏源'}, {ts_code:'600999.SH', name:'招商证券'},
  ],
  '化工': [
    {ts_code:'600309.SH', name:'万华化学'}, {ts_code:'002493.SZ', name:'荣盛石化'},
    {ts_code:'600426.SH', name:'华鲁恒升'}, {ts_code:'002648.SZ', name:'卫星化学'},
    {ts_code:'600989.SH', name:'宝丰能源'}, {ts_code:'000301.SZ', name:'东方盛虹'},
    {ts_code:'002470.SZ', name:'金正大'}, {ts_code:'600803.SH', name:'新奥股份'},
    {ts_code:'600746.SH', name:'江苏索普'}, {ts_code:'002054.SZ', name:'德美化工'},
  ],
  '煤炭': [
    {ts_code:'601088.SH', name:'中国神华'}, {ts_code:'601225.SH', name:'陕西煤业'},
    {ts_code:'601898.SH', name:'中煤能源'}, {ts_code:'600188.SH', name:'兖矿能源'},
    {ts_code:'601015.SH', name:'陕西黑猫'}, {ts_code:'000983.SZ', name:'山西焦煤'},
    {ts_code:'600508.SH', name:'上海能源'}, {ts_code:'601699.SH', name:'潞安环能'},
    {ts_code:'600123.SH', name:'兰花科创'}, {ts_code:'000937.SZ', name:'冀中能源'},
  ],
  '房地产': [
    {ts_code:'000002.SZ', name:'万科A'}, {ts_code:'600048.SH', name:'保利发展'},
    {ts_code:'001979.SZ', name:'招商蛇口'}, {ts_code:'600340.SH', name:'华夏幸福'},
    {ts_code:'000069.SZ', name:'华侨城A'}, {ts_code:'600606.SH', name:'绿地控股'},
    {ts_code:'001872.SZ', name:'招商港口'}, {ts_code:'600383.SH', name:'金地集团'},
    {ts_code:'000031.SZ', name:'大悦城'}, {ts_code:'601155.SH', name:'新城控股'},
  ],
  '医疗器械': [
    {ts_code:'300760.SZ', name:'迈瑞医疗'}, {ts_code:'688050.SH', name:'爱博医疗'},
    {ts_code:'300003.SZ', name:'乐普医疗'}, {ts_code:'688060.SH', name:'联影医疗'},
    {ts_code:'300633.SZ', name:'开立医疗'}, {ts_code:'002901.SZ', name:'大博医疗'},
    {ts_code:'688108.SH', name:'美迪西'}, {ts_code:'300832.SZ', name:'新产业'},
    {ts_code:'688185.SH', name:'康希诺'}, {ts_code:'300347.SZ', name:'泰格医药'},
  ],
  '中药': [
    {ts_code:'600436.SH', name:'片仔癀'}, {ts_code:'000538.SZ', name:'云南白药'},
    {ts_code:'600085.SH', name:'同仁堂'}, {ts_code:'600750.SH', name:'江中药业'},
    {ts_code:'000423.SZ', name:'东阿阿胶'}, {ts_code:'002607.SZ', name:'中公教育'},
    {ts_code:'600129.SH', name:'太极集团'}, {ts_code:'000590.SZ', name:'启迪古汉'},
    {ts_code:'600771.SH', name:'广誉远'}, {ts_code:'002118.SZ', name:'紫鑫药业'},
  ],
  '工程机械': [
    {ts_code:'600031.SH', name:'三一重工'}, {ts_code:'000157.SZ', name:'中联重科'},
    {ts_code:'600815.SH', name:'厦工股份'}, {ts_code:'000425.SZ', name:'徐工机械'},
    {ts_code:'600710.SH', name:'常林股份'}, {ts_code:'002097.SZ', name:'山河智能'},
    {ts_code:'600761.SH', name:'安徽合力'}, {ts_code:'601100.SH', name:'恒立液压'},
    {ts_code:'603338.SH', name:'浙江鼎力'}, {ts_code:'002523.SZ', name:'航天工程'},
  ],
  '通信设备': [
    {ts_code:'000063.SZ', name:'中兴通讯'}, {ts_code:'002396.SZ', name:'星网锐捷'},
    {ts_code:'600050.SH', name:'中国联通'}, {ts_code:'600487.SH', name:'亨通光电'},
    {ts_code:'002281.SZ', name:'光迅科技'}, {ts_code:'300136.SZ', name:'信维通信'},
    {ts_code:'688036.SH', name:'传音控股'}, {ts_code:'300308.SZ', name:'中际旭创'},
    {ts_code:'002446.SZ', name:'盛路通信'}, {ts_code:'300502.SZ', name:'新易盛'},
  ],
  '物流': [
    {ts_code:'002352.SZ', name:'顺丰控股'}, {ts_code:'601156.SH', name:'圆通速递'},
    {ts_code:'600233.SH', name:'圆通速递'}, {ts_code:'002120.SZ', name:'韵达股份'},
    {ts_code:'603813.SH', name:'原尚股份'}, {ts_code:'600270.SH', name:'外运发展'},
    {ts_code:'601633.SH', name:'长城汽车'}, {ts_code:'000996.SZ', name:'中国中期'},
    {ts_code:'603167.SH', name:'渤海轮渡'}, {ts_code:'603567.SH', name:'珍宝岛'},
  ],
  '轨道交通': [
    {ts_code:'601766.SH', name:'中国中车'}, {ts_code:'600845.SH', name:'中国通号'},
    {ts_code:'601006.SH', name:'大秦铁路'}, {ts_code:'600018.SH', name:'上港集团'},
    {ts_code:'601333.SH', name:'广深铁路'}, {ts_code:'600009.SH', name:'上海机场'},
    {ts_code:'601880.SH', name:'大连港'}, {ts_code:'600017.SH', name:'日照港'},
    {ts_code:'601000.SH', name:'唐山港'}, {ts_code:'600717.SH', name:'天津港'},
  ],
  '旅游': [
    {ts_code:'601888.SH', name:'中国中免'}, {ts_code:'600054.SH', name:'黄山旅游'},
    {ts_code:'000978.SZ', name:'桂林旅游'}, {ts_code:'600138.SH', name:'中青旅'},
    {ts_code:'002033.SZ', name:'丽江股份'}, {ts_code:'600593.SH', name:'大连圣亚'},
    {ts_code:'000610.SZ', name:'西安旅游'}, {ts_code:'600706.SH', name:'曲江文旅'},
    {ts_code:'002059.SZ', name:'云南旅游'}, {ts_code:'600749.SH', name:'西藏旅游'},
  ],
  '面板': [
    {ts_code:'000725.SZ', name:'京东方A'}, {ts_code:'000100.SZ', name:'TCL科技'},
    {ts_code:'002387.SZ', name:'维信诺'}, {ts_code:'600551.SH', name:'时代出版'},
    {ts_code:'002415.SZ', name:'海康威视'}, {ts_code:'300487.SZ', name:'蓝晓科技'},
    {ts_code:'688060.SH', name:'联影医疗'}, {ts_code:'002618.SZ', name:'丹邦科技'},
    {ts_code:'300323.SZ', name:'华灿光电'}, {ts_code:'688303.SH', name:'大全能源'},
  ],
  '安防': [
    {ts_code:'002415.SZ', name:'海康威视'}, {ts_code:'002236.SZ', name:'大华股份'},
    {ts_code:'300364.SZ', name:'中文在线'}, {ts_code:'002512.SZ', name:'达华智能'},
    {ts_code:'300177.SZ', name:'中海达'}, {ts_code:'002465.SZ', name:'海格通信'},
    {ts_code:'300010.SZ', name:'立思辰'}, {ts_code:'300496.SZ', name:'中科创达'},
    {ts_code:'688208.SH', name:'道通科技'}, {ts_code:'002512.SZ', name:'达华智能'},
  ],
  '乳制品': [
    {ts_code:'600887.SH', name:'伊利股份'}, {ts_code:'600429.SH', name:'三元股份'},
    {ts_code:'002570.SZ', name:'贝因美'}, {ts_code:'600597.SH', name:'光明乳业'},
    {ts_code:'000918.SZ', name:'嘉凯城'}, {ts_code:'002746.SZ', name:'仙坛股份'},
    {ts_code:'600873.SH', name:'梅花生物'}, {ts_code:'000876.SZ', name:'新希望'},
    {ts_code:'002311.SZ', name:'海大集团'}, {ts_code:'600965.SH', name:'福成股份'},
  ],
  '互联网': [
    {ts_code:'300059.SZ', name:'东方财富'}, {ts_code:'300454.SZ', name:'深信服'},
    {ts_code:'300033.SZ', name:'同花顺'}, {ts_code:'002555.SZ', name:'三七互娱'},
    {ts_code:'300418.SZ', name:'昆仑万维'}, {ts_code:'002602.SZ', name:'世纪华通'},
    {ts_code:'300496.SZ', name:'中科创达'}, {ts_code:'688111.SH', name:'金山办公'},
    {ts_code:'300431.SZ', name:'暴风集团'}, {ts_code:'002174.SZ', name:'游族网络'},
  ],
  '软件': [
    {ts_code:'600588.SH', name:'用友网络'}, {ts_code:'002368.SZ', name:'太极股份'},
    {ts_code:'600845.SH', name:'宝信软件'}, {ts_code:'300033.SZ', name:'同花顺'},
    {ts_code:'002410.SZ', name:'广联达'}, {ts_code:'300454.SZ', name:'深信服'},
    {ts_code:'688111.SH', name:'金山办公'}, {ts_code:'600588.SH', name:'用友网络'},
    {ts_code:'300496.SZ', name:'中科创达'}, {ts_code:'002230.SZ', name:'科大讯飞'},
  ],
  '机器人': [
    {ts_code:'300124.SZ', name:'汇川技术'}, {ts_code:'688169.SH', name:'石头科技'},
    {ts_code:'002747.SZ', name:'埃斯顿'}, {ts_code:'300024.SZ', name:'机器人'},
    {ts_code:'688006.SH', name:'杭可科技'}, {ts_code:'300607.SZ', name:'拓斯达'},
    {ts_code:'688005.SH', name:'容百科技'}, {ts_code:'300159.SZ', name:'新研股份'},
    {ts_code:'002097.SZ', name:'山河智能'}, {ts_code:'300307.SZ', name:'慈星股份'},
  ],
  '电子制造': [
    {ts_code:'601138.SH', name:'工业富联'}, {ts_code:'002916.SZ', name:'深南电路'},
    {ts_code:'002475.SZ', name:'立讯精密'}, {ts_code:'300433.SZ', name:'蓝思科技'},
    {ts_code:'002008.SZ', name:'大族激光'}, {ts_code:'300136.SZ', name:'信维通信'},
    {ts_code:'002371.SZ', name:'北方华创'}, {ts_code:'603501.SH', name:'韦尔股份'},
    {ts_code:'300661.SZ', name:'圣邦股份'}, {ts_code:'002049.SZ', name:'紫光国微'},
  ],
  '建材': [
    {ts_code:'600585.SH', name:'海螺水泥'}, {ts_code:'600801.SH', name:'华新水泥'},
    {ts_code:'600720.SH', name:'祁连山'}, {ts_code:'000786.SZ', name:'北新建材'},
    {ts_code:'002271.SZ', name:'东方雨虹'}, {ts_code:'600586.SH', name:'金晶科技'},
    {ts_code:'000672.SZ', name:'上峰水泥'}, {ts_code:'600449.SH', name:'宁夏建材'},
    {ts_code:'600883.SH', name:'博闻科技'}, {ts_code:'600553.SH', name:'河钢股份'},
  ],
  '航运': [
    {ts_code:'601919.SH', name:'中远海控'}, {ts_code:'601872.SH', name:'招商轮船'},
    {ts_code:'600018.SH', name:'上港集团'}, {ts_code:'601880.SH', name:'辽港股份'},
    {ts_code:'600428.SH', name:'中远海特'}, {ts_code:'601022.SH', name:'宁波港'},
    {ts_code:'600017.SH', name:'日照港'}, {ts_code:'601000.SH', name:'唐山港'},
    {ts_code:'600717.SH', name:'天津港'}, {ts_code:'601006.SH', name:'大秦铁路'},
  ],
  '石油化工': [
    {ts_code:'600028.SH', name:'中国石化'}, {ts_code:'600688.SH', name:'上海石化'},
    {ts_code:'601857.SH', name:'中国石油'}, {ts_code:'002493.SZ', name:'荣盛石化'},
    {ts_code:'600989.SH', name:'宝丰能源'}, {ts_code:'000301.SZ', name:'东方盛虹'},
    {ts_code:'600803.SH', name:'新奥股份'}, {ts_code:'002648.SZ', name:'卫星化学'},
    {ts_code:'600426.SH', name:'华鲁恒升'}, {ts_code:'000554.SZ', name:'泰山石油'},
  ],
  '汽车零部件': [
    {ts_code:'600660.SH', name:'福耀玻璃'}, {ts_code:'002594.SZ', name:'比亚迪'},
    {ts_code:'601100.SH', name:'恒立液压'}, {ts_code:'002048.SZ', name:'宁波华翔'},
    {ts_code:'600741.SH', name:'华域汽车'}, {ts_code:'002703.SZ', name:'浙江世宝'},
    {ts_code:'603197.SH', name:'保隆科技'}, {ts_code:'002920.SZ', name:'德赛西威'},
    {ts_code:'300750.SZ', name:'宁德时代'}, {ts_code:'603799.SH', name:'华友钴业'},
  ],
  '养殖': [
    {ts_code:'002714.SZ', name:'牧原股份'}, {ts_code:'000876.SZ', name:'新希望'},
    {ts_code:'002157.SZ', name:'正邦科技'}, {ts_code:'002311.SZ', name:'海大集团'},
    {ts_code:'000895.SZ', name:'双汇发展'}, {ts_code:'002458.SZ', name:'益生股份'},
    {ts_code:'002299.SZ', name:'圣农发展'}, {ts_code:'300498.SZ', name:'温氏股份'},
    {ts_code:'002746.SZ', name:'仙坛股份'}, {ts_code:'600965.SH', name:'福成股份'},
  ],
  '医疗服务': [
    {ts_code:'300015.SZ', name:'爱尔眼科'}, {ts_code:'688111.SH', name:'金山办公'},
    {ts_code:'300347.SZ', name:'泰格医药'}, {ts_code:'603259.SH', name:'药明康德'},
    {ts_code:'300017.SZ', name:'网宿科技'}, {ts_code:'300759.SZ', name:'康希诺'},
    {ts_code:'688108.SH', name:'美迪西'}, {ts_code:'300760.SZ', name:'迈瑞医疗'},
    {ts_code:'688060.SH', name:'联影医疗'}, {ts_code:'002432.SZ', name:'九安医疗'},
  ],
  '包装': [
    {ts_code:'002032.SZ', name:'苏泊尔'}, {ts_code:'002012.SZ', name:'凯恩股份'},
    {ts_code:'002599.SZ', name:'盛通股份'}, {ts_code:'600872.SH', name:'中炬高新'},
    {ts_code:'002812.SZ', name:'恩捷股份'}, {ts_code:'300429.SZ', name:'强力新材'},
    {ts_code:'002545.SZ', name:'东方铁塔'}, {ts_code:'300056.SZ', name:'三维丝'},
    {ts_code:'002557.SZ', name:'洽洽食品'}, {ts_code:'600963.SH', name:'岳阳林纸'},
  ],
  '黄金': [
    {ts_code:'601899.SH', name:'紫金矿业'}, {ts_code:'600489.SH', name:'中金黄金'},
    {ts_code:'600547.SH', name:'山东黄金'}, {ts_code:'002155.SZ', name:'湖南黄金'},
    {ts_code:'600988.SH', name:'赤峰黄金'}, {ts_code:'002237.SZ', name:'恒邦股份'},
    {ts_code:'600311.SH', name:'荣华实业'}, {ts_code:'000975.SZ', name:'银泰黄金'},
    {ts_code:'601212.SH', name:'白银有色'}, {ts_code:'002867.SZ', name:'周大生'},
  ],
  '食品': [
    {ts_code:'000895.SZ', name:'双汇发展'}, {ts_code:'600872.SH', name:'中炬高新'},
    {ts_code:'002557.SZ', name:'洽洽食品'}, {ts_code:'600779.SH', name:'水井坊'},
    {ts_code:'000848.SZ', name:'承德露露'}, {ts_code:'002568.SZ', name:'百润股份'},
    {ts_code:'002330.SZ', name:'得利斯'}, {ts_code:'603345.SH', name:'安井食品'},
    {ts_code:'002847.SZ', name:'盐津铺子'}, {ts_code:'603517.SH', name:'绝味食品'},
  ],
  '石油': [
    {ts_code:'601857.SH', name:'中国石油'}, {ts_code:'600028.SH', name:'中国石化'},
    {ts_code:'601857.SH', name:'中国石油'}, {ts_code:'600688.SH', name:'上海石化'},
    {ts_code:'000554.SZ', name:'泰山石油'}, {ts_code:'600157.SH', name:'永泰能源'},
    {ts_code:'002207.SZ', name:'准油股份'}, {ts_code:'600546.SH', name:'山煤国际'},
    {ts_code:'601015.SH', name:'陕西黑猫'}, {ts_code:'600508.SH', name:'上海能源'},
  ],
};

var insertCount = 0;
var updateCount = 0;

for (var industry in sectors) {
  var stocks = sectors[industry];
  for (var i = 0; i < stocks.length; i++) {
    var s = stocks[i];
    var close = rand(3, 300);
    var pct = randPct();
    var existing = db.daily_quotes.findOne({ts_code: s.ts_code, trade_date: trade_date});
    if (!existing) {
      db.daily_quotes.insertOne({
        ts_code: s.ts_code,
        trade_date: trade_date,
        close: close,
        pct_change: pct,
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

var total = db.daily_quotes.distinct('ts_code').length;
var industries = db.stocks.distinct('industry', {industry: {$ne: ''}});
print('Total stocks with quotes: ' + total);
print('Industry count: ' + industries.length);
