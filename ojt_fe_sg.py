#! /usr/bin/python3

import PySimpleGUI as sg
import glob, os, tempfile, subprocess

# Open JTalk 本体
ojt_command = "/usr/bin/open_jtalk"

# 音響モデルの置き場所
voice_dir = "/usr/share/hts-voice/"

# 辞書
dic_dir = "/var/lib/mecab/dic/open-jtalk/naist-jdic"

# 音声ファイルを再生するためのコマンド
play_command = ["/usr/bin/aplay", "-q"]

# -----------------------------------

TITLE = "OpenJTalk FrontEnd-SG"

CAPTION = 0	# キャプション
MIN_VAL = 1	# 最小値
MAX_VAL = 2	# 最大値
DEF_VAL = 3	# 初期値
RES_VAL = 4	# 変化量
PARAM   = 5	# OpenJTalkのパラメータ
KEY     = 6	# コントロールを特定するためのキー
param_info = [
    ("α ",      0.0,  1.0, 0.5, 0.01, "-a",  "-ALPHA-"),
    ("β  ",     0.0,  1.0, 0.0, 0.01, "-b",  "-BETA-"),
    ("速度 ",    0.0,  2.0, 1.0, 0.01, "-r",  "-SPEED-"),
    ("ﾊｰﾌﾄｰﾝ", -10.0, 10.0, 0.0, 0.1,  "-fm", "-HALFTONE-"),
    ("境界  ",   0.0,  1.0, 0.5, 0.01, "-u",  "-MSD-"),
    ("GV0   ",   0.0,  5.0, 1.0, 0.01, "-jm", "-GV0-"),
    ("GV1    ",  0.0,  5.0, 1.0, 0.01, "-jf", "-GV1-"),
    ("音量    ", 0.0, 20.0, 1.0, 0.1,  "-g",  "-VOLUME-"),
]
# キャプションの末尾のスペースで、スライダーとの位置合わせ。
# 環境によってはズレるかも。


def splitMessage(value):
    return [n.strip() for n in value.splitlines() if n.strip()]

def makeOJTCommand(values, output_file_path):
    cmd = [ojt_command,
           "-x", dic_dir,
           "-m", os.path.join(voice_dir, values["-MODEL-"]),
           "-ow", output_file_path]

    for n in param_info:
        auto_key = "-AUTO" + n[KEY]
        if auto_key in values and values[auto_key]:
            continue
        cmd.append(n[PARAM])
        cmd.append(str(values[n[KEY]]))

    return cmd

voice = [
    os.path.relpath(f, voice_dir)
    for f
    in glob.iglob(os.path.join(voice_dir, "**/*.htsvoice"), recursive=True)
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
     sg.InputText('voice', size=(6,1),key="-PREFIX-")
    ]
]

window = sg.Window(TITLE, layout)

while True:
    event, values = window.read()

    if event is None:
        break

    if event == "再生":
        mes = splitMessage(values["-MES-"])

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            cmd = makeOJTCommand(values, path)

            for m in mes:
                c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                c.stdin.write(m.encode('utf-8'))
                c.stdin.close()
                c.wait()

                c = subprocess.Popen(play_command + [path])
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
                cmd = makeOJTCommand(values, output_path)
                
                c = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                c.stdin.write(m.encode('utf-8'))
                c.stdin.close()
                c.wait()
            sg.popup("完了")
        

window.close()
