@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%
echo ja,google,18���ł��B�Ō�̑ދΎ҂́A�G�X�A�����A�G�X�A�{���A�P�C�A�A�x���A�f�B�[�A�ō��B���f�������悤�ɁA�G�X�G�X�P�C�A�A�f�B�[�B�Y�ꂸ�ɂ��肢���܂��B > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_sjis.txt"
exit
