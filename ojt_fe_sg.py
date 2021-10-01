#! /usr/bin/python3
#-*- coding: utf-8 -*-

import PySimpleGUI as sg
import glob, os, tempfile, subprocess, json
import configparser

# -----------------------------------
# 各種設定


# Open JTalk 本体
OJT_COMMAND = "/usr/bin/open_jtalk"

# 音響モデルの置き場所
VOICE_DIR = "/usr/share/hts-voice/"

# 辞書
DIC_DIR = "/var/lib/mecab/dic/open-jtalk/naist-jdic"

# Open JTalk が音声再生をサポートしているか
SUPPORT_PLAY = False

# 音声再生用のバッファサイズ （SUPPORT_PLAY = True 時に使用）
AUDIO_BUFFER_SIZE = 4096

# 音声ファイルを再生するためのコマンド （SUPPORT_PLAY = False 時に使用）
PLAY_COMMAND = ["/usr/bin/aplay", "-q"]

# ユーザ設定ファイルの保存場所
USER_CONF_DIR = ["./", f"{os.environ.get('HOME')}/.config/"]

# -----------------------------------
# ウインドウタイトル
TITLE = "OpenJTalk FrontEnd-SG"

# param_infoの各キーの意味
CAPTION = 0	# キャプション
MIN_VAL = 1	# 最小値
MAX_VAL = 2	# 最大値
DEF_VAL = 3	# 初期値
RES_VAL = 4	# 変化量
PARAM   = 5	# OpenJTalkのパラメータ
KEY     = 6	# コントロールを特定するためのキー

DEFAULT_PARAM_DICT = {
    "ALPHA" : 0.5,
    "BETA" : 0.0,
    "SPEED" : 1.0,
    "HALFTONE" : 0.0,
    "MSD" : 0.5,
    "GV0" : 1.0,
    "GV1" : 1.0,
    "VOLUME" : 1.0
}

# ユーザコンフィグ読み込み
user_conf = configparser.ConfigParser()

for index, user_conf_dir in enumerate(USER_CONF_DIR):
    if os.path.exists(os.path.abspath(os.path.join(user_conf_dir, "user_settings.ini"))):
        user_conf_path = os.path.abspath(os.path.join(user_conf_dir, "user_settings.ini"))
        user_conf.read(user_conf_path)
        param_dict = json.loads(user_conf["User"]["param"])
        break
    else:
        if index + 1 >= len(USER_CONF_DIR):
            # デフォルトのパラメータを読み込み
            param_dict = DEFAULT_PARAM_DICT.copy()
            break

# パラメータのフォーマット
param_info = [
    ("α ",      0.0,  1.0, param_dict["ALPHA"], 0.01, "-a",  "-ALPHA-"),
    ("β  ",     0.0,  1.0, param_dict["BETA"], 0.01, "-b",  "-BETA-"),
    ("速度 ",    0.0,  2.0, param_dict["SPEED"], 0.01, "-r",  "-SPEED-"),
    ("ﾊｰﾌﾄｰﾝ", -10.0, 10.0, param_dict["HALFTONE"], 0.1,  "-fm", "-HALFTONE-"),
    ("境界  ",   0.0,  1.0, param_dict["MSD"], 0.01, "-u",  "-MSD-"),
    ("GV0   ",   0.0,  5.0, param_dict["GV0"], 0.01, "-jm", "-GV0-"),
    ("GV1    ",  0.0,  5.0, param_dict["GV1"], 0.01, "-jf", "-GV1-"),
    ("音量    ", 0.0, 20.0, param_dict["VOLUME"], 0.1,  "-g",  "-VOLUME-"),
]

def splitMessage(value):
    return [n.strip() for n in value.splitlines() if n.strip()]

def makeOJTCommand(values, output_file_path, audio_buffer):
    cmd = [OJT_COMMAND,
           "-x", DIC_DIR,
           "-m", os.path.join(VOICE_DIR, values["-MODEL-"])]

    if output_file_path is not None:
        cmd = cmd + ["-ow", output_file_path]
    if audio_buffer is not None:
        cmd = cmd + ["-z", str(audio_buffer)]

    for n in param_info:
        auto_key = "-AUTO" + n[KEY]
        if auto_key in values and values[auto_key]:
            continue
        cmd.append(n[PARAM])
        cmd.append(str(values[n[KEY]]))

    return cmd

