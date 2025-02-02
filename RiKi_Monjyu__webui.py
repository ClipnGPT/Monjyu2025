#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/konsan1101
# Thank you for keeping the rules.
# ------------------------------------------------

# RiKi_Monjyu__webui.py

import sys
import os
import time
import datetime
import codecs
import glob
import shutil

import requests
import json
import re

from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from fastapi import Form
from typing import List
import uvicorn
from pydantic import BaseModel
import chardet

import threading
import base64
import socket
qHOSTNAME = socket.gethostname().lower()

# 各種ディレクトリパスの設定
qPath_temp   = 'temp/'
qPath_log    = 'temp/_log/'
qPath_input  = 'temp/input/'
qPath_output = 'temp/output/'
qPath_tts    = 'temp/s6_5tts_txt/'
qPath_reacts = '_datas/reacts/'
qPath_templates = '_webui/monjyu'
qPath_static    = '_webui/monjyu/static'
DEFAULT_ICON    = qPath_static + '/' + "icon_monjyu.png"

# 共通ルーチンのインポートと初期化
import _v6__qLog
qLog = _v6__qLog.qLog_class()
import  _v6__qFunc
qFunc = _v6__qFunc.qFunc_class()

# 定数の定義
CONNECTION_TIMEOUT = 15  # 接続タイムアウト設定
REQUEST_TIMEOUT = 30     # 要求タイムアウト設定
LIST_RESULT_LIMITSEC = 1800  # ファイルリストの制限時間
LIST_RESULT_AUTOCHECK = 120  # 自動チェックの時間

# ユーザーIDモデル
class UserIdModel(BaseModel):
    user_id: str

# モード別設定データモデル
class postModeDataModel(BaseModel):
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

# Addins設定データモデル
class postAddinsDataModel(BaseModel):
    result_text_save: str
    speech_tts_engine: str
    speech_stt_engine: str
    text_clip_input: str
    text_url_execute: str
    text_pdf_execute: str
    image_ocr_execute: str
    image_yolo_execute: str

# エンジン設定データモデル
class postEngineSettingDataModel(BaseModel):
    engine: str
    max_wait_sec: str
    a_model: str
    a_use_tools: str
    b_model: str
    b_use_tools: str
    v_model: str
    v_use_tools: str
    x_model: str
    x_use_tools: str

# Live設定データモデル
class postLiveDataModel(BaseModel):
    engine: str
    voice: str
    shot_interval_sec: str
    clip_interval_sec: str

# webAgent engine設定データモデル
class postWebAgentEngine(BaseModel):
    useBrowser: str
    modelAPI: str

# webAgent setting設定データモデル
class postWebAgentSetting(BaseModel):
    modelAPI: str
    modelName: str
    maxSteps: str

# 音声入力項目モデル
class sttFieldModel(BaseModel):
    field: str

# 音声合成文字列モデル
class ttsTextModel(BaseModel):
    speech_text: str

# speech json 文字列モデル
class speechJsonModel(BaseModel):
    speech_json: str
    speaker_male1: str
    speaker_male2: str
    speaker_female1: str
    speaker_female2: str
    speaker_etc: str
    tts_yesno: str

# set react json 文字列モデル
class setReactModel(BaseModel):
    filename: str

class WebUiProcess:
    """
    Web UIプロセスの管理クラス
    """
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None, data=None, addin=None, botFunc=None,
                        coreai=None,
                        core_port: str = '8000', sub_base: str = '8100', num_subais: str = '48', 
                        self_port: str = '8008'):

        # Web UIクラスのインスタンス化とスレッドの開始
        webui_class = WebUiClass(   runMode=runMode, qLog_fn=qLog_fn,
                                    main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                    coreai=coreai,
                                    core_port=core_port, sub_base=sub_base, num_subais=num_subais, 
                                    self_port=self_port, )
        webui_thread = threading.Thread(target=webui_class.run)
        webui_thread.daemon = True
        webui_thread.start()

        # 永続的な実行
        while True:
            time.sleep(5)

