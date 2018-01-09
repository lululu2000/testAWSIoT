# AWS IoTで温度データ収集の検証
## 概要

Raspberryに温度センサーを取り付け、取得された温度データをAWSIoTPythonSDKを利用し、AWS IoTへ送信する。送信された温度データをElasticsearchで蓄積し、Kibanaで統計結果を確認する。

## Raspberryに温度センサーを取り付ける

### 配線

下図に示すように温度センサーDA18B20の３本の足をRaspberryにつなぐ。
![DA18B20](imgs/DS18B20.jpg)
![Raspberry](imgs/Raspberry.png)

### /boot/config.txtの編集

/boot/config.txtに下記記述を追加する。

`dtoverlay=w1-gpio,gpiopin=4,pullup=y`

### カーネルモジュールをロードする

1-wire用下記モジュールをロードし、Raspberryを再起動する。

    $ sudo modprobe w1-gpio
    $ sudo modprobe w1-therm
    $ sudo reboot


### 温度センサーが正常に動作していることを確認する

モジュールが正常動作するなら、/sys/bus/w1/devicesの下に「28-」で始まるディレクトリーが作成される。その中にw1_slaveのファイルに温度を書き込まれる。

    $ cat /sys/bus/w1/devices/28-0216258811ee/w1_slave
    a1 01 4b 46 7f ff 0c 10 8c : crc=8c YES
    a1 01 4b 46 7f ff 0c 10 8c t=26062

上記ファイルの２行目のtの1000分の1は摂氏温度である。

