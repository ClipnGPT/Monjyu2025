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
import pygame

import threading
import queue

import websocket

from pynput import keyboard
#from pynput.keyboard import Controller

# クリップボード画像処理
from PIL import Image, ImageGrab, ImageTk, ImageEnhance
import io
import screeninfo
import pyautogui
import cv2
import hashlib

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

# モデル設定 (openai)
#MODEL = "gpt-4o-realtime-preview-2024-12-17"
MODEL = "gpt-4o-mini-realtime-preview-2024-12-17"
VOICE = "alloy"

# 音声ストリーム 設定
INPUT_CHUNK = 2048
INPUT_RATE = 24000
FORMAT = pyaudio.paInt16
CHANNELS = 1
OUTPUT_CHUNK = 2048
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
        self.openai_key_id = self.config_dic['openai_key_id']

        # liveAPI クラス
        self.liveAPI = _live_api_openai(api_key=self.openai_key_id, model=MODEL, )

        # liveAPI 監視
        self.liveAPI_rerun = 0
        self.liveAPI_task = threading.Thread(target=self.liveAPI_check, daemon=True)
        self.liveAPI_task.start()

        # キーボード監視 開始
        self.start_kb_listener()

    # liveAPI監視
    def liveAPI_check(self):
        while True:
            if (self.liveAPI_rerun > 0):
                if self.liveAPI.session is None:
                    if (self.liveAPI_rerun != 1):
                        time.sleep(2.00)
                    self.liveAPI.start()
                    chkTime = time.time()
                    while ((time.time() - chkTime) < 10) and (self.liveAPI.session is None):
                        time.sleep(1.00)
                    self.liveAPI_rerun += 1
            time.sleep(1.00)
            if (self.liveAPI.error_flag == True):
                self.liveAPI_rerun = 0

    # キーボード監視 開始
    def start_kb_listener(self):
        self.last_ctrl_r_time  = 0
        self.last_ctrl_r_count = 0
        self.kb_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.kb_listener.start()

    # キーボード監視 終了
    def stop_kb_listener(self):
        if self.kb_listener:
            self.kb_listener.stop()

    # キーボードイベント
    def on_press(self, key):
        if   (key == keyboard.Key.ctrl_r):
            pass
        else:
            self.last_ctrl_r_time  = 0
            self.last_ctrl_r_count = 0

    def on_release(self, key):

        # --------------------
        # ctrl_r キー
        # --------------------
        if (key == keyboard.Key.ctrl_r):
            press_time = time.time()
            if ((press_time - self.last_ctrl_r_time) > 1):
                self.last_ctrl_r_time  = press_time
                self.last_ctrl_r_count = 1
            else:
                self.last_ctrl_r_count += 1
                if (self.last_ctrl_r_count < 3):
                    self.last_ctrl_r_time = press_time
                else:
                    self.last_ctrl_r_time  = 0
                    self.last_ctrl_r_count = 0
                    #print("Press ctrl_r x 3 !")

                    # キー操作監視 停止
                    self.stop_kb_listener()

                    # live API クラス
                    if self.liveAPI.session is None:
                        #self.liveAPI.start()
                        self.liveAPI.break_flag = False
                        self.liveAPI.error_flag = False
                        self.liveAPI_rerun = 1
                    else:
                        self.liveAPI_rerun = 0
                        self.liveAPI.stop()

                    # キー操作監視 再開
                    self.start_kb_listener()

        # --------------------
        # end キー
        # --------------------
        elif (key == keyboard.Key.end):
            self.last_ctrl_l_time  = 0
            self.last_ctrl_l_count = 0

            # キー操作監視 停止
            self.stop_kb_listener()

            # live API クラス
            self.liveAPI_rerun = 0
            if self.liveAPI.session is not None:
                self.liveAPI.stop()

            # キー操作監視 再開
            self.start_kb_listener()

        # --------------------
        # print_screen キー
        # --------------------
        elif (key == keyboard.Key.print_screen):
            # live API クラス
            if self.liveAPI.session is not None:
                self.liveAPI.screen_shot_flag = True

        else:
            self.last_ctrl_r_time  = 0
            self.last_ctrl_r_count = 0



