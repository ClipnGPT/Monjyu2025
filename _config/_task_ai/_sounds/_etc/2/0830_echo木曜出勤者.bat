@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%

echo ja,google,おはようございます。 > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_1_sjis.txt"
echo ja,google,木曜日の出勤予定者は、近藤さん、藤本さん、大田さん、土居さん、井上こうへいさん、山西さん、ひださん、です。 > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_2_sjis.txt"

exit
