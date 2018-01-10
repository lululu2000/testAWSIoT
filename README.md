# AWS IoTで温度データ収集の検証手順
## 概要

RaspberryPiに温度センサーを取り付け、取得された温度データをAWSIoTPythonSDKを利用し、AWS IoTへ送信する。送信された温度データをElasticsearchで蓄積し、Kibanaで統計結果を確認する。

## Raspberryに温度センサーを取り付ける

### 配線

下図に示すように温度センサーDA18B20の３本の足をRaspberryPiにつなぐ。
![DA18B20](imgs/DS18B20.jpg)
![Raspberry](imgs/Raspberry.png)

### /boot/config.txtの編集

/boot/config.txtに下記記述を追加する。

    dtoverlay=w1-gpio,gpiopin=4,pullup=y

### カーネルモジュールをロードする

1-wire用下記モジュールをロードし、RaspberryPiを再起動する。

    pi $ sudo modprobe w1-gpio
    pi $ sudo modprobe w1-therm
    pi $ sudo reboot


### 温度センサーが正常に動作していることを確認する

モジュールが正常動作するなら、/sys/bus/w1/devicesの下に「28-」で始まるディレクトリーが作成される。その中にw1_slaveのファイルに温度が書き込まれる。

    pi $ cat /sys/bus/w1/devices/28-0216258811ee/w1_slave
    a1 01 4b 46 7f ff 0c 10 8c : crc=8c YES
    a1 01 4b 46 7f ff 0c 10 8c t=26062

上記ファイルの２行目のtの1000分の1は摂氏温度である。

## AWS IoTへ接続の準備

主な流れは下記の通り
- AWSアカウント作成
- IoTにデバイス(RaspberryPi)の登録、証明書等の発行
- RaspberryPiからの送信、及びサーバ側の受信を確認する
### AWSアカウントの作成

