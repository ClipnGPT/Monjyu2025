@echo off
set yyyy=%date:~0,4%
set mm=%date:~5,2%
set dd=%date:~8,2%
set time2=%time: =0%
set hh=%time2:~0,2%
set mn=%time2:~3,2%
set dt=%yyyy%%mm%%dd%%hh%%mn%

echo ja,google,第１週の月曜日は、姫路営業所のクリーンアップ実施日です。 > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_1_sjis.txt"
echo ja,google,大川さん、秀夫さん、井上こうへいさん、１階を中心に、清掃よろしくお願いします。 > "c:\RiKi_assistant\temp\s6_5tts_txt\%dt%_2_sjis.txt"

exit