def saveParametersAsMySettings(values, user_conf):
    '''設定値をユーザ設定として、保存する関数

    Args:
        values (Object) : 設定された設定値
        user_conf (Object) : 読み込まれたユーザ設定情報
    
    Returns:
        (bool)
    '''
    user_param_candidate = DEFAULT_PARAM_DICT.copy()

    for index, val in values.items():
        if index.strip("-") in user_param_candidate:
            user_param_candidate[index.strip("-")] = val
        else:
            pass

    dialog = sg.popup_yes_no('設定値を保存しますか？')
    if dialog == "Yes":
        user_conf["User"]["param"] = json.dumps(user_param_candidate)
        with open(user_conf_path, "w") as conf_file:
            user_conf.write(conf_file)
        sg.popup_ok("保存しました")

    elif dialog == "No":
        sg.popup_ok("キャンセルしました")
    
    else: 
        raise Exception
    
    return True

def setDefaultValueOntoSlider(window):
    '''リセットボタン押下時に実行される関数

    Args:
        window (Object) : ウインドウを構成するオブジェクト
    
    Returns:
        (bool)
    '''
    for param in param_info:
        window[param[KEY]].Update(param[DEF_VAL])
    
    return True

voice = [
    os.path.relpath(f, VOICE_DIR)
    for f
    in glob.iglob(os.path.join(VOICE_DIR, "**/*.htsvoice"), recursive=True)
]

if not voice:
    sg.Popup("音響モデルファイルが無い。", title=TITLE)
    exit()

frame_layout = [
    [sg.Text("音響モデル"), sg.Combo(voice, default_value=voice[0], readonly=True, key="-MODEL-")],
    [sg.Text(n[CAPTION], size=(7, 1), justification="right") for n in param_info],
    [sg.Slider((n[MIN_VAL], n[MAX_VAL]),
               orientation="vertical",
               default_value=n[DEF_VAL],
               resolution=n[RES_VAL],
               key=n[KEY])
     for n in param_info],
    [sg.Checkbox("auto", default=True, key="-AUTO-ALPHA-")]
]

layout = [
    [sg.Multiline(size=(64,10), key="-MES-")],
    [sg.Frame("パラメータ", frame_layout)],
    [sg.Submit(button_text="再生"),
     sg.Submit(button_text="保存"),
     sg.InputText('voice', size=(6,1),key="-PREFIX-"),
     sg.Submit(button_text="設定保存"),
     sg.Submit(button_text="リセット")
    ]
]

window = sg.Window(TITLE, layout)

while True:
    event, values = window.read()

    if event is None:
        break

    if event == "再生":
        mes = splitMessage(values["-MES-"])

        if SUPPORT_PLAY:
            cmd = makeOJTCommand(values, None, AUDIO_BUFFER_SIZE)
            for m in mes:
                c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                c.stdin.write(m.encode('utf-8'))
                c.stdin.close()
                c.wait()
        else:
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            try:
                cmd = makeOJTCommand(values, path, None)

                for m in mes:
                    c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    c.stdin.write(m.encode('utf-8'))
                    c.stdin.close()
                    c.wait()

                    c = subprocess.Popen(PLAY_COMMAND + [path])
                    c.wait()
            
            finally:
                os.remove(path)
        
    elif event == "保存":
        save_dir = sg.PopupGetFolder("保存先", title=TITLE)
        if save_dir:

            prefix = values["-PREFIX-"]
            mes = splitMessage(values["-MES-"])
            no = 0
            for m in mes:

                output_path = os.path.join(save_dir,"{0}{1:03d}.wav".format(prefix, no))
                no += 1
                cmd = makeOJTCommand(values, output_path, None)
                
                c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                c.stdin.write(m.encode('utf-8'))
                c.stdin.close()
                c.wait()
            sg.popup("完了")
    
    elif event == "設定保存":
        saveParametersAsMySettings(values, user_conf)

    elif event == "リセット":
        setDefaultValueOntoSlider(window)

window.close()
