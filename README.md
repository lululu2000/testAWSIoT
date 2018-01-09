# AWS IoTで温度データ収集の検証
## 概要
Raspberryに温度センサーを取り付け、取得された温度データをAWSIoTPythonSDKを利用し、AWS IoTへ送信する。送信された温度データをElasticsearchで蓄積し、Kibanaで統計結果を確認する。
---
## Raspberryに温度センサーを取り付ける
### 配線
下図のように温度センサーDA18B20をRaspberryにつなぐ。
!DA18B20(imgs/DS18B20.jpg)
!Raspberry(imgs/Raspberry.png)


