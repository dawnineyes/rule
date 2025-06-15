// bilibili_splash.js 
let body = $response.body;
if (body) {
  try {
    let obj = JSON.parse(body);
    if (obj.data?.list) {
      for (let item of obj.data.list) {
        item.duration = 0;
        item.begin_time = 4102329600;
        item.end_time = 4102329600;
      }
    }
    body = JSON.stringify(obj);
  } catch (e) {
    console.log("bilibili openad error:" + e);
  }
}
$done({ body });
