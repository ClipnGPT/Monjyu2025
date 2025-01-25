#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/konsan1101
# Thank you for keeping the rules.
# ------------------------------------------------

# RiKi_Monjyu__subbot.py

import sys
import os
import time
import datetime
import codecs
import glob
import shutil

import json

import requests
from typing import Dict, List, Tuple
import random

import socket
qHOSTNAME = socket.gethostname().lower()

# インターフェース
qPath_temp   = 'temp/'
qPath_log    = 'temp/_log/'
qPath_input  = 'temp/input/'
qPath_output = 'temp/output/'

# 共通ルーチン
import _v6__qLog
qLog = _v6__qLog.qLog_class()

# DEBUG
DEBUG_FLAG = False

# freeai チャットボット
import speech_bot_function
import speech_bot_freeai
import speech_bot_freeai_key as freeai_key
import speech_bot_perplexity
import speech_bot_perplexity_key as perplexity_key
import speech_bot_openai
import speech_bot_openai_key as openai_key
import speech_bot_azureoai
import speech_bot_azureoai_key as azureoai_key
import speech_bot_claude
import speech_bot_claude_key as claude_key
import speech_bot_gemini
import speech_bot_gemini_key as gemini_key
import speech_bot_openrt
import speech_bot_openrt_key as openrt_key
import speech_bot_ollama
import speech_bot_ollama_key as ollama_key
import speech_bot_groq
import speech_bot_groq_key as groq_key
import speech_bot_plamo
import speech_bot_plamo_key as plamo_key

# 定数の定義
CONNECTION_TIMEOUT = 15
REQUEST_TIMEOUT = 30

MEMBER_RESULT_TIMEOUT  = 600
MEMBER_RESULT_INTERVAL = 2

