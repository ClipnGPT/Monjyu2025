#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/konsan1101
# Thank you for keeping the rules.
# ------------------------------------------------

# RiKi_Monjyu__coreai.py

import sys
import os
import time
import datetime
import codecs
import glob
import shutil

import json
import requests

from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

import random
import threading

import socket
qHOSTNAME = socket.gethostname().lower()

# パスの設定
qPath_temp   = 'temp/'
qPath_log    = 'temp/_log/'
qPath_output = 'temp/output/'
qPath_tts    = 'temp/s6_5tts_txt/'

# 共通ルーチン
import  _v6__qLog
qLog  = _v6__qLog.qLog_class()
import  _v6__qFunc
qFunc = _v6__qFunc.qFunc_class()
import RiKi_Monjyu__subbot

# 定数の定義
CONNECTION_TIMEOUT = 15
REQUEST_TIMEOUT = 30
DELETE_INPUTLOG_SEC   = 600
DELETE_OUTPUTLOG_SEC  = 600
DELETE_DEBUGLOG_SEC   = 600
DELETE_SESSIONS_SEC   = 1200
DELETE_HISTORIES_SEC  = 3600

# リクエストデータモデル(Mini)
class RequestMiniModel(BaseModel):
    user_id: str
    from_port: str
    to_port: str
    req_mode: str
    system_text: str
    request_text: str
    input_text: str
    file_names: list[str]
    result_savepath: str
    result_schema: str

# リクエストデータモデル(Full)
class RequestFullModel(BaseModel):
    user_id: str
    from_port: str
    to_port: str
    req_mode: str
    req_engine: str
    req_functions: str
    req_reset: str
    max_retry: str
    max_ai_count: str
    before_proc: str
    before_engine: str
    after_proc: str
    after_engine: str
    check_proc: str
    check_engine: str
    system_text: str
    request_text: str
    input_text: str
    file_names: list[str]
    result_savepath: str
    result_schema: str

# 結果データモデル
class ResultDataModel(BaseModel):
    user_id: str
    from_port: str
    to_port: str
    req_mode: str
    system_text: str
    request_text: str
    input_text: str
    result_savepath: str
    result_schema: str
    output_text: str
    output_data: str
    output_path: str
    output_files: list[str]
    status: str

# ユーザーIDモデル
class UserIdModel(BaseModel):
    user_id: str

# input_logモデル
class InputLogModel(BaseModel):
    user_id: str
    request_text: str
    input_text: str

# output_logモデル
class OutputLogModel(BaseModel):
    user_id: str
    output_text: str
    output_data: str

# クリップファイル名モデル
class postClipNamesModel(BaseModel):
    user_id: str
    clip_names: list[str]

# クリップテキストモデル
class postClipTextModel(BaseModel):
    user_id: str
    clip_text: str

class CoreAiProcess:
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None, data=None, addin=None, botFunc=None,
                        core_port: str = '8000', sub_base: str = '8100', num_subais: str = '48', ):
        # コアAIクラスの初期化とスレッドの開始
        coreai_class = CoreAiClass( runMode=runMode, qLog_fn=qLog_fn,
                                    main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                    core_port=core_port, sub_base=sub_base, num_subais=num_subais, )
        coreai_thread = threading.Thread(target=coreai_class.run, daemon=True, )
        coreai_thread.start()
        while True:
            time.sleep(5)