class WebUiClass:
    """
    ウェブUIクラス
    """
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None, data=None, addin=None, botFunc=None,
                        coreai=None,
                        core_port: str = '8000', sub_base: str = '8100', num_subais: str = '48', 
                        self_port: str = '8008', ):
        self.runMode = runMode

        # ログ設定
        self.proc_name = f"{ self_port }:ui"
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
        self.data      = data
        self.addin     = addin
        self.botFunc   = botFunc
        self.coreai    = coreai
        self.core_port = core_port
        self.sub_base  = sub_base
        self.self_port = self_port
        self.num_subais = int(num_subais)
        self.local_endpoint = f'http://localhost:{ self.core_port }'
        self.core_endpoint = self.local_endpoint.replace('localhost', qHOSTNAME)

        # スレッドロックの初期化
        self.thread_lock = threading.Lock()

        # 送信処理用の初期化
        self.next_image_file = None
        self.last_input_files = []
        self.last_output_files = []

        # FastAPIの設定
        self.app = FastAPI()

        # APIエンドポイントの設定
        self.app.get("/")(self.root)
        self.app.get("/{filename}.html")(self.html_serve)
        self.app.get("/get_mode_setting")(self.get_mode_setting)
        self.app.post("/post_mode_setting")(self.post_mode_setting)
        self.app.get("/get_engine_models")(self.get_engine_models)
        self.app.get("/get_engine_setting")(self.get_engine_setting)
        self.app.post("/post_engine_setting")(self.post_engine_setting)
        self.app.get("/get_addins_setting")(self.get_addins_setting)
        self.app.post("/post_addins_setting")(self.post_addins_setting)
        self.app.get("/get_live_voices")(self.get_live_voices)
        self.app.get("/get_live_setting")(self.get_live_setting)
        self.app.post("/post_live_setting")(self.post_live_setting)
        self.app.get("/get_webAgent_engine")(self.get_webAgent_engine)
        self.app.get("/get_webAgent_setting")(self.get_webAgent_setting)
        self.app.post("/post_webAgent_engine")(self.post_webAgent_engine)
        self.app.post("/post_webAgent_setting")(self.post_webAgent_setting)
        self.app.get("/get_default_image")(self.get_default_image)
        self.app.get("/get_image_info")(self.get_image_info)
        self.app.post("/post_text_files")(self.post_text_files)
        self.app.get("/get_input_list")(self.get_input_list)
        self.app.get("/get_output_list")(self.get_output_list)
        self.app.post("/post_drop_files")(self.post_drop_files)
        self.app.get("/get_output_file/{filename}")(self.get_output_file)
        self.app.get("/get_source")(self.get_source)
        self.app.post("/post_tts_text")(self.post_tts_text)
        self.app.post("/post_tts_csv")(self.post_tts_csv)
        self.app.get("/get_stt")(self.get_stt)
        self.app.get("/get_url_to_text")(self.get_url_to_text)
        self.app.post("/post_speech_json")(self.post_speech_json)
        self.app.post("/post_set_react")(self.post_set_react)

        # テンプレートとスタティックファイルのマウント
        self.app.mount("/", StaticFiles(directory=qPath_templates), name="root")
        self.app.mount("/static", StaticFiles(directory=qPath_static), name="static")

    async def root(self, request: Request):
        return RedirectResponse(url="/index.html")

    async def html_serve(self, filename: str, request: Request):
        # HTMLファイルのパスを構築
        file_path = f"_webui/monjyu/{filename}.html"        
        # ファイルが存在するか確認
        if not os.path.isfile(file_path):
            return HTMLResponse(content="File not found", status_code=404)
        # ファイルを読み込む
        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        # コンテンツ一部書き換え
        html_content = html_content.replace("http://localhost:8000", self.core_endpoint)
        if (filename == 'statuses'):
            subai_ports = [str(port) for port in range(int(self.sub_base) + 1, int(self.sub_base) + 1 + self.num_subais)]
            subai_divs = "\n".join([f'<div class="subai NONE" id="subai-{port}">{port}<span class="tooltip"></span></div>' for port in subai_ports])
            html_content = html_content.replace("{subai_divs}", subai_divs)
        # 返信
        return HTMLResponse(content=html_content)

    async def get_mode_setting(self, req_mode: str):
        # 設定情報を返す
        if (self.data is not None):
            result = self.data.mode_setting[req_mode]
        else:
            result = {}
        return JSONResponse(content=result)

    async def post_mode_setting(self, data: postModeDataModel):
        # 設定情報を更新する
        req_mode = str(data.req_mode) if data.req_mode else ""
        req_engine = str(data.req_engine) if data.req_engine else ""
        req_functions = str(data.req_functions) if data.req_functions else ""
        req_reset = str(data.req_reset) if data.req_reset else ""
        max_retry = str(data.max_retry) if data.max_retry else ""
        max_ai_count = str(data.max_ai_count) if data.max_ai_count else ""
        before_proc = str(data.before_proc) if data.before_proc else ""
        before_engine = str(data.before_engine) if data.before_engine else ""
        after_proc = str(data.after_proc) if data.after_proc else ""
        after_engine = str(data.after_engine) if data.after_engine else ""
        check_proc = str(data.check_proc) if data.check_proc else ""
        check_engine = str(data.check_engine) if data.check_engine else ""
        if (self.data is not None):
            self.data.mode_setting[req_mode] = {    "req_engine": req_engine,
                                                    "req_functions": req_functions, "req_reset": req_reset,
                                                    "max_retry": max_retry, "max_ai_count": max_ai_count,
                                                    "before_proc": before_proc, "before_engine": before_engine,
                                                    "after_proc": after_proc, "after_engine": after_engine,
                                                    "check_proc": check_proc, "check_engine": check_engine }
        return JSONResponse(content={'message': 'post_mode_setting successfully'})

    async def get_engine_models(self, engine: str) -> Dict[str, str]:
        # 設定情報を返す
        try:
            if (self.data is not None) and (self.coreai is not None):

                if (engine == 'gemini'):
                    if (len(self.data.engine_models['gemini']) != len(self.coreai.chat_class.geminiAPI.models)):
                        self.data.engine_models['gemini'] = {}
                        for key,value in self.coreai.chat_class.geminiAPI.models.items():
                            self.data.engine_models['gemini'][key]      = self.coreai.chat_class.geminiAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.geminiAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.geminiAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.geminiAPI.models[key]["modality"] + ", "

                elif (engine == 'freeai'):
                    if (len(self.data.engine_models['freeai']) != len(self.coreai.chat_class.freeaiAPI.models)):
                        self.data.engine_models['freeai'] = {}
                        for key,value in self.coreai.chat_class.freeaiAPI.models.items():
                            self.data.engine_models['freeai'][key]      = self.coreai.chat_class.freeaiAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.freeaiAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.freeaiAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.freeaiAPI.models[key]["modality"] + ", "

                elif (engine == 'claude'):
                    if (len(self.data.engine_models['claude']) != len(self.coreai.chat_class.claudeAPI.models)):
                        self.data.engine_models['claude'] = {}
                        for key,value in self.coreai.chat_class.claudeAPI.models.items():
                            self.data.engine_models['claude'][key]      = self.coreai.chat_class.claudeAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.claudeAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.claudeAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.claudeAPI.models[key]["modality"] + ", "

                elif (engine == 'openrt'):
                    if (len(self.data.engine_models['openrt']) != len(self.coreai.chat_class.openrtAPI.models)):
                        self.data.engine_models['openrt'] = {}
                        for key,value in self.coreai.chat_class.openrtAPI.models.items():
                            self.data.engine_models['openrt'][key]      = self.coreai.chat_class.openrtAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.openrtAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.openrtAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.openrtAPI.models[key]["modality"] + ", "

                elif (engine == 'perplexity'):
                    if (len(self.data.engine_models['perplexity']) != len(self.coreai.chat_class.perplexityAPI.models)):
                        self.data.engine_models['perplexity'] = {}
                        for key,value in self.coreai.chat_class.perplexityAPI.models.items():
                            self.data.engine_models['perplexity'][key]  = self.coreai.chat_class.perplexityAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.perplexityAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.perplexityAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.perplexityAPI.models[key]["modality"] + ", "

                elif (engine == 'groq'):
                    if (len(self.data.engine_models['groq']) != len(self.coreai.chat_class.groqAPI.models)):
                        self.data.engine_models['groq'] = {}
                        for key,value in self.coreai.chat_class.groqAPI.models.items():
                            self.data.engine_models['groq'][key]        = self.coreai.chat_class.groqAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.groqAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.groqAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.groqAPI.models[key]["modality"] + ", "

                elif (engine == 'ollama'):
                    if (len(self.data.engine_models['ollama']) != len(self.coreai.chat_class.ollamaAPI.models)):
                        self.data.engine_models['ollama'] = {}
                        for key,value in self.coreai.chat_class.ollamaAPI.models.items():
                            self.data.engine_models['ollama'][key]      = self.coreai.chat_class.ollamaAPI.models[key]["date"] + " : " \
                                                                        + self.coreai.chat_class.ollamaAPI.models[key]["id"] + ", " \
                                                                        + str(self.coreai.chat_class.ollamaAPI.models[key]["token"]) + ", " \
                                                                        + self.coreai.chat_class.ollamaAPI.models[key]["modality"] + ", "

                result = self.data.engine_models[engine]
            else:
                result = {}

        except Exception as e:
            #print(e)
            raise HTTPException(status_code=500, detail='post_engine_models error:' + e)
        return JSONResponse(content=result)

    async def get_engine_setting(self, engine: str):
        # 設定情報を返す
        try:
            if (self.data is not None) and (self.coreai is not None):

                if (engine == 'gemini'):
                    self.data.engine_setting['gemini'] = {
                        "a_nick_name": self.coreai.chat_class.geminiAPI.gemini_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.geminiAPI.gemini_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.geminiAPI.gemini_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.geminiAPI.gemini_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.geminiAPI.gemini_max_wait_sec),
                        "a_model": self.coreai.chat_class.geminiAPI.gemini_a_model,
                        "a_use_tools": self.coreai.chat_class.geminiAPI.gemini_a_use_tools,
                        "b_model": self.coreai.chat_class.geminiAPI.gemini_b_model,
                        "b_use_tools": self.coreai.chat_class.geminiAPI.gemini_b_use_tools,
                        "v_model": self.coreai.chat_class.geminiAPI.gemini_v_model,
                        "v_use_tools": self.coreai.chat_class.geminiAPI.gemini_v_use_tools,
                        "x_model": self.coreai.chat_class.geminiAPI.gemini_x_model,
                        "x_use_tools": self.coreai.chat_class.geminiAPI.gemini_x_use_tools,
                    }

                elif (engine == 'freeai'):
                    self.data.engine_setting['freeai'] = {
                        "a_nick_name": self.coreai.chat_class.freeaiAPI.freeai_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.freeaiAPI.freeai_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.freeaiAPI.freeai_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.freeaiAPI.freeai_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.freeaiAPI.freeai_max_wait_sec),
                        "a_model": self.coreai.chat_class.freeaiAPI.freeai_a_model,
                        "a_use_tools": self.coreai.chat_class.freeaiAPI.freeai_a_use_tools,
                        "b_model": self.coreai.chat_class.freeaiAPI.freeai_b_model,
                        "b_use_tools": self.coreai.chat_class.freeaiAPI.freeai_b_use_tools,
                        "v_model": self.coreai.chat_class.freeaiAPI.freeai_v_model,
                        "v_use_tools": self.coreai.chat_class.freeaiAPI.freeai_v_use_tools,
                        "x_model": self.coreai.chat_class.freeaiAPI.freeai_x_model,
                        "x_use_tools": self.coreai.chat_class.freeaiAPI.freeai_x_use_tools,
                    }

                elif (engine == 'claude'):
                    self.data.engine_setting['claude'] = {
                        "a_nick_name": self.coreai.chat_class.claudeAPI.claude_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.claudeAPI.claude_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.claudeAPI.claude_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.claudeAPI.claude_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.claudeAPI.claude_max_wait_sec),
                        "a_model": self.coreai.chat_class.claudeAPI.claude_a_model,
                        "a_use_tools": self.coreai.chat_class.claudeAPI.claude_a_use_tools,
                        "b_model": self.coreai.chat_class.claudeAPI.claude_b_model,
                        "b_use_tools": self.coreai.chat_class.claudeAPI.claude_b_use_tools,
                        "v_model": self.coreai.chat_class.claudeAPI.claude_v_model,
                        "v_use_tools": self.coreai.chat_class.claudeAPI.claude_v_use_tools,
                        "x_model": self.coreai.chat_class.claudeAPI.claude_x_model,
                        "x_use_tools": self.coreai.chat_class.claudeAPI.claude_x_use_tools,
                    }

                elif (engine == 'openrt'):
                    self.data.engine_setting['openrt'] = {
                        "a_nick_name": self.coreai.chat_class.openrtAPI.openrt_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.openrtAPI.openrt_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.openrtAPI.openrt_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.openrtAPI.openrt_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.openrtAPI.openrt_max_wait_sec),
                        "a_model": self.coreai.chat_class.openrtAPI.openrt_a_model,
                        "a_use_tools": self.coreai.chat_class.openrtAPI.openrt_a_use_tools,
                        "b_model": self.coreai.chat_class.openrtAPI.openrt_b_model,
                        "b_use_tools": self.coreai.chat_class.openrtAPI.openrt_b_use_tools,
                        "v_model": self.coreai.chat_class.openrtAPI.openrt_v_model,
                        "v_use_tools": self.coreai.chat_class.openrtAPI.openrt_v_use_tools,
                        "x_model": self.coreai.chat_class.openrtAPI.openrt_x_model,
                        "x_use_tools": self.coreai.chat_class.openrtAPI.openrt_x_use_tools,
                    }

                elif (engine == 'perplexity'):
                    self.data.engine_setting['perplexity'] = {
                        "a_nick_name": self.coreai.chat_class.perplexityAPI.perplexity_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.perplexityAPI.perplexity_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.perplexityAPI.perplexity_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.perplexityAPI.perplexity_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.perplexityAPI.perplexity_max_wait_sec),
                        "a_model": self.coreai.chat_class.perplexityAPI.perplexity_a_model,
                        "a_use_tools": self.coreai.chat_class.perplexityAPI.perplexity_a_use_tools,
                        "b_model": self.coreai.chat_class.perplexityAPI.perplexity_b_model,
                        "b_use_tools": self.coreai.chat_class.perplexityAPI.perplexity_b_use_tools,
                        "v_model": self.coreai.chat_class.perplexityAPI.perplexity_v_model,
                        "v_use_tools": self.coreai.chat_class.perplexityAPI.perplexity_v_use_tools,
                        "x_model": self.coreai.chat_class.perplexityAPI.perplexity_x_model,
                        "x_use_tools": self.coreai.chat_class.perplexityAPI.perplexity_x_use_tools,
                    }

                elif (engine == 'groq'):
                    self.data.engine_setting['groq'] = {
                        "a_nick_name": self.coreai.chat_class.groqAPI.groq_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.groqAPI.groq_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.groqAPI.groq_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.groqAPI.groq_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.groqAPI.groq_max_wait_sec),
                        "a_model": self.coreai.chat_class.groqAPI.groq_a_model,
                        "a_use_tools": self.coreai.chat_class.groqAPI.groq_a_use_tools,
                        "b_model": self.coreai.chat_class.groqAPI.groq_b_model,
                        "b_use_tools": self.coreai.chat_class.groqAPI.groq_b_use_tools,
                        "v_model": self.coreai.chat_class.groqAPI.groq_v_model,
                        "v_use_tools": self.coreai.chat_class.groqAPI.groq_v_use_tools,
                        "x_model": self.coreai.chat_class.groqAPI.groq_x_model,
                        "x_use_tools": self.coreai.chat_class.groqAPI.groq_x_use_tools,
                    }

                elif (engine == 'ollama'):
                    self.data.engine_setting['ollama'] = {
                        "a_nick_name": self.coreai.chat_class.ollamaAPI.ollama_a_nick_name,
                        "b_nick_name": self.coreai.chat_class.ollamaAPI.ollama_b_nick_name,
                        "v_nick_name": self.coreai.chat_class.ollamaAPI.ollama_v_nick_name,
                        "x_nick_name": self.coreai.chat_class.ollamaAPI.ollama_x_nick_name,
                        "max_wait_sec": str(self.coreai.chat_class.ollamaAPI.ollama_max_wait_sec),
                        "a_model": self.coreai.chat_class.ollamaAPI.ollama_a_model,
                        "a_use_tools": self.coreai.chat_class.ollamaAPI.ollama_a_use_tools,
                        "b_model": self.coreai.chat_class.ollamaAPI.ollama_b_model,
                        "b_use_tools": self.coreai.chat_class.ollamaAPI.ollama_b_use_tools,
                        "v_model": self.coreai.chat_class.ollamaAPI.ollama_v_model,
                        "v_use_tools": self.coreai.chat_class.ollamaAPI.ollama_v_use_tools,
                        "x_model": self.coreai.chat_class.ollamaAPI.ollama_x_model,
                        "x_use_tools": self.coreai.chat_class.ollamaAPI.ollama_x_use_tools,
                    }

                result = self.data.engine_setting[engine]
            else:
                result = {}

        except Exception as e:
            #print(e)
            raise HTTPException(status_code=500, detail='get_engine_setting error:' + str(e))
        return JSONResponse(content=result)

    async def post_engine_setting(self, data: postEngineSettingDataModel):
        # 設定情報を更新する
        engine = str(data.engine) if data.engine else ""
        max_wait_sec = str(data.max_wait_sec) if data.max_wait_sec else ""
        a_model = str(data.a_model) if data.a_model else ""
        a_use_tools = str(data.a_use_tools) if data.a_use_tools else ""
        b_model = str(data.b_model) if data.b_model else ""
        b_use_tools = str(data.b_use_tools) if data.b_use_tools else ""
        v_model = str(data.v_model) if data.v_model else ""
        v_use_tools = str(data.v_use_tools) if data.v_use_tools else ""
        x_model = str(data.x_model) if data.x_model else ""
        x_use_tools = str(data.x_use_tools) if data.x_use_tools else ""
        try:
            if (self.data is not None):
                self.data.engine_setting[engine] = {"max_wait_sec": str(max_wait_sec),
                                                    "a_model": a_model, "a_use_tools": a_use_tools,
                                                    "b_model": b_model, "b_use_tools": b_use_tools,
                                                    "v_model": v_model, "v_use_tools": v_use_tools,
                                                    "x_model": x_model, "x_use_tools": x_use_tools, }
                if (self.coreai is not None):

                    if (engine == 'gemini'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.geminiAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'freeai'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.freeaiAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'claude'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.claudeAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'openrt'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.openrtAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'perplexity'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.perplexityAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'groq'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.groqAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

                    elif (engine == 'ollama'):
                        engine_set_thread = threading.Thread(
                            target=self.coreai.chat_class.ollamaAPI.set_models,
                            args=(max_wait_sec, a_model, a_use_tools, b_model, b_use_tools,
                                                v_model, v_use_tools, x_model, x_use_tools, ),
                            daemon=True, )
                        engine_set_thread.start()

        except Exception as e:
            #print(e)
            raise HTTPException(status_code=500, detail='post_engine_setting error:' + str(e))
        return JSONResponse(content={'message': 'post_engine_setting successfully'})

    async def get_addins_setting(self):
        # 設定情報を返す
        if (self.data is not None):
            result = self.data.addins_setting
        else:
            result = {}
        return JSONResponse(content=result)

    async def post_addins_setting(self, data: postAddinsDataModel):
        # 設定情報を更新する
        result_text_save = str(data.result_text_save) if data.result_text_save else ""
        speech_tts_engine = str(data.speech_tts_engine) if data.speech_tts_engine else ""
        speech_stt_engine = str(data.speech_stt_engine) if data.speech_stt_engine else ""
        text_clip_input = str(data.text_clip_input) if data.text_clip_input else ""
        text_url_execute = str(data.text_url_execute) if data.text_url_execute else ""
        text_pdf_execute = str(data.text_pdf_execute) if data.text_pdf_execute else ""
        image_ocr_execute = str(data.image_ocr_execute) if data.image_ocr_execute else ""
        image_yolo_execute = str(data.image_yolo_execute) if data.image_yolo_execute else ""
        if (self.data is not None):
            self.data.addins_setting = {"result_text_save": result_text_save,
                                        "speech_tts_engine": speech_tts_engine,
                                        "speech_stt_engine": speech_stt_engine, 
                                        "text_clip_input": text_clip_input, 
                                        "text_url_execute": text_url_execute, 
                                        "text_pdf_execute": text_pdf_execute, 
                                        "image_ocr_execute": image_ocr_execute, 
                                        "image_yolo_execute": image_yolo_execute, }
        return JSONResponse(content={'message': 'post_addins_setting successfully'})

    async def get_live_voices(self, engine: str) -> Dict[str, str]:
        # 設定情報を返す
        if (self.data is not None):
            result = self.data.live_voices[engine]
        else:
            result = {}
        return JSONResponse(content=result)

    async def get_live_setting(self, engine: str):
        # 設定情報を返す
        if (self.data is not None):
            result = self.data.live_setting[engine]
        else:
            result = {}
        return JSONResponse(content=result)

    async def post_live_setting(self, data: postLiveDataModel):
        # 設定情報を更新する
        engine = str(data.engine) if data.engine else ""
        voice = str(data.voice) if data.voice else ""
        shot_interval_sec = str(data.shot_interval_sec) if data.shot_interval_sec else ""
        clip_interval_sec = str(data.clip_interval_sec) if data.clip_interval_sec else ""
        if (self.data is not None):
            self.data.live_setting[engine] = {  "voice": voice,
                                                "shot_interval_sec": shot_interval_sec,
                                                "clip_interval_sec": clip_interval_sec, }
        return JSONResponse(content={'message': 'post_live_setting successfully'})

    async def get_webAgent_engine(self):
        # 設定情報を返す
        useBrowser = self.data.webAgent_useBrowser
        modelAPI = self.data.webAgent_modelAPI
        modelNames = {}
        if (modelAPI != ''):
            modelNames = self.data.webAgent_modelNames[modelAPI]
        if (self.data is not None):
            result = { "useBrowser": useBrowser,
                       "modelAPI": modelAPI,
                       "modelNames": modelNames, }
        else:
            result = {}
        return JSONResponse(content=result)

    async def get_webAgent_setting(self, modelAPI: str):
        # 設定情報を返す
        modelAPI = str(modelAPI) if modelAPI else "freeai"
        if (self.data is not None):
            result = self.data.webAgent_setting[modelAPI]
        else:
            result = {}
        return JSONResponse(content=result)

    async def post_webAgent_engine(self, data: postWebAgentEngine):
        # 設定情報を更新する
        useBrowser = str(data.useBrowser) if data.useBrowser else ""
        modelAPI = str(data.modelAPI) if data.modelAPI else ""
        if (self.data is not None):
            self.data.webAgent_useBrowser = useBrowser
            self.data.webAgent_modelAPI = modelAPI
        return JSONResponse(content={'message': 'post_webAgent_engine successfully'})

    async def post_webAgent_setting(self, data: postWebAgentSetting):
        # 設定情報を更新する
        modelAPI  = str(data.modelAPI)  if data.modelAPI  else "freeai"
        modelName = str(data.modelName) if data.modelName else ""
        maxSteps  = str(data.maxSteps ) if data.maxSteps  else ""
        if (self.data is not None):
            self.data.webAgent_setting[modelAPI] = {"modelName": modelName,
                                                    "maxSteps":  maxSteps,  }
        return JSONResponse(content={'message': 'post_webAgent_setting successfully'})

    async def get_default_image(self):
        # デフォルト画像データの取得
        image_data = self._get_image_data(DEFAULT_ICON)
        return JSONResponse(content={"image_data": image_data})

    async def get_image_info(self):
        # 次回表示する画像データの取得
        image_data = None
        if (self.next_image_file is not None):
            if (self.next_image_file != ''):
                image_data = self._get_image_data(self.next_image_file)
            else:
                image_data = self._get_image_data(DEFAULT_ICON)
            self.next_image_file = None
        return JSONResponse(content={"image_data": image_data})

    def _get_image_data(self, image_path):
        # 画像ファイルをBase64エンコードしてデータURIスキーマ形式で返す
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        image_data = None
        if any(image_path.lower().endswith(ext) for ext in image_extensions):
            try:
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    image_data = f"data:image/png;base64,{encoded_string}"
            except Exception as e:
                print(e)
        return image_data

    async def post_text_files(self, drop_target: str = Form(...), files: list[UploadFile] = File(...)):
        # アップロードされた複数ファイルを解析してテキストを返す
        drop_text = ''
        for file in files:
            file_extension = file.filename.lower().split('.')[-1]
            if f".{file_extension}" in [".py", ".txt", ".html", ".json", ".bas"]:
                file_content = await file.read()
                encoding = chardet.detect(file_content)['encoding']
                text = file_content.decode(encoding)
                if (drop_target == 'system_text'):
                    drop_text += f"\n{ text.rstrip() }\n"
                else:
                    drop_text += f"\n''' { file.filename }\n{ text.rstrip() }\n'''"
        return JSONResponse(content={ "drop_text": drop_text })

    async def get_input_list(self):
        # 入力ディレクトリ内のファイル一覧を取得
        now = datetime.datetime.now()
        file_table = [
            (f, os.path.getmtime(os.path.join(qPath_input, f)))
            for f in os.listdir(qPath_input)
            if os.path.isfile(os.path.join(qPath_input, f))
        ]
        file_table.sort(key=lambda x: x[1], reverse=True)
        input_files = []
        image_file = ''
        
        checked = True # 最初の１件チェック
        for f, mod_time in file_table:
            if (now - datetime.datetime.fromtimestamp(mod_time)) < datetime.timedelta(seconds=LIST_RESULT_LIMITSEC):
                file_path = os.path.join(qPath_input, f)
                if (now - datetime.datetime.fromtimestamp(mod_time)) < datetime.timedelta(seconds=LIST_RESULT_AUTOCHECK):
                    if (image_file == ''):
                        image_file = file_path
                else:
                    checked = False
                input_files.append(
                    #f"{f} {datetime.datetime.fromtimestamp(mod_time).strftime('%Y/%m/%d %H:%M:%S')} {checked}"
                    {"file_name": f, "upd_time": datetime.datetime.fromtimestamp(mod_time).strftime('%Y/%m/%d %H:%M:%S'), "checked": checked}
                )
                checked = False # 最初の１件チェック
            else:
                break
        
        if self.last_input_files != input_files:
            self.last_input_files = input_files
            self.next_image_file = image_file
        return JSONResponse(content={"files": input_files})

    async def get_output_list(self):
        # 出力ディレクトリ内のファイル一覧を取得
        now = datetime.datetime.now()
        file_table = [
            (f, os.path.getmtime(os.path.join(qPath_output, f)))
            for f in os.listdir(qPath_output)
            if os.path.isfile(os.path.join(qPath_output, f))
        ]
        file_table.sort(key=lambda x: x[1], reverse=True)
        output_files = []
        image_file = ''
    
        for f, mod_time in file_table:
            if (now - datetime.datetime.fromtimestamp(mod_time)) < datetime.timedelta(seconds=LIST_RESULT_LIMITSEC):
                file_path = os.path.join(qPath_output, f)
                if (now - datetime.datetime.fromtimestamp(mod_time)) < datetime.timedelta(seconds=LIST_RESULT_AUTOCHECK):
                    checked = True # 時間内全てチェック
                    if (image_file == ''):
                        image_file = file_path
                else:
                    checked = False
                output_files.append(
                    #f"{f} {datetime.datetime.fromtimestamp(mod_time).strftime('%Y/%m/%d %H:%M:%S')} {checked}"
                    {"file_name": f, "upd_time": datetime.datetime.fromtimestamp(mod_time).strftime('%Y/%m/%d %H:%M:%S'), "checked": checked}
                )
            else:
                break
        
        if (self.last_output_files != output_files):
            self.last_output_files = output_files
            self.next_image_file = image_file
        return JSONResponse(content={"files": output_files})

    async def post_drop_files(self, files: List[UploadFile] = File(...)):
        # アップロードされたファイルを入力ディレクトリに保存
        for file in files:
            contents = await file.read()
            with open(os.path.join(qPath_input, file.filename), "wb") as f:
                f.write(contents)
        return JSONResponse(content={'message': 'post_drop_files successfully'})

    async def get_output_file(self, filename: str):
        # 指定された出力ファイルをダウンロード用に返す
        file_path = os.path.join(qPath_output, filename)
        return FileResponse(file_path, filename=filename)

    async def get_source(self, source_name: str):
        # ソースコードを取得する
        try:
            res_content = f"''' { source_name }\n"
            with open(source_name, 'r', encoding='utf-8') as f:
                source_code = f.read()
            res_content += source_code
            res_content = res_content.strip() + "\n'''\n"
            return JSONResponse(content={"source_text": res_content})
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail='get_source error:' + str(source_name))

    async def post_tts_text(self, data: ttsTextModel):
        speech_text = data.speech_text

        # 音声合成
        ext_module = self.addin.addin_modules.get('addin_UI_TTS', None)
        nowTime  = datetime.datetime.now()
        stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
        file_seq = 0

        if (ext_module is not None):
            try:
                # [で始まる１行目削除
                speech_text = speech_text.strip()
                if (speech_text[:1] == '[') and (speech_text.find('\n') >= 0):
                    speech_text = speech_text[speech_text.find('\n')+1:]
                # エンジン指定
                text = speech_text
                if (self.data is not None):
                    engine = self.data.addins_setting['speech_tts_engine']
                    if (engine != ''):
                        text = engine + ',\n' + speech_text
                # TTS
                #file_seq += 1
                seq = '{:04}'.format(file_seq)
                filename = qPath_tts + stamp + '.' + seq + '.tts_text.txt'
                qFunc.txtsWrite(filename, txts=[text], encoding='utf-8', exclusive=False, mode='w', )
            except Exception as e:
                print(e)

        return JSONResponse({'message': 'post_tts_text successfully'})

    async def post_tts_csv(self, data: ttsTextModel):
        speech_text = data.speech_text

        # 音声合成
        ext_module = self.addin.addin_modules.get('addin_UI_TTS', None)
        nowTime  = datetime.datetime.now()
        stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
        file_seq = 0

        if (ext_module is not None):
            try:
                # [で始まる１行目削除
                speech_text = speech_text.strip()
                if (speech_text[:1] == '[') and (speech_text.find('\n') >= 0):
                    speech_text = speech_text[speech_text.find('\n')+1:]
                # 行分割
                text_list = speech_text.splitlines()
                # TTS
                for text in text_list:
                    if (text.strip() != ''):
                        file_seq += 1
                        seq = '{:04}'.format(file_seq)
                        filename = qPath_tts + stamp + '.' + seq + '.tts_csv.txt'
                        qFunc.txtsWrite(filename, txts=[text], encoding='utf-8', exclusive=False, mode='w', )
            except Exception as e:
                print(e)

        return JSONResponse({'message': 'post_tts_csv successfully'})

    async def get_stt(self, input_field: str ):
        # 音声入力
        ext_module = None
        for module_dic in self.botFunc.function_modules:
            if (module_dic['script'] == '認証済_音声入力202405'):
                ext_module = module_dic
                break
        if (ext_module is not None):
            try:
                dic = {}
                dic['runMode']  = self.runMode
                dic['api']      = 'auto' # auto, google, openai,
                dic['language'] = 'auto'
                # エンジン指定
                if (self.data is not None):
                    engine = self.data.addins_setting['speech_stt_engine']
                    if (engine != ''):
                        dic['api'] = engine
                json_dump = json.dumps(dic, ensure_ascii=False, )
                ext_func_proc  = ext_module['func_proc']
                res_json = ext_func_proc( json_dump )
                args_dic = json.loads(res_json)
                recognition_text = args_dic.get('recognition_text')
                return JSONResponse(content={"recognition_text": recognition_text})
            except Exception as e:
                print(e)
                recognition_text = '!'
        raise HTTPException(status_code=503, detail='get_stt error')

    async def get_url_to_text(self, url_path: str ):
        # 認証済_URLからテキスト取得
        ext_module = None
        for module_dic in self.botFunc.function_modules:
            if (module_dic['script'] == '認証済_URLからテキスト取得'):
                ext_module = module_dic
                break
        if (ext_module is not None):
            try:
                dic = {}
                dic['runMode']  = self.runMode
                dic['url_path'] = url_path
                json_dump = json.dumps(dic, ensure_ascii=False, )
                ext_func_proc  = ext_module['func_proc']
                res_json = ext_func_proc( json_dump )
                args_dic = json.loads(res_json)
                result_text = args_dic.get('result_text')
                return JSONResponse(content={"result_text": result_text})
            except Exception as e:
                print(e)
                result_text = '!'
        raise HTTPException(status_code=503, detail='get_url_to_text error')

    async def post_speech_json(self, data: speechJsonModel):
        # speech json 音声合成
        speech_json = data.speech_json
        speaker_male1 = data.speaker_male1
        speaker_male2 = data.speaker_male2
        speaker_female1 = data.speaker_female1
        speaker_female2 = data.speaker_female2
        speaker_etc = data.speaker_etc
        tts_yesno = data.tts_yesno

        # 音声合成
        ext_module = self.addin.addin_modules.get('addin_UI_TTS', None)
        nowTime  = datetime.datetime.now()
        stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
        file_seq = 0

        # 正規表現を使用してJSONを抽出
        json_match = re.search(r'\{.*\}', speech_json, re.DOTALL)
        if not json_match:
            raise HTTPException(status_code=503, detail='post_speech_json error')

        try:
            json_text = json_match.group()
            speech_dic = json.loads( json_text.replace('\n', '') )

            # 話者分類
            male = 0
            female = 0
            speaker = {}
            for speech in speech_dic['speech']:
                gender = speech['gender']
                if (speech['who'] not in speaker.keys()):
                    if (gender.lower() in ['男', 'male']):
                        male += 1
                        speaker[ speech['who'] ] = '男' + str(male).strip()
                    if (gender.lower() in ['女', 'female']):
                        female += 1
                        speaker[ speech['who'] ] = '女' + str(female).strip()

            # 話者変換
            for key in speaker.keys():
                if   (speaker[key][:2] == '男1'):
                    if (speaker_male1 != 'none'):
                        if (speaker_male1 == ''):
                            speaker[key] = '青山龍星'
                        else:
                            speaker[key] = speaker_male1
                elif (speaker[key][:1] == '男'):
                    if (speaker_male2 != 'none'):
                        if (speaker_male2 == ''):
                            speaker[key] = '玄野武宏'
                        else:
                            speaker[key] = speaker_male2
                elif (speaker[key][:2] == '女1'):
                    if (speaker_female1 != 'none'):
                        if (speaker_female1 == ''):
                            speaker[key] = '四国めたん'
                        else:
                            speaker[key] = speaker_female1
                elif (speaker[key][:2] == '女2'):
                    if (speaker_female2 != 'none'):
                        if (speaker_female2 == ''):
                            speaker[key] = '九州そら'
                        else:
                            speaker[key] = speaker_female2
                else:
                    if (speaker_etc != 'none'):
                        if (speaker_etc == ''):
                            speaker[key] = 'ずんだもん'
                        else:
                            speaker[key] = speaker_etc

            # 読み上げ
            speech_text = ''
            for speech in speech_dic['speech']:
                gender = speech['gender']
                if (gender.lower() in ['男', 'male']):
                    gender = '男'
                if (gender.lower() in ['女', 'female']):
                    gender = '女'
                name = speech['who']
                if (name in speaker.keys()):
                    name = speaker[ name ]
                text = speech['text'].replace('\n',' ')
                text = speech['text'].replace('。','. ')
                tts_text = f'{ name },"{ text }"\n'
                speech_text += tts_text

                # TTS
                if (ext_module is not None):
                    if (tts_yesno == 'yes'):
                        try:
                            text = tts_text.strip()
                            file_seq += 1
                            seq = '{:04}'.format(file_seq)
                            filename = qPath_tts + stamp + '.' + seq + '.speech_json.txt'
                            qFunc.txtsWrite(filename, txts=[text], encoding='utf-8', exclusive=False, mode='w', )
                        except Exception as e:
                            print(e)

            # 結果出力
            nowTime  = datetime.datetime.now()
            stamp    = nowTime.strftime('%Y%m%d.%H%M%S')
            filename = qPath_output + stamp + '.speech.csv'
            qFunc.txtsWrite(filename, txts=[speech_text], encoding='utf-8', exclusive=False, mode='w', )

            return JSONResponse(content={'message': 'post_speech_json successfully', 'speech_text': speech_text})

        except Exception as e:
            print('post_speech_json', e)
        raise HTTPException(status_code=503, detail='post_speech_json error')

    async def post_set_react(self, data: setReactModel):
        filename = data.filename
        print(filename)
        from_file = qPath_reacts + filename
        to_file   = qPath_output + filename
        if (not os.path.isfile(from_file)):
            raise HTTPException(status_code=404, detail='post_set_react error')

        try:
            shutil.copy(from_file, to_file)
            if (not os.path.isfile(to_file)):
                raise HTTPException(status_code=404, detail='post_set_react error')

            # SandBox
            ext_module = self.addin.addin_modules.get('addin_autoSandbox', None)
            if (ext_module is not None):

                dic = {}
                dic['runMode']   = self.runMode
                dic['file_path'] = filename
                dic['browser']   = 'no'
                json_dump = json.dumps(dic, ensure_ascii=False, )
                ext_func_proc  = ext_module['func_proc']
                res_json = ext_func_proc( json_dump )
                #args_dic = json.loads(res_json)
                return JSONResponse(content={'message': 'post_set_react successfully'})

        except Exception as e:
            print('post_speech_json', e)
        raise HTTPException(status_code=503, detail='post_set_react error')

    def run(self):
        # サーバー設定と起動
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # フロントエンドのオリジンを指定
            allow_credentials=True,
            allow_methods=["*"],  # すべてのHTTPメソッドを許可
            allow_headers=["*"],  # すべてのヘッダーを許可
        )

        # ウェブUIを起動する
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

    # Web UIプロセスの開始
    webui = WebUiProcess(   runMode='debug', qLog_fn='', 
                            core_port=core_port, sub_base=sub_base, num_subais=numSubAIs)