1.[AWS](https://aws.amazon.co.jp)からアカウントを作成する。

  詳細手順は省略

2.AWSコンソールでIAMユーザとアクセスキーペアを作成する。
  - AWSコンソールを開いて、「サービス」→「IAM」→「ユーザー」を選択する。
  ![IAMユーザ](imgs/Shot001.png)
  - 「ユーザーを追加」をクリックして、ゆーざーの追加画面にユーザーIDを入力し、アクセスの種類に「プログラムによるアクセス」をチェック。「次のステップ：アクセス権限」をクリックする。
  ![ユーザーの追加](imgs/Shot002.png)
  - IoT及びElasticsearchサービスを使う予定なので、「既存のポリシーを直接アタッチ」を選んで、「AWSIoTFullAccess」「AmazonESFullAccess」をチェックし、「次のステップ：確認」をクリックする。
  ![アクセス権限の設定](imgs/Shot003.png)
  - 設定内容を確認し、「ユーザーの作成」をクリックする。
  ![確認](imgs/Shot004.png)
  - ユーザ追加結果画面にアクセスキーペアが表示される。「.csvのダウンロード」をクリックしてキーペア等情報をダウンロードし、控えておく。
  ![結果確認](imgs/Shot005.png)  

### IoTにデバイス(RaspberryPi)の登録、証明書等の発行
1.AWSCLIのインストール

    $ pip install awscli --upgrade --user
  AWSCLIの初期設定

    $ aws configure
    AWS Access Key ID [None]: (先ダウンロードしたアクセスキーID)
    AWS Secret Access Key [None]: (先ダウンロードしたシークレットアクセスキー)
    Default region name [None]: ap-northeast-1
    Default output format [None]: json

2.デバイスを登録

  - デバイスを登録
  ```
    $ aws iot create-thing --thing-name raspberry01
    {
      "thingArn": "arn:aws:iot:ap-northeast-1:011960800664:thing/raspberry01",
      "thingName": "raspberry01",
      "thingId": "f3f84490-06ca-4934-bbbc-81151eecef67"
    }
  ```
  - デバイスの証明書を作成

  ```
  $ mkdir certs
  $ cd certs
  $ aws iot create-keys-and-certificate --set-as-active \
> --certificate-pem-outfile cert.pem \
> --public-key-outfile public.key \
> --private-key-outfile private.key
{
    "certificateArn": "arn:aws:iot:ap-northeast-1:011960800664:cert/d03e8b1c52bdf612a2d6bf4b1c33e3cec6dde2aec591af1135167adb4ffe6c7d",
    "certificatePem": "-----BEGIN CERTIFICATE-----\nMIIDWTCCAkGgAwIBAgIUEiTcjrReHLcZ4nm+K859BCkZ/zEwDQYJKoZIhvcNAQEL\nBQAwTTFLMEkGA1UECwxCQW1hem9uIFdlYiBTZXJ2aWNlcyBPPUFtYXpvbi5jb20g\nSW5jLiBMPVNlYXR0bGUgU1Q9V2FzaGluZ3RvbiBDPVVTMB4XDTE4MDExMDA0MTIz\nOVoXDTQ5MTIzMTIzNTk1OVowHjEcMBoGA1UEAwwTQVdTIElvVCBDZXJ0aWZpY2F0\nZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMEK4R5mlvgrITN+abhD\nI/cOphuZgxr4P93G+kDXFL8ryifcTgJ3osqxO7NQaFL78QcULFhJkxNH66mKn0c5\npiM9UiZtE3WtdlDyBgLhIx6eYBXdqDBnRswnPxWy47QFZHo8LpGegSx4cxk3PElp\ndT0RFbfrApv/qAIowxK5Bbsq6WRFxA5T94kKqu83a4y4g2I1U+YLMX8VlgC5L4dm\niOT8bk934DiDubviyGNlxQA5N6/lr+xbEpRbdAERMmN6KGtjOq1Wd6WZbu3/pvtx\npRbJTkKNN1Qtm9dHrLwl84mtSuiBgIv+jUfwDLTqKYVJY/kOXNQ79RH1pNr57oga\n9xkCAwEAAaNgMF4wHwYDVR0jBBgwFoAUj1vzVoaz/YUh/R3FgBjbw9MwoN0wHQYD\nVR0OBBYEFIjsprCA08I0/5GnNmnyYT1IVV8QMAwGA1UdEwEB/wQCMAAwDgYDVR0P\nAQH/BAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQBk4MbnUOOIPiQs22L61zWNJIpG\nux3AnsRZ3PyC79KfffuJKhc4In65Ww/RcIbnA1WgB8dsz583xB2OzGHb7d+iylay\nrA6jTrmpNnP0RirHqAIYxpkfcpbQhchOlordCngHS4MF0jJz0SyVAux8KPeOUg34\ntZZf+OIBxJkat3js7AXFjOKQe3t1lk2U9tw0kiJMMk4IeynJFrN2jxB/k0SNjOsw\n0w+2rc+J0bM/mXR76npiillSLzInmmXfJMAZemYWcAobdPWPRA1JPTAZDF35QjnJ\nEMrHw+w1KCty2krv9hSjXbKmg44/YJU1N6vauQGanUjEJktQFrmwZWtmBJZq\n-----END CERTIFICATE-----\n",
    "keyPair": {
        "PublicKey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwQrhHmaW+CshM35puEMj\n9w6mG5mDGvg/3cb6QNcUvyvKJ9xOAneiyrE7s1BoUvvxBxQsWEmTE0frqYqfRzmm\nIz1SJm0Tda12UPIGAuEjHp5gFd2oMGdGzCc/FbLjtAVkejwukZ6BLHhzGTc8SWl1\nPREVt+sCm/+oAijDErkFuyrpZEXEDlP3iQqq7zdrjLiDYjVT5gsxfxWWALkvh2aI\n5PxuT3fgOIO5u+LIY2XFADk3r+Wv7FsSlFt0AREyY3ooa2M6rVZ3pZlu7f+m+3Gl\nFslOQo03VC2b10esvCXzia1K6IGAi/6NR/AMtOophUlj+Q5c1Dv1EfWk2vnuiBr3\nGQIDAQAB\n-----END PUBLIC KEY-----\n",
        "PrivateKey": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAwQrhHmaW+CshM35puEMj9w6mG5mDGvg/3cb6QNcUvyvKJ9xO\nAneiyrE7s1BoUvvxBxQsWEmTE0frqYqfRzmmIz1SJm0Tda12UPIGAuEjHp5gFd2o\nMGdGzCc/FbLjtAVkejwukZ6BLHhzGTc8SWl1PREVt+sCm/+oAijDErkFuyrpZEXE\nDlP3iQqq7zdrjLiDYjVT5gsxfxWWALkvh2aI5PxuT3fgOIO5u+LIY2XFADk3r+Wv\n7FsSlFt0AREyY3ooa2M6rVZ3pZlu7f+m+3GlFslOQo03VC2b10esvCXzia1K6IGA\ni/6NR/AMtOophUlj+Q5c1Dv1EfWk2vnuiBr3GQIDAQABAoIBAEbm/w5ScerOtJAc\nQypJhsEsYThL5wqV2adUeQAtv1ID/Gktkn13gZRfCmVvCBJKtRl7gFohE+MGDHmm\nD6ByfSH+WNkCQR58yrMqYajXFjYdx37gffDhTfCYDaSjotyxClmXFyenBxzVVLkT\nP5JbKJN4XfjCWaAAg63fWN7clE1M7gtHwtEXf+xQ/t6FPbtOq+3po+8nTPR0d2FD\nEHiz8g8abxM4HLLZfx4GPDJsR7AQxKJD2lRPIben729ZS6xeqQgK2TMShQoCJunh\nVPP+hdwCCBvQtu6RhcFe/4/ocrPDsB1dPAm7u4TTTMk7r6dQshcuTblNQPnE92TR\ngnxYaXECgYEA+0Jdc9Zbsf+VFqjucJ+w8k1EfxZT0k8QtEznRRmcTBKuv5+oF6Yk\nJRnS7ELtS18Z32vxrsi0nOhMumHWazfgutY170EW7H596wi+V5TZADEfaL5foMjZ\nmaQGDIGma6/VIL9CDMD/oF75LhqSp2dLlMmAOxw0JYQGD5B16dtKs5UCgYEAxK9Q\nsmTN8X/guhZ9Qpnxa/Vu5xMAs03TN418aVoUGgMPhIhSNumUeEYozsXM6CWRhFOl\nQUy6p9cylgXfcVDcjZ5+oU2O2V57oxPd2fwRqeaRnXmeg+38cg1CZyk3QgoJ+zTF\n0C5qh51JQQPxwzGm9/OqB2Pquy1Y+e8ufJliVHUCgYBjkaodBH5z7Fe1kh5jbTUe\n4DXbswpmlkSFXtBrVrnUf7bWYzumm4VJWpF2ZRNKQharrkgpPoosf/YgCjOBa7RX\n9hmLhZzC/WGC6YUcifTwmYbb6E1XFyD8PL7U5+/+TsDD6GcRTM5ATEKs3YTuaAXQ\noYV6ZzPXBhmsw0+m6+sPfQKBgQDCE6wxG78Lef+qH97iBT1wJfKVGO8r/rNYscf9\nvODw+ewp/soBXWMfeztxLUUQHWIFjPQYBzp3u6Uy3ACrs/qt06NoTzuRyeV9+XCE\nVHKpj9ZH6WY9EGx1rhfD66uXAoju1BgNYH/F6bIK8XVyAmCbclhoinNo10pg9V6N\nnFymsQKBgA92YZ5vfWbnwvHDDNz/6pAVd9abowxaMZjblXrajfXkichqc52ySvhM\nRU2HqRicZFiY6r/SdB4j6i8wTMR9EdLvPNskl2ERTTmRiF6WLlwI3Y5jJbA36Zym\nNGxiakEZj9bx6sH+TPAE5KEvMfSi1wPopxHvn0yGxNpsWDwuKRm+\n-----END RSA PRIVATE KEY-----\n"
    },
    "certificateId": "d03e8b1c52bdf612a2d6bf4b1c33e3cec6dde2aec591af1135167adb4ffe6c7d"
}
  ```
  AWS IoT ルート証明書を取得する
  ```
  curl https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem -o root.pem
  ```
  作成された証明書ファイルを確認する。
  ```
  $ ls
  cert.pem	private.key	public.key	root.pem
  ```
  - デバイスポリシーを作成

  ポリシーファイルを用意する。(policy.json)
  ```
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe"
        ],
        "Resource": "*"
      }
    ]
  }
  ```
  ポリシーを作成する
  ```
  $ aws iot create-policy --policy-name RaspberryPolicy --policy-document file://policy.json
{
    "policyName": "RaspberryPolicy",
    "policyArn": "arn:aws:iot:ap-northeast-1:011960800664:policy/RaspberryPolicy",
    "policyDocument": "{\n  \"Version\": \"2012-10-17\",\n  \"Statement\": [\n    {\n      \"Effect\": \"Allow\",\n      \"Action\": [\n        \"iot:Connect\", \n        \"iot:Publish\", \n        \"iot:Subscribe\"\n      ],\n      \"Resource\": \"*\"\n    }\n  ]\n}\n\n",
    "policyVersionId": "1"
}
  ```
  - デバイスとポリシーを証明書へアタッチする
  ```
  # ポリシーをアタッチする
  $ aws iot attach-policy --policy-name RaspberryPolicy --target "arn:aws:iot:ap-northeast-1:011960800664:cert/d03e8b1c52bdf612a2d6bf4b1c33e3cec6dde2aec591af1135167adb4ffe6c7d"

  # デバイスをアタッチする
  $ aws iot attach-thing-principal --thing-name raspberry01 --principal "arn:aws:iot:ap-northeast-1:011960800664:cert/d03e8b1c52bdf612a2d6bf4b1c33e3cec6dde2aec591af1135167adb4ffe6c7d"
  ```

## RaspberryPiからの送信、及びサーバ側の受信を確認する
  - 作成された証明書をRaspberryPiへ転送

  ```
  $ scp cert.pem private.key root.pem pi@192.168.145.193:/home/pi/iotClient/
  ```

  - RaspberryPiにAWSIoTPythonSDKをインストールする

  ```
  pi $ pip install AWSIoTPythonSDK
  ```

  - AWSIoTPythonSDKのサンプルを基づいた温度データ送信プログラムを起動して送信する。

  ```
  pi $ python sendTemp.py
  ```
  正常の場合、一秒ごと温度を取得し、AWS IoTへ送信する。送信する際に、下記メッセージが出力される。

  ```
  Published topic /thermometer/thermometer01: {"temperature": 25.875}
  ```

  - AWS IoTでの受信確認
  
    AWSコンソールを開いて、「サービス」→「AWS IoT」→「テスト」を選択し、サブスクリプションのテスト画面を開く。
    トピックは`/thermometer/thermometer01`で送信されるため、「トピックのサブスクリプション」に`/thermometer/thermometer01`を入力して、「トピックへのサブスクライブ」をクリックする。
    ![トピックへサブスクライブする](imgs/Shot006.png)
    受信したメッセージが画面に表示される。
    ![サブスクリプション](imgs/Shot007.png)