class _live_api_openai:
    def __init__(self, api_key, model, ):
        self.mixer_enable = False

        # API情報
        self.WS_URL = f"wss://api.openai.com/v1/realtime?model={ model }"
        self.HEADERS = {"Authorization": "Bearer " + api_key,
                        "OpenAI-Beta": "realtime=v1"}

        # 設定
        self.image_send_queue = queue.Queue()
        self.audio_send_queue = queue.Queue()
        self.audio_receive_queue = queue.Queue()
        self.graph_input_queue = queue.Queue()
        self.graph_output_queue = queue.Queue()
        self.break_flag = False
        self.error_flag = False
        self.last_send_time = time.time()
        self.session = None
        self.monjyu_once_flag = False
        self.monjyu_enable = False
        self.monjyu_funcinfo = ''
        self.screen_shot_flag = False

        # スクリーンショット設定
        self.SS = _screenShot_class()

        # botFunc
        self.botFunc = None

        # monjyu
        self.monjyu = _monjyu_class(runMode='assistant', )

    def play(self, outFile='temp/_work/sound.mp3', ):
        if (not os.path.exists(outFile)):
            return False
        # ミキサー開始、リセット
        if (self.mixer_enable == False):
            try:
                pygame.mixer.init()
                self.mixer_enable = True
            except Exception as e:
                print(e)
        # ミキサー再生
        if (self.mixer_enable == True):
            try:
                #print(outFile)
                #pygame.mixer.init()
                pygame.mixer.music.load(outFile)
                pygame.mixer.music.play(1)
                while (pygame.mixer.music.get_busy() == True):
                    time.sleep(0.10)
                pygame.mixer.music.unload()
                return True
            except Exception as e:
                print(e)
                self.mixer_enable = False
        return False

    def input_audio(self, input_stream, input_rate, input_chunk):
        delay_count = int( (input_rate/input_chunk) * 2)
        try:

            # マイク入力
            last_zero_count = 0
            while (self.session is not None) and (not self.break_flag):
                audio_data = input_stream.read(input_chunk, exception_on_overflow=False)
                if audio_data is not None:
                    input_data = np.abs(np.frombuffer(audio_data, dtype=np.int16))
                    max_val = np.max(input_data)
                    if max_val > 1000:
                        self.audio_send_queue.put(audio_data)
                        self.graph_input_queue.put(audio_data)
                        last_zero_count = 0
                    else:
                        #if ((time.time() - self.last_send_time) > 180): # ３分おきにゼロデータ送信
                        #    self.last_send_time = time.time()
                        #    last_zero_count = 0
                        if last_zero_count <= delay_count:
                            last_zero_count += 1
                            self.audio_send_queue.put(audio_data)
                        self.graph_input_queue.put(bytes(input_chunk * 2))
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(f"input_audio: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def send_audio(self):
        try:

            # 音声送信
            while (self.session is not None) and (not self.break_flag):
                audio_data = self.audio_send_queue.get()
                if audio_data is not None:
                    audio_base64 = self.pcm16_to_base64(audio_data)
                    audio_event = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_base64
                    }
                    self.session.send(json.dumps(audio_event))
                    self.last_send_time = time.time()
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(f"send_audio: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def clip_image(self):
        last_image_hash = None
        new_image = ImageGrab.grabclipboard()
        if isinstance(new_image, Image.Image):
            last_image_hash = hashlib.sha256(new_image.tobytes()).hexdigest()
        try:

            # イメージ確認
            while (self.session is not None) and (not self.break_flag):
                try:
                    new_image = ImageGrab.grabclipboard()
                    if isinstance(new_image, Image.Image):
                        image_hash = hashlib.sha256(new_image.tobytes()).hexdigest()
                        if (last_image_hash is None) or (image_hash != last_image_hash):  # 変更確認
                            last_image_hash = image_hash
                            print(" Live(openai) : [IMAGE] Detected ")

                            # jpeg変換
                            jpeg_io = io.BytesIO()
                            rgb = new_image.convert("RGB")
                            rgb.thumbnail([1024, 1024])
                            rgb.save(jpeg_io, format="jpeg")
                            jpeg_io.seek(0)
                            jpeg_bytes = jpeg_io.read()

                            self.image_send_queue.put(jpeg_bytes)
                except:
                    pass
                time.sleep(0.50)

        except Exception as e:
            print(f"clip_image: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def input_image(self):
        last_image_hash = None
        try:

            # イメージ確認
            while (self.session is not None) and (not self.break_flag):
                if (self.screen_shot_flag == True):
                    if self.image_send_queue.empty():
                        try:
                            new_image = self.SS.screen_shot(screen_number='auto')
                            if new_image is not None:
                                image_hash = hashlib.sha256(new_image.tobytes()).hexdigest()
                                if (last_image_hash is None) or (image_hash != last_image_hash):  # 変更確認
                                    last_image_hash = image_hash
                                    #print(" Live(openai) : [IMAGE] Detected ")

                                    pil_image = self.SS.cv2pil(new_image)

                                    # jpeg変換
                                    jpeg_io = io.BytesIO()
                                    rgb = pil_image.convert("RGB")
                                    rgb.thumbnail([1024, 1024])
                                    rgb.save(jpeg_io, format="jpeg")
                                    jpeg_io.seek(0)
                                    jpeg_bytes = jpeg_io.read()

                                    self.image_send_queue.put(jpeg_bytes)
                                    time.sleep(2.00)
                        except:
                            pass
                time.sleep(1.00)

        except Exception as e:
            print(f"input_image: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def send_image(self):
        try:

            # イメージ送信
            while (self.session is not None) and (not self.break_flag):
                jpeg_bytes = self.image_send_queue.get()
                if jpeg_bytes is not None:
                    #print(" Live(openai) : [IMAGE] Sending... ")
                    pass
                    #self.visualizer.update_image(jpeg_bytes)
                    #self.last_send_time = time.time()
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(f"send_image: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def play_audio(self, output_stream, output_rate, output_chunk):
        try:

            # 音声再生
            while (self.session is not None) and (not self.break_flag):
                audio_data = self.audio_receive_queue.get()
                if audio_data is not None:
                    output_stream.write(audio_data)
                    self.graph_output_queue.put(audio_data)
                else:
                    time.sleep(0.01)

        except Exception as e:
            print(f"play_audio: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def send_request(self, request_text='',):
        try:
            if (request_text is not None) and (request_text != ''):
                print(f" User(text): { request_text }")
                if (self.session is not None) and (not self.break_flag):

                    # テキスト送信
                    request = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [ {
                                "type": "input_text",
                                "text": request_text, 
                            } ]
                        },
                    }
                    self.session.send(json.dumps(request))
                    request = {
                        "type": "response.create",
                    }
                    self.session.send(json.dumps(request))
                    self.last_send_time = time.time()

        except Exception as e:
            print(f"send_request: {e}")
            self.error_flag = True
            return False
        return True

    def receive_proc(self):
        try:
            while (self.session is not None) and (not self.break_flag):
                response = self.session.recv()
                if response:
                    response_data = json.loads(response)
                    type  = response_data.get('type')
                    delta = response_data.get('delta')
                    transcript = response_data.get('transcript')
                    if type is not None:
                        if   type == "error":
                            res_err = response_data.get('error')
                            err_msg = res_err.get('message')
                            print(f" Live(openai) : ERROR { err_msg }")
                            self.break_flag = True
                            break
                        elif type == "response.audio.delta":
                            audio_base64_response = response_data["delta"]
                            if audio_base64_response:
                                audio_data = self.base64_to_pcm16(audio_base64_response)
                                self.audio_receive_queue.put(audio_data)
                        elif type == "input_audio_buffer.speech_started":
                            if not self.audio_receive_queue.empty():
                                self.audio_receive_queue.queue.clear() 
                            if not self.graph_output_queue.empty():
                                self.graph_output_queue.queue.clear() 
                        elif type == "response.audio_transcript.delta":
                            pass # stream!
                        elif type == "response.audio_transcript.done":
                            print(f" Live(openai) : { transcript }")
                            try:
                                #self.monjyu.post_output_log(outText=transcript, outData=transcript)
                                thread = threading.Thread(
                                    target=self.monjyu.post_output_log,args=(transcript, transcript),
                                    daemon=True
                                )
                                thread.start()
                            except Exception as e:
                                print(e)

                        elif type == "conversation.item.input_audio_transcription.completed":
                            print(f" Audio in : { transcript }")
                            try:
                                #self.monjyu.post_input_log(reqText=transcript, inpText='')
                                thread = threading.Thread(
                                    target=self.monjyu.post_input_log,args=(transcript, ''),
                                    daemon=True
                                )
                                thread.start()
                            except Exception as e:
                                print(e)

                        elif type == "response.function_call_arguments.delta":
                            pass # stream!

                        elif type == "response.function_call_arguments.done":
                            #print(response_data)
                            #function_call: {'type': 'response.function_call_arguments.done', 'event_id': 'event_ALmEfkiWKqDURkButy6ao', 'response_id': 'resp_ALmEfMfNpweiZtvT8xuWY', 'item_id': 'item_ALmEfBwmW2hVho7a5ayy7', 'output_index': 0, 'call_id': 'call_kKkSCI8UdT26zFZS', 'name': 'get_location_weather', 'arguments': '{"location":"東京"}'}

                            f_id = response_data.get('call_id')
                            f_name = response_data.get('name')
                            f_kwargs = response_data.get('arguments')
                            hit = False

                            #print()
                            if self.botFunc is not None:
                                for module_dic in self.botFunc.function_modules:
                                    if (f_name == module_dic['func_name']):
                                        hit = True
                                        print(f" Live(openai) :   function_call '{ module_dic['script'] }' ({ f_name })")
                                        print(f" Live(openai) :   → { f_kwargs }")

                                        # function 実行
                                        try:
                                            ext_func_proc  = module_dic['func_proc']
                                            res_json = ext_func_proc( f_kwargs )
                                        except Exception as e:
                                            print(e)
                                            # エラーメッセージ
                                            dic = {}
                                            dic['error'] = e 
                                            res_json = json.dumps(dic, ensure_ascii=False, )

                                        # tool_result
                                        print(f" Live(openai) :   → { res_json }")
                                        #print()

                                        try:
                                            # result 送信
                                            request = {
                                                "type": "conversation.item.create",
                                                "item": {
                                                    "type": "function_call_output",
                                                    "call_id": f_id,
                                                    "output": res_json,
                                                },
                                            }
                                            self.session.send(json.dumps(request))

                                            # 送信通知
                                            request = {
                                                "type": "response.create",
                                            }
                                            self.session.send(json.dumps(request))

                                        except Exception as e:
                                            print(f"function_call: {e}")

                        elif type in [
                            "session.created",
                            "session.updated",
                            "response.created",
                            "conversation.item.created",
                            "rate_limits.updated",
                            "response.output_item.added",
                            "conversation.item.created",
                            "response.content_part.added",
                            "response.audio.done",
                            "response.content_part.done",
                            "response.output_item.done",
                            "response.done",
                            "input_audio_buffer.speech_stopped",
                            "input_audio_buffer.committed",
                        ]:
                            pass

                        else:
                            print(response_data)
                    else:
                        print(response_data)
                else:
                    print(response)

        except Exception as e:
            print(f"receive_proc: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
        return True

    def start(self):
        self.break_flag = False
        self.error_flag = False
        self.last_send_time = time.time()
        self.screen_shot_flag = False
        print(f" Live(openai) : [START] ({ MODEL }) ")
        # Monjyu 確認
        if (self.monjyu_once_flag == False):
            self.monjyu_once_flag = True
            self.monjyu_enable = False
            self.monjyu_funcinfo = ''
            # 有効確認
            if self.botFunc is not None:
                for module_dic in self.botFunc.function_modules:
                    if (module_dic['func_name'] == 'execute_monjyu_request'):
                        self.monjyu_enable = True
                        print(f" Live(openai) : [INIT] (execute_monjyu_request) ")
                        # function 実行
                        dic = {}
                        dic['runMode'] = 'live'
                        dic['userId'] = 'live'
                        dic['reqText'] = '利用できるFunctions(Tools)と機能内容を要約して報告してください'
                        f_kwargs = json.dumps(dic, ensure_ascii=False, )
                        try:
                            ext_func_proc = module_dic['func_proc']
                            res_json = ext_func_proc( f_kwargs )
                            res_dic = json.loads(res_json)
                            res_text = res_dic.get('result_text','')
                            res_text = res_text.replace('`', '"')
                            #print(res_text)
                            self.monjyu_funcinfo = res_text
                        except Exception as e:
                            print(e)
                        break
        # 初期化
        self.image_send_queue = queue.Queue()
        self.audio_send_queue = queue.Queue()
        self.audio_receive_queue = queue.Queue()
        self.graph_input_queue = queue.Queue()
        self.graph_output_queue = queue.Queue()
        # スレッド処理
        def main_thread():
            try:
                # visualizer開始
                self.visualizer = _visualizer_class()
                self.visualizer.api_instance = self  # 自身への参照を追加
                self._main()
                # visualizer停止
                self.visualizer.root.quit()
                self.visualizer.root.destroy()
            except Exception as e:
                #print(f"main_thread: {e}")
                pass
            finally:
                self.break_flag = True
                print(f" Live(openai) : [END] ")
        # 起動
        self.main_task = threading.Thread(target=main_thread, daemon=True)
        self.main_task.start()
        return True

    def stop(self):
        print(" Live(openai) : [STOP] ")
        # 停止
        self.break_flag = True
        self.main_task.join()
        return True

    def _main(self):
        try:
            # 起動
            if (self.session is None):

                # Monjyu 無効
                if (self.monjyu_enable != True):
                    instructions = \
"""
あなたは美しい日本語を話す賢いアシスタントです。
あなたはLiveAPI(RealtimeAPI)で実行中のアシスタントです。
あなたの名前は「RiKi(りき)」です。
複数人で会話をしていますので、会話の流れを把握するようにして、口出しは最小限にお願いします。
あなたへの指示でない場合、相槌も必要ありません。できるだけ静かにお願いします。
"""
                # Monjyu 有効
                else:
                    print(" Live(openai) : [READY] 外部AI(execute_monjyu_request) ")
                    instructions = \
"""
あなたは美しい日本語を話す賢いアシスタントです。
あなたはLiveAPI(RealtimeAPI)で実行中のアシスタントです。
あなたの名前は「RiKi(りき)」です。
複数人で会話をしていますので、会話の流れを把握するようにして、口出しは最小限にお願いします。
あなたへの指示でない場合、相槌も必要ありません。できるだけ静かにお願いします。
あなたへの指示の場合、あなたが回答できない場合は、外部AI(execute_monjyu_request)を呼び出すことで、
適切なFunctions(Tools)も間接的に利用して、その結果で回答してしてください。
"""
                    if (self.monjyu_funcinfo != ''):
                        instructions += '\n【外部AI(execute_monjyu_request)経由で利用可能なFunctions(Tools)の情報】\n'
                        instructions += self.monjyu_funcinfo

                # ツール設定 通常はexecute_monjyu_requestのみ有効として処理
                tools = []
                if self.botFunc is not None:
                    for module_dic in self.botFunc.function_modules:
                        if (self.monjyu_enable == True):
                            if (module_dic['func_name'] == 'execute_monjyu_request'):
                                tool = {'type': 'function'} | module_dic['function']
                                tools.append( tool )
                                break
                        else:
                                tool = {'type': 'function'} | module_dic['function']
                                tools.append( tool )

                # Live 実行
                self.session = websocket.create_connection(self.WS_URL, header=self.HEADERS)
                if self.session is not None:
                    # 開始音
                    self.play(outFile='_sounds/_sound_up.mp3')

                    # Live 更新
                    update_request = {
                        "type": "session.update",
                        "session": {
                            "modalities": ["audio", "text"],
                            "instructions": instructions,
                            "voice": VOICE,
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                            },
                            "input_audio_transcription": {
                                "model": "whisper-1"
                            },
                            "tools": tools,
                            "tool_choice": "auto",
                        }
                    }
                    self.session.send(json.dumps(update_request))

                    audio_stream = pyaudio.PyAudio()
                    input_stream = audio_stream.open(format=FORMAT, channels=CHANNELS, rate=INPUT_RATE, input=True, frames_per_buffer=INPUT_CHUNK)
                    output_stream = audio_stream.open(format=FORMAT, channels=CHANNELS, rate=OUTPUT_RATE, output=True, frames_per_buffer=OUTPUT_CHUNK)

                    threads = [
                        threading.Thread(target=self.clip_image, daemon=True),
                        threading.Thread(target=self.input_image, daemon=True),
                        threading.Thread(target=self.send_image, daemon=True),
                        threading.Thread(target=self.input_audio, args=(input_stream, INPUT_RATE, INPUT_CHUNK), daemon=True),
                        threading.Thread(target=self.send_audio, daemon=True),
                        threading.Thread(target=self.play_audio, args=(output_stream, OUTPUT_RATE, OUTPUT_CHUNK), daemon=True),
                        threading.Thread(target=self.receive_proc, daemon=True),
                        #threading.Thread(target=self.tools_debug, daemon=True)
                    ]

                    for thread in threads:
                        thread.start()

                    # 待機
                    print(" Live(openai) : [RUN] Waiting... ")
                    self.inp_flag = False
                    self.inp_zero = True
                    self.out_flag = False
                    self.out_zero = True
                    while (not self.break_flag):
                        self.visualizer_update()
                        if (self.inp_flag == True) or (self.out_flag == True):
                            self.visualizer.update_graph()
                        time.sleep(0.01)

        except Exception as e:
            print(f"_main: {e}")
            self.error_flag = True
        finally:
            self.break_flag = True
            if self.session and self.session.connected:
                self.session.close()
            self.session = None
            # 解放
            if input_stream:
                input_stream.stop_stream()
                input_stream.close()
            if output_stream:
                output_stream.stop_stream()
                output_stream.close()
            audio_stream.terminate()
        # 終了音
        self.play(outFile='_sounds/_sound_down.mp3')
        return True

    def base64_to_pcm16(self, audio_base64):
        audio_data = base64.b64decode(audio_base64)
        return audio_data

    def pcm16_to_base64(self, audio_data):
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        return audio_base64

    def visualizer_update(self):
        #self.inp_flag = False
        #self.inp_zero = True
        #self.out_flag = False
        #self.out_zero = True
        try:
            ## グラフ更新
            #while (self.session is not None) and (not self.break_flag):

                if not self.graph_input_queue.empty():
                    input_data = self.graph_input_queue.get()
                    self.visualizer.update_value(input_chunk=input_data)
                    self.inp_flag = True
                    self.inp_zero = False
                else:
                    self.visualizer.update_value(input_chunk=bytes(INPUT_CHUNK * 2))
                    if (self.inp_zero == False):
                        self.inp_flag = True
                        self.inp_zero = True
                    
                if not self.graph_output_queue.empty():
                    output_data = self.graph_output_queue.get()
                    self.visualizer.update_value(output_chunk=output_data)
                    self.out_flag = True
                    self.out_zero = False
                else:
                    self.visualizer.update_value(output_chunk=bytes(OUTPUT_CHUNK * 2))
                    if (self.out_zero == False):
                        self.out_flag = True
                        self.out_zero = True

                #if (self.inp_flag == True) or (self.out_flag == True):
                #    self.visualizer.update_graph()
                #time.sleep(0.01)

        except Exception as e:
            print(f"visualizer_update: {e}")
            #self.error_flag = True
        #finally:
        #    self.break_flag = True
        return True



class _screenShot_class:
    def __init__(self):
        pass

    def screen_shot(self, screen_number='auto', ):
        cv_img   = None

        # 全画面
        if (str(screen_number) == 'all'):
            try:
                pil_img  = ImageGrab.grab(all_screens=True,)
                cv_image = self.pil2cv(pil_image=pil_img, )
                cv_img   = cv_image.copy()
            except:
                time.sleep(0.50)
                pil_img  = ImageGrab.grab(all_screens=True,)
                cv_image = self.pil2cv(pil_image=pil_img, )
                cv_img   = cv_image.copy()

        # マルチ画面 切り出し
        else:
            try:
                pil_img  = ImageGrab.grab(all_screens=True,)
                cv_image = self.pil2cv(pil_image=pil_img, )
            except:
                time.sleep(0.50)
                pil_img  = ImageGrab.grab(all_screens=True,)
                cv_image = self.pil2cv(pil_image=pil_img, )

            # スクリーン指定確認
            if (str(screen_number).isdigit()):
                if (int(screen_number) < 0) \
                or (int(screen_number) >= len(screeninfo.get_monitors())):
                    screen_number = 'auto'

            # 全スクリーンの配置
            min_left     = 0
            min_top      = 0
            max_right    = 0
            max_buttom   = 0
            for s in screeninfo.get_monitors():
                if (s.x < min_left):
                    min_left = s.x
                if (s.y  < min_top):
                    min_top = s.y
                if ((s.x+s.width) > max_right):
                    max_right = (s.x+s.width)
                if ((s.y+s.height) > max_buttom):
                    max_buttom = (s.y+s.height)

            # マウス配置
            mouse_x,mouse_y = pyautogui.position()

            # 画像切り出し
            screen = -1
            for s in screeninfo.get_monitors():
                screen += 1

                # 処理スクリーン？
                flag = False
                if (str(screen_number).isdigit()):
                    if (int(screen_number) == screen):
                        flag = True
                else:
                    if  (mouse_x >= s.x) and (mouse_x <= (s.x+s.width)) \
                    and (mouse_y >= s.y) and (mouse_y <= (s.y+s.height)):
                        flag = True

                # 切り出し
                if (flag == True):
                    left = s.x - min_left
                    top  = s.y - min_top

                    cv_img = np.zeros((s.height, s.width, 3), np.uint8)
                    cv_img[ 0:s.height, 0:s.width ] = cv_image[ top:top+s.height, left:left+s.width ]

        # 戻り値
        return cv_img

    def pil2cv(self, pil_image=None):
        try:
            cv2_image = np.array(pil_image, dtype=np.uint8)
            if (cv2_image.ndim == 2):  # モノクロ
                pass
            elif (cv2_image.shape[2] == 3):  # カラー
                cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR)
            elif (cv2_image.shape[2] == 4):  # 透過
                cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGBA2BGRA)
            return cv2_image
        except:
            pass
        return None

    def cv2pil(self, cv2_image=None):
        try:
            wrk_image = cv2_image.copy()
            if (wrk_image.ndim == 2):  # モノクロ
                pass
            elif (wrk_image.shape[2] == 3):  # カラー
                wrk_image = cv2.cvtColor(wrk_image, cv2.COLOR_BGR2RGB)
            elif (wrk_image.shape[2] == 4):  # 透過
                wrk_image = cv2.cvtColor(wrk_image, cv2.COLOR_BGRA2RGBA)
            pil_image = Image.fromarray(wrk_image)
            return pil_image
        except:
            pass
        return None



class _visualizer_class:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Visualizer")
        
        # ウィンドウクローズイベントのハンドラを追加
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
                
        # グラフ用のフレーム作成
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky="nsew")

        # 画像用のキャンバス無効
        self.img_canvas = None

        # グラフの初期化を直接実行
        self.initialize_plot()
        
    def initialize_plot(self):
        # Matplotlibのfigure作成（サイズを512x256に修正）
        self.fig, self.ax = plt.subplots(1, 1, figsize=(5.12,2.56))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # グラフの初期設定
        self.ax.set_title('Audio Level')

        # 背景を黒に設定
        self.fig.patch.set_facecolor('black')
        self.ax.set_facecolor('black')

        # グリッド線と軸の色を設定
        self.ax.grid(True, color='gray')
        self.ax.tick_params(colors='white',axis='y') # y軸のみ表示
        for spine in self.ax.spines.values():
            spine.set_color('white')
        
        # タイトルの色を白に
        self.ax.set_title('Audio Level', color='white')
        
        # 入力を赤、出力を青の棒グラフに設定
        self.line1, = self.ax.plot([], [], 'r', drawstyle='steps-pre', label='Input')  # 赤色
        self.line2, = self.ax.plot([], [], 'b', drawstyle='steps-pre', label='Output')  # 青色
        
        # Y軸の範囲設定（絶対値を100分率表示）
        self.ax.set_ylim(0, 100)
        
        # X軸の表示を消す
        self.ax.set_xticks([])
        
        # Y軸のラベルを追加
        self.ax.set_ylabel('Level (%)', color='white')
        
        # 凡例を表示
        self.ax.legend(loc='upper right', facecolor='black', labelcolor='white')
        
        # データバッファ
        self.input_data = []
        self.output_data = []

    def on_closing(self):
        pyautogui.keyDown('end')
        pyautogui.keyUp('end')
        if hasattr(self, 'api_instance'):
            self.api_instance.break_flag = True
            
    def update_value(self, input_chunk=None, output_chunk=None):
        # 入力波形
        if input_chunk is not None:
            # 絶対値に変換
            input_data = np.abs( np.frombuffer(input_chunk, dtype=np.int16) )
            # 最初のINPUT_CHUNKバイトを有効に
            if (len(input_data) > INPUT_CHUNK):
                 input_data = input_data[:INPUT_CHUNK]
            # バイト数がINPUT_CHUNK未満の場合
            elif (len(input_data) < INPUT_CHUNK):
                input_data = np.pad(input_data, (0, (INPUT_CHUNK - len(input_data))), 'constant')
            # 最大値に対する100分率に変換
            max_val = np.max(input_data)
            if max_val > 0:  # ゼロ除算を防ぐ
                input_data = (input_data / max_val) * 100
            self.input_data = input_data
            self.line1.set_data(range(len(input_data)), input_data)
            self.ax.set_xlim(0, len(input_data))

        # 出力波形
        if output_chunk is not None:
            # 絶対値に変換
            output_data = np.abs( np.frombuffer(output_chunk, dtype=np.int16) )
            # 最初のOUTPUT_CHUNKバイトを有効に
            if (len(output_data) > OUTPUT_CHUNK):
                 output_data = output_data[:OUTPUT_CHUNK]
            # バイト数がOUTPUT_CHUNK未満の場合
            elif (len(output_data) < OUTPUT_CHUNK):
                output_data = np.pad(output_data, (0, (OUTPUT_CHUNK - len(output_data))), 'constant')
            # 最大値に対する100分率に変換
            max_val = np.max(output_data)
            if max_val > 0:  # ゼロ除算を防ぐ
                output_data = (output_data / max_val) * 100
            self.output_data = output_data
            self.line2.set_data(range(len(output_data)), output_data)
            self.ax.set_xlim(0, len(output_data))

    def update_image(self, jpeg_bytes):
        try:
            # JPEGバイト列からPIL Imageを作成
            image = Image.open(io.BytesIO(jpeg_bytes))

            # 画像用のキャンバス作成
            if self.img_canvas is None:
                self.img_canvas = tk.Canvas(self.root, bg="black")
                self.img_canvas.place(relx=1.0, rely=1.0, anchor="se")
                self.canvas.draw()
                self.root.update()

            # ウィンドウサイズを更新
            max_width = int(self.root.winfo_width() / 2)
            max_height = int(self.root.winfo_height() / 2)
            
            # ウィンドウサイズが取得できた場合のみリサイズ
            if max_width > 0 and max_height > 0:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS) # 必要に応じてImage.LANCZOSに変更
            
            # PIL ImageからPhotoImageを作成
            self.img_photo = ImageTk.PhotoImage(image)
            
            # キャンバスに画像を追加
            self.img_canvas.config(width=image.width, height=image.height)
            
            # 画像を右下に配置
            self.img_canvas.create_image(0, 0, image=self.img_photo, anchor="nw")
            
        except Exception as e:
            print(f"Error updating background image: {e}")

    def update_graph(self):
        try:
            self.canvas.draw()
            self.root.update()
        except:
            pass