class ChatClass:
    """
    チャットボットクラス
    """
    def __init__(self,  runMode: str = 'debug', qLog_fn: str = '',
                        main=None, conf=None, data=None, addin=None, botFunc=None,
                        core_port: str = '8000', self_port: str = '8001', ):
        """
        コンストラクタ
        Args:
            qLog_fn (str, optional): ログファイル名。
            runMode (str, optional): 実行モード。
            core_port (str, optional): メインポート番号。
            self_port (str, optional): 自分のポート番号。
        """
        self.runMode = runMode

        # ログ
        self.proc_name = f"{ self_port }:bot"
        self.proc_id = '{0:10s}'.format(self.proc_name).replace(' ', '_')
        if not os.path.isdir(qPath_log):
            os.makedirs(qPath_log)
        if qLog_fn == '':
            nowTime = datetime.datetime.now()
            qLog_fn = qPath_log + nowTime.strftime('%Y%m%d.%H%M%S') + '.' + os.path.basename(__file__) + '.log'
        qLog.init(mode='logger', filename=qLog_fn)
        qLog.log('info', self.proc_id, 'init')

        # 設定
        self.main = main
        self.conf = conf
        self.data = data
        self.addin = addin
        self.botFunc = botFunc
        self.core_port = core_port
        self.self_port = self_port
        self.local_endpoint = f'http://localhost:{ self.core_port }'
        self.core_endpoint = self.local_endpoint.replace('localhost', qHOSTNAME)

        # bot 定義
        self.history       = []
        self.freeai_enable = None
        self.perplexity_enable = None
        self.openai_enable = None
        self.azureoai_enable = None
        self.claude_enable = None
        self.gemini_enable = None
        self.openrt_enable = None
        self.ollama_enable = None
        self.groq_enable = None
        self.plamo_enable = None

        # CANCEL要求
        self.bot_cancel_request = False

    def freeai_auth(self):
        """
        freeai 認証
        """

        # freeai 定義
        self.freeaiAPI = speech_bot_freeai._freeaiAPI()
        self.freeaiAPI.init(log_queue=None)

        # freeai 認証情報
        api_type = freeai_key.getkey('freeai','freeai_api_type')
        key_id   = freeai_key.getkey('freeai','freeai_key_id')
        if (self.conf.freeai_key_id not in ['', '< your freeai key >']):
            key_id = self.conf.freeai_key_id

        # freeai 認証実行
        res = self.freeaiAPI.authenticate('freeai',
                            api_type,
                            freeai_key.getkey('freeai','freeai_default_gpt'), freeai_key.getkey('freeai','freeai_default_class'),
                            freeai_key.getkey('freeai','freeai_auto_continue'),
                            freeai_key.getkey('freeai','freeai_max_step'), freeai_key.getkey('freeai','freeai_max_session'),
                            key_id,
                            freeai_key.getkey('freeai','freeai_a_nick_name'), freeai_key.getkey('freeai','freeai_a_model'), freeai_key.getkey('freeai','freeai_a_token'),
                            freeai_key.getkey('freeai','freeai_b_nick_name'), freeai_key.getkey('freeai','freeai_b_model'), freeai_key.getkey('freeai','freeai_b_token'),
                            freeai_key.getkey('freeai','freeai_v_nick_name'), freeai_key.getkey('freeai','freeai_v_model'), freeai_key.getkey('freeai','freeai_v_token'),
                            freeai_key.getkey('freeai','freeai_x_nick_name'), freeai_key.getkey('freeai','freeai_x_model'), freeai_key.getkey('freeai','freeai_x_token'),
                            )

        if res == True:
            self.freeai_enable = True
            #qLog.log('info', self.proc_id, 'google (FreeAI) authenticate OK!')
        else:
            self.freeai_enable = False
            qLog.log('error', self.proc_id, 'google (FreeAI) authenticate NG!')

        return self.freeai_enable

    def perplexity_auth(self):
        """
        perplexity 認証
        """

        # perplexity 定義
        self.perplexityAPI = speech_bot_perplexity._perplexityAPI()
        self.perplexityAPI.init(log_queue=None)

        # perplexity 認証情報
        api_type = perplexity_key.getkey('perplexity','perplexity_api_type')
        key_id   = perplexity_key.getkey('perplexity','perplexity_key_id')
        if (self.conf.perplexity_key_id not in ['', '< your perplexity key >']):
            key_id = self.conf.perplexity_key_id

        # perplexity 認証実行
        res = self.perplexityAPI.authenticate('perplexity',
                            api_type,
                            perplexity_key.getkey('perplexity','perplexity_default_gpt'), perplexity_key.getkey('perplexity','perplexity_default_class'),
                            perplexity_key.getkey('perplexity','perplexity_auto_continue'),
                            perplexity_key.getkey('perplexity','perplexity_max_step'), perplexity_key.getkey('perplexity','perplexity_max_session'),
                            key_id,
                            perplexity_key.getkey('perplexity','perplexity_a_nick_name'), perplexity_key.getkey('perplexity','perplexity_a_model'), perplexity_key.getkey('perplexity','perplexity_a_token'),
                            perplexity_key.getkey('perplexity','perplexity_b_nick_name'), perplexity_key.getkey('perplexity','perplexity_b_model'), perplexity_key.getkey('perplexity','perplexity_b_token'),
                            perplexity_key.getkey('perplexity','perplexity_v_nick_name'), perplexity_key.getkey('perplexity','perplexity_v_model'), perplexity_key.getkey('perplexity','perplexity_v_token'),
                            perplexity_key.getkey('perplexity','perplexity_x_nick_name'), perplexity_key.getkey('perplexity','perplexity_x_model'), perplexity_key.getkey('perplexity','perplexity_x_token'),
                            )

        if res == True:
            self.perplexity_enable = True
            #qLog.log('info', self.proc_id, 'perplexity authenticate OK!')
        else:
            self.perplexity_enable = False
            qLog.log('error', self.proc_id, 'perplexity authenticate NG!')

        return self.perplexity_enable

    def openai_auth(self):
        """
        openai 認証
        """

        # openai 定義
        self.openaiAPI = speech_bot_openai.ChatBotAPI()
        self.openaiAPI.init(log_queue=None)

        # openai 認証情報
        api_type      = openai_key.getkey('chatgpt','openai_api_type')
        organization  = openai_key.getkey('chatgpt','openai_organization')
        openai_key_id = openai_key.getkey('chatgpt','openai_key_id')
        endpoint      = openai_key.getkey('chatgpt','azure_endpoint')
        version       = openai_key.getkey('chatgpt','azure_version')
        azure_key_id  = openai_key.getkey('chatgpt','azure_key_id'),
        if (self.conf.openai_api_type != ''):
            api_type = self.conf.openai_api_type
        if (self.conf.openai_organization not in ['', '< your openai organization >']):
            organization = self.conf.openai_organization
        if (self.conf.openai_key_id not in ['', '< your openai key >']):
            openai_key_id = self.conf.openai_key_id
        if (self.conf.azure_endpoint not in ['', '< your azure endpoint base >']):
            endpoint = self.conf.azure_endpoint
        if (self.conf.azure_version not in ['', 'yyyy-mm-dd']):
            version = self.conf.azure_version
        if (self.conf.azure_key_id not in ['', '< your azure key >']):
            azure_key_id = self.conf.azure_key_id

        # openai 認証実行
        if (api_type != 'azure'):
            res = self.openaiAPI.authenticate('chatgpt',
                            api_type,
                            openai_key.getkey('chatgpt','openai_default_gpt'), openai_key.getkey('chatgpt','openai_default_class'),
                            openai_key.getkey('chatgpt','openai_auto_continue'),
                            openai_key.getkey('chatgpt','openai_max_step'), openai_key.getkey('chatgpt','openai_max_session'),
                            organization, openai_key_id,
                            endpoint, version, azure_key_id,
                            openai_key.getkey('chatgpt','gpt_a_nick_name'),
                            openai_key.getkey('chatgpt','gpt_a_model1'), openai_key.getkey('chatgpt','gpt_a_token1'),
                            openai_key.getkey('chatgpt','gpt_a_model2'), openai_key.getkey('chatgpt','gpt_a_token2'),
                            openai_key.getkey('chatgpt','gpt_a_model3'), openai_key.getkey('chatgpt','gpt_a_token3'),
                            openai_key.getkey('chatgpt','gpt_b_nick_name'),
                            openai_key.getkey('chatgpt','gpt_b_model1'), openai_key.getkey('chatgpt','gpt_b_token1'),
                            openai_key.getkey('chatgpt','gpt_b_model2'), openai_key.getkey('chatgpt','gpt_b_token2'),
                            openai_key.getkey('chatgpt','gpt_b_model3'), openai_key.getkey('chatgpt','gpt_b_token3'),
                            openai_key.getkey('chatgpt','gpt_b_length'),
                            openai_key.getkey('chatgpt','gpt_v_nick_name'),
                            openai_key.getkey('chatgpt','gpt_v_model'), openai_key.getkey('chatgpt','gpt_v_token'),
                            openai_key.getkey('chatgpt','gpt_x_nick_name'),
                            openai_key.getkey('chatgpt','gpt_x_model1'), openai_key.getkey('chatgpt','gpt_x_token1'),
                            openai_key.getkey('chatgpt','gpt_x_model2'), openai_key.getkey('chatgpt','gpt_x_token2'),
                            )
        else:
            res = self.openaiAPI.authenticate('chatgpt',
                            api_type,
                            openai_key.getkey('chatgpt','openai_default_gpt'), openai_key.getkey('chatgpt','openai_default_class'),
                            openai_key.getkey('chatgpt','openai_auto_continue'),
                            openai_key.getkey('chatgpt','openai_max_step'), openai_key.getkey('chatgpt','openai_max_session'),
                            organization, openai_key_id,
                            endpoint, version, azure_key_id,
                            openai_key.getkey('chatgpt','azure_a_nick_name'),
                            openai_key.getkey('chatgpt','azure_a_model1'), openai_key.getkey('chatgpt','azure_a_token1'),
                            openai_key.getkey('chatgpt','azure_a_model2'), openai_key.getkey('chatgpt','azure_a_token2'),
                            openai_key.getkey('chatgpt','azure_a_model3'), openai_key.getkey('chatgpt','azure_a_token3'),
                            openai_key.getkey('chatgpt','azure_b_nick_name'),
                            openai_key.getkey('chatgpt','azure_b_model1'), openai_key.getkey('chatgpt','azure_b_token1'),
                            openai_key.getkey('chatgpt','azure_b_model2'), openai_key.getkey('chatgpt','azure_b_token2'),
                            openai_key.getkey('chatgpt','azure_b_model3'), openai_key.getkey('chatgpt','azure_b_token3'),
                            openai_key.getkey('chatgpt','azure_b_length'),
                            openai_key.getkey('chatgpt','azure_v_nick_name'),
                            openai_key.getkey('chatgpt','azure_v_model'), openai_key.getkey('chatgpt','azure_v_token'),
                            openai_key.getkey('chatgpt','azure_x_nick_name'),
                            openai_key.getkey('chatgpt','azure_x_model1'), openai_key.getkey('chatgpt','azure_x_token1'),
                            openai_key.getkey('chatgpt','azure_x_model2'), openai_key.getkey('chatgpt','azure_x_token2'),
                            )

        if res == True:
            self.openai_enable = True
            #qLog.log('info', self.proc_id, 'openai (ChatGPT) authenticate OK!')
        else:
            self.openai_enable = False
            qLog.log('error', self.proc_id, 'openai (ChatGPT) authenticate NG!')

        return self.openai_enable

    def azureoai_auth(self):
        """
        azureoai 認証
        """

        # openai 定義
        self.azureAPI = speech_bot_azureoai.AzureOaiAPI()
        self.azureAPI.init(log_queue=None)

        # openai 認証情報
        api_type      = openai_key.getkey('chatgpt','openai_api_type')
        organization  = openai_key.getkey('chatgpt','openai_organization')
        openai_key_id = openai_key.getkey('chatgpt','openai_key_id')
        endpoint      = openai_key.getkey('chatgpt','azure_endpoint')
        version       = openai_key.getkey('chatgpt','azure_version')
        azure_key_id  = openai_key.getkey('chatgpt','azure_key_id'),
        if (self.conf.openai_api_type != ''):
            api_type = self.conf.openai_api_type
        if (self.conf.openai_organization not in ['', '< your openai organization >']):
            organization = self.conf.openai_organization
        if (self.conf.openai_key_id not in ['', '< your openai key >']):
            openai_key_id = self.conf.openai_key_id
        if (self.conf.azure_endpoint not in ['', '< your azure endpoint base >']):
            endpoint = self.conf.azure_endpoint
        if (self.conf.azure_version not in ['', 'yyyy-mm-dd']):
            version = self.conf.azure_version
        if (self.conf.azure_key_id not in ['', '< your azure key >']):
            azure_key_id = self.conf.azure_key_id

        # azureoai 認証実行
        if (api_type != 'azure'):
            res = self.azureAPI.authenticate('chatgpt',
                            api_type,
                            azureoai_key.getkey('chatgpt','openai_default_gpt'), azureoai_key.getkey('chatgpt','openai_default_class'),
                            azureoai_key.getkey('chatgpt','openai_auto_continue'),
                            azureoai_key.getkey('chatgpt','openai_max_step'), azureoai_key.getkey('chatgpt','openai_max_session'),
                            organization, openai_key_id,
                            endpoint, version, azure_key_id,
                            azureoai_key.getkey('chatgpt','gpt_a_nick_name'),
                            azureoai_key.getkey('chatgpt','gpt_a_model1'), azureoai_key.getkey('chatgpt','gpt_a_token1'),
                            azureoai_key.getkey('chatgpt','gpt_a_model2'), azureoai_key.getkey('chatgpt','gpt_a_token2'),
                            azureoai_key.getkey('chatgpt','gpt_a_model3'), azureoai_key.getkey('chatgpt','gpt_a_token3'),
                            azureoai_key.getkey('chatgpt','gpt_b_nick_name'),
                            azureoai_key.getkey('chatgpt','gpt_b_model1'), azureoai_key.getkey('chatgpt','gpt_b_token1'),
                            azureoai_key.getkey('chatgpt','gpt_b_model2'), azureoai_key.getkey('chatgpt','gpt_b_token2'),
                            azureoai_key.getkey('chatgpt','gpt_b_model3'), azureoai_key.getkey('chatgpt','gpt_b_token3'),
                            azureoai_key.getkey('chatgpt','gpt_b_length'),
                            azureoai_key.getkey('chatgpt','gpt_v_nick_name'),
                            azureoai_key.getkey('chatgpt','gpt_v_model'), azureoai_key.getkey('chatgpt','gpt_v_token'),
                            azureoai_key.getkey('chatgpt','gpt_x_nick_name'),
                            azureoai_key.getkey('chatgpt','gpt_x_model1'), azureoai_key.getkey('chatgpt','gpt_x_token1'),
                            azureoai_key.getkey('chatgpt','gpt_x_model2'), azureoai_key.getkey('chatgpt','gpt_x_token2'),
                            )
        else:
            res = self.azureAPI.authenticate('chatgpt',
                            api_type,
                            azureoai_key.getkey('chatgpt','openai_default_gpt'), azureoai_key.getkey('chatgpt','openai_default_class'),
                            azureoai_key.getkey('chatgpt','openai_auto_continue'),
                            azureoai_key.getkey('chatgpt','openai_max_step'), azureoai_key.getkey('chatgpt','openai_max_session'),
                            organization, openai_key_id,
                            endpoint, version, azure_key_id,
                            azureoai_key.getkey('chatgpt','azure_a_nick_name'),
                            azureoai_key.getkey('chatgpt','azure_a_model1'), azureoai_key.getkey('chatgpt','azure_a_token1'),
                            azureoai_key.getkey('chatgpt','azure_a_model2'), azureoai_key.getkey('chatgpt','azure_a_token2'),
                            azureoai_key.getkey('chatgpt','azure_a_model3'), azureoai_key.getkey('chatgpt','azure_a_token3'),
                            azureoai_key.getkey('chatgpt','azure_b_nick_name'),
                            azureoai_key.getkey('chatgpt','azure_b_model1'), azureoai_key.getkey('chatgpt','azure_b_token1'),
                            azureoai_key.getkey('chatgpt','azure_b_model2'), azureoai_key.getkey('chatgpt','azure_b_token2'),
                            azureoai_key.getkey('chatgpt','azure_b_model3'), azureoai_key.getkey('chatgpt','azure_b_token3'),
                            azureoai_key.getkey('chatgpt','azure_b_length'),
                            azureoai_key.getkey('chatgpt','azure_v_nick_name'),
                            azureoai_key.getkey('chatgpt','azure_v_model'), azureoai_key.getkey('chatgpt','azure_v_token'),
                            azureoai_key.getkey('chatgpt','azure_x_nick_name'),
                            azureoai_key.getkey('chatgpt','azure_x_model1'), azureoai_key.getkey('chatgpt','azure_x_token1'),
                            azureoai_key.getkey('chatgpt','azure_x_model2'), azureoai_key.getkey('chatgpt','azure_x_token2'),
                            )

        if res == True:
            self.azureoai_enable = True
            #qLog.log('info', self.proc_id, 'azure (openai) authenticate OK!')
        else:
            self.azureoai_enable = False
            qLog.log('error', self.proc_id, 'azure (openai) authenticate NG!')

        return self.azureoai_enable

    def claude_auth(self):
        """
        claude 認証
        """

        # claude 定義
        self.claudeAPI = speech_bot_claude._claudeAPI()
        self.claudeAPI.init(log_queue=None)

        # claude 認証情報
        api_type = claude_key.getkey('claude','claude_api_type')
        key_id   = claude_key.getkey('claude','claude_key_id')
        if (self.conf.claude_key_id not in ['', '< your claude key >']):
            key_id = self.conf.claude_key_id

        # claude 認証実行
        res = self.claudeAPI.authenticate('claude',
                            api_type,
                            claude_key.getkey('claude','claude_default_gpt'), claude_key.getkey('claude','claude_default_class'),
                            claude_key.getkey('claude','claude_auto_continue'),
                            claude_key.getkey('claude','claude_max_step'), claude_key.getkey('claude','claude_max_session'),
                            key_id,
                            claude_key.getkey('claude','claude_a_nick_name'), claude_key.getkey('claude','claude_a_model'), claude_key.getkey('claude','claude_a_token'),
                            claude_key.getkey('claude','claude_b_nick_name'), claude_key.getkey('claude','claude_b_model'), claude_key.getkey('claude','claude_b_token'),
                            claude_key.getkey('claude','claude_v_nick_name'), claude_key.getkey('claude','claude_v_model'), claude_key.getkey('claude','claude_v_token'),
                            claude_key.getkey('claude','claude_x_nick_name'), claude_key.getkey('claude','claude_x_model'), claude_key.getkey('claude','claude_x_token'),
                            )

        if res == True:
            self.claude_enable = True
            #qLog.log('info', self.proc_id, 'anthropic (Claude) authenticate OK!')
        else:
            self.claude_enable = False
            qLog.log('error', self.proc_id, 'anthropic (Claude) authenticate NG!')

        return self.claude_enable

    def gemini_auth(self):
        """
        gemini 認証
        """

        # gemini 定義
        self.geminiAPI = speech_bot_gemini._geminiAPI()
        self.geminiAPI.init(log_queue=None)

        # gemini 認証情報
        api_type = gemini_key.getkey('gemini','gemini_api_type')
        key_id   = gemini_key.getkey('gemini','gemini_key_id')
        if (self.conf.gemini_key_id not in ['', '< your gemini key >']):
            key_id = self.conf.gemini_key_id

        # gemini 認証実行
        res = self.geminiAPI.authenticate('gemini',
                            api_type,
                            gemini_key.getkey('gemini','gemini_default_gpt'), gemini_key.getkey('gemini','gemini_default_class'),
                            gemini_key.getkey('gemini','gemini_auto_continue'),
                            gemini_key.getkey('gemini','gemini_max_step'), gemini_key.getkey('gemini','gemini_max_session'),
                            key_id,
                            gemini_key.getkey('gemini','gemini_a_nick_name'), gemini_key.getkey('gemini','gemini_a_model'), gemini_key.getkey('gemini','gemini_a_token'),
                            gemini_key.getkey('gemini','gemini_b_nick_name'), gemini_key.getkey('gemini','gemini_b_model'), gemini_key.getkey('gemini','gemini_b_token'),
                            gemini_key.getkey('gemini','gemini_v_nick_name'), gemini_key.getkey('gemini','gemini_v_model'), gemini_key.getkey('gemini','gemini_v_token'),
                            gemini_key.getkey('gemini','gemini_x_nick_name'), gemini_key.getkey('gemini','gemini_x_model'), gemini_key.getkey('gemini','gemini_x_token'),
                            )

        if res == True:
            self.gemini_enable = True
            #qLog.log('info', self.proc_id, 'google (Gemini) authenticate OK!')
        else:
            self.gemini_enable = False
            qLog.log('error', self.proc_id, 'google (Gemini) authenticate NG!')

        return self.gemini_enable

    def openrt_auth(self):
        """
        openrt 認証
        """

        # openrt 定義
        self.openrtAPI = speech_bot_openrt._openrtAPI()
        self.openrtAPI.init(log_queue=None)

        # openrt 認証情報
        api_type = openrt_key.getkey('openrt','openrt_api_type')
        key_id   = openrt_key.getkey('openrt','openrt_key_id')
        if (self.conf.openrt_key_id not in ['', '< your openrt key >']):
            key_id = self.conf.openrt_key_id

        # openrt 認証実行
        res = self.openrtAPI.authenticate('openrt',
                            api_type,
                            openrt_key.getkey('openrt','openrt_default_gpt'), openrt_key.getkey('openrt','openrt_default_class'),
                            openrt_key.getkey('openrt','openrt_auto_continue'),
                            openrt_key.getkey('openrt','openrt_max_step'), openrt_key.getkey('openrt','openrt_max_session'),
                            key_id,
                            openrt_key.getkey('openrt','openrt_a_nick_name'), openrt_key.getkey('openrt','openrt_a_model'), openrt_key.getkey('openrt','openrt_a_token'),
                            openrt_key.getkey('openrt','openrt_a_use_tools'),
                            openrt_key.getkey('openrt','openrt_b_nick_name'), openrt_key.getkey('openrt','openrt_b_model'), openrt_key.getkey('openrt','openrt_b_token'),
                            openrt_key.getkey('openrt','openrt_b_use_tools'),
                            openrt_key.getkey('openrt','openrt_v_nick_name'), openrt_key.getkey('openrt','openrt_v_model'), openrt_key.getkey('openrt','openrt_v_token'),
                            openrt_key.getkey('openrt','openrt_v_use_tools'),
                            openrt_key.getkey('openrt','openrt_x_nick_name'), openrt_key.getkey('openrt','openrt_x_model'), openrt_key.getkey('openrt','openrt_x_token'),
                            openrt_key.getkey('openrt','openrt_x_use_tools'),
                            )

        if res == True:
            self.openrt_enable = True
            #qLog.log('info', self.proc_id, 'openRouter authenticate OK!')
        else:
            self.openrt_enable = False
            qLog.log('error', self.proc_id, 'openRouter authenticate NG!')

        return self.openrt_enable

    def ollama_auth(self):
        """
        ollama 認証
        """

        # ollama 定義
        self.ollamaAPI = speech_bot_ollama._ollamaAPI()
        self.ollamaAPI.init(log_queue=None)

        # ollama 認証情報
        api_type = ollama_key.getkey('ollama','ollama_api_type')
        server   = ollama_key.getkey('ollama','ollama_server')
        port     = ollama_key.getkey('ollama','ollama_port')
        if (self.conf.ollama_server not in['', 'auto']):
            server = self.conf.ollama_server
        if (self.conf.ollama_port not in['', 'auto']):
            port = self.conf.ollama_port

        # ollama 認証実行
        res = self.ollamaAPI.authenticate('ollama',
                            api_type,
                            ollama_key.getkey('ollama','ollama_default_gpt'), ollama_key.getkey('ollama','ollama_default_class'),
                            ollama_key.getkey('ollama','ollama_auto_continue'),
                            ollama_key.getkey('ollama','ollama_max_step'), ollama_key.getkey('ollama','ollama_max_session'),
                            server, port,
                            ollama_key.getkey('ollama','ollama_a_nick_name'), ollama_key.getkey('ollama','ollama_a_model'), ollama_key.getkey('ollama','ollama_a_token'),
                            ollama_key.getkey('ollama','ollama_b_nick_name'), ollama_key.getkey('ollama','ollama_b_model'), ollama_key.getkey('ollama','ollama_b_token'),
                            ollama_key.getkey('ollama','ollama_v_nick_name'), ollama_key.getkey('ollama','ollama_v_model'), ollama_key.getkey('ollama','ollama_v_token'),
                            ollama_key.getkey('ollama','ollama_x_nick_name'), ollama_key.getkey('ollama','ollama_x_model'), ollama_key.getkey('ollama','ollama_x_token'),
                            )

        if res == True:
            self.ollama_enable = True
            #qLog.log('info', self.proc_id, 'ollama authenticate OK!')
        else:
            self.ollama_enable = False
            qLog.log('error', self.proc_id, 'ollama authenticate NG!')

        return self.ollama_enable

    def groq_auth(self):
        """
        groq 認証
        """

        # groq 定義
        self.groqAPI = speech_bot_groq._groqAPI()
        self.groqAPI.init(log_queue=None)

        # groq 認証情報
        api_type = groq_key.getkey('groq','groq_api_type')
        key_id   = groq_key.getkey('groq','groq_key_id')
        if (self.conf.groq_key_id not in ['', '< your groq key >']):
            key_id = self.conf.groq_key_id

        # groq 認証実行
        res = self.groqAPI.authenticate('groq',
                            api_type,
                            groq_key.getkey('groq','groq_default_gpt'), groq_key.getkey('groq','groq_default_class'),
                            groq_key.getkey('groq','groq_auto_continue'),
                            groq_key.getkey('groq','groq_max_step'), groq_key.getkey('groq','groq_max_session'),
                            key_id,
                            groq_key.getkey('groq','groq_a_nick_name'), groq_key.getkey('groq','groq_a_model'), groq_key.getkey('groq','groq_a_token'),
                            groq_key.getkey('groq','groq_b_nick_name'), groq_key.getkey('groq','groq_b_model'), groq_key.getkey('groq','groq_b_token'),
                            groq_key.getkey('groq','groq_v_nick_name'), groq_key.getkey('groq','groq_v_model'), groq_key.getkey('groq','groq_v_token'),
                            groq_key.getkey('groq','groq_x_nick_name'), groq_key.getkey('groq','groq_x_model'), groq_key.getkey('groq','groq_x_token'),
                            )

        if res == True:
            self.groq_enable = True
            #qLog.log('info', self.proc_id, 'groq authenticate OK!')
        else:
            self.groq_enable = False
            qLog.log('error', self.proc_id, 'groq authenticate NG!')

        return self.groq_enable

    def plamo_auth(self):
        """
        plamo 認証
        """

        # plamo 定義
        self.plamoAPI = speech_bot_plamo._plamoAPI()
        self.plamoAPI.init(log_queue=None)

        # plamo 認証情報
        api_type = plamo_key.getkey('plamo','plamo_api_type')
        key_id   = plamo_key.getkey('plamo','plamo_key_id')
        if (self.conf.plamo_key_id not in ['', '< your plamo key >']):
            key_id = self.conf.plamo_key_id

        # plamo 認証実行
        res = self.plamoAPI.authenticate('plamo',
                            api_type,
                            plamo_key.getkey('plamo','plamo_default_gpt'), plamo_key.getkey('plamo','plamo_default_class'),
                            plamo_key.getkey('plamo','plamo_auto_continue'),
                            plamo_key.getkey('plamo','plamo_max_step'), plamo_key.getkey('plamo','plamo_max_session'),
                            key_id,
                            plamo_key.getkey('plamo','plamo_a_nick_name'), plamo_key.getkey('plamo','plamo_a_model'), plamo_key.getkey('plamo','plamo_a_token'),
                            plamo_key.getkey('plamo','plamo_b_nick_name'), plamo_key.getkey('plamo','plamo_b_model'), plamo_key.getkey('plamo','plamo_b_token'),
                            plamo_key.getkey('plamo','plamo_v_nick_name'), plamo_key.getkey('plamo','plamo_v_model'), plamo_key.getkey('plamo','plamo_v_token'),
                            plamo_key.getkey('plamo','plamo_x_nick_name'), plamo_key.getkey('plamo','plamo_x_model'), plamo_key.getkey('plamo','plamo_x_token'),
                            )

        if res == True:
            self.plamo_enable = True
            #qLog.log('info', self.proc_id, 'plamo authenticate OK!')
        else:
            self.plamo_enable = False
            qLog.log('error', self.proc_id, 'plamo authenticate NG!')

        return self.plamo_enable

    def post_request(self,  user_id: str, from_port: str, to_port: str, 
                            req_mode: str, 
                            system_text: str, request_text: str, input_text: str,
                            file_names: list[str], result_savepath: str, result_schema: str, ) -> str:
        """
        AIメンバー要求送信
        """
        res_port = None
        try:
            response = requests.post(
                self.local_endpoint + '/post_req',
                json={'user_id': user_id, 'from_port': from_port, 'to_port': to_port,
                      'req_mode': req_mode, 
                      'system_text': system_text, 'request_text': request_text, 'input_text': input_text,
                      'file_names': file_names, 'result_savepath': result_savepath, 'result_schema': result_schema, },
                timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
            )
            if response.status_code == 200:
                res_port = str(response.json()['port'])
            else:
                qLog.log('error', self.proc_id, f"Error response ({self.core_port}/post_req) : {response.status_code} - {response.text}")
        except Exception as e:
            qLog.log('error', self.proc_id, f"Error communicating ({self.core_port}/post_req) : {e}")
        return res_port

    def wait_result(self, user_id: str, member_port: Dict[int, str], parent_self=None, ) -> Dict[int, str]:
        """
        AIメンバー応答待機
        """
        out_text: Dict[int, str] = {n: '' for n in range(1, len(member_port))}

        # AIメンバー応答待機
        timeout = time.time() + MEMBER_RESULT_TIMEOUT
        all_done = False
        while time.time() < timeout and all_done == False:

            # キャンセル確認
            if  (parent_self is not None) \
            and (parent_self.cancel_request == True):
                break

            try:
                all_done = False
                response = requests.get(
                    self.local_endpoint + '/get_sessions_port?user_id=' + user_id + '&from_port=' + self.self_port,
                    timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
                )
                if response.status_code == 200:
                    results = response.json()
                    all_done = True
                    for n in range(1, len(member_port)):
                        key_val = f"{ user_id }:{ self.self_port }:{ member_port[n] }"
                        if key_val in results:
                            if results[key_val]["out_time"] is not None:
                                out_text[n] = str(results[key_val]["out_text"])
                            else:
                                all_done = False
                                break
                else:
                    qLog.log('error', self.proc_id, f"Error response ({self.core_port}/get_sessions_port) : {response.status_code} - {response.text}")
            except Exception as e:
                qLog.log('error', self.proc_id, f"Error communicating ({self.core_port}/get_sessions_port) : {e}")
            time.sleep(MEMBER_RESULT_INTERVAL)
        return out_text

    def chatBot(self,   req_mode='chat', engine='freeai',
                        chat_class='auto', model_select='auto', session_id='debug', 
                        history=[], function_modules=[],
                        sysText='', reqText='', inpText='',
                        filePath=[], jsonSchema=None, inpLang='ja', outLang='ja'):

        # debug
        if (DEBUG_FLAG == True):
            print('DEBUG', 'subbot.chatBot:reqText', )
            print('DEBUG', reqText, )

        # cancel
        self.bot_cancel_request = False
        
        # 戻り値
        res_text        = ''
        res_path        = ''
        res_files       = []
        nick_name       = None
        model_name      = None
        res_history     = history

        # 認証実行

        if (self.freeai_enable is None):
            self.freeai_auth()
        if (self.perplexity_enable is None):
            self.perplexity_auth()
        if (self.openai_enable is None):
            self.openai_auth()
        if (self.azureoai_enable is None):
            self.azureoai_auth()
        if (self.claude_enable is None):
            self.claude_auth()
        if (self.gemini_enable is None):
            self.gemini_auth()
        if (self.openrt_enable is None):
            self.openrt_auth()
        if (self.ollama_enable is None):
            self.ollama_auth()
        if (self.groq_enable is None):
            self.groq_auth()
        if (self.plamo_enable is None):
            self.plamo_auth()

        # chatBot 実行

        engine_text = ''

        # # schema 指定
        # if (jsonSchema is not None) and (jsonSchema != ''):
        #     if (engine == ''):
        #         if (self.openai_enable == True):
        #             engine = '[openai]'

        # perplexity
        if (self.perplexity_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'perplexity, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[perplexity]'):
                engine_text = self.perplexityAPI.perplexity_b_nick_name.lower() + ',\n'
            else:
                model_nick_name1 = 'perplexity'
                model_nick_name2 = 'pplx'
                a_nick_name = self.perplexityAPI.perplexity_a_nick_name.lower()
                b_nick_name = self.perplexityAPI.perplexity_b_nick_name.lower()
                v_nick_name = self.perplexityAPI.perplexity_v_nick_name.lower()
                x_nick_name = self.perplexityAPI.perplexity_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        reqText = reqText[len(model_nick_name1)+1:].strip()
                    elif (req_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        reqText = reqText[len(model_nick_name2)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        inpText = inpText[len(model_nick_name1)+1:].strip()
                    elif (inp_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        inpText = inpText[len(model_nick_name2)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot perplexity ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.perplexityAPI.chatBot( chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # openai
        if (self.openai_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'openai, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[openai]'):
                engine_text = self.openaiAPI.gpt_b_nick_name.lower() + ',\n'
            else:
                model_nick_name1 = 'openai'
                model_nick_name2 = 'riki'
                model_nick_name3 = 'assistant'
                model_nick_name4 = 'vision'
                a_nick_name = self.openaiAPI.gpt_a_nick_name.lower()
                b_nick_name = self.openaiAPI.gpt_b_nick_name.lower()
                v_nick_name = self.openaiAPI.gpt_v_nick_name.lower()
                x_nick_name = self.openaiAPI.gpt_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        reqText = reqText[len(model_nick_name1)+1:].strip()
                    elif (req_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        reqText = reqText[len(model_nick_name2)+1:].strip()
                    elif (req_nick_name == model_nick_name3):
                        engine_text = model_nick_name3 + ',\n'
                        reqText = reqText[len(model_nick_name3)+1:].strip()
                    elif (req_nick_name == model_nick_name4):
                        engine_text = model_nick_name4 + ',\n'
                        reqText = reqText[len(model_nick_name4)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        inpText = inpText[len(model_nick_name1)+1:].strip()
                    elif (inp_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        inpText = inpText[len(model_nick_name2)+1:].strip()
                    elif (inp_nick_name == model_nick_name3):
                        engine_text = model_nick_name3 + ',\n'
                        inpText = inpText[len(model_nick_name3)+1:].strip()
                    elif (inp_nick_name == model_nick_name4):
                        engine_text = model_nick_name4 + ',\n'
                        inpText = inpText[len(model_nick_name4)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot openai ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.openaiAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # azureoai
        if (self.azureoai_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'azureoai, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[azure]'):
                engine_text = self.azureAPI.gpt_b_nick_name.lower() + ',\n'
            else:
                model_nick_name1 = 'azure'
                a_nick_name = self.azureAPI.gpt_a_nick_name.lower()
                b_nick_name = self.azureAPI.gpt_b_nick_name.lower()
                v_nick_name = self.azureAPI.gpt_v_nick_name.lower()
                x_nick_name = self.azureAPI.gpt_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        reqText = reqText[len(model_nick_name1)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        inpText = inpText[len(model_nick_name1)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot azure ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.azureAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # claude
        if (self.claude_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'claude, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[claude]'):
                engine_text = self.claudeAPI.claude_b_nick_name.lower() + ',\n'
            else:
                model_nick_name = 'claude'
                a_nick_name = self.claudeAPI.claude_a_nick_name.lower()
                b_nick_name = self.claudeAPI.claude_b_nick_name.lower()
                v_nick_name = self.claudeAPI.claude_v_nick_name.lower()
                x_nick_name = self.claudeAPI.claude_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        inpText = inpText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot claude ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.claudeAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # gemini
        if (self.gemini_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'gemini, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[gemini]'):
                engine_text = self.geminiAPI.gemini_b_nick_name.lower() + ',\n'
            else:
                model_nick_name = 'gemini'
                a_nick_name = self.geminiAPI.gemini_a_nick_name.lower()
                b_nick_name = self.geminiAPI.gemini_b_nick_name.lower()
                v_nick_name = self.geminiAPI.gemini_v_nick_name.lower()
                x_nick_name = self.geminiAPI.gemini_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        inpText = inpText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot gemini ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.geminiAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # openrt
        if (self.openrt_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'openrt, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[openrt]'):
                engine_text = self.openrtAPI.openrt_b_nick_name.lower() + ',\n'
            else:
                model_nick_name = 'openrt'
                a_nick_name = self.openrtAPI.openrt_a_nick_name.lower()
                b_nick_name = self.openrtAPI.openrt_b_nick_name.lower()
                v_nick_name = self.openrtAPI.openrt_v_nick_name.lower()
                x_nick_name = self.openrtAPI.openrt_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        inpText = inpText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot openrt ...')

                    if (self.data is not None):
                        self.openrtAPI.set_models(  a_model=self.data.ort_setting['ort_a_model'],
                                                    a_use_tools=self.data.ort_setting['ort_a_use_tools'],
                                                    b_model=self.data.ort_setting['ort_b_model'],
                                                    b_use_tools=self.data.ort_setting['ort_b_use_tools'],
                                                    v_model=self.data.ort_setting['ort_v_model'],
                                                    v_use_tools=self.data.ort_setting['ort_v_use_tools'],
                                                    x_model=self.data.ort_setting['ort_x_model'],
                                                    x_use_tools=self.data.ort_setting['ort_x_use_tools'], )

                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.openrtAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # ollama
        if (self.ollama_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'ollama, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[ollama]'):
                engine_text = self.ollamaAPI.ollama_b_nick_name.lower() + ',\n'
            else:
                model_nick_name1 = 'local'
                model_nick_name2 = 'ollama'
                a_nick_name = self.ollamaAPI.ollama_a_nick_name.lower()
                b_nick_name = self.ollamaAPI.ollama_b_nick_name.lower()
                v_nick_name = self.ollamaAPI.ollama_v_nick_name.lower()
                x_nick_name = self.ollamaAPI.ollama_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        reqText = reqText[len(model_nick_name1)+1:].strip()
                    elif (req_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        reqText = reqText[len(model_nick_name2)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        inpText = inpText[len(model_nick_name1)+1:].strip()
                    elif (inp_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        inpText = inpText[len(model_nick_name2)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot ollama ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.ollamaAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # groq
        if (self.groq_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'groq, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[groq]'):
                engine_text = self.groqAPI.groq_b_nick_name.lower() + ',\n'
            else:
                model_nick_name = 'groq'
                a_nick_name = self.groqAPI.groq_a_nick_name.lower()
                b_nick_name = self.groqAPI.groq_b_nick_name.lower()
                v_nick_name = self.groqAPI.groq_v_nick_name.lower()
                x_nick_name = self.groqAPI.groq_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        inpText = inpText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot groq ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.groqAPI.chatBot( chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))

        # plamo
        if (self.plamo_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'plamo, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if (engine == '[plamo]'):
                engine_text = self.plamoAPI.plamo_b_nick_name.lower() + ',\n'
            else:
                model_nick_name = 'plamo'
                a_nick_name = self.plamoAPI.plamo_a_nick_name.lower()
                b_nick_name = self.plamoAPI.plamo_b_nick_name.lower()
                v_nick_name = self.plamoAPI.plamo_v_nick_name.lower()
                x_nick_name = self.plamoAPI.plamo_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (engine_text == '') and (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                if (engine_text == '') and (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        inpText = inpText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

                try:
                    qLog.log('info', self.proc_id, 'chatBot plamo ...')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.plamoAPI.chatBot( chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))



        # freeai
        if (self.freeai_enable == True):

            # DEBUG
            if (DEBUG_FLAG == True):
                if (engine == '') and (reqText.find(',') < 1) and (inpText.find(',') < 1):
                    print('DEBUG', 'freeai, reqText and inpText not nick_name !!!', inpText, )

            engine_text = ''
            if True:
                model_nick_name1 = 'free'
                model_nick_name2 = 'freeai'
                a_nick_name = self.freeaiAPI.freeai_a_nick_name.lower()
                b_nick_name = self.freeaiAPI.freeai_b_nick_name.lower()
                v_nick_name = self.freeaiAPI.freeai_v_nick_name.lower()
                x_nick_name = self.freeaiAPI.freeai_x_nick_name.lower()
                if (engine != ''):
                    if   ((len(a_nick_name) != 0) and (engine.lower() == a_nick_name)):
                        engine_text = a_nick_name + ',\n'
                    elif ((len(b_nick_name) != 0) and (engine.lower() == b_nick_name)):
                        engine_text = b_nick_name + ',\n'
                    elif ((len(v_nick_name) != 0) and (engine.lower() == v_nick_name)):
                        engine_text = v_nick_name + ',\n'
                    elif ((len(x_nick_name) != 0) and (engine.lower() == x_nick_name)):
                        engine_text = x_nick_name + ',\n'
                if (reqText.find(',') >= 1):
                    req_nick_name = reqText[:reqText.find(',')].lower()
                    if   (req_nick_name == model_nick_name):
                        engine_text = model_nick_name + ',\n'
                        reqText = reqText[len(model_nick_name)+1:].strip()
                    elif (len(a_nick_name) != 0) and (req_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        reqText = reqText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (req_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        reqText = reqText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (req_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        reqText = reqText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (req_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        reqText = reqText[len(x_nick_name)+1:].strip()
                elif (inpText.find(',') >= 1):
                    inp_nick_name = inpText[:inpText.find(',')].lower()
                    if   (inp_nick_name == model_nick_name1):
                        engine_text = model_nick_name1 + ',\n'
                        inpText = inpText[len(model_nick_name1)+1:].strip()
                    elif (inp_nick_name == model_nick_name2):
                        engine_text = model_nick_name2 + ',\n'
                        inpText = inpText[len(model_nick_name2)+1:].strip()
                    elif (len(a_nick_name) != 0) and (inp_nick_name == a_nick_name):
                        engine_text = a_nick_name + ',\n'
                        inpText = inpText[len(a_nick_name)+1:].strip()
                    elif (len(b_nick_name) != 0) and (inp_nick_name == b_nick_name):
                        engine_text = b_nick_name + ',\n'
                        inpText = inpText[len(b_nick_name)+1:].strip()
                    elif (len(v_nick_name) != 0) and (inp_nick_name == v_nick_name):
                        engine_text = v_nick_name + ',\n'
                        inpText = inpText[len(v_nick_name)+1:].strip()
                    elif (len(x_nick_name) != 0) and (inp_nick_name == x_nick_name):
                        engine_text = x_nick_name + ',\n'
                        inpText = inpText[len(x_nick_name)+1:].strip()

            if (engine_text == ''):
                #engine_text = self.freeaiAPI.freeai_b_nick_name.lower() + ',\n'
                if (req_mode == 'session'):
                    engine_text = a_nick_name + ',\n'
                else:
                    engine_text = b_nick_name + ',\n'

            inpText2 = inpText
            if (engine_text != ''):
                inpText2 = engine_text + inpText
                engine_text = ''

            #if (engine == 'freeai'):
            n_max = 4
            n = 0
            while ((res_text == '') or (res_text == '!')) and (n < n_max) and (self.bot_cancel_request != True):

                n += 1
                try:
                    if (n == 1):
                        qLog.log('info', self.proc_id, 'chatBot freeai ...')
                    else:
                        qLog.log('warning', self.proc_id, f'freeai retry = { n }/{ n_max },')
                    res_text, res_path, res_files, nick_name, model_name, res_history = \
                        self.freeaiAPI.chatBot(     chat_class=chat_class, model_select=model_select, session_id=session_id, 
                                                    history=history, function_modules=function_modules,
                                                    sysText=sysText, reqText=reqText, inpText=inpText2,
                                                    filePath=filePath, jsonSchema=jsonSchema, inpLang=inpLang, outLang=outLang, )
                except Exception as e:
                    qLog.log('error', self.proc_id, str(e))
                    if (n >= n_max):
                        break

                    # n*20 + 40～60秒待機
                    wait_sec = n*20 + random.uniform(40, 60)
                    qLog.log('warning', self.proc_id, f'freeai retry waitting { float(wait_sec) :.1f}s ...')
                    chkTime = time.time()
                    while ((time.time() - chkTime) < wait_sec):
                        time.sleep(0.25)

                        # キャンセル確認
                        if (self.bot_cancel_request == True):
                            break

        if (res_text == ''):
            res_text = '!'

        # DEBUG
        if (DEBUG_FLAG == True):
            print('DEBUG', 'subbot.chatBot:model_name', )
            print('DEBUG', model_name, )
            print('DEBUG', 'subbot.chatBot:res_text', )
            print('DEBUG', res_text, )

        return res_text, res_path, res_files, nick_name, model_name, res_history



    def proc_chat(self, user_id: str, from_port: str, to_port: str,
                        req_mode: str, req_engine: str, 
                        req_functions: str, req_reset: str,
                        max_retry: str, max_ai_count: str,
                        before_proc: str, before_engine: str,
                        after_proc: str, after_engine: str,
                        check_proc: str, check_engine: str,
                        system_text: str, request_text: str, input_text: str,
                        file_names: list[str], result_savepath: str, result_schema: str, parent_self=None, ) -> Tuple[str, str, str]:
        proc_cancel = False

        """
        デバッグ処理
        """
        if (request_text.lower()[:6] == 'debug,'):
            output_text = request_text
            output_data = input_text
            output_path = ''
            output_files = []

            # デバッグ報告
            if (parent_self is not None):
                _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=request_text, input_text=input_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=output_text, output_data=output_data,
                                            output_path=output_path, output_files=output_files,
                                            status='', )

            # 10～30秒待機
            wait_sec = random.uniform(10, 30)
            chkTime = time.time()
            while ((time.time() - chkTime) < wait_sec):
                time.sleep(0.25)

                # キャンセル確認
                if  (parent_self is not None) \
                and (parent_self.cancel_request == True):
                    return '', '', '', []

            # 最終報告
            if (req_mode == 'session'):
                status = 'SESSION'
            else:
                status = 'READY'        
            if (parent_self is not None):
                _ = parent_self.post_complete(  user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=request_text, input_text=input_text,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=output_text, output_data=output_data,
                                                output_path=output_path, output_files=output_files,
                                                status=status, )

            return output_text, output_data, output_path, output_files

        """
        チャット処理
        """

        # パラメータ設定
        if (req_mode == 'chat'):
            if (req_functions == ''):
                req_functions = 'yes,'
            if (max_retry == ''):
                max_retry = '1'
            if (before_proc == ''):
                if (parent_self is not None):
                    before_proc = 'profile,prompt,'
                else:
                    before_proc = 'prompt,'
            if (after_proc == ''):
                after_proc = 'all,'
        if (system_text.strip() != ''):
            system_text = system_text.rstrip() + '\n'
        if (request_text.strip() != ''):
            request_text = request_text.rstrip() + '\n'
        if (input_text.strip() != ''):
            input_text = input_text.rstrip() + '\n'

        # リトライ回数
        MAX_RETRY = 1
        if (max_retry.isdigit()):
            MAX_RETRY = int(max_retry)

        # function_modules 設定
        function_modules = []
        if (req_functions == 'yes,'):
            if (parent_self is not None):
                function_modules = parent_self.function_modules

        # リセット 要求
        if (req_reset == 'yes,'):
            self.history = []

        # ファイル設定
        filePath = []
        for fname in file_names:
            fpath = qPath_input + os.path.basename(fname)
            if (os.path.isfile(fpath)):
                filePath.append(fpath)

        # ----------------------------------------
        # AIメンバー編成
        # ----------------------------------------
        AI_COUNT = 0
        full_name: Dict[int, str]     = {}
        member_prompt: Dict[int, str] = {}
        full_name[AI_COUNT]     = 'ASSISTANT'
        member_prompt[AI_COUNT] = ''

        # ----------------------------------------
        # シンプル実行
        # ----------------------------------------
        if  ((max_retry == '') or (max_retry == '0')) \
        and (before_proc.find('profile,' ) < 0) \
        and (before_proc.find('prompt,'  ) < 0) \
        and (after_proc.find('all,'     ) < 0) \
        and (after_proc.find('summary,' ) < 0) \
        and (after_proc.find('code,'    ) < 0):

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # chatBot処理
            res_text, res_path, res_files, res_name, res_api, self.history = \
                self.chatBot(   req_mode=req_mode, engine=req_engine,
                                chat_class='auto', model_select='auto', session_id=self.self_port, 
                                history=self.history, function_modules=function_modules,
                                sysText=system_text, reqText=request_text, inpText=input_text,
                                filePath=filePath, jsonSchema=result_schema, inpLang='ja', outLang='ja', )
            if (res_path is None):
                res_path = ''

            output_text = ''
            output_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
            output_text += res_text
            output_data = output_text
            st = str('\n' + output_text).find('\n```')
            if (st >= 0):
                en = str('\n' + output_text).rfind('\n```')
                if (en > st):
                    output_data = str('\n' + output_text)[st+1:en+4]
            output_path  = res_path
            output_files = res_files

            # 最終報告
            if (req_mode == 'session'):
                status = 'SESSION'
            else:
                status = 'READY'        
            if (parent_self is not None):
                _ = parent_self.post_complete(  user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=request_text, input_text=input_text,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=output_text, output_data=output_data,
                                                output_path=output_path, output_files=output_files,
                                                status=status, )

            return output_text, output_data, output_path, output_files

        # ----------------------------------------
        # ユーザーの要求
        # ----------------------------------------
        user_text = \
"""
### [USER] ユーザーの要求 ###
$$$ request_text $$$$$$ input_text $$$
###
"""
        user_text = user_text.replace('$$$ request_text $$$', request_text)
        user_text = user_text.replace('$$$ input_text $$$', input_text)
        if (user_text.strip() != ''):
            user_text = user_text.rstrip() + '\n'
            user_text = user_text.replace('\n\n', '\n')
        assistant_text = ''

        # チャットテキスト
        sysText   = system_text
        chat_text = ''

        # ----------------------------------------
        # 前処理
        # ----------------------------------------
        if  (before_proc.find('profile,' ) < 0) \
        and (before_proc.find('prompt,'  ) < 0):
            inpText = \
"""
[SYSTEM]
$$$ system_text $$$
"""
            inpText = inpText.replace('$$$ system_text $$$', system_text)
            inpText = inpText.replace('\n\n', '\n')
            chat_text += inpText.rstrip() + '\n\n'

        else:

            # AI要求
            reqText = ''
            inpText = \
"""
[SYSTEM]
$$$ system_text $$$
$$$ system_text[0] $$$
"""
            if (before_proc.find('profile,') >= 0):
                full_name[0]     = parent_self.info['full_name']
                member_prompt[0] = ''
                inpText += \
"""
あなたは、AIですが歴史上の偉人 [$$$ full_name[0] $$$] として振舞ってください。
あなたは、最新情報まで知っている賢い賢者です。
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
よろしくお願いします。
"""
            if (before_proc.find('prompt,') >= 0):
                inpText += \
"""
ユーザーの要求の意図を推察してください。
ユーザーの要求に明記されていない注意するべき点を見逃さないでください。
ユーザーの求めているもの（出力するべき内容）を推察してください。
ユーザーの要求は簡単な挨拶の返答の場合もあります。何を返答するべきか整理してください。
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
$$$ user_text $$$
ユーザーの要求を誰でも解るように補足、修正をお願いします。
"""
            inpText = inpText.replace('$$$ system_text $$$', system_text)
            inpText = inpText.replace('$$$ system_text[0] $$$', member_prompt[0])
            inpText = inpText.replace('$$$ system_text $$$', system_text)
            inpText = inpText.replace('$$$ full_name[0] $$$', full_name[0])
            inpText = inpText.replace('$$$ user_text $$$', user_text)

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # chatBot処理
            res_text, res_path, res_files, res_name, res_api, self.history = \
                self.chatBot(   req_mode=req_mode, engine=before_engine,
                                chat_class='auto', model_select='auto', session_id=self.self_port, 
                                history=self.history, function_modules=[],
                                sysText=sysText, reqText=reqText, inpText=inpText,
                                filePath=filePath, jsonSchema=None, inpLang='ja', outLang='ja', )
            if (res_path is None):
                res_path = ''

            if (res_text == '') and (res_text == '!'):
                proc_cancel = True
            else:
                res_text = res_text.replace('\n\n', '\n')
                if (before_proc.find('prompt,') >= 0):
                    assistant_text = \
"""
### ユーザーの要求の補足 ###
$$$ res_text $$$
###
"""
                    assistant_text = assistant_text.replace('$$$ res_text $$$', res_text)
                    assistant_text = assistant_text.replace('\n\n', '\n')

            # デバッグ報告
            if (parent_self is not None):
                _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=before_proc, input_text=user_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=inpText, output_data=res_text,
                                            output_path='', output_files=[],
                                            status='', )

            chat_text += inpText.rstrip() + '\n\n'
            chat_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
            chat_text += res_text.rstrip() + '\n\n'

        # ----------------------------------------
        # チャットループ
        # ----------------------------------------
        if (proc_cancel == True):
            res_text ='!'
        else:
            run_count = 0
            while (run_count <= MAX_RETRY):
                run_count += 1

                # AI要求
                reqText = ''
                inpText = ''
                if (run_count == 1):
                    inpBase = \
"""
[SYSTEM]
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
"""
                    inpText = chat_text + inpBase + user_text + assistant_text
                else:
                    inpBase = \
"""
[SYSTEM]
ユーザーの要求の意図は把握されていますか？
ユーザーの求めているもの（出力するべき内容）になっていますか？
それらを自己確認して、もう一度改善した結果の出力をお願いします。
"""
                    inpText = chat_text + inpBase + user_text

                # キャンセル確認
                if (parent_self is not None) \
                and (parent_self.cancel_request == True):
                    return '', '', '', []

                # エンジン変更
                engine = req_engine
                if (after_proc == '') and (run_count >= MAX_RETRY):
                    engine = after_engine

                # chatBot処理
                res_text, res_path, res_files, res_name, res_api, self.history = \
                    self.chatBot(   req_mode=req_mode, engine=engine,
                                    chat_class='auto', model_select='auto', session_id=self.self_port, 
                                    history=self.history, function_modules=function_modules,
                                    sysText=sysText, reqText=reqText, inpText=inpText,
                                    filePath=filePath, jsonSchema=result_schema, inpLang='ja', outLang='ja', )
                if (res_path is None):
                    res_path = ''

                # デバッグ報告
                if (parent_self is not None):
                    _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=inpBase, input_text=chat_text,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=inpText, output_data=res_text,
                                                output_path=res_path, output_files=res_files,
                                                status='', )

                chat_text += inpBase.rstrip() + '\n\n'
                chat_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                res_text2 = res_text.replace('\n\n', '\n')
                chat_text += res_text2.rstrip() + '\n\n'

        output_raw  = res_text
        output_text = ''
        output_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
        output_text += res_text
        output_data = output_text
        st = str('\n' + output_text).find('\n```')
        if (st >= 0):
            en = str('\n' + output_text).rfind('\n```')
            if (en > st):
                output_data = str('\n' + output_text)[st+1:en+4]
        output_path = res_path
        output_files = res_files

        # ----------------------------------------
        # 後処理
        # ----------------------------------------
        if (proc_cancel != True):
            if (after_proc.find('all,'     ) >= 0) \
            or (after_proc.find('summary,' ) >= 0) \
            or (after_proc.find('code,'    ) >= 0):

                # AI要求
                reqText = ''
                inpBase1 = \
"""
[SYSTEM]
回答予定内容の文章を整理し、最終回答文を作成します。
最終回答文は、他のシステムで利用しますので、不必要な説明は削除してください。
同様に、この文章に至った経緯も不要です。その部分も削除してください。
回答本文と思われる結果のみ、シンプルな文章にしてください。
"""
                inpBase2 = \
"""
あなたの回答は別のAIにより評価、採点されます。
適切な位置で改行して、読みやすい文章にしてください。
文章は、美しい日本語でお願いします。
"""
                if (after_proc.find('all,'     ) >= 0) \
                or (after_proc.find('code,'    ) >= 0):
                    inpBase2 += \
"""
ソースコードが含まれている場合、ソースコードのみ抽出してください。
執筆中の小説の原稿の場合、原稿部分のみ抽出してください。
"""
                if (after_proc.find('all,'     ) >= 0) \
                or (after_proc.find('summary,' ) >= 0):
                    inpBase2 += \
"""
ソースコードや執筆中の小説の原稿ではない場合、最大１分で読み切れる文章長さまで要約してください。
"""
                if  (after_proc.find('all,'     ) >= 0) \
                and (req_engine != after_engine):
                    inpBase2 += \
"""
最終回答文は別のAIで生成されました。ミスがあれば修正をお願いします。
"""
                inpText = \
"""
$$$ inpBase1 $$$

$$$ user_text $$$

### 回答予定内容 ###
$$$ output_text $$$
###

$$$ inpBase2 $$$
"""
                inpText = inpText.replace('$$$ inpBase1 $$$', inpBase1)
                inpText = inpText.replace('$$$ user_text $$$', user_text)
                inpText = inpText.replace('$$$ output_text $$$', output_raw)
                inpText = inpText.replace('$$$ inpBase2 $$$', inpBase2)

                # キャンセル確認
                if (parent_self is not None) \
                and (parent_self.cancel_request == True):
                    return '', '', '', []

                # chatBot処理
                res_text, res_path, res_files, res_name, res_api, self.history = \
                    self.chatBot(   req_mode=req_mode, engine=after_engine,
                                    chat_class='auto', model_select='auto', session_id=self.self_port, 
                                    history=self.history, function_modules=function_modules,
                                    sysText=sysText, reqText=reqText, inpText=inpText,
                                    filePath=filePath, jsonSchema=result_schema, inpLang='ja', outLang='ja', )
                if (res_path is None):
                    res_path = ''

                chat_text += inpBase1.rstrip() + '\n' + inpBase2.rstrip() + '\n\n'
                chat_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                res_text2 = res_text.replace('\n\n', '\n')
                chat_text += res_text2.rstrip() + '\n\n'

                output_raw  = res_text
                output_data = ''
                output_data += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                output_data += res_text
                output_path  = res_path
                output_files = res_files

                # デバッグ報告
                if (parent_self is not None):
                    _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=after_proc, input_text=inpText,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=output_text, output_data=output_data,
                                                output_path=output_path, output_files=output_files,
                                                status='', )

        # 最終報告
        if (req_mode == 'session'):
            status = 'SESSION'
        else:
            status = 'READY'        
        if (parent_self is not None):
            _ = parent_self.post_complete(  user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=request_text, input_text=input_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=output_text, output_data=output_data,
                                            output_path=output_path, output_files=output_files,
                                            status=status, )

        # デバッグ報告(会話履歴)
        if (parent_self is not None):
            _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                        from_port=from_port, to_port=to_port,
                                        system_text=system_text, request_text='*** 会話履歴 ***', input_text=user_text,
                                        result_savepath=result_savepath, result_schema=result_schema,
                                        output_text=chat_text, output_data=output_data,
                                        output_path=output_path, output_files=output_files,
                                        status='', )

        return output_text, output_data, output_path, output_files

    def proc_assistant(self,user_id: str, from_port: str, to_port: str,
                            req_mode: str, req_engine: str, 
                            req_functions: str, req_reset: str,
                            max_retry: str, max_ai_count: str, 
                            before_proc: str, before_engine: str,
                            after_proc: str, after_engine: str,
                            check_proc: str, check_engine: str,
                            system_text: str, request_text: str, input_text: str,
                            file_names: list[str], result_savepath: str, result_schema: str, parent_self=None, ) -> Tuple[str, str, str]:
        proc_cancel = False

        """
        アシスタント処理
        """

        # パラメータ設定
        if (req_mode in ['serial', 'parallel']):
            if (req_functions == ''):
                req_functions = 'no,'
            if (max_retry == ''):
                max_retry = '1'
            if (before_proc == ''):
                if (parent_self is not None):
                    before_proc = 'profile,prompt,'
                else:
                    before_proc = 'prompt,'
            if (after_proc == ''):
                after_proc = 'all,'
        if (req_mode == 'serial'):
            if (max_ai_count.isdigit()):
                if (int(max_ai_count) != 0):
                    pass
                else:
                    max_ai_count = '1'
            else:                
                    max_ai_count = '1'

        if (system_text.strip() != ''):
            system_text = system_text.rstrip() + '\n'
        if (request_text.strip() != ''):
            request_text = request_text.rstrip() + '\n'
        if (input_text.strip() != ''):
            input_text = input_text.rstrip() + '\n'

        if (request_text.lower()[:6] == 'debug,'):
            before_proc = ''
            after_proc = ''

        # リトライ回数
        MAX_RETRY = 1
        if (max_retry.isdigit()):
            MAX_RETRY = int(max_retry)

        # AIメンバー数
        AI_MAX = 3
        if (max_ai_count.isdigit()):
            if (int(max_ai_count) != 0):
                AI_MAX = int(max_ai_count)

        # function_modules 設定
        function_modules = []
        if (req_functions == 'yes,'):
            if (parent_self is not None):
                function_modules = parent_self.function_modules

        # リセット 要求
        if (req_reset == 'yes,'):
            self.history = []

        # ファイル設定
        filePath = []
        for fname in file_names:
            fpath = qPath_input + os.path.basename(fname)
            if (os.path.isfile(fpath)):
                filePath.append(fpath)

        # ----------------------------------------
        # AIメンバー編成
        # ----------------------------------------
        AI_COUNT = 0
        full_name: Dict[int, str]   = {}
        member_port: Dict[int, str] = {}
        member_inp: Dict[int, str]  = {}
        member_out: Dict[int, str]  = {}

        full_name[AI_COUNT]   = 'ASSISTANT'
        member_port[AI_COUNT] = self.self_port
        member_inp[AI_COUNT]  = None
        member_out[AI_COUNT]  = None

        for n in range(AI_MAX):

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # メンバー要求
            begin_text = 'begin,'
            res_port = self.post_request(   user_id=user_id, from_port=to_port, to_port='', 
                                            req_mode='session', 
                                            system_text='', request_text=begin_text, input_text='', 
                                            file_names=[], result_savepath='', result_schema='', )
            if res_port is not None:
                AI_COUNT += 1
                full_name[AI_COUNT]   = res_port
                member_port[AI_COUNT] = res_port
                member_inp[AI_COUNT]  = None
                member_out[AI_COUNT]  = None

        # メンバーゼロ
        if AI_COUNT == 0:

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # チャット処理
            output_text, output_data, output_path, output_files = self.proc_chat(
                user_id=user_id, from_port=from_port, to_port=to_port,
                req_mode=req_mode, req_engine=req_engine,
                req_functions=req_functions, req_reset=req_reset,
                max_retry=max_retry, max_ai_count=max_ai_count,
                before_proc=before_proc, before_engine=before_engine,
                after_proc=after_proc, after_engine=after_engine,
                check_proc=check_proc, check_engine=check_engine,
                system_text=system_text, request_text=request_text, input_text=input_text,
                file_names=file_names, result_savepath=result_savepath, result_schema=result_schema, parent_self=parent_self )

            return output_text, output_data, output_path, output_files

        # AIメンバー情報取得
        full_name: Dict[int, str]     = {}
        member_info: Dict[int, str]   = {}
        member_point: Dict[int, str]  = {}
        member_prompt: Dict[int, str] = {}
        for n in range(0, len(member_port)):
            full_name[n]     = member_port[n]
            member_info[n]   = ''
            member_point[n]  = '50'
            member_prompt[n] = ''

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # AIメンバー情報取得
            try:
                endpoint = self.local_endpoint.replace( f':{ self.core_port }', f':{ member_port[n] }' )
                response = requests.get(
                    endpoint + '/get_info',
                    timeout=(CONNECTION_TIMEOUT, REQUEST_TIMEOUT)
                )
                if response.status_code == 200:
                    full_name[n]     = response.json()['full_name']
                    member_info[n]   = response.json()['info_text']
                    member_point[n]  = response.json()['self_point']
                    member_prompt[n] = response.json()['self_prompt']
                    if (member_prompt[n].strip() == system_text.strip()):
                        member_prompt[n] = ''
                else:
                    qLog.log('error', self.proc_id, f"Error response ({member_port[n]}/get_info) : {response.status_code} - {response.text}")
            except Exception as e:
                qLog.log('error', self.proc_id, f"Error communicating ({member_port[n]}/get_info) : {e}")


        members_list = ''
        for n in range(1, len(member_port)):
            members_list += '[' + full_name[n] + '] \n'

        # ----------------------------------------
        # ユーザーの要求
        # ----------------------------------------
        user_text = \
"""
### [USER] ユーザーの要求 ###
$$$ request_text $$$$$$ input_text $$$
###
"""
        user_text = user_text.replace('$$$ request_text $$$', request_text)
        user_text = user_text.replace('$$$ input_text $$$', input_text)
        if (user_text.strip() != ''):
            user_text = user_text.rstrip() + '\n'
            user_text = user_text.replace('\n\n', '\n')
        assistant_text = ''

        # チャットテキスト
        sysText   = system_text
        chat_text = ''

        # ----------------------------------------
        # 前処理
        # ----------------------------------------
        if  (before_proc.find('profile,' ) < 0) \
        and (before_proc.find('prompt,'  ) < 0):
            inpText = \
"""
[SYSTEM]
$$$ system_text $$$
"""
            inpText = inpText.replace('$$$ system_text $$$', system_text)
            inpText = inpText.replace('\n\n', '\n')
            chat_text += inpText.rstrip() + '\n\n'

        else:

            # AI要求
            reqText = ''
            inpText = \
"""
[SYSTEM]
$$$ system_text $$$
$$$ system_text[0] $$$
あなたはAIリーダーに選出されました。
複数のAIでユーザーからの要求に対して最適解を出します。
"""
            if (before_proc.find('profile,') >= 0):
                full_name[0] = parent_self.info['full_name']
                inpText += \
"""
あなたは、AIですが歴史上の偉人 [$$$ full_name[0] $$$] として振舞ってください。
あなたは、最新情報まで知っている賢い賢者です。
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
よろしくお願いします。
"""
            if (before_proc.find('prompt,') >= 0):
                inpText += \
"""
ユーザーの要求の意図を推察してください。
ユーザーの要求に明記されていない注意するべき点を見逃さないでください。
ユーザーの求めているもの（出力するべき内容）を推察してください。
ユーザーの要求は簡単な挨拶の返答の場合もあります。何を返答するべきか整理してください。
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
$$$ user_text $$$
ユーザーの要求を誰でも解るように補足、修正をお願いします。

あなたは、AIメンバーに個別に作業依頼を出せます。作業依頼できるAIメンバーは以下のとおりです。
$$$ members_list $$$
AIメンバー毎に重複しても構わないし総合的なことでもよいので、作業依頼(指示)出しをお願いします。
"""
            inpText = inpText.replace('$$$ system_text $$$', system_text)
            inpText = inpText.replace('$$$ system_text[0] $$$', member_prompt[0])
            inpText = inpText.replace('$$$ full_name[0] $$$', full_name[0])
            inpText = inpText.replace('$$$ user_text $$$', user_text)
            inpText = inpText.replace('$$$ members_list $$$', members_list)

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # chatBot処理
            res_text, res_path, res_files, res_name, res_api, self.history = \
                self.chatBot(   req_mode=req_mode, engine=before_engine,
                                chat_class='auto', model_select='auto', session_id=self.self_port, 
                                history=self.history, function_modules=[],
                                sysText=sysText, reqText=reqText, inpText=inpText,
                                filePath=filePath, jsonSchema=None, inpLang='ja', outLang='ja', )
            if (res_path is None):
                res_path = ''

            if (res_text == '') and (res_text == '!'):
                proc_cancel = True
            else:
                res_text = res_text.replace('\n\n', '\n')
                if (before_proc.find('prompt,') >= 0):
                    assistant_text = \
"""
### ユーザーの要求の補足 ###
$$$ res_text $$$
###
"""
                    assistant_text = assistant_text.replace('$$$ res_text $$$', res_text)
                    assistant_text = assistant_text.replace('\n\n', '\n')

            # デバッグ報告
            if (parent_self is not None):
                _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=before_proc, input_text=user_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=inpText, output_data=res_text,
                                            output_path=res_path, output_files=res_files,
                                            status='', )

            chat_text += inpText.rstrip() + '\n\n'
            chat_text += f"[{ full_name[0] }] ({ member_port[0] }:{ res_api }) \n"
            chat_text += res_text.rstrip() + '\n\n'

        # ----------------------------------------
        # チャットループ
        # ----------------------------------------
        if (proc_cancel == True):
            res_text ='!'
        else:
            run_count = 0
            while (run_count <= MAX_RETRY):
                run_count += 1

                # AIメンバー要求
                sysText = system_text
                reqText = chat_text
                if (run_count == 1):
                    inpBase = \
"""
[SYSTEM]
あなたはAIメンバーに選出されました。
複数のAIでユーザーの要求に対して最適解を出します。
あなたは、AIですが歴史上の偉人 [### full_name[n] ###] として振舞ってください。
あなたは、最新情報まで知っている賢い賢者です。
ユーザーの要求を正しく理解し、AIリーダーの解釈とあなたへの依頼をもとに、やるべきことを行ってください。
あなたの回答は別のAIにより評価、採点されます。
ユーザーの要求には常に思慮深く考えて回答してください。
よろしくお願いします。
"""
                else:
                    inpBase = \
"""
[SYSTEM]
よく考えて、他のAIの意見も参考に、もう一度お願いします。
"""
                for n in range(1, len(member_port)):
                    inpText = inpBase.replace('### full_name[n] ###', full_name[n])
                    inpText += user_text
                    inpText += assistant_text
                    if (request_text.lower()[:6] == 'debug,'):
                        reqText = request_text

                    # キャンセル確認
                    if (parent_self is not None) \
                    and (parent_self.cancel_request == True):
                        return '', '', '', []

                    # メンバー要求
                    res_port = self.post_request(   user_id=user_id, from_port=to_port, to_port=member_port[n],
                                                    req_mode='session', 
                                                    system_text=sysText, request_text=reqText, input_text=inpText,
                                                    file_names=file_names, result_savepath=result_savepath, result_schema=result_schema, )

                    if res_port is not None:
                        member_inp[n] = inpText
                        member_out[n] = None

                # AIメンバー待機
                out_text = self.wait_result(user_id=user_id, member_port=member_port, parent_self=parent_self, )

                # キャンセル確認
                if (parent_self is not None) \
                and (parent_self.cancel_request == True):
                    return '', '', '', []

                # AIメンバー応答
                member_text = ''
                for n in range(1, len(member_port)):
                    if out_text[n] is not None:
                        #member_text += f"[{ full_name[n] }] ({ member_port[n] }) \n"
                        member_text += out_text[n].rstrip() + '\n\n'

                # 中間報告
                _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=inpBase, input_text=chat_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=inpText, output_data='***回答検証中***\n\n' + member_text, 
                                            output_path='', output_files=[],
                                            status='', )

                chat_text += inpBase.rstrip() + '\n\n'
                chat_text += member_text.rstrip() + '\n\n'

                # AIリーダー要求
                sysText = system_text
                reqText = chat_text
                inpBase = \
"""
[SYSTEM]
あなたは、AIリーダー [$$$ full_name[0] $$$] ($$$ member_port[0] $$$) として、
あなたは、最初にAIメンバーに作業依頼(指示)出ししましたが、それは他のAIの回答を参考にするためです。
前記、これまでのAIメンバーの回答も参考にしつつ、適切な回答を行ってください。
$$$ user_text $$$
ユーザーの要求を推察、正しく解釈して、求められている回答を生成してください。
"""
                if (run_count != 1):
                    inpBase += \
"""
ユーザーの要求の意図は把握されていますか？
ユーザーの求めているもの（出力するべき内容）になっていますか？
それらを自己確認して、もう一度改善した結果の出力をお願いします。
"""
                inpBase = inpBase.replace('$$$ full_name[0] $$$', full_name[0])
                inpBase = inpBase.replace('$$$ member_port[0] $$$', member_port[0])
                inpText = inpBase.replace('$$$ user_text $$$', user_text)
                inpBase = inpBase.replace('$$$ user_text $$$', '')

                if (request_text.lower()[:6] == 'debug,'):
                    res_text = request_text
                    res_api  = 'debug'
                    res_path = ''
                    res_files = []
                else:

                    # キャンセル確認
                    if (parent_self is not None) \
                    and (parent_self.cancel_request == True):
                        return '', '', '', []

                    # エンジン変更
                    engine = req_engine
                    if (after_proc == '') and (run_count >= MAX_RETRY):
                        engine = after_engine

                    # chatBot 処理
                    res_text, res_path, res_files, res_name, res_api, self.history = \
                        self.chatBot(   req_mode=req_mode, engine=engine,
                                        chat_class='auto', model_select='auto', session_id=self.self_port, 
                                        history=self.history, function_modules=function_modules,
                                        sysText=sysText, reqText=reqText, inpText=inpText,
                                        filePath=filePath, jsonSchema=result_schema, inpLang='ja', outLang='ja', )
                    if (res_path is None):
                        res_path = ''

                    if (res_text == '') and (res_text == '!'):
                        proc_cancel = True
                        break

                # デバッグ報告
                if (parent_self is not None):
                    _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=inpBase, input_text=chat_text,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=inpText, output_data=res_text,
                                                output_path=res_path, output_files=res_files,
                                                status='', )

                chat_text += inpBase.rstrip() + '\n\n'
                chat_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                res_text2 = res_text.replace('\n\n', '\n')
                chat_text += res_text2.rstrip() + '\n\n'

        output_raw  = res_text
        output_text = ''
        output_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
        output_text += res_text
        output_data = output_text
        st = str('\n' + output_text).find('\n```')
        if (st >= 0):
            en = str('\n' + output_text).rfind('\n```')
            if (en > st):
                output_data = str('\n' + output_text)[st+1:en+4]
        output_path = res_path
        output_files = res_files

        if (request_text.lower()[:6] == 'debug,'):
            output_data = input_text

        # ----------------------------------------
        # 後処理
        # ----------------------------------------
        if (proc_cancel != True):
            if (after_proc.find('all,'     ) >= 0) \
            or (after_proc.find('summary,' ) >= 0) \
            or (after_proc.find('code,'    ) >= 0):

                # AI要求
                reqText = ''
                inpBase1 = \
"""
[SYSTEM]
回答予定内容の文章を整理し、最終回答文を作成します。
最終回答文は、他のシステムで利用しますので、不必要な説明は削除してください。
同様に、この文章に至った経緯も不要です。その部分も削除してください。
回答本文と思われる結果のみ、シンプルな文章にしてください。
"""
                inpBase2 = \
"""
あなたの回答は別のAIにより評価、採点されます。
適切な位置で改行して、読みやすい文章にしてください。
文章は、美しい日本語でお願いします。
"""
                if (after_proc.find('all,'     ) >= 0) \
                or (after_proc.find('code,'    ) >= 0):
                    inpBase2 += \
"""
ソースコードが含まれている場合、ソースコードのみ抽出してください。
執筆中の小説の原稿の場合、原稿部分のみ抽出してください。
"""
                if (after_proc.find('all,'     ) >= 0) \
                or (after_proc.find('summary,' ) >= 0):
                    inpBase2 += \
"""
ソースコードや執筆中の小説の原稿ではない場合、最大１分で読み切れる文章長さまで要約してください。
"""
                if  (after_proc.find('all,'     ) >= 0) \
                and (req_engine != after_engine):
                    inpBase2 += \
"""
最終回答文は別のAIで生成されました。ミスがあれば修正をお願いします。
"""
                inpText = \
"""
$$$ inpBase1 $$$

$$$ user_text $$$

### 回答予定内容 ###
$$$ output_text $$$
###

$$$ inpBase2 $$$
"""
                inpText = inpText.replace('$$$ inpBase1 $$$', inpBase1)
                inpText = inpText.replace('$$$ user_text $$$', user_text)
                inpText = inpText.replace('$$$ output_text $$$', output_raw)
                inpText = inpText.replace('$$$ inpBase2 $$$', inpBase2)

                # キャンセル確認
                if (parent_self is not None) \
                and (parent_self.cancel_request == True):
                    return '', '', '', []

                # chatBot処理
                res_text, res_path, res_files, res_name, res_api, self.history = \
                    self.chatBot(   req_mode=req_mode, engine=after_engine,
                                    chat_class='auto', model_select='auto', session_id=self.self_port, 
                                    history=self.history, function_modules=function_modules,
                                    sysText=sysText, reqText=reqText, inpText=inpText,
                                    filePath=filePath, jsonSchema=result_schema, inpLang='ja', outLang='ja', )
                if (res_path is None):
                    res_path = ''

                chat_text += inpBase1.rstrip() + '\n' + inpBase2.rstrip() + '\n\n'
                chat_text += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                res_text2 = res_text.replace('\n\n', '\n')
                chat_text += res_text2.rstrip() + '\n\n'

                output_raw  = res_text
                output_data = ''
                output_data += f"[{ full_name[0] }] ({ self.self_port }:{ res_api }) \n"
                output_data += res_text
                output_path = res_path
                output_files = res_files

                # デバッグ報告
                if (parent_self is not None):
                    _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                                from_port=from_port, to_port=to_port,
                                                system_text=system_text, request_text=after_proc, input_text=inpText,
                                                result_savepath=result_savepath, result_schema=result_schema,
                                                output_text=output_text, output_data=output_data,
                                                output_path=output_path, output_files=output_files,
                                                status='', )

        # キャンセル確認
        if (parent_self is not None) \
        and (parent_self.cancel_request == True):
            return '', '', '', []

        # 最終報告
        if (req_mode == 'session'):
            status = 'SESSION'
        else:
            status = 'READY'        
        if (parent_self is not None):
            _ = parent_self.post_complete(  user_id=user_id, req_mode=req_mode,
                                            from_port=from_port, to_port=to_port,
                                            system_text=system_text, request_text=request_text, input_text=input_text,
                                            result_savepath=result_savepath, result_schema=result_schema,
                                            output_text=output_text, output_data=output_data,
                                            output_path=output_path, output_files=output_files,
                                            status=status, )

        # デバッグ報告(会話履歴)
        if (parent_self is not None):
            _ = parent_self.post_debug_log( user_id=user_id, req_mode=req_mode,
                                        from_port=from_port, to_port=to_port,
                                        system_text=system_text, request_text='*** 会話履歴 ***', input_text=user_text,
                                        result_savepath=result_savepath, result_schema=result_schema,
                                        output_text=chat_text, output_data=output_data,
                                        output_path=output_path, output_files=output_files,
                                        status='', )

        # ----------------------------------------
        # AIメンバー解散
        # ----------------------------------------
        for n in range(1, len(member_port)):

            # キャンセル確認
            if (parent_self is not None) \
            and (parent_self.cancel_request == True):
                return '', '', '', []

            # メンバー要求
            bye_text = 'bye,'
            res_port = self.post_request(user_id=user_id, from_port=to_port, to_port=member_port[n],
                                         req_mode='session', 
                                         system_text='', request_text=bye_text, input_text='',
                                         file_names=[], result_savepath='', result_schema='', )

        return output_text, output_data, output_path, output_files



if __name__ == '__main__':
    core_port = '8000'
    self_port = '8001'

    chat_class = ChatClass(runMode='debug', qLog_fn='', core_port=core_port, self_port=self_port)

    input_text = 'おはよう'
    output_text, _, _, _, _ = chat_class.proc_chat(user_id='debug', from_port='debug', to_port='8001',
                                       req_mode='chat', req_engine='',
                                       req_functions='', req_reset='',
                                       max_retry='', max_ai_count='', 
                                       before_proc='', before_engine='', 
                                       after_proc='', after_engine='',
                                       check_proc='', check_engine='',
                                       system_text='', request_text='', input_text=input_text,
                                       filePath=[], result_schema='', )

    print(output_text)
