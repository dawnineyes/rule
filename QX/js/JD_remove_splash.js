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
} else if (url.includes("functionId=basicConfig")) {
  // 屏蔽 ttt_new_link_string
  if (obj?.data?.babel?.TTTNewLoad?.ttt_new_link_string) {
    obj.data.babel.TTTNewLoad.ttt_new_link_string = "";
  }

  // 屏蔽 confirmH5 aids
  if (obj?.data?.babel?.["TTT-confirmH5-aids"]) {
    obj.data.babel["TTT-confirmH5-aids"]={"TTT-confirmH5-aids":""};
  }

  // 屏蔽 LiveWebView 激励广告
  if (obj?.data?.mPaaSABTest?.LiveWebView?.activityOpen) {
    obj.data.mPaaSABTest.LiveWebView.activityOpen = {};
  }

  // 屏蔽微信分享中推广排序
  //if (obj?.data?.JDShare?.sortWeiXinContentParam) {
  //  obj.data.JDShare.sortWeiXinContentParam.sort = "";
  //}
}

$done({ body: JSON.stringify(obj) });