class _monjyu_class:
    def __init__(self, runMode='assistant' ):
        self.runMode = runMode

        # ポート設定等
        self.local_endpoint = f'http://localhost:{ CORE_PORT }'
        self.user_id = 'admin'

    def post_input_log(self, reqText='', inpText=''):
        # AI要求送信
        try:
            response = requests.post(
                self.local_endpoint + '/post_input_log',
                json={'user_id': self.user_id, 
                      'request_text': reqText,
                      'input_text': inpText, },
                timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
            )
            if response.status_code != 200:
                print('error', f"Error response ({ CORE_PORT }/post_input_log) : {response.status_code} - {response.text}")
        except Exception as e:
            print('error', f"Error communicating ({ CORE_PORT }/post_input_log) : {e}")
        return True

    def post_output_log(self, outText='', outData=''):
        # AI要求送信
        try:
            response = requests.post(
                self.local_endpoint + '/post_output_log',
                json={'user_id': self.user_id, 
                      'output_text': outText,
                      'output_data': outData, },
                timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
            )
            if response.status_code != 200:
                print('error', f"Error response ({ CORE_PORT }/post_output_log) : {response.status_code} - {response.text}")
        except Exception as e:
            print('error', f"Error communicating ({ CORE_PORT }/post_output_log) : {e}")
        return True



class _class:

    def __init__(self, ):
        self.version   = "v0"
        self.func_name = "extension_UI_key2Live_openai"
        self.func_ver  = "v0.20241008"
        self.func_auth = "h0MmuBSfyHFVSPQ+uqVSZFzgtA/0GfSQa4URyA0F0O5bcSMXp28PFOLPq3YGTbri"
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
    #api_key = ext.sub_proc.api_key

    #liveAPI = _live_api_openai(api_key, MODEL)
    #liveAPI.start()
    #time.sleep(5)
    #liveAPI.send_request(request_text='日本語で話してください')
    #time.sleep(30)
    #liveAPI.stop()
    #time.sleep(5)


    #ext = _class()
    print(ext.func_proc('{ "runMode" : "assistant", "reqText" : "" }'))

    time.sleep(2)

    print(ext.func_proc('{ "runMode" : "assistant", "reqText" : "おはようございます" }'))

    time.sleep(60)


