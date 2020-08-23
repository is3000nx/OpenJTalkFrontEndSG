Open JTalk Frontend SG
====

[Open JTalk](http://open-jtalk.sourceforge.net/) の GUIプログラムです。

Linuxでの使用を想定してますが、Python製なので、若干の修正で他の環境でも動作するはずです。

## 前準備

必要なものをインストールしておきます。

* [Open JTalk](http://open-jtalk.sourceforge.net/)
```
sudo apt install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001
```
* Python 3
```
sudo apt install python3
```
* PySimpleGUI
```
sudo apt install python3-tk
pip3 install pysimplegui
```

## インストール

1. ojt_fe_sg.py をダウンロードして、どこか適当な所に置く。
2. 上記ファイルをテキストエディタで開き、各フォルダを自分の環境に合わせて書き換える。
3. ojt_fe_sg.py を実行。

## 使い方

喋らせたい内容を入力し、  
適当にパラメータを調整し、  
「再生」ボタンで再生。「保存」ボタンでWAV形式で保存。


## 連絡先

https://twitter.com/is3000nx

In Japanese as possible, please.
