// JD_remove_splash.js 去开屏

const url = $request.url;
if (!$response.body)
    $done({});
let obj = JSON.parse($response.body);

// 只处理开屏广告请求
if (url.includes("functionId=start")) {
    try {
        for (let i = 0; i < obj.images.length; i++) {
            for (let j = 0; j < obj.images[i].length; j++) {
                if (obj.images[i][j].showTimes) {
                    obj.images[i][j].showTimes = 0;
                    obj.images[i][j].onlineTime = "2030-12-24 00:00:00";
                    obj.images[i][j].referralsTime = "2030-12-25 00:00:00";
                    obj.images[i][j].time = 0;
                }
            }
        }
        obj.countdown = 100;
        obj.showTimesDaily = 0;
    } catch (err) {
        $.logger.error(`京东开屏去广告出现异常：${err}`);
    }
} else if (url.includes("functionId=basicConfig")) {
    // 屏蔽 ttt_new_link_string
    if (obj?.data?.babel?.TTTNewLoad?.ttt_new_link_string) {
        obj.data.babel.TTTNewLoad.ttt_new_link_string = "";
    }

    // 屏蔽 confirmH5 aids
    if (obj?.data?.babel?.["TTT-confirmH5-aids"]) {
        obj.data.babel["TTT-confirmH5-aids"] = {
            "TTT-confirmH5-aids": ""
        };
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

$done({
    body: JSON.stringify(obj)
});
