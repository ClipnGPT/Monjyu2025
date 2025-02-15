@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%
echo ja,google,‚¨‚Í‚æ‚¤‚²‚´‚¢‚Ü‚· > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_sjis.txt"
exit
