#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2024 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/ClipnGPT
# Thank you for keeping the rules.
# ------------------------------------------------

import sys
import os
import time
import datetime
import codecs
import glob

import json
import base64
import pyaudio

import asyncio
import threading
import queue
import traceback

from google import genai

from pynput import keyboard
#from pynput.keyboard import Controller

# クリップボード画像処理
from PIL import Image, ImageGrab
import io

# Monjyu連携
import requests

# グラフ表示
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')



# インターフェース
config_path  = '_config/'
config_file1 = 'RiKi_Monjyu_key.json'
config_file2 = 'RiKi_ClipnGPT_key.json'

# モデル設定 (freeai)
MODEL = "models/gemini-2.0-flash-exp"

# 音声ストリーム 設定
INPUT_CHUNK = 2000 #512
INPUT_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
OUTPUT_CHUNK = 2000 #512
OUTPUT_RATE = 24000

# 定数の定義
CORE_PORT = '8000'
CONNECTION_TIMEOUT = 15
REQUEST_TIMEOUT = 30



class _key2Action:

    def __init__(self, runMode='assistant', ):
        self.runMode = runMode

        # APIキーを取得
        if (os.path.isfile(config_path + config_file1)):
            with codecs.open(config_path + config_file1, 'r', 'utf-8') as f:
                self.config_dic = json.load(f)
        if (os.path.isfile(config_path + config_file2)):
            with codecs.open(config_path + config_file2, 'r', 'utf-8') as f:
                self.config_dic = json.load(f)
        elif (os.path.isfile('../../' + config_path + config_file1)):
            with codecs.open('../../' + config_path + config_file1, 'r', 'utf-8') as f:
                self.config_dic = json.load(f)
        elif (os.path.isfile('../../' + config_path + config_file2)):
            with codecs.open('../../' + config_path + config_file2, 'r', 'utf-8') as f:
                self.config_dic = json.load(f)
        self.freeai_key_id = self.config_dic['freeai_key_id']

        # liveAPI クラス
        self.liveAPI = _live_api_freeai(api_key=self.freeai_key_id, model=MODEL, )

        # キーボード監視 開始
        self.start_kb_listener()

    # キーボード監視 開始
    def start_kb_listener(self):
        self.last_ctrl_l_time  = 0
        self.last_ctrl_l_count = 0
        self.kb_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.kb_listener.start()

    # キーボード監視 終了
    def stop_kb_listener(self):
        if self.kb_listener:
            self.kb_listener.stop()

    # キーボードイベント
    def on_press(self, key):
        if (key == keyboard.Key.ctrl_l):
            pass
        else:
            self.last_ctrl_l_time  = 0
            self.last_ctrl_l_count = 0

    def on_release(self, key):

        # --------------------
        # ctrl_l キー
        # --------------------
        if (key == keyboard.Key.ctrl_l):
            press_time = time.time()
            if ((press_time - self.last_ctrl_l_time) > 1):
                self.last_ctrl_l_time  = press_time
                self.last_ctrl_l_count = 1
            else:
                self.last_ctrl_l_count += 1
                if (self.last_ctrl_l_count < 3):
                    self.last_ctrl_l_time = press_time
                else:
                    self.last_ctrl_l_time  = 0
                    self.last_ctrl_l_count = 0
                    #print("Press ctrl_l x 3 !")

                    # キー操作監視 停止
                    self.stop_kb_listener()

                    # live API クラス
                    if self.liveAPI.session is None:
                        self.liveAPI.start()
                    else:
                        self.liveAPI.stop()

                    #keycontrol = Controller()
                    #keycontrol.press(keyboard.Key.ctrl)
                    #keycontrol.release(keyboard.Key.ctrl)

                    # キー操作監視 再開
                    self.start_kb_listener()

        else:
            self.last_ctrl_l_time  = 0
            self.last_ctrl_l_count = 0



