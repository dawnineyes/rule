// JD_remove_splash.js 去开屏

const url = $request.url;
if (!$response.body) $done({});
let obj = JSON.parse($response.body);

// 只处理开屏广告请求
if (url.includes("functionId=start")) {
  // 清除开屏广告图片
  if (obj?.images?.length > 0) {
    obj.images = [];
  }
  // 禁用每日广告展示次数
  if (obj?.showTimesDaily) {
    obj.showTimesDaily = 0;
  }
}

$done({ body: JSON.stringify(obj) });
