@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%

echo ja,google,��Q�T�̐��j���́A�P�H�c�Ə��̃N���[���A�b�v���{���ł��B > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_1_sjis.txt"
echo ja,google,��c����A���{����A�O�炳��A�Q�K�𒆐S�ɁA���|��낵�����肢���܂��B > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_2_sjis.txt"

exit
