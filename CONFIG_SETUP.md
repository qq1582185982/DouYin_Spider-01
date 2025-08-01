# 配置说明

## 环境变量配置

在项目根目录创建 `.env` 文件，包含以下配置：

```env
# 抖音爬虫Cookie配置
# 在浏览器中打开 www.douyin.com，登录后按F12打开开发者工具
# 在Network标签页中找到任意一个请求，复制其Cookie值
DY_COOKIES=your_douyin_cookies_here

# 抖音直播间监听Cookie配置  
# 在浏览器中打开 live.douyin.com，登录后按F12打开开发者工具
# 在Network标签页中找到任意一个请求，复制其Cookie值
DY_LIVE_COOKIES=your_douyin_live_cookies_here
```

## 获取Cookie步骤

1. 打开浏览器，访问 `www.douyin.com`
2. 登录你的抖音账号
3. 按F12打开开发者工具
4. 切换到Network标签页
5. 刷新页面或进行任意操作
6. 在Network中找到任意一个请求（如api请求）
7. 点击该请求，在Headers中找到Cookie字段
8. 复制整个Cookie值到 `.env` 文件的 `DY_COOKIES` 变量中

对于直播间监听，重复上述步骤，但访问 `live.douyin.com`，将Cookie值填入 `DY_LIVE_COOKIES` 变量中。

## 注意事项

- 必须登录抖音账号才能获取有效的Cookie
- Cookie会定期过期，需要重新获取
- 请妥善保管你的Cookie信息，不要泄露给他人 