@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%

echo ja,google,‘æ‚PT‚ÌŒŽ—j“ú‚ÍA•P˜H‰c‹ÆŠ‚ÌƒNƒŠ[ƒ“ƒAƒbƒvŽÀŽ{“ú‚Å‚·B > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_1_sjis.txt"
echo ja,google,‘åì‚³‚ñAG•v‚³‚ñAˆäã‚±‚¤‚Ö‚¢‚³‚ñA‚PŠK‚ð’†S‚ÉA´‘|‚æ‚ë‚µ‚­‚¨Šè‚¢‚µ‚Ü‚·B > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_2_sjis.txt"

exit