class _live_api_freeai:
    def __init__(self, api_key, model):

        # API情報
        self.client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1alpha'})

        # 設定
        self.image_send_queue = None
        self.audio_send_queue = None
        self.audio_receive_queue = None
        self.graph_input_queue = None
        self.graph_output_queue = None
        self.break_flag = False
        self.session = None
        self.once_debug_flag = False

        # タスク設定
        self.tasks = []
        self.tg = None

        # botFunc
        self.botFunc = None

    async def input_audio(self):
        delay_count = int( (INPUT_RATE/INPUT_CHUNK) * 2)
        input_stream = None
        try:

            # ストリーム設定
            audio_stream = pyaudio.PyAudio()
            mic_info = audio_stream.get_default_input_device_info()
            input_stream = await asyncio.to_thread(
                audio_stream.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=INPUT_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=INPUT_CHUNK,
            )

            # マイク入力
            last_zero_count = 0
            while (self.session is not None) and (not self.break_flag):
                audio_data = await asyncio.to_thread(input_stream.read, INPUT_CHUNK)
                if audio_data is not None:
                    input_data = np.abs(np.frombuffer(audio_data, dtype=np.int16))
                    max_val = np.max(input_data)
                    if max_val > 1000:
                        self.audio_send_queue.put_nowait(audio_data)
                        self.graph_input_queue.put_nowait(audio_data)
                        last_zero_count = 0
                    else:
                        if last_zero_count <= delay_count:
                            last_zero_count += 1
                            self.audio_send_queue.put_nowait(audio_data)
                        self.graph_input_queue.put_nowait(bytes(INPUT_CHUNK))
                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"input_audio: {e}")
        finally:
            self.break_flag = True
            # ストリーム解放
            if input_stream:
                input_stream.stop_stream()
                input_stream.close()
                audio_stream.terminate()
        return True

    async def send_audio(self):
        try:

            # 音声送信
            while (self.session is not None) and (not self.break_flag):
                audio_data = await self.audio_send_queue.get()
                if audio_data is not None:
                    await self.session.send({"mime_type": "audio/pcm", "data": audio_data})
                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"send_audio: {e}")
        finally:
            self.break_flag = True
        return True

    async def input_image(self):
        last_image = None
        try:
            last_image = ImageGrab.grabclipboard()
        except:
            pass
        try:

            # イメージ確認
            while (self.session is not None) and (not self.break_flag):
                try:
                    new_image = ImageGrab.grabclipboard()
                    if isinstance(new_image, Image.Image):
                        if (new_image != last_image):
                            print(" Live(freeai) : NEW IMAGE")
                            last_image = new_image

                            # jpeg変換
                            jpeg_io = io.BytesIO()
                            rgb = new_image.convert("RGB")
                            rgb.thumbnail([1024, 1024])
                            #rgb.save("debug.jpg")
                            rgb.save(jpeg_io, format="jpeg")
                            jpeg_io.seek(0)
                            jpeg_bytes = jpeg_io.read()

                            self.image_send_queue.put_nowait(jpeg_bytes)
                except:
                    pass
                await asyncio.sleep(0.50)

        except Exception as e:
            print(f"input_image: {e}")
        finally:
            self.break_flag = True
        return True

    async def send_image(self):
        try:

            # イメージ送信
            while (self.session is not None) and (not self.break_flag):
                jpeg_bytes = await self.image_send_queue.get()
                if jpeg_bytes is not None:
                    print(" Live(freeai) : IMAGE SENDING")
                    await self.session.send({"mime_type": "image/jpeg", "data": base64.b64encode(jpeg_bytes).decode()})
                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"send_image: {e}")
        finally:
            self.break_flag = True
        return True

    async def play_audio(self):
        output_stream = None
        try:

            # ストリーム設定
            audio_stream = pyaudio.PyAudio()
            output_stream = await asyncio.to_thread(
                audio_stream.open, 
                format=FORMAT, 
                channels=CHANNELS, 
                rate=OUTPUT_RATE, 
                output=True,
            )

            # 音声再生
            while (self.session is not None) and (not self.break_flag):
                audio_data = await self.audio_receive_queue.get()
                if audio_data is not None:
                    await asyncio.to_thread(output_stream.write, audio_data)
                    self.graph_output_queue.put_nowait(audio_data)
                else:
                     await asyncio.sleep(0.01)

        except Exception as e:
            print(f"play_audio: {e}")
        finally:
            self.break_flag = True
            # ストリーム解放
            if output_stream:
                output_stream.stop_stream()
                output_stream.close()
                audio_stream.terminate()
        return True

    def send_request(self, request_text='',):
        return asyncio.run(self.send_request_async(request_text))

    async def send_request_async(self, request_text='',):
        try:
            if (request_text is not None) and (request_text != ''):
                print(f" User(text): { request_text }")
                if (self.session is not None) and (not self.break_flag):

                    # テキスト送信
                    await self.session.send(request_text or ".", end_of_turn=True)

        except Exception as e:
            print(f"send_request: {e}")
            return False
        return True

    async def receive_proc(self):
        try:
            while (self.session is not None) and (not self.break_flag):
                async for response in self.session.receive():
                    server_content = response.server_content
                    if server_content is None:
                        print('response ???')
                        print(response)

                    else:
                        model_turn = server_content.model_turn
                        turn_complete = server_content.turn_complete

                        # model_turn
                        if model_turn is not None:
                            parts = model_turn.parts
                            for part in parts:
                                if part.text is not None:
                                    print(part.text, end="")
                                elif part.inline_data is not None:
                                    self.audio_receive_queue.put_nowait(part.inline_data.data)
                                else:
                                    print('server_content.model_turn.parts [ ??? ]')
                                    print(part)

                        # turn_cmplete = True
                        if turn_complete:
                            print('server_content.turn_complete = True ')
                            while not self.audio_receive_queue.empty():
                                await self.audio_receive_queue.get()

                        if  model_turn is None \
                        and not turn_complete:
                            print('server_content.??? ')
                            print(server_content)

        except Exception as e:
            print(f"receive_proc: {e}")
        finally:
            self.break_flag = True
        return True

    def start(self):
        print(" Live(freeai) : START")
        # 初期化
        self.break_flag = False
        self.image_send_queue = asyncio.Queue()
        self.audio_send_queue = asyncio.Queue()
        self.audio_receive_queue = asyncio.Queue()
        self.graph_input_queue = asyncio.Queue()
        self.graph_output_queue = asyncio.Queue()
        # スレッド処理
        def main_thread():
            # visualizer開始
            self.visualizer = _visualizer_class()
            self.visualizer.api_instance = self  # 自身への参照を追加
            asyncio.run(self._main())
            # visualizer停止
            self.visualizer.root.quit()
            self.visualizer.root.destroy()
        # 起動
        self.main_task = threading.Thread(target=main_thread, daemon=True)
        self.main_task.start()
        return True

    def stop(self):
        print(" Live(freeai) : STOP")
        # 停止
        self.break_flag = True
        if self.tg: # TaskGroupが初期化されているか確認
            for task in self.tasks:
                try:
                    task.cancel()
                except:
                    pass
            self.tg = None  # TaskGroupをNoneに設定
        self.main_task.join()
        return True
    
    async def _main(self):
        try:
            # 起動
            if (self.session is None):

                # Monjyu実行が可能か確認
                ext_monjyu = False
                instructions = \
