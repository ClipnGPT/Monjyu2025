#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/konsan1101
# Thank you for keeping the rules.
# ------------------------------------------------

# RiKi_Monjyu.py

import sys
import os
import time
import datetime
import codecs
import glob
import shutil
import random
import threading
import multiprocessing

# ダミーインポート
#import pip
import pygame
import screeninfo
import pyautogui
import pynput
import pyperclip
import hashlib
import PIL  # Pillow
from PIL import Image, ImageGrab, ImageTk, ImageEnhance
import numpy
import cv2
import pandas
import openpyxl
import pyodbc
import sqlalchemy
import matplotlib
import seaborn
import pytesseract
import websocket

# google
from google import genai
from google.genai import types

# win32/OCR
import pytesseract
if (os.name == 'nt'):
    import win32clipboard
    import comtypes.client
    import comtypes.stream
    import winocr

# seleniumモジュールのインポート
from selenium import webdriver
from selenium.webdriver import Edge
from selenium.webdriver import Chrome
from selenium.webdriver import Firefox
from selenium.webdriver import Safari
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import webdriver_manager.chrome
import webdriver_manager.firefox
if (os.name == 'nt'):
    import webdriver_manager.microsoft

# PDF解析用モジュールのインポート
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

# 音声関連モジュールのインポート
import gtts
try:
    import googletrans
except:
    pass
import pyaudio
import speech_recognition as sr

# インターフェースのパス設定
qPath_temp    = 'temp/'
qPath_log     = 'temp/_log/'
qPath_work    = 'temp/_work/'
qPath_input   = 'temp/input/'
qPath_output  = 'temp/output/'
qPath_sandbox = 'temp/sandbox/'

# 共通ルーチンのインポート
import _v6__qFunc
qFunc = _v6__qFunc.qFunc_class()
import _v6__qLog
qLog = _v6__qLog.qLog_class()

# 処理ルーチンのインポート
import RiKi_Monjyu__conf
import RiKi_Monjyu__data
import RiKi_Monjyu__addin
import RiKi_Monjyu__coreai
import RiKi_Monjyu__subai
import RiKi_Monjyu__webui
import speech_bot_function

# コアAIのポート番号設定
CORE_PORT = 8000
SUB_BASE  = 8100

# 実行モードの設定
runMode = 'debug'
numSubAIs = '48'
if getattr(sys, 'frozen', False):
    numSubAIs = '128'



class _main_class:
    def __init__(self):
        self.main_all_ready = False

    def init(self, runMode='debug', qLog_fn=''):
        self.runMode = runMode
        # ログ設定
        self.proc_name = 'main'
        self.proc_id = '{0:10s}'.format(self.proc_name).replace(' ', '_')
        if not os.path.isdir(qPath_log):
            os.makedirs(qPath_log)
        if qLog_fn == '':
            nowTime = datetime.datetime.now()
            qLog_fn = qPath_log + nowTime.strftime('%Y%m%d.%H%M%S') + '.' + os.path.basename(__file__) + '.log'
        qLog.init(mode='logger', filename=qLog_fn)
        qLog.log('info', self.proc_id, 'init')
        return True



