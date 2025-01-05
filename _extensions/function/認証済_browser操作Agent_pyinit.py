#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------
# COPYRIGHT (C) 2014-2025 Mitsuo KONDOU.
# This software is released under the not MIT License.
# Permission from the right holder is required for use.
# https://github.com/ClipnGPT
# Thank you for keeping the rules.
# ------------------------------------------------

# 静的インストール
import sys
import os
import time
import datetime
import codecs

import subprocess

# インターフェース
qText_ready       = 'Browser-use Agent function ready!'
qText_start       = 'Browser-use Agent function start!'
qText_complete    = 'Browser-use Agent function complete!'
qIO_func2py       = 'temp/browser操作Agent_func2py.txt'
qIO_py2func       = 'temp/browser操作Agent_py2func.txt'

def io_text_read(filename=''):
    text = ''
    file1 = filename
    file2 = filename[:-4] + '.@@@'
    try:
        while (os.path.isfile(file2)):
            os.remove(file2)
            time.sleep(0.10)
        if (os.path.isfile(file1)):
            os.rename(file1, file2)
            time.sleep(0.10)
        if (os.path.isfile(file2)):
            r = codecs.open(file2, 'r', 'utf-8-sig')
            for t in r:
                t = t.replace('\r', '')
                text += t
            r.close
            r = None
            time.sleep(0.25)
        while (os.path.isfile(file2)):
            os.remove(file2)
            time.sleep(0.10)
    except:
        pass
    return text

def io_text_write(filename='', text='', ):
    try:
        w = codecs.open(filename, 'w', 'utf-8')
        w.write(text)
        w.close()
        w = None
        return True
    except:
        pass
    return False

# 動的インストール
def pip_install(module='', ver=None):
    try:
        if ver is None:
            pip_parm = ['python', '-m', 'pip', 'install', '--upgrade', module]
            install_proc = subprocess.call(pip_parm, shell=True, )
        else:
            pip_parm = ['python', '-m', 'pip', 'install', '--upgrade', '{}=={}'.format(module, ver)]
            install_proc = subprocess.call(pip_parm, shell=True, )
    except:
        print("pip install error!: {}".format(module))

# 動的インストール
try:
    import langchain_openai
    #import langchain_anthropic
    #import langchain_google_genai

    from browser_use import Agent, Controller
    from browser_use.browser.browser import Browser, BrowserConfig

except:
    print('pip install ...')
    pip_install('pip')
    pip_install('wheel')
    pip_install('setuptools')

    pip_install('pygame')
    pip_install('playwright')
    #print('playwright install ...')
    if (os.name == 'nt'):
        install_proc = subprocess.Popen(['cmd', '/c', 'start playwright install'], shell=True, )
    else:
        install_proc = subprocess.Popen(['playwright install'])

    pip_install('langchain_openai')
    #pip_install('langchain_anthropic')
    #pip_install('langchain_google_genai')
    pip_install('browser_use')

    print('playwright install ...')
    if (os.name == 'nt'):
        install_proc = subprocess.Popen(['cmd', '/c', 'start playwright install'], shell=True, )
    else:
        install_proc = subprocess.Popen(['playwright install'])

    import langchain_openai
    #import langchain_anthropic
    #import langchain_google_genai

    from browser_use import Agent, Controller
    from browser_use.browser.browser import Browser, BrowserConfig



if __name__ == '__main__':

    # 出力フォルダ用意
    if (not os.path.isdir('temp')):
        os.makedirs('temp')

    # 準備完了
    #print(qText_ready)
    res = io_text_write(qIO_py2func, qText_ready)

    print('pip install ok')
    sys.exit(0)