class CoreAiClass:
    """
    コアAIクラス
    サブAIとの通信や結果管理、FastAPIサーバーの管理を行う。
    """
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None, data=None, addin=None, botFunc=None,
                        core_port: str = '8000', sub_base: str = '8100', num_subais: str = '48', ):
        self.runMode = runMode
        self_port = core_port

        # ログ設定
        self.proc_name = f"{ self_port }:core"
        self.proc_id = '{0:10s}'.format(self.proc_name).replace(' ', '_')
        if not os.path.isdir(qPath_log):
            os.makedirs(qPath_log)
        if qLog_fn == '':
            nowTime = datetime.datetime.now()
            qLog_fn = qPath_log + nowTime.strftime('%Y%m%d.%H%M%S') + '.' + os.path.basename(__file__) + '.log'
        qLog.init(mode='logger', filename=qLog_fn)
        qLog.log('info', self.proc_id, 'init')

        # 設定
        self.main      = main
        self.conf      = conf
        self.data      = data
        self.addin     = addin
        self.botFunc   = botFunc
        self.core_port = core_port
        self.sub_base  = sub_base
        self.num_subais = int(num_subais)
        self.self_port = self_port
        self.local_endpoint = f'http://localhost:{ self.core_port }'
        self.core_endpoint = self.local_endpoint.replace('localhost', qHOSTNAME)
        self.webui_endpoint = self.core_endpoint.replace( f':{ self.core_port }', f':{ int(self.core_port) + 8 }' )

        # 自己bot設定
        self.chat_class = RiKi_Monjyu__subbot.ChatClass(runMode=runMode, qLog_fn=qLog_fn, 
                                                        main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                                        core_port=core_port, self_port=self_port)
        self.history    = []

        # スレッドロック
        self.thread_lock = threading.Lock()

        # 最終回答の保存
        self.last_input_log_user = None
        self.last_output_log_user = None
        self.last_debug_log_user = None

        # サブAIの順番をランダムにシャッフル
        if (self.data is not None):
            self.random_order = random.sample(self.data.subai_ports, len(self.data.subai_ports))
        self.current_order_index = 0

        # FastAPI設定
        self.app = FastAPI()
        self.app.get("/")(self.root)
        self.app.get("/get_ready_count")(self.get_ready_count)
        self.app.get('/get_models')(self.get_models)
        self.app.get("/get_subai_info_all")(self.get_subai_info_all)
        self.app.get("/get_subai_statuses_all")(self.get_subai_statuses_all)
        self.app.get("/get_sessions_all")(self.get_sessions_all)
        self.app.get("/get_sessions_port")(self.get_sessions_port)
        self.app.get("/get_histories_all")(self.get_histories_all)
        self.app.get("/get_debug_log_all")(self.get_debug_log_all)
        self.app.get("/get_input_log_user")(self.get_input_log_user)
        self.app.get("/get_output_log_user")(self.get_output_log_user)
        self.app.get("/get_debug_log_user")(self.get_debug_log_user)
        self.app.post("/post_req")(self.post_req)
        self.app.post("/post_request")(self.post_request)
        self.app.post("/post_complete")(self.post_complete)
        self.app.post("/post_debug_log")(self.post_debug_log)
        self.app.post("/post_reset")(self.post_reset)
        self.app.post("/post_cancel")(self.post_cancel)
        self.app.post("/post_clear")(self.post_clear)
        self.app.post("/post_input_log")(self.post_input_log)
        self.app.post("/post_output_log")(self.post_output_log)
        self.app.post("/post_clip_names")(self.post_clip_names)
        self.app.post("/post_clip_text")(self.post_clip_text)

    async def root(self, request: Request):
        # Web UI にリダイレクト
        return RedirectResponse(url=self.webui_endpoint + '/')

    async def get_ready_count(self):
        """
        レディ状態とビジー状態のサブAI数を返す。
        """
        if (self.data is None):
            ready_count = 0
            busy_count = 0
            res = {'ready_count': ready_count, 'busy_count': busy_count}
            return JSONResponse(content=res)

        with self.thread_lock:
            ready_count = sum(1 for info in self.data.subai_info.values() if info['status'] == 'READY')
            busy_count = sum(1 for info in self.data.subai_info.values() if info['status'] in ['BUSY', 'SERIAL', 'PARALLEL', 'CHAT'])
        res = {'ready_count': ready_count, 'busy_count': busy_count}
        return JSONResponse(content=res)

    async def get_models(self, req_mode: str) -> Dict[str, str]:
        """ 有効AI名取得(応答) """
        models = {}

        if True:
            if self.chat_class.freeai_enable is None:
                self.chat_class.freeai_auth()
            if self.chat_class.freeai_enable:
                models['[freeai]'] = '[FreeAI]'
                if self.chat_class.freeaiAPI.freeai_a_enable and self.chat_class.freeaiAPI.freeai_a_nick_name:
                    models[self.chat_class.freeaiAPI.freeai_a_nick_name.lower()] = ' ' + self.chat_class.freeaiAPI.freeai_a_nick_name
                if self.chat_class.freeaiAPI.freeai_b_enable and self.chat_class.freeaiAPI.freeai_b_nick_name:
                    models[self.chat_class.freeaiAPI.freeai_b_nick_name.lower()] = ' ' + self.chat_class.freeaiAPI.freeai_b_nick_name
                if self.chat_class.freeaiAPI.freeai_v_enable and self.chat_class.freeaiAPI.freeai_v_nick_name:
                    models[self.chat_class.freeaiAPI.freeai_v_nick_name.lower()] = ' ' + self.chat_class.freeaiAPI.freeai_v_nick_name
                if self.chat_class.freeaiAPI.freeai_x_enable and self.chat_class.freeaiAPI.freeai_x_nick_name:
                    models[self.chat_class.freeaiAPI.freeai_x_nick_name.lower()] = ' ' + self.chat_class.freeaiAPI.freeai_x_nick_name

        if (req_mode == 'chat'):
            if self.chat_class.perplexity_enable is None:
                self.chat_class.perplexity_auth()
                if not self.chat_class.perplexity_enable:
                    self.data.perplexity_enable = self.chat_class.perplexity_enable
                    self.data._reset()
            if self.chat_class.perplexity_enable:
                models['[perplexity]'] = '[Perplexity]'
                if self.chat_class.perplexityAPI.perplexity_a_enable and self.chat_class.perplexityAPI.perplexity_a_nick_name:
                    models[self.chat_class.perplexityAPI.perplexity_a_nick_name.lower()] = ' ' + self.chat_class.perplexityAPI.perplexity_a_nick_name
                if self.chat_class.perplexityAPI.perplexity_b_enable and self.chat_class.perplexityAPI.perplexity_b_nick_name:
                    models[self.chat_class.perplexityAPI.perplexity_b_nick_name.lower()] = ' ' + self.chat_class.perplexityAPI.perplexity_b_nick_name
                if self.chat_class.perplexityAPI.perplexity_v_enable and self.chat_class.perplexityAPI.perplexity_v_nick_name:
                    models[self.chat_class.perplexityAPI.perplexity_v_nick_name.lower()] = ' ' + self.chat_class.perplexityAPI.perplexity_v_nick_name
                if self.chat_class.perplexityAPI.perplexity_x_enable and self.chat_class.perplexityAPI.perplexity_x_nick_name:
                    models[self.chat_class.perplexityAPI.perplexity_x_nick_name.lower()] = ' ' + self.chat_class.perplexityAPI.perplexity_x_nick_name

        if (req_mode == 'chat'):
            if self.chat_class.openai_enable is None:
                self.chat_class.openai_auth()
                if not self.chat_class.openai_enable:
                    self.data.openai_enable = self.chat_class.openai_enable
                    self.data._reset()
            if self.chat_class.openai_enable:
                models['[openai]'] = '[OpenAI]'
                if self.chat_class.openaiAPI.gpt_a_nick_name:
                    models[self.chat_class.openaiAPI.gpt_a_nick_name.lower()] = ' ' + self.chat_class.openaiAPI.gpt_a_nick_name
                if self.chat_class.openaiAPI.gpt_b_nick_name:
                    models[self.chat_class.openaiAPI.gpt_b_nick_name.lower()] = ' ' + self.chat_class.openaiAPI.gpt_b_nick_name
                if self.chat_class.openaiAPI.gpt_v_nick_name:
                    models[self.chat_class.openaiAPI.gpt_v_nick_name.lower()] = ' ' + self.chat_class.openaiAPI.gpt_v_nick_name
                if self.chat_class.openaiAPI.gpt_x_nick_name:
                    models[self.chat_class.openaiAPI.gpt_x_nick_name.lower()] = ' ' + self.chat_class.openaiAPI.gpt_x_nick_name

        if (req_mode == 'chat'):
            if self.chat_class.azureoai_enable is None:
                self.chat_class.azureoai_auth()
            if self.chat_class.azureoai_enable:
                models['[azure]'] = '[Azure]'
                if self.chat_class.azureAPI.gpt_a_nick_name:
                    models[self.chat_class.azureAPI.gpt_a_nick_name.lower()] = ' ' + self.chat_class.azureAPI.gpt_a_nick_name
                if self.chat_class.azureAPI.gpt_b_nick_name:
                    models[self.chat_class.azureAPI.gpt_b_nick_name.lower()] = ' ' + self.chat_class.azureAPI.gpt_b_nick_name
                if self.chat_class.azureAPI.gpt_v_nick_name:
                    models[self.chat_class.azureAPI.gpt_v_nick_name.lower()] = ' ' + self.chat_class.azureAPI.gpt_v_nick_name
                if self.chat_class.azureAPI.gpt_x_nick_name:
                    models[self.chat_class.azureAPI.gpt_x_nick_name.lower()] = ' ' + self.chat_class.azureAPI.gpt_x_nick_name

        if (req_mode == 'chat'):
            if self.chat_class.claude_enable is None:
                self.chat_class.claude_auth()
                if not self.chat_class.claude_enable:
                    self.data.claude_enable = self.chat_class.claude_enable
                    self.data._reset()
            if self.chat_class.claude_enable:
                models['[claude]'] = '[Claude]'
                if self.chat_class.claudeAPI.claude_a_enable and self.chat_class.claudeAPI.claude_a_nick_name:
                    models[self.chat_class.claudeAPI.claude_a_nick_name.lower()] = ' ' + self.chat_class.claudeAPI.claude_a_nick_name
                if self.chat_class.claudeAPI.claude_b_enable and self.chat_class.claudeAPI.claude_b_nick_name:
                    models[self.chat_class.claudeAPI.claude_b_nick_name.lower()] = ' ' + self.chat_class.claudeAPI.claude_b_nick_name
                if self.chat_class.claudeAPI.claude_v_enable and self.chat_class.claudeAPI.claude_v_nick_name:
                    models[self.chat_class.claudeAPI.claude_v_nick_name.lower()] = ' ' + self.chat_class.claudeAPI.claude_v_nick_name
                if self.chat_class.claudeAPI.claude_x_enable and self.chat_class.claudeAPI.claude_x_nick_name:
                    models[self.chat_class.claudeAPI.claude_x_nick_name.lower()] = ' ' + self.chat_class.claudeAPI.claude_x_nick_name

        if (req_mode == 'chat'):
            if self.chat_class.gemini_enable is None:
                self.chat_class.gemini_auth()
            if self.chat_class.gemini_enable:
                models['[gemini]'] = '[Gemini]'
                if self.chat_class.geminiAPI.gemini_a_enable and self.chat_class.geminiAPI.gemini_a_nick_name:
                    models[self.chat_class.geminiAPI.gemini_a_nick_name.lower()] = ' ' + self.chat_class.geminiAPI.gemini_a_nick_name
                if self.chat_class.geminiAPI.gemini_b_enable and self.chat_class.geminiAPI.gemini_b_nick_name:
                    models[self.chat_class.geminiAPI.gemini_b_nick_name.lower()] = ' ' + self.chat_class.geminiAPI.gemini_b_nick_name
                if self.chat_class.geminiAPI.gemini_v_enable and self.chat_class.geminiAPI.gemini_v_nick_name:
                    models[self.chat_class.geminiAPI.gemini_v_nick_name.lower()] = ' ' + self.chat_class.geminiAPI.gemini_v_nick_name
                if self.chat_class.geminiAPI.gemini_x_enable and self.chat_class.geminiAPI.gemini_x_nick_name:
                    models[self.chat_class.geminiAPI.gemini_x_nick_name.lower()] = ' ' + self.chat_class.geminiAPI.gemini_x_nick_name

        if True:
            if self.chat_class.ollama_enable is None:
                self.chat_class.ollama_auth()
            if self.chat_class.ollama_enable:
                models['[ollama]'] = '[Ollama]'
                if self.chat_class.ollamaAPI.ollama_a_enable and self.chat_class.ollamaAPI.ollama_a_nick_name:
                    models[self.chat_class.ollamaAPI.ollama_a_nick_name.lower()] = ' ' + self.chat_class.ollamaAPI.ollama_a_nick_name
                if self.chat_class.ollamaAPI.ollama_b_enable and self.chat_class.ollamaAPI.ollama_b_nick_name:
                    models[self.chat_class.ollamaAPI.ollama_b_nick_name.lower()] = ' ' + self.chat_class.ollamaAPI.ollama_b_nick_name
                if self.chat_class.ollamaAPI.ollama_v_enable and self.chat_class.ollamaAPI.ollama_v_nick_name:
                    models[self.chat_class.ollamaAPI.ollama_v_nick_name.lower()] = ' ' + self.chat_class.ollamaAPI.ollama_v_nick_name
                if self.chat_class.ollamaAPI.ollama_x_enable and self.chat_class.ollamaAPI.ollama_x_nick_name:
                    models[self.chat_class.ollamaAPI.ollama_x_nick_name.lower()] = ' ' + self.chat_class.ollamaAPI.ollama_x_nick_name

        if True:
            if self.chat_class.plamo_enable is None:
                self.chat_class.plamo_auth()
            if self.chat_class.plamo_enable:
                models['[plamo]'] = '[PLaMo]'
                if self.chat_class.plamoAPI.plamo_a_enable and self.chat_class.plamoAPI.plamo_a_nick_name:
                    models[self.chat_class.plamoAPI.plamo_a_nick_name.lower()] = ' ' + self.chat_class.plamoAPI.plamo_a_nick_name
                if self.chat_class.plamoAPI.plamo_b_enable and self.chat_class.plamoAPI.plamo_b_nick_name:
                    models[self.chat_class.plamoAPI.plamo_b_nick_name.lower()] = ' ' + self.chat_class.plamoAPI.plamo_b_nick_name
                if self.chat_class.plamoAPI.plamo_v_enable and self.chat_class.plamoAPI.plamo_v_nick_name:
                    models[self.chat_class.plamoAPI.plamo_v_nick_name.lower()] = ' ' + self.chat_class.plamoAPI.plamo_v_nick_name
                if self.chat_class.plamoAPI.plamo_x_enable and self.chat_class.plamoAPI.plamo_x_nick_name:
                    models[self.chat_class.plamoAPI.plamo_x_nick_name.lower()] = ' ' + self.chat_class.plamoAPI.plamo_x_nick_name

        return models

    async def get_subai_info_all(self):
        """
        すべてのサブAIの情報を返す。
        """
        if (self.data is None):
            return JSONResponse(content={})
        
        return JSONResponse(content=self.data.subai_info)

    async def get_subai_statuses_all(self):
        """
        すべてのサブAIのステータスとニックネームを返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        subai_status = {port: {'status': info['status'], 'nick_name': info['nick_name'], 'upd_time': info['upd_time']} for port, info in self.data.subai_info.items()}
        return JSONResponse(content=subai_status)

    async def get_sessions_all(self, user_id: str):
        """
        すべての結果を返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        with self.thread_lock:
            current_time = datetime.datetime.now()
            sessions_to_delete = [
                key for key, value in self.data.subai_sessions_all.items()
                if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_SESSIONS_SEC
            ]
            for key in sessions_to_delete:
                del self.data.subai_sessions_all[key]
        return JSONResponse(content=self.data.subai_sessions_all)

    async def get_sessions_port(self, user_id: str, from_port: str):
        """
        ポート指定で、結果を返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        result = {}
        with self.thread_lock:
            for key, value in self.data.subai_sessions_all.items():
                if (value['user_id'] == user_id) and (value['from_port'] == from_port):
                    result[key] = value
            if (len(result) == 0):
                current_time = datetime.datetime.now()
                sessions_to_delete = [
                    key for key, value in self.data.subai_sessions_all.items()
                    if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_SESSIONS_SEC
                ]
                for key in sessions_to_delete:
                    del self.data.subai_sessions_all[key]
        return JSONResponse(content=result)

    async def get_histories_all(self, user_id: str):
        """
        すべての結果を返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        with self.thread_lock:
            current_time = datetime.datetime.now()
            histories_to_delete = [
                key for key, value in self.data.subai_histories_all.items()
                if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_HISTORIES_SEC
            ]
            for key in histories_to_delete:
                del self.data.subai_histories_all[key]
        return JSONResponse(content=self.data.subai_histories_all)

    async def get_debug_log_all(self, user_id: str):
        """
        すべてのデバッグログを返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        with self.thread_lock:
            current_time = datetime.datetime.now()
            debug_log_to_delete = [
                key for key, value in self.data.subai_debug_log_all.items()
                if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_DEBUGLOG_SEC
            ]
            for key in debug_log_to_delete:
                del self.data.subai_debug_log_all[key]
        return JSONResponse(content=self.data.subai_debug_log_all)

    async def get_input_log_user(self, user_id: str):
        """
        最新の1件の入力ログを返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        result = self.last_input_log_user
        result_hit = False
        with self.thread_lock:
            now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            for key, value in self.data.subai_input_log_all.items():
                if (value['user_id'] == user_id):
                    if (value['dsp_time'] == None):
                        result = {}
                        result['system_text'] = ''
                        result['request_text'] = ''
                        result['input_text'] = ''
                        if value['sys_text'] is not None:
                            result['system_text'] = value['sys_text']
                        if value['req_text'] is not None:
                            result['request_text'] = value['req_text']
                        if value['inp_text'] is not None:
                            result['input_text'] = value['inp_text']
                        value['dsp_time'] = now_time
                        self.last_input_log_user = result
                        result_hit = True
            # 応答なしの合間に古いデータ削除
            if (result_hit == False):
                current_time = datetime.datetime.now()
                # input log 整理
                input_log_to_delete = [
                    key for key, value in self.data.subai_input_log_all.items()
                    if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_INPUTLOG_SEC
                ]
                for key in input_log_to_delete:
                    del self.data.subai_input_log_all[key]
        return JSONResponse(content=result)

    async def get_output_log_user(self, user_id: str):
        """
        最新の1件の出力ログを返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        result = self.last_output_log_user
        result_hit = False
        with self.thread_lock:
            now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            for key, value in self.data.subai_output_log_all.items():
                if (value['user_id'] == user_id):
                    if (value['dsp_time'] == None):
                        result = {}
                        result['output_text'] = ''
                        result['output_data'] = ''
                        if value['out_text'] is not None:
                            result['output_text'] = value['out_text']
                        if value['out_data'] is not None:
                            result['output_data'] = value['out_data']
                        value['dsp_time'] = now_time
                        self.last_output_log_user = result
                        result_hit = True
            # 応答なしの合間に古いデータ削除
            if (result_hit == False):
                current_time = datetime.datetime.now()
                # output log 整理
                output_log_to_delete = [
                    key for key, value in self.data.subai_output_log_all.items()
                    if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_OUTPUTLOG_SEC
                ]
                for key in output_log_to_delete:
                    del self.data.subai_output_log_all[key]
                # histories 整理
                histories_to_delete = [
                    key for key, value in self.data.subai_histories_all.items()
                    if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_HISTORIES_SEC
                ]
                for key in histories_to_delete:
                    del self.data.subai_histories_all[key]
        return JSONResponse(content=result)

    async def get_debug_log_user(self, user_id: str):
        """
        最新の1件のデバッグログを返す。
        """
        if (self.data is None):
            return JSONResponse(content={})

        result = self.last_debug_log_user
        result_hit = False
        with self.thread_lock:
            now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            for key, value in self.data.subai_debug_log_all.items():
                if (value['user_id'] == user_id):
                    if (value['dsp_time'] == None):
                        result = {}
                        result['debug_text'] = ''
                        result['debug_data'] = ''
                        if value['out_text'] is not None:
                            result['debug_text'] = value['out_text']
                        if value['out_data'] is not None:
                            result['debug_data'] = value['out_data']
                        value['dsp_time'] = now_time
                        self.last_debug_log_user = result
                        result_hit = True
            # 応答なしの合間に古いデータ削除
            if (result_hit == False):
                current_time = datetime.datetime.now()
                debug_log_to_delete = [
                    key for key, value in self.data.subai_debug_log_all.items()
                    if (current_time - datetime.datetime.strptime(value['upd_time'], "%Y/%m/%d %H:%M:%S")).total_seconds() > DELETE_DEBUGLOG_SEC
                ]
                for key in debug_log_to_delete:
                    del self.data.subai_debug_log_all[key]
        return JSONResponse(content=result)

    async def post_req(self, postData: RequestMiniModel):
        """
        サブAIにリクエストを送信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = str(postData.user_id) if postData.user_id else "debug"
        from_port = str(postData.from_port) if postData.from_port else self.core_port
        to_port = str(postData.to_port) if postData.to_port else self._get_available_port()
        req_mode = str(postData.req_mode) if postData.req_mode else "chat"
        req_engine = self.data.mode_setting[req_mode]['req_engine']
        req_functions = self.data.mode_setting[req_mode]['req_functions']
        req_reset = self.data.mode_setting[req_mode]['req_reset']
        max_retry = self.data.mode_setting[req_mode]['max_retry']
        max_ai_count = self.data.mode_setting[req_mode]['max_ai_count']
        before_proc = self.data.mode_setting[req_mode]['before_proc']
        before_engine = self.data.mode_setting[req_mode]['before_engine']
        after_proc = self.data.mode_setting[req_mode]['after_proc']
        after_engine = self.data.mode_setting[req_mode]['after_engine']
        check_proc = self.data.mode_setting[req_mode]['check_proc']
        check_engine = self.data.mode_setting[req_mode]['check_engine']
        system_text = postData.system_text
        request_text = postData.request_text
        input_text = postData.input_text
        file_names = postData.file_names
        result_savepath = postData.result_savepath
        result_schema = postData.result_schema

        # resetの自動設定
        if (req_reset == '') and (postData.to_port == ''):
            req_reset = 'yes,'

        # シンプル実行
        if  (req_mode in ['clip', 'voice']):
            if  ((max_retry == '') or (max_retry == '0')) \
            and (before_proc.find('profile,' ) < 0) \
            and (before_proc.find('prompt,'  ) < 0) \
            and (after_proc.find('all,'     ) < 0) \
            and (after_proc.find('summary,' ) < 0) \
            and (after_proc.find('code,'    ) < 0):

                # ローカル実行
                if (to_port is None) or (to_port == ''):
                    to_port = from_port
                local_bot_thread = threading.Thread(target=self._local_bot, 
                                                    args=(user_id, from_port, to_port, 
                                                    req_mode, req_engine,
                                                    req_functions,
                                                    system_text, request_text, input_text,
                                                    file_names, result_savepath, result_schema, ), 
                                                    daemon=True, )
                local_bot_thread.start()

                return JSONResponse(content={'message': f'Processing started on port {to_port} with request text: {request_text}', 'port': to_port})

        return self._request(   user_id=user_id, from_port=from_port, to_port=to_port, 
                                req_mode=req_mode, req_engine=req_engine,
                                req_functions=req_functions, req_reset= req_reset,
                                max_retry=max_retry, max_ai_count=max_ai_count, 
                                before_proc=before_proc, before_engine=before_engine, 
                                after_proc=after_proc, after_engine=after_engine,
                                check_proc=check_proc, check_engine=check_engine,
                                system_text=system_text, request_text=request_text, input_text=input_text,
                                file_names=file_names, result_savepath=result_savepath, result_schema=result_schema, )

    # ローカル実行
    def _local_bot(self,    user_id: str, from_port: str, to_port: str, 
                            req_mode: str, req_engine: str,
                            req_functions: str,
                            system_text: str, request_text: str, input_text: str,
                            file_names: list[str], result_savepath: str, result_schema: str, ):

        # パラメータ設定
        if True:
            if (req_functions == ''):
                req_functions = 'yes,'

        # 開始
        with self.thread_lock:
            key_val = f"{user_id}:{from_port}:{to_port}"
            now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            self.data.subai_sessions_all[key_val] = {
                "key_val": key_val,
                "user_id": user_id, "from_port": from_port, "to_post": to_port,
                "req_mode": req_mode,
                "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text, 
                "file_names": file_names, 
                "out_time": None, "out_text": None, "out_data": None,
                "status": None,
                "upd_time": now_time, "dsp_time": None, }

        # function_modules 設定
        function_modules = []
        if (req_functions == 'yes,'):
            if (self.botFunc is not None):
                function_modules = self.botFunc.function_modules

        # chatBot処理
        res_text, res_path, res_files, res_name, res_api, self.history = \
            self.chat_class.chatBot(    req_mode=req_mode, engine=req_engine,
                                        chat_class='auto', model_select='auto', session_id=self.self_port, 
                                        history=self.history, function_modules=function_modules,
                                        sysText=system_text, reqText=request_text, inpText=input_text,
                                        filePath=file_names, inpLang='ja', outLang='ja', )
        if (res_path is None):
            res_path = ''

        output_text = ''
        output_text += f"[ASSISTANT] ({ self.self_port }:{ res_api }) \n"
        output_text += res_text
        output_data = output_text
        output_path = res_path
        output_files = res_files

        # 終了
        self._post_complete(    user_id=user_id, from_port=from_port, to_port=to_port,
                                req_mode=req_mode,
                                system_text=system_text, request_text=request_text, input_text=input_text,
                                result_savepath=result_savepath, result_schema=result_schema,
                                output_text=output_text, output_data=output_data,
                                output_path=output_path, output_files=output_files,
                                status='', )

        return True

    async def post_request(self, postData: RequestFullModel):
        """
        サブAIにリクエストを送信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = str(postData.user_id) if postData.user_id else "debug"
        from_port = str(postData.from_port) if postData.from_port else self.core_port
        to_port = str(postData.to_port) if postData.to_port else self._get_available_port()
        req_mode = str(postData.req_mode) if postData.req_mode else "chat"
        req_engine = str(postData.req_engine) if postData.req_engine else ""
        req_functions = str(postData.req_functions) if postData.req_functions else ""
        req_reset = str(postData.req_reset) if postData.req_reset else ""
        max_retry = str(postData.max_retry) if postData.max_retry else ""
        max_ai_count = str(postData.max_ai_count) if postData.max_ai_count else ""
        before_proc = str(postData.before_proc) if postData.before_proc else ""
        before_engine = str(postData.before_engine) if postData.before_engine else ""
        after_proc = str(postData.after_proc) if postData.after_proc else ""
        after_engine = str(postData.after_engine) if postData.after_engine else ""
        check_proc = str(postData.check_proc) if postData.check_proc else ""
        check_engine = str(postData.check_engine) if postData.check_engine else ""
        system_text = postData.system_text
        request_text = postData.request_text
        input_text = postData.input_text
        file_names = postData.file_names
        result_savepath = postData.result_savepath
        result_schema = postData.result_schema

        # resetの自動設定
        if (req_reset == '') and (postData.to_port == ''):
            req_reset = 'yes,'

        return self._request(   user_id=user_id, from_port=from_port, to_port=to_port, 
                                req_mode=req_mode, req_engine=req_engine,
                                req_functions=req_functions, req_reset= req_reset,
                                max_retry=max_retry, max_ai_count=max_ai_count, 
                                before_proc=before_proc, before_engine=before_engine, 
                                after_proc=after_proc, after_engine=after_engine,
                                check_proc=check_proc, check_engine=check_engine,
                                system_text=system_text, request_text=request_text, input_text=input_text,
                                file_names=file_names, result_savepath=result_savepath, result_schema=result_schema, )

    def _request(self,  user_id: str, from_port: str, to_port: str, 
                        req_mode: str, req_engine: str,
                        req_functions: str, req_reset: str,
                        max_retry: str, max_ai_count: str, 
                        before_proc: str, before_engine: str, 
                        after_proc: str, after_engine: str,
                        check_proc: str, check_engine: str,
                        system_text: str, request_text: str, input_text: str,
                        file_names: list[str], result_savepath: str, result_schema: str, ):
        begin_bye_flag = False
        if (request_text[:6] == 'begin,') \
        or (request_text[:4] == 'bye,'):
            begin_bye_flag = True
        """
        サブAIにリクエストを送信する内部処理。
        """
        with self.thread_lock:
            if self.data.subai_info[to_port]['status'] not in ['READY', 'SESSION']:
                raise HTTPException(status_code=503, detail=f'subai on port {to_port} is not available')
        try:
            if (self.data.subai_reset[to_port]['reset'] == 'yes,'):
                self.data.subai_reset[to_port]['reset'] = ''
                req_reset = 'yes,'
            if (req_mode == 'websearch'):
                request_text, input_text = self._web_search(request_text=request_text, input_text=input_text, )
            endpoint = self.local_endpoint.replace( f':{ self.core_port }', f':{ to_port }' )
            response = requests.post(
                endpoint + '/post_request',
                json={'user_id': user_id, 'from_port': from_port, 'to_port': to_port, 
                      'req_mode': req_mode, 'req_engine': req_engine,
                      'req_functions': req_functions, 'req_reset': req_reset,
                      'max_retry': max_retry, 'max_ai_count': max_ai_count, 
                      'before_proc': before_proc, 'before_engine': before_engine, 
                      'after_proc': after_proc, 'after_engine': after_engine,
                      'check_proc': check_proc, 'check_engine': check_engine,
                      'system_text': system_text, 'request_text': request_text, 'input_text': input_text,
                      'file_names': file_names, 'result_savepath': result_savepath, 'result_schema': result_schema, },
                timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
            )
            if response.status_code == 200:
                with self.thread_lock:
                    self.data.subai_reset[to_port]['reset'] = ''
                    if (req_mode not in ['serial', 'parallel', 'session']):
                        self.data.subai_info[to_port]['status'] = 'CHAT'
                    else:
                        self.data.subai_info[to_port]['status'] = req_mode.upper()
                    self.data.subai_info[to_port]['upd_time'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    key_val = f"{user_id}:{from_port}:{to_port}"
                    now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    if (begin_bye_flag != True):
                        if (from_port == self.core_port):
                            self.data.subai_input_log_key += 1
                            self.data.subai_input_log_all[self.data.subai_input_log_key] = {
                                    "user_id": user_id, "from_port": from_port, "to_post": to_port,
                                    "req_mode": req_mode,
                                    "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text,
                                    "upd_time": now_time, "dsp_time": None, }
                            self.data.subai_output_log_key += 1
                            self.data.subai_output_log_all[self.data.subai_output_log_key] = {
                                    "key_val": key_val,
                                    "user_id": user_id, "from_port": from_port, "to_post": to_port,
                                    "req_mode": req_mode,
                                    "out_time": now_time, "out_text": '... Now Processing ...', "out_data": '... Now Processing ...',
                                    "status": None,
                                    "upd_time": now_time, "dsp_time": None, }
                        self.data.subai_sessions_all[key_val] = {
                            "key_val": key_val,
                            "user_id": user_id, "from_port": from_port, "to_post": to_port,
                            "req_mode": req_mode,
                            "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text, 
                            "file_names": file_names, 
                            "out_time": None, "out_text": None, "out_data": None,
                            "status": None,
                            "upd_time": now_time, "dsp_time": None, }
                return JSONResponse(content={'message': f'Processing started on port {to_port} with request text: {request_text}', 'port': to_port})
            else:
                qLog.log('error', self.proc_id, f"Error response ({ to_port }/post_request) : {response.status_code} - {response.text}")
                with self.thread_lock:
                    self.data.subai_info[to_port]['status'] = 'NONE'
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except Exception as e:
            qLog.log('error', self.proc_id, f"Error communicating ({ to_port }/post_request) : {e}")
            with self.thread_lock:
                self.data.subai_info[to_port]['status'] = 'NONE'
            raise HTTPException(status_code=503, detail=f'Error communicating with subai on port {to_port}')

    def _get_available_port(self):
        """
        空いているサブAIのポートを返す。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        with self.thread_lock:
            for _ in range(self.num_subais):
                port = self.random_order[self.current_order_index]
                self.current_order_index = (self.current_order_index + 1) % self.num_subais
                if self.data.subai_info[port]['status'] == 'READY':
                    return port
        raise HTTPException(status_code=503, detail='Service Unavailable')
    
    def _web_search(self, request_text: str, input_text: str, ):
        ext_module = self.addin.addin_modules.get('addin_web_search', None)
        if (ext_module is not None):
            if (ext_module['onoff'] == 'on'):
                try:
                    dic = {}
                    dic['runMode']  = self.runMode
                    dic['search_text'] = request_text
                    json_dump = json.dumps(dic, ensure_ascii=False, )
                    func_proc = ext_module['func_proc']
                    res_json  = func_proc(json_dump)
                    args_dic = json.loads(res_json)
                    text = args_dic.get('result_text')
                    if (text is not None) and (text != '') and (text != '!'):
                        input_text = input_text.rstrip() + '\n' + text
                except Exception as e:
                    print(e)
        return request_text, input_text

    async def post_complete(self, postData: ResultDataModel):
        """
        サブAIから結果を受信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = str(postData.user_id) if postData.user_id is not None else "debug"
        from_port = str(postData.from_port) if postData.from_port is not None else ""
        to_port = str(postData.to_port) if postData.to_port is not None else ""
        req_mode = str(postData.req_mode) if postData.req_mode is not None else "chat"
        system_text = postData.system_text
        request_text = postData.request_text
        input_text  = postData.input_text
        result_savepath = postData.result_savepath
        result_schema = postData.result_schema
        output_text = postData.output_text
        output_data = postData.output_data
        output_path = postData.output_path
        output_files = postData.output_files
        status = postData.status
        self._post_complete(    user_id=user_id, from_port=from_port, to_port=to_port,
                                req_mode=req_mode,
                                system_text=system_text, request_text=request_text, input_text=input_text,
                                result_savepath=result_savepath, result_schema=result_schema,
                                output_text=output_text, output_data=output_data,
                                output_path=output_path, output_files=output_files,
                                status=status, )                            
        return JSONResponse(content={'message': 'post_complete received'})

    def _post_complete(self,    user_id: str, from_port: str, to_port: str,
                                req_mode: str,
                                system_text: str, request_text: str, input_text: str,
                                result_savepath: str, result_schema: str,
                                output_text: str, output_data: str,
                                output_path: str, output_files: list[str],
                                status: str, ):
        begin_bye_flag = False
        if (output_text[:6] == 'begin,') \
        or (output_text[:4] == 'bye,'):
            begin_bye_flag = True
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if (status != ''):
            with self.thread_lock:
                self.data.subai_info[to_port]['status'] = status
                self.data.subai_info[to_port]['upd_time'] = now_time
        key_val = f"{user_id}:{from_port}:{to_port}"
        with self.thread_lock:
            if (begin_bye_flag != True):
                if (status == 'READY'):
                    self.data.subai_debug_log_key += 1
                    self.data.subai_debug_log_all[self.data.subai_debug_log_key] = {
                            "key_val": key_val,
                            "user_id": user_id, "from_port": from_port, "to_post": to_port,
                            "req_mode": req_mode,
                            "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text,
                            "out_time": now_time, "out_text": output_text, "out_data": output_data,
                            "status": status,
                            "upd_time": now_time, "dsp_time": None, }
                    if (req_mode in ['chat', 'websearch', 'serial', 'parallel']):
                        self.data.subai_output_log_key += 1
                        self.data.subai_output_log_all[self.data.subai_output_log_key] = {
                                "key_val": key_val,
                                "user_id": user_id, "from_port": from_port, "to_post": to_port,
                                "req_mode": req_mode,
                                "out_time": now_time, "out_text": output_text, "out_data": output_data, 
                                "status": status,
                                "upd_time": now_time, "dsp_time": None, }
                    self.data.subai_histories_key += 1
                    self.data.subai_histories_all[self.data.subai_histories_key] = {
                                "key_val": key_val,
                                "user_id": user_id, "from_port": from_port, "to_post": to_port,
                                "req_mode": req_mode,
                                "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text,
                                "out_time": now_time, "out_text": output_text, "out_data": output_data, 
                                "status": status,
                                "upd_time": now_time, "dsp_time": None, }
                if key_val in self.data.subai_sessions_all:
                    self.data.subai_sessions_all[key_val]["out_time"] = now_time
                    self.data.subai_sessions_all[key_val]["out_text"] = output_text
                    self.data.subai_sessions_all[key_val]["out_data"] = output_data
                    self.data.subai_sessions_all[key_val]["status"]  = status
                    self.data.subai_sessions_all[key_val]["upd_time"] = now_time
                    self.data.subai_sessions_all[key_val]["dsp_time"] = None
            if key_val in self.data.subai_sessions_all:
                self.data.subai_sessions_all[key_val]["upd_time"] = now_time
   
        # 結果保存
        if (begin_bye_flag != True):
            if (self.data.addins_setting['result_text_save'] == 'yes,') \
            or (result_savepath != ''):
                to_write_proc = threading.Thread(target=self.to_write, args=(user_id, output_text, output_data, result_savepath), daemon=True, )
                to_write_proc.start()

        # 音声フィードバック
        if (begin_bye_flag != True):
            if (req_mode == 'voice'):
                to_tts_proc = threading.Thread(target=self.to_tts, args=(user_id, output_text, output_data), daemon=True, )
                to_tts_proc.start()
   
        # メモ帳コピー
        if (begin_bye_flag != True):
            if True:
                to_memo_proc = threading.Thread(target=self.to_memo, args=(user_id, output_text, output_data), daemon=True, )
                to_memo_proc.start()

        # ファイル有
        if (begin_bye_flag != True):
            if (output_path != ''):
                out_path_proc = threading.Thread(target=self.out_path, args=(user_id, output_path), daemon=True, )
                out_path_proc.start()

        return True

    def to_write(self, user_id: str, output_text: str, output_data: str, result_savepath: str, ):
        filename = ''
        if (result_savepath != ''):
            filename = qPath_output + os.path.basename(result_savepath)
        else:
            nowTime  = datetime.datetime.now()
            stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
            filename = qPath_output + stamp + '.output.txt'
        try:
            text = output_text.strip()
            if (output_data != ''):
                text = output_data.strip()
            if (text[:1] == '[') and (text.find('\n') >= 0):
                text = text[text.find('\n')+1:]
            qFunc.txtsWrite(filename, txts=[text], encoding='utf-8', exclusive=False, mode='w', )
        except Exception as e:
            print(e)

    def to_tts(self, user_id: str, output_text: str, output_data: str, ):
        ext_module = self.addin.addin_modules.get('addin_UI_TTS', None)
        if (ext_module is not None):
            if (ext_module['onoff'] == 'on'):
                try:
                    text = output_text.strip()
                    if (output_data != ''):
                        text = output_data.strip()
                    if (text[:1] == '[') and (text.find('\n') >= 0):
                        text = text[text.find('\n')+1:]
                    if (len(text) >= 2) and (len(text) <= 100):
                        nowTime  = datetime.datetime.now()
                        stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
                        filename = qPath_tts + stamp + '.coreai_tts.txt'
                        qFunc.txtsWrite(filename, txts=[text], encoding='utf-8', exclusive=False, mode='w', )
                except Exception as e:
                    print(e)

    def to_memo(self, user_id: str, output_text: str, output_data: str, ):
        ext_module = self.addin.addin_modules.get('monjyu_UI_ClipnMonjyu', None)
        if (ext_module is not None):
            if (ext_module['onoff'] == 'on'):
                try:
                    dic = {}
                    dic['runMode']  = self.runMode
                    dic['userId']   = user_id
                    dic['sendText'] = output_text
                    if (output_data != ''):
                        dic['sendText'] = output_data
                    json_dump = json.dumps(dic, ensure_ascii=False, )
                    func_proc = ext_module['func_proc']
                    res_json  = func_proc(json_dump)
                except Exception as e:
                    print(e)

    def out_path(self, user_id: str, output_path: str, ):
        if (output_path.lower()[-4:] == '.zip'):
            # 自動サンドボックス
            ext_module = self.addin.addin_modules.get('addin_autoSandbox', None)
            if (ext_module is not None):
                res_json = None
                try:
                    if (ext_module['onoff'] == 'on'):
                        dic = {}
                        dic['file_path'] = output_path
                        dic['browser'] = "no"
                        json_dump = json.dumps(dic, ensure_ascii=False, )
                        func_proc = ext_module['func_proc']
                        res_json  = func_proc(json_dump)
                except Exception as e:
                    print(e)
                    res_json = None

    async def post_debug_log(self, postData: ResultDataModel):
        """
        サブAIから途中経過を受信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = str(postData.user_id) if postData.user_id is not None else "debug"
        from_port = str(postData.from_port) if postData.from_port is not None else ""
        to_port = str(postData.to_port) if postData.to_port is not None else ""
        req_mode = str(postData.req_mode) if postData.req_mode is not None else "chat"
        system_text = postData.system_text
        request_text = postData.request_text
        input_text  = postData.input_text
        result_savepath = postData.result_savepath
        result_schema = postData.result_schema
        output_text = postData.output_text
        output_data = postData.output_data
        status = postData.status
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        with self.thread_lock:
            self.data.subai_info[to_port]['upd_time'] = now_time
        key_val = f"{user_id}:{from_port}:{to_port}"
        with self.thread_lock:
            self.data.subai_debug_log_key += 1
            self.data.subai_debug_log_all[self.data.subai_debug_log_key] = {
                    "key_val": key_val,
                    "user_id": user_id, "from_port": from_port, "to_post": to_port,
                    "req_mode": req_mode,
                    "inp_time": now_time, "sys_text": system_text, "req_text": request_text, "inp_text": input_text,
                    "out_time": now_time, "out_text": output_text, "out_data": output_data,
                    "status": status,
                    "upd_time": now_time, "dsp_time": None, }
            if key_val in self.data.subai_sessions_all:
                self.data.subai_sessions_all[key_val]["upd_time"] = now_time
        return JSONResponse(content={'message': 'post_debug_log received'})

    async def post_reset(self, postData: UserIdModel):
        """
        全サブAIのリセットを送信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = postData.user_id
        # 表示消去
        self.history = []
        self._text_clear(user_id=user_id, req_mode='RESET')
        # コアAI CANCEL 処理
        self.chat_class.bot_cancel_request = True
        # リセット設定
        if (self.data is not None):
            self.data.reset(user_id=user_id)
        return JSONResponse(content={'message': 'post_reset successfully'})

    async def post_cancel(self, postData: UserIdModel):
        """
        サブAIのキャンセルを送信する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = postData.user_id
        # コアAI CANCEL 処理
        self.chat_class.bot_cancel_request = True
        # サブAI CANCEL 処理
        if (self.data is not None):
            self.data.cancel(user_id=user_id)
        return JSONResponse(content={'message': 'post_cancel successfully'})

    async def post_clear(self, postData: UserIdModel):
        """
        表示内容をクリアする。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = postData.user_id
        # 表示消去
        self._text_clear(user_id=user_id, req_mode='CLEAR')
        return JSONResponse(content={'message': 'post_clear successfully'})

    async def post_input_log(self, postData: InputLogModel):
        """
        input_logを更新する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = postData.user_id
        request_text = postData.request_text
        input_text = postData.input_text
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        self.data.subai_input_log_key += 1
        self.data.subai_input_log_all[self.data.subai_input_log_key] = {
                "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
                "req_mode": 'log',
                "inp_time": now_time, 
                "sys_text": 'あなたは美しい日本語を話す賢いアシスタントです。', 
                "req_text": request_text, 
                "inp_text": input_text,
                "upd_time": now_time, "dsp_time": None, }

        # 処理結果
        return JSONResponse(content={'message': 'post_input_log successfully'})

    async def post_output_log(self, postData: OutputLogModel):
        """
        output_logを更新する。
        """
        if (self.data is None):
            raise HTTPException(status_code=503, detail='Service Unavailable')

        user_id = postData.user_id
        output_text = postData.output_text
        output_data = postData.output_data
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        self.data.subai_output_log_key += 1
        self.data.subai_output_log_all[self.data.subai_output_log_key] = {
            "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
            "req_mode": 'log',
            "out_time": now_time, "out_text": output_text, "out_data": output_data,
            "status": None,
            "upd_time": now_time, "dsp_time": None, }

        # 処理結果
        return JSONResponse(content={'message': 'post_input_log successfully'})

    def _text_clear(self, user_id: str, req_mode: str):
        """
        ログと表示内容のクリア処理。
        """
        if (self.data is None):
            return False

        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # log 消去
        self.data.subai_debug_log_all = {}
        # 表示消去
        with self.thread_lock:
            if (req_mode == 'RESET'):
                self.data.subai_input_log_key += 1
                self.data.subai_input_log_all[self.data.subai_input_log_key] = {
                        "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
                        "req_mode": req_mode,
                        "inp_time": now_time, 
                        "sys_text": 'あなたは美しい日本語を話す賢いアシスタントです。', 
                        "req_text": '', 
                        "inp_text": '',
                        "upd_time": now_time, "dsp_time": None, }
            self.data.subai_output_log_key += 1
            self.data.subai_output_log_all[self.data.subai_output_log_key] = {
                "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
                "req_mode": req_mode,
                "out_time": now_time, "out_text": '', "out_data": '',
                "status": None,
                "upd_time": now_time, "dsp_time": None, }
            self.data.subai_debug_log_key += 1
            self.data.subai_debug_log_all[self.data.subai_debug_log_key] = {
                "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
                "req_mode": req_mode,
                "inp_time": now_time, "sys_text": '', "req_text": req_mode, "inp_text": '',
                "out_time": now_time, "out_text": '', "out_data": '',
                "status": '',
                "upd_time": now_time, "dsp_time": None, }
        return True

    async def post_clip_names(self, postData: postClipNamesModel):
        """
        クリップファイル名処理
        """
        user_id = str(postData.user_id) if postData.user_id else "debug"
        clip_names = postData.clip_names

        input_text = ''
        for clip_file in clip_names:
            if (self.data is None):
                input_text += clip_file + '\n'

            else:
                _, ext = os.path.splitext(clip_file)

                # url 処理
                if (clip_file[:7] == 'http://') or (clip_file[:8] == 'https://'):
                    if (self.data.addins_setting['text_url_execute'] != 'no,'):

                        ext_module = self.addin.addin_modules.get('addin_url', None)
                        if (ext_module is not None):
                            if (ext_module['onoff'] == 'on'):
                                try:
                                    dic = {}
                                    dic['runMode']   = self.runMode
                                    dic['url_path'] = clip_file
                                    json_dump = json.dumps(dic, ensure_ascii=False, )
                                    func_proc = ext_module['func_proc']
                                    res_json  = func_proc(json_dump)
                                    res_dic   = json.loads(res_json)
                                    res_text  = res_dic.get('result_text')
                                    if (res_text is not None) and (res_text != '') and (res_text != '!'):
                                        input_text += "''' " + clip_file + "\n"
                                        input_text += res_text.rstrip() + "\n"
                                        input_text += "'''\n"
                                except Exception as e:
                                    #print(e)
                                    pass

                else:

                    # pdf 処理
                    if  (ext.lower() in ['.pdf']) \
                    and (self.data.addins_setting['text_pdf_execute'] != 'no,'):

                        ext_module = self.addin.addin_modules.get('addin_pdf', None)
                        if (ext_module is not None):
                            if (ext_module['onoff'] == 'on'):
                                try:
                                    dic = {}
                                    dic['runMode']   = self.runMode
                                    dic['file_path'] = clip_file
                                    json_dump = json.dumps(dic, ensure_ascii=False, )
                                    func_proc = ext_module['func_proc']
                                    res_json  = func_proc(json_dump)
                                    res_dic   = json.loads(res_json)
                                    res_text  = res_dic.get('result_text')
                                    if (res_text is not None) and (res_text != '') and (res_text != '!'):
                                        input_text += "''' " + os.path.basename(clip_file) + "\n"
                                        input_text += res_text.rstrip() + "\n"
                                        input_text += "'''\n"
                                except Exception as e:
                                    #print(e)
                                    pass

                    # ocr 処理
                    if  (ext.lower() in ['.png', '.jpg']) \
                    and (self.data.addins_setting['image_ocr_execute'] != 'no,'):

                        ext_module = self.addin.addin_modules.get('addin_ocr', None)
                        if (ext_module is not None):
                            if (ext_module['onoff'] == 'on'):
                                try:
                                    dic = {}
                                    dic['runMode']   = self.runMode
                                    dic['file_path'] = clip_file
                                    json_dump = json.dumps(dic, ensure_ascii=False, )
                                    func_proc = ext_module['func_proc']
                                    res_json  = func_proc(json_dump)
                                    res_dic   = json.loads(res_json)
                                    res_text  = res_dic.get('result_text')
                                    if (res_text is not None) and (res_text != '') and (res_text != '!'):
                                        input_text += "''' [OCR] " + os.path.basename(clip_file) + "\n"
                                        input_text += res_text.rstrip() + "\n"
                                        input_text += "'''\n"
                                except Exception as e:
                                    #print(e)
                                    pass

                    # yolo 処理
                    if  (ext.lower() in ['.png', '.jpg']) \
                    and (self.data.addins_setting['image_yolo_execute'] == 'yes,'):

                        ext_module = self.addin.addin_modules.get('addin_yolo', None)
                        if (ext_module is not None):
                            if (ext_module['onoff'] == 'on'):
                                try:
                                    dic = {}
                                    dic['runMode']   = self.runMode
                                    dic['file_path'] = clip_file
                                    json_dump = json.dumps(dic, ensure_ascii=False, )
                                    func_proc = ext_module['func_proc']
                                    res_json  = func_proc(json_dump)
                                    res_dic   = json.loads(res_json)
                                    json_str  = res_dic['result_text']
                                    res_text  = ''
                                    if (json_str is not None):
                                        res_val = json.loads(json_str)
                                        for key, val in res_val.items():
                                            res_text += key + ': ' + val + '\n'
                                    if (res_text != ''):
                                        input_text += "''' [YOLO] " + os.path.basename(clip_file) + "\n"
                                        input_text += res_text.rstrip() + "\n"
                                        input_text += "'''\n"
                                except Exception as e:
                                    #print(e)
                                    pass

        if (input_text != ''):
            self._clip_text(user_id=user_id, clip_text=input_text, )

        return JSONResponse(content={'message': 'post_clip_names successfully'})

    async def post_clip_text(self, postData: postClipTextModel):
        """
        クリップテキスト処理
        """
        user_id = str(postData.user_id) if postData.user_id else "debug"
        clip_text = postData.clip_text
        
        if (self.data is not None):
            if (self.data.addins_setting['text_clip_input'] == 'yes,'):
                self._clip_text(user_id=user_id, clip_text=clip_text, )

        return JSONResponse(content={'message': 'post_clip_text successfully'})

    def _clip_text(self, user_id: str, clip_text: str):
        now_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        with self.thread_lock:
            self.data.subai_input_log_key += 1
            self.data.subai_input_log_all[self.data.subai_input_log_key] = {
                    "user_id": user_id, "from_port": self.core_port, "to_post": self.core_port,
                    "req_mode": 'clip',
                    "inp_time": now_time, 
                    "sys_text": 'same,', 
                    "req_text": 'same,', 
                    "inp_text": clip_text,
                    "upd_time": now_time, "dsp_time": None, }
        return True

    def run(self):
        """
        サーバー設定と起動
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # フロントエンドのオリジンを指定
            allow_credentials=True,
            allow_methods=["*"],  # すべてのHTTPメソッドを許可
            allow_headers=["*"],  # すべてのヘッダーを許可
        )
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=int(self.self_port),
            log_level="error",
            access_log=False
        )

        

if __name__ == '__main__':
    core_port = '8000'
    sub_base  = '8100'
    numSubAIs = '48'

    coreai = CoreAiProcess( runMode='debug', qLog_fn='', 
                            core_port=core_port, sub_base=sub_base, num_subais=numSubAIs)

    #while True:
    #    time.sleep(5)