if __name__ == '__main__':
    main_name = 'Monjyu'
    main_id = '{0:10s}'.format(main_name).replace(' ', '_')

    # 制限日設定
    limit_date = '{:1d}{:1d}'.format(int(float(3.0)), int(float(1.0)))
    limit_date = '{:1d}{:1d}'.format(int(float(1.0)), int(float(2.0))) + '/' + limit_date
    limit_date = '/' + limit_date
    limit_date = '{:3d}{:1d}'.format(int(float(202.0)), int(float(6.0))) + limit_date
    #limit_date = '2026/12/31'
    dt = datetime.datetime.now()
    dateinfo_today = dt.strftime('%Y/%m/%d')
    dt = datetime.datetime.strptime(limit_date, '%Y/%m/%d') + datetime.timedelta(days=-60)
    dateinfo_start = dt.strftime('%Y/%m/%d')
    main_start = time.time()

    # ディレクトリ作成
    qFunc.makeDirs(qPath_temp, remove=False)
    qFunc.makeDirs(qPath_log, remove=False)
    qFunc.makeDirs(qPath_work, remove=False)
    qFunc.makeDirs(qPath_input, remove=False)
    qFunc.makeDirs(qPath_output, remove=False)
    qFunc.makeDirs(qPath_sandbox, remove=False)

    # ログの初期化
    nowTime = datetime.datetime.now()
    basename = os.path.basename(__file__)
    basename = basename.replace('.py', '')
    qLog_fn = qPath_log + nowTime.strftime('%Y%m%d.%H%M%S') + '.' + basename + '.log'
    qLog.init(mode='logger', filename=qLog_fn)
    qLog.log('info', main_id, 'init')
    qLog.log('info', main_id, basename + ' runMode, ... ')

    # パラメータの取得
    if True:
        if len(sys.argv) >= 2:
            runMode = str(sys.argv[1]).lower()
        if len(sys.argv) >= 3:
            numSubAIs = str(sys.argv[2])
        qLog.log('info', main_id, 'runMode   = ' + str(runMode))
        qLog.log('info', main_id, 'numSubAIs = ' + str(numSubAIs))

    # 初期設定
    if True:
         # ライセンス制限
        if (dateinfo_today >= dateinfo_start):
            qLog.log('warning', main_id, '利用ライセンスは、 ' + limit_date + ' まで有効です。')
        if (dateinfo_today > limit_date):
            time.sleep(60)
            sys.exit(0)

        # ポート設定
        core_port = str(CORE_PORT)
        sub_base  = str(SUB_BASE)

        # main 初期化
        main = _main_class()
        main.init(runMode=runMode, qLog_fn=qLog_fn)
        
        # conf 初期化
        conf = RiKi_Monjyu__conf._conf_class()
        conf.init(runMode=runMode, qLog_fn=qLog_fn)

        # data 初期化
        data = RiKi_Monjyu__data._data_class(   runMode=runMode, qLog_fn=qLog_fn,
                                                main=main, conf=conf,
                                                core_port=core_port, sub_base=sub_base, num_subais=numSubAIs)

        # addin 初期化
        addin = RiKi_Monjyu__addin._addin_class()
        addin.init(runMode=runMode, qLog_fn=qLog_fn,
                   addins_path='_extensions/monjyu/', secure_level='low')
        res, msg = addin.addins_load()
        if res != True or msg != '':
            print(msg)
            print()
        res, msg = addin.addins_reset()
        if res != True or msg != '':
            print(msg)
            print()

        # botFunction 初期化
        botFunc = speech_bot_function.botFunction()
        res, msg = botFunc.functions_load(
            functions_path='_extensions/function/', secure_level='low')
        if res != True or msg != '':
            print(msg)
            print()
        res, msg = botFunc.functions_reset()
        if res != True or msg != '':
            print(msg)
            print()

        # key2Live_freeai
        liveai_enable = False
        ext_module = addin.addin_modules.get('monjyu_UI_key2Live_freeai', None)
        if (ext_module is not None):
            try:
                if (ext_module['onoff'] == 'on'):
                    func_reset = ext_module['func_reset']
                    res  = func_reset(botFunc=botFunc, data=data, )
                    print('reset', 'monjyu_UI_key2Live_freeai')
                    liveai_enable = True
            except Exception as e:
                print(e)

        # key2Live_openai
        #liveai_enable = False
        ext_module = addin.addin_modules.get('monjyu_UI_key2Live_openai', None)
        if (ext_module is not None):
            try:
                if (ext_module['onoff'] == 'on'):
                    func_reset = ext_module['func_reset']
                    res  = func_reset(botFunc=botFunc, data=data, )
                    print('reset', 'monjyu_UI_key2Live_openai')
                    liveai_enable = True
            except Exception as e:
                print(e)

        # browser操作Agent
        webAgent_enable = False
        for module_dic in botFunc.function_modules:
            if (module_dic['func_name'] == 'webBrowser_operation_agent'):
                try:
                    if (module_dic['onoff'] == 'on'):
                        data.webAgent_modelNames['freeai'] = module_dic['class'].ModelNames['freeai']
                        data.webAgent_modelNames['openai'] = module_dic['class'].ModelNames['openai']
                        data.webAgent_modelNames['claude'] = module_dic['class'].ModelNames['claude']
                        func_reset = module_dic['func_reset']
                        res  = func_reset(data=data, )
                        print('reset', 'webBrowser_operation_agent')
                        webAgent_enable = True
                except Exception as e:
                    print(e)
                break

    # サブAI起動
    if True:
        # サブプロフィール設定(ランダム)
        subai_profiles = random.sample(range(int(numSubAIs)), int(numSubAIs))

        subai_class = {}
        subai_thread = {}
        for n in range(int(numSubAIs)):
            self_port = str(SUB_BASE + n + 1)
            subai_class[n] = RiKi_Monjyu__subai.SubAiClass(runMode=runMode, qLog_fn=qLog_fn,
                                                        main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                                        core_port=core_port, sub_base=sub_base, num_subais=numSubAIs,
                                                        self_port=self_port, profile_number=subai_profiles[n])
            subai_thread[n] = threading.Thread(target=subai_class[n].run)
            subai_thread[n].daemon = True
            subai_thread[n].start()

    # コアAI起動
    if True:
        coreai_class = RiKi_Monjyu__coreai.CoreAiClass(runMode=runMode, qLog_fn=qLog_fn,
                                                    main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                                    core_port=core_port, sub_base=sub_base, num_subais=numSubAIs)
        coreai_thread = threading.Thread(target=coreai_class.run)
        coreai_thread.daemon = True
        coreai_thread.start()

    # ウェブUI起動
    if True:
        self_port = str(CORE_PORT + 8)
        webui_class = RiKi_Monjyu__webui.WebUiClass(runMode=runMode, qLog_fn=qLog_fn,
                                                    main=main, conf=conf, data=data, addin=addin, botFunc=botFunc,
                                                    core_port=core_port, sub_base=sub_base, num_subais=numSubAIs,
                                                    self_port=self_port)
        webui_thread = threading.Thread(target=webui_class.run)
        webui_thread.daemon = True
        webui_thread.start()

    # 起動メッセージ
    print()
    qLog.log('info', main_id, "Thank you for using our systems.")
    qLog.log('info', main_id, "To use [ Assistant AI 文殊/Monjyu(もんじゅ) ], Access 'http://localhost:8008/' in your browser.")
    if (liveai_enable == True):
        qLog.log('info', main_id, "To use [ Live AI 力/RiKi(りき) ], Press ctrl-l or ctrl-r three times.")
    if (webAgent_enable == True):
        qLog.log('info', main_id, "To use [ Agentic AI WebAgent(ウェブエージェント) ], Specify use at the prompt.")
    print()
    main.main_all_ready = True

    # 無限ループでプロセスを監視
    while True:
        time.sleep(5)