"""
あなたは美しい日本語を話す賢いアシスタントです。
あなたはLiveAPI(RealtimeAPI)で実行中のアシスタントです。
"""
                if self.botFunc is not None:
                    for module_dic in self.botFunc.function_modules:
                        if (module_dic['func_name'] == 'execute_monjyu_request'):
                            ext_monjyu = True
                            instructions = \
"""
あなたは美しい日本語を話す賢いアシスタントです。
あなたはLiveAPI(RealtimeAPI)で実行中のアシスタントです。
あなたはリアルタイム会話を中心に実行してください。
あなた自身で回答できない場合は、外部AI(execute_monjyu_request)を呼び出すことで、
適切なFunctions(Tools)も間接的に利用して、その結果で回答してしてください。
"""
                            print(" Live(freeai) : 外部AI(execute_monjyu_request) READY")
                            break

                # ツール設定 通常はexecute_monjyu_requestのみ有効として処理
                tools = []
                tools.append({"code_execution": {}, })
                tools.append({"google_search": {}, })
                if self.botFunc is not None:
                    for module_dic in self.botFunc.function_modules:
                        func_dic = module_dic['function']
                        func_str = json.dumps(func_dic, ensure_ascii=False, )
                        func_str = func_str.replace('"type"', '"type_"')
                        func_str = func_str.replace('"object"', '"OBJECT"')
                        func_str = func_str.replace('"string"', '"STRING"')
                        func     = json.loads(func_str)
                        if (ext_monjyu):
                            if (module_dic['func_name'] == 'execute_monjyu_request'):
                                tools.append(func)
                        else:
                                tools.append(func)

                # config 設定
                speech_config = {"voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}}
                voice_config = {"prebuilt_voice_config": {"voice_name": "Aoede"}}
                #                    "speech_config": speech_config,
                #                    "voice_config": voice_config,
                config =    {"generation_config": {
                                "response_modalities": ["AUDIO"],
                                },
                            "system_instruction": instructions,
                            "tools": tools,
                            }

                # Live 実行
                #session = await self.client.aio.live.connect(model=MODEL, config=config)
                #tg = asyncio.TaskGroup()
                async with (
                    self.client.aio.live.connect(model=MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):

                    self.session = session 
                    self.tg = tg

                    def cleanup(task):
                        for t in self.tg._tasks:
                            t.cancel()

                    self.tasks = []
                    self.tasks.append(self.tg.create_task(self.input_image()))
                    self.tasks.append(self.tg.create_task(self.send_image()))
                    self.tasks.append(self.tg.create_task(self.input_audio()))
                    self.tasks.append(self.tg.create_task(self.send_audio()))
                    self.tasks.append(self.tg.create_task(self.play_audio()))
                    self.tasks.append(self.tg.create_task(self.receive_proc()))
                    self.tasks.append(self.tg.create_task(self.visualizer_update()))
                    
                    def check_error(task):
                        if task.cancelled():
                            return
                        if task.exception() is None:
                            return
                        e = task.exception()
                        traceback.print_exception(None, e, e.__traceback__)
                        #sys.exit(1)

                    for task in self.tg._tasks:
                        task.add_done_callback(check_error)

                    # 待機
                    print(" Live(freeai) : RUN (WAIT)")
                    #while (not self.break_flag):
                    #    await asyncio.sleep(0.1)
                    #sys.exit(1)

        except Exception as e:
            print(f"_main: {e}")
        finally:
            self.break_flag = True
            self.session = None

        print(" Live(freeai) : END")
        return True

    async def visualizer_update(self):
        try:

            # グラフ更新
            while (self.session is not None) and (not self.break_flag):
                if not self.graph_input_queue.empty():
                    input_data = await self.graph_input_queue.get()
                    self.visualizer.update_value(input_chunk=input_data)
                else:
                    self.visualizer.update_value(input_chunk=bytes(INPUT_CHUNK))
                    
                if not self.graph_output_queue.empty():
                    output_data = await self.graph_output_queue.get()
                    self.visualizer.update_value(output_chunk=output_data)
                else:
                    self.visualizer.update_value(output_chunk=bytes(OUTPUT_CHUNK))

                self.visualizer.update_graph()
                await asyncio.sleep(0.01)

        except Exception as e:
            print(f"visualizer_update: {e}")
        finally:
            self.break_flag = True
        return True



class _visualizer_class:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Visualizer")
        
        # ウィンドウクローズイベントのハンドラを追加
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # グラフ用のフレーム作成
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky="nsew")
                
        # グラフの初期化を直接実行
        self.initialize_plot()
        
    def initialize_plot(self):
        # Matplotlibのfigure作成（サイズを512x512に修正）
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5.12, 5.12), gridspec_kw={'hspace': 0.3})
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # グラフの初期設定
        self.ax1.set_title('Input Audio')
        self.ax2.set_title('Output Audio')
        
        # 背景を黒に設定
        self.fig.patch.set_facecolor('black')
        self.ax1.set_facecolor('black')
        self.ax2.set_facecolor('black')
        
        # グリッド線と軸の色を設定
        self.ax1.grid(True, color='gray')
        self.ax2.grid(True, color='gray')
        self.ax1.tick_params(colors='white')
        self.ax2.tick_params(colors='white')
        for spine in self.ax1.spines.values():
            spine.set_color('white')
        for spine in self.ax2.spines.values():
            spine.set_color('white')
        
        # タイトルの色を白に
        self.ax1.set_title('Input Audio', color='white')
        self.ax2.set_title('Output Audio', color='white')
        
        # 入力を赤、出力を青の棒グラフに設定
        self.line1, = self.ax1.plot([], [], 'r', drawstyle='steps-pre')  # 赤色
        self.line2, = self.ax2.plot([], [], 'b', drawstyle='steps-pre')  # 青色
        
        # Y軸の範囲設定（絶対値を100分率表示）
        self.ax1.set_ylim(0, 100)
        self.ax2.set_ylim(0, 100)
        
        # Y軸のラベルを追加
        self.ax1.set_ylabel('Level (%)', color='white')
        self.ax2.set_ylabel('Level (%)', color='white')
        
        # データバッファ
        self.input_data = []
        self.output_data = []

    def on_closing(self):
        if hasattr(self, 'api_instance'):
            self.api_instance.break_flag = True
            
    def update_value(self, input_chunk=None, output_chunk=None):
        # 入力波形
        if input_chunk is not None:
            # 入力データの更新（絶対値に変換）
            input_data = np.abs(np.frombuffer(input_chunk, dtype=np.int16))
            # 最大値に対する100分率に変換
            max_val = np.max(input_data)
            if max_val > 0:  # ゼロ除算を防ぐ
                input_data = (input_data / max_val) * 100
            self.input_data = input_data
            self.line1.set_data(range(len(input_data)), input_data)
            self.ax1.set_xlim(0, len(input_data))
        # 出力波形
        if output_chunk is not None:
            # 出力データの更新（絶対値に変換）
            output_data = np.abs(np.frombuffer(output_chunk, dtype=np.int16))
            # 最大値に対する100分率に変換
            max_val = np.max(output_data)
            if max_val > 0:  # ゼロ除算を防ぐ
                output_data = (output_data / max_val) * 100
            self.output_data = output_data
            self.line2.set_data(range(len(output_data)), output_data)
            self.ax2.set_xlim(0, len(output_data))
        # グラフ更新
        #self.update_graph()

    def update_graph(self):
        try:
            self.canvas.draw()
            self.root.update()
        except:
            pass



