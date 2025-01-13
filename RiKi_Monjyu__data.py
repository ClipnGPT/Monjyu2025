#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/konsan1101
# Thank you for keeping the rules.
# ------------------------------------------------

# RiKi_Monjyu__data.py

import sys
import os
import time
import datetime
import codecs
import glob
import shutil

import requests

import random
import threading

import socket
qHOSTNAME = socket.gethostname().lower()

# 一時ファイル保存用パス
qPath_temp   = 'temp/'
qPath_log    = 'temp/_log/'

# ログクラスのインポートとインスタンス生成
import _v6__qLog
qLog = _v6__qLog.qLog_class()

# 定数の定義
CONNECTION_TIMEOUT = 15
REQUEST_TIMEOUT = 30



class _data_class:
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None,
                        core_port: str = '8000', sub_base: str = '8100', num_subais: str = '48', ):
        self.runMode = runMode

        # ログ設定
        self.proc_name = 'data'
        self.proc_id = '{0:10s}'.format(self.proc_name).replace(' ', '_')
        if not os.path.isdir(qPath_log):
            os.makedirs(qPath_log)
        if qLog_fn == '':
            nowTime = datetime.datetime.now()
            qLog_fn = qPath_log + nowTime.strftime('%Y%m%d.%H%M%S') + '.' + os.path.basename(__file__) + '.log'
        qLog.init(mode='logger', filename=qLog_fn)
        qLog.log('info', self.proc_id, 'init')

        # 各種設定の初期化
        self.main      = main
        self.conf      = conf

        # 設定
        self.core_port = core_port
        self.sub_base  = sub_base
        self.num_subais = int(num_subais)
        self.local_endpoint = f'http://localhost:{ self.core_port }'
        self.core_endpoint = self.local_endpoint.replace('localhost', qHOSTNAME)
        self.webui_endpoint = self.core_endpoint.replace( f':{ self.core_port }', f':{ int(self.core_port) + 8 }' )

        # サブAIの情報
        self.subai_ports = [str(port) for port in range(int(self.sub_base) + 1, int(self.sub_base) + 1 + self.num_subais)]
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.subai_info = {port: {'status': 'NONE', 'nick_name': None, 'upd_time':now_time} for port in self.subai_ports}
        self.subai_reset = {port: {'reset': 'yes,'} for port in self.subai_ports}

        # 結果の保存
        self.subai_sessions_all   = {}
        self.subai_input_log_key  = 0
        self.subai_input_log_all  = {}
        self.subai_output_log_key = 0
        self.subai_output_log_all = {}
        self.subai_debug_log_key  = 0
        self.subai_debug_log_all  = {}
        self.subai_histories_key  = 0
        self.subai_histories_all  = {}

        # 設定の保存
        self.perplexity_enable = True
        self.claude_enable = True
        self.openai_enable = True
        self.mode_setting = {}
        self.addins_setting = {}
        self.live_voices = {}
        self.live_setting = {}
        self.webAgent_useBrowser = ""
        self.webAgent_modelAPI = ""
        self.webAgent_modelNames = {}
        self.webAgent_setting = {}
        self._reset()

        # スレッドロック
        self.thread_lock = threading.Lock()

        # サブAI監視 開始
        self.start_subais()

    def _reset(self):

        # 各動作モードの設定
        self.mode_setting['chat'] = {
            "req_engine": "",
            "req_functions": "", "req_reset": "",
            "max_retry": "0", "max_ai_count": "0",
            "before_proc": "none,", "before_engine": "[perplexity]",
            "after_proc": "none,", "after_engine": "[claude]",
            "check_proc": "none,", "check_engine": "[openai]"
        }

        self.mode_setting['websearch'] = {
            "req_engine": "",
            "req_functions": "", "req_reset": "",
            "max_retry": "0", "max_ai_count": "0",
            "before_proc": "none,", "before_engine": "[perplexity]",
            "after_proc": "none,", "after_engine": "[claude]",
            "check_proc": "none,", "check_engine": "[openai]"
        }

        if (self.perplexity_enable != True):
            self.mode_setting['chat']['before_engine'] = ''
            self.mode_setting['websearch']['before_engine'] = ''

        if (self.claude_enable != True):
            self.mode_setting['chat']['after_engine'] = ''
            self.mode_setting['websearch']['after_engine'] = ''

        if (self.openai_enable != True):
            self.mode_setting['chat']['check_engine'] = ''
            self.mode_setting['websearch']['check_engine'] = ''

        self.mode_setting['serial'] = {
            "req_engine": "", 
            "req_functions": "", "req_reset": "",
            "max_retry": "", "max_ai_count": "",
            "before_proc": "", "before_engine": "",
            "after_proc": "", "after_engine": "",
            "check_proc": "", "check_engine": ""
        }

        self.mode_setting['parallel'] = {
            "req_engine": "", 
            "req_functions": "", "req_reset": "",
            "max_retry": "", "max_ai_count": "",
            "before_proc": "", "before_engine": "",
            "after_proc": "", "after_engine": "",
            "check_proc": "", "check_engine": ""
        }

        self.mode_setting['session'] = {
            "req_engine": "",
            "req_functions": "", "req_reset": "",
            "max_retry": "0", "max_ai_count": "0",
            "before_proc": "none,", "before_engine": "",
            "after_proc": "none,", "after_engine": "",
            "check_proc": "none,", "check_engine": ""
        }

        self.mode_setting['clip'] = {
            "req_engine": "",
            "req_functions": "", "req_reset": "",
            "max_retry": "0", "max_ai_count": "0",
            "before_proc": "none,", "before_engine": "",
            "after_proc": "none,", "after_engine": "",
            "check_proc": "none,", "check_engine": ""
        }

        self.mode_setting['voice'] = {
            "req_engine": "",
            "req_functions": "", "req_reset": "",
            "max_retry": "0", "max_ai_count": "0",
            "before_proc": "none,", "before_engine": "",
            "after_proc": "none,", "after_engine": "",
            "check_proc": "none,", "check_engine": ""
        }

        # addinsの設定
        self.addins_setting = {
            "result_text_save": "", 
            "speech_tts_engine": "", 
            "speech_stt_engine": "",
            "text_clip_input": "",
            "text_url_execute": "",
            "text_pdf_execute": "",
            "image_ocr_execute": "",
            "image_yolo_execute": ""
        }

        # liveの設定
        self.live_voices[ 'freeai'] = {"Puck": "Puck", 
                                       "Charon": "Charon", 
                                       "Kore": "Kore", 
                                       "Fenrir": "Fenrir", 
                                       "Aoede": "Aoede" }
        self.live_setting['freeai'] = { "voice": "Aoede", }
        self.live_voices[ 'openai'] = {"alloy": "Alloy", 
                                       "ash": "Ash",
                                       "ballad": "Ballad",
                                       "coral": "Coral", 
                                       "echo": "Echo", 
                                       "sage": "Sage", 
                                       "shimmer": "Shimmer",
                                       "verse": "Verse" }
        self.live_setting['openai'] = { "voice": "alloy", }

        # Agentの設定
        self.webAgent_useBrowser =  ""
        self.webAgent_modelAPI =  ""
        self.webAgent_modelNames[ 'freeai'] = {}
        self.webAgent_setting[    'freeai'] = { "modelName": "", 
                                                "maxSteps": "", }
        self.webAgent_modelNames[ 'openai'] = {}
        self.webAgent_setting[    'openai'] = { "modelName": "", 
                                                "maxSteps": "", }
        self.webAgent_modelNames[ 'claude'] = {}
        self.webAgent_setting[    'claude'] = { "modelName": "", 
                                                "maxSteps": "", }

    def update_subai_status(self, port: str):
        """
        サブAIのステータスを定期的に更新する。
        """
        while True:
            sleep_sec = random.uniform(self.num_subais, self.num_subais * 2)
            time.sleep(sleep_sec)
            if  (self.main is None) \
            or ((self.main is not None) and (self.main.main_all_ready == True)):

                try:
                    endpoint = self.local_endpoint.replace( f':{ self.core_port }', f':{ port }' )
                    response = requests.get(endpoint + '/get_info', timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT))
                    if response.status_code == 200:
                        new_status = response.json()['status']
                        nick_name = response.json()['nick_name']
                        full_name = response.json()['full_name']
                        info_text = response.json()['info_text']
                        with self.thread_lock:
                            old_status = self.subai_info[port].get('status')
                            upd_time   = self.subai_info[port].get('upd_time')
                            if (new_status != old_status):
                                upd_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                            self.subai_info[port] = {
                                'status': new_status, 
                                'nick_name': nick_name, 
                                'full_name': full_name, 
                                'info_text': info_text, 
                                'upd_time': upd_time, }
                    else:
                        qLog.log('error', self.proc_id, f"Error response ({ port }/get_info) : {response.status_code}")
                        with self.thread_lock:
                            self.subai_info[port]['status'] = 'NONE'
                            self.subai_info[port]['upd_time'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                except Exception as e:
                    qLog.log('error', self.proc_id, f"Error communicating ({ port }/get_info) : {e}")
                    with self.thread_lock:
                        self.subai_info[port]['status'] = 'NONE'
                        self.subai_info[port]['upd_time'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def start_subais(self):
        """
        サブAIのステータス更新スレッドを開始する。
        """
        for port in self.subai_ports:
            try:
                thread = threading.Thread(target=self.update_subai_status, args=(port,), daemon=True, )
                thread.start()
            except Exception as e:
                qLog.log('error', self.proc_id, f"Failed to start subai on port {port}: {e}")

    def reset(self, user_id: str, ):
        # 設定リセット
        self._reset()
        # サブAIリセット
        with self.thread_lock:
            self.subai_reset = {port: {'reset': 'yes,'} for port in self.subai_ports}
        # サブAI CANCEL 処理
        self.cancel(user_id=user_id, )
        return True

    def cancel(self, user_id: str, ):
        # サブAI CANCEL 処理
        for port in self.subai_ports:
            if self.subai_info[port]['status'] in ['SERIAL', 'PARALLEL', 'CHAT', 'SESSION']:
                thread = threading.Thread(target=self._send_cancel, args=(user_id, port,), daemon=True, )
                thread.start()
        return True

    def _send_cancel(self, user_id: str, to_port: str):
        """
        サブAIへのキャンセル送信処理。
        """
        try:
            endpoint = self.local_endpoint.replace( f':{ self.core_port }', f':{ to_port }' )
            response = requests.post(
                endpoint + '/post_cancel',
                json={'user_id': user_id, },
                timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
            )
            if response.status_code == 200:
                with self.thread_lock:
                    self.subai_info[to_port]['status'] = 'CANCEL'
                return True
            else:
                with self.thread_lock:
                    self.subai_info[to_port]['status'] = 'ERROR'
                return False
        except Exception as e:
            qLog.log('error', self.proc_id, f"Error communicating ({ to_port }/post_cancel) : {e}")
            with self.thread_lock:
                self.subai_info[to_port]['status'] = 'NONE'
        return False



if __name__ == '__main__':
    core_port = '8000'
    sub_base  = '8100'
    numSubAIs = '48'

    data = _data_class( runMode='debug', qLog_fn='', 
                        core_port=core_port, sub_base=sub_base, num_subais=numSubAIs)