class _class:

    def __init__(self, ):
        self.version   = "v0"
        self.func_name = "extension_UI_key2Live_freeai"
        self.func_ver  = "v0.20241215"
        self.func_auth = "h0MmuBSfyHFVSPQ+uqVSZLedZDYu9tr2O6EXUhHJ+hwDwrMGiDGqDTlC4v4DSj2G"
        self.function  = {
            "name": self.func_name,
            "description": "拡張ＵＩ_キー(ctrl)連打で、LiveAPI(RealTimeAPI)を起動または停止する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "runMode": {
                        "type": "string",
                        "description": "実行モード 例) assistant"
                    },
                    "reqText": {
                        "type": "string",
                        "description": "要求文字列 例) おはようございます"
                    },
                },
                "required": ["runMode"]
            }
        }

        # 設定
        self.runMode = 'assistant'

        # キーボード監視 開始
        self.sub_proc = _key2Action(runMode=self.runMode, )

        # 初期化
        self.func_reset()

    def func_reset(self, botFunc=None, ):
        if botFunc is not None:
            self.sub_proc.liveAPI.botFunc = botFunc
        return True

    def func_proc(self, json_kwargs=None, ):
        #print(json_kwargs)

        # 引数
        runMode = None
        reqText = None
        if (json_kwargs is not None):
            args_dic = json.loads(json_kwargs)
            runMode = args_dic.get('runMode')
            reqText = args_dic.get('reqText')

        if (runMode is None) or (runMode == ''):
            runMode = self.runMode
        else:
            self.runMode = runMode

        # 処理
        if (reqText != ''):
            if self.sub_proc.liveAPI.session is None:
                self.sub_proc.liveAPI.start()
                time.sleep(5.00)
            self.sub_proc.liveAPI.send_request(request_text=reqText, )

        # 戻り
        dic = {}
        dic['result'] = "ok"
        json_dump = json.dumps(dic, ensure_ascii=False, )
        #print('  --> ', json_dump)
        return json_dump

if __name__ == '__main__':

    ext = _class()
    api_key = ext.sub_proc.freeai_key_id

    #liveAPI = _live_api_freeai(api_key, MODEL)
    #liveAPI.start()
    #time.sleep(5)
    #liveAPI.send_request(request_text='日本語で話してください')
    #time.sleep(30)
    #liveAPI.stop()
    #time.sleep(5)
    #liveAPI.start()
    #time.sleep(10)
    #liveAPI.stop()


    #ext = _class()
    print(ext.func_proc('{ "runMode" : "assistant", "reqText" : "" }'))

    time.sleep(2)

    print(ext.func_proc('{ "runMode" : "assistant", "reqText" : "おはようございます" }'))

    time.sleep(60)


