// vision.js

// 入力ファイルのリストを保持する配列
let currentInputFiles = []; 

// 前回受信した画像データを保持する変数
let last_image_data = null; 

// 日時文字列を時刻のみの文字列に変換する関数
function formatDateTime(dateTimeStr) {
    var date = new Date(dateTimeStr);
    var hours = date.getHours().toString().padStart(2, '0'); // 時間を2桁にフォーマット
    var minutes = date.getMinutes().toString().padStart(2, '0'); // 分を2桁にフォーマット
    return `${hours}:${minutes}`; // フォーマットされた時間を返す
}

// ドロップされたファイルをサーバーに送信する関数
function post_drop_files(files) {
    var formData = new FormData();
    $.each(files, function(index, file) {
        formData.append('files', file);
    });
    
    $.ajax({
        url: '/post_drop_files',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
            updateInputFileList(data.files);
        },
        error: function(xhr, status, error) {
            console.error('post_drop_files error:', error);
        }
    });
}

// サーバーから入力ファイルリストを取得し、更新する関数
function get_input_list() {
    $.ajax({
        url: '/get_input_list', // ファイルリスト取得のエンドポイント
        method: 'GET',
        success: function(data) {
            // ファイルリストが更新された場合のみ、リストを更新
            if (JSON.stringify(data.files) !== JSON.stringify(currentInputFiles)) {
                updateInputFileList(data.files);
            }
            currentInputFiles = data.files; // 現在のファイルリストを更新
        },
        error: function(xhr, status, error) {
            console.error('get_input_list error:', error); // エラーログを出力
        }
    });
}

// 入力ファイルリストを更新する関数
function updateInputFileList(files) {
    $('#input_files_list').empty(); // 既存のリストをクリア
        
    // 各ファイルをリストに追加
    files.forEach(file => {
        // フォーマットされた日時を取得
        var formattedTime = formatDateTime(file.upd_time);
        var li = $('<li>');
        var checkbox = $('<input>').attr({
            type:    'checkbox',
            checked: file.checked,
            value:   file.file_name
        });
        li.append(checkbox).append(`${file.file_name} (${formattedTime})`);
        $('#input_files_list').append(li);
    });

}

// イメージ情報を取得する関数
function get_image_info() {
    // サーバーからイメージ情報を取得するAJAXリクエスト
    $.ajax({
        url: '/get_image_info',
        method: 'GET',
        success: function(data) {
            if (data.image_data !== last_image_data) {
                // 画像データが存在する場合
                if (data.image_data) {
                    $('#drop_message').hide();
                    $('#image_img').attr('src', data.image_data);
                    $('#image_img').show();
                } else {
                    $('#image_img').hide();
                    $('#drop_message').show();
                }
                // 画像を2秒間点滅させる
                $('#image_info').addClass('blink-border');
                setTimeout(() => {
                    $('#image_info').removeClass('blink-border');
                }, 2000);
                // 最新の画像データを保持
                last_image_data = data.image_data;
            }
        },
        error: function(xhr, status, error) {
            console.error('get_image_info error:', error);
        }
    });
}

// リクエストをサーバーに送信する共通関数
function post_request(req_mode, system_text, request_text, input_text, result_savepath, result_schema) {
    var file_names = [];
    $('#input_files_list input[type="checkbox"]:checked').each(function() {
        file_names.push($(this).val()); // 選択されたファイル名を追加
    });
    // フォームデータを作成
    var formData = {
        user_id: $('#user_id').val(),
        from_port: '',
        to_port: $('#to_port').val(),
        req_mode: req_mode,
        system_text: system_text,
        request_text: request_text,
        input_text: input_text,
        file_names: file_names,
        result_savepath: result_savepath,
        result_schema: result_schema
    };
    // サーバーにリクエストを送信
    $.ajax({
        url: $('#core_endpoint').val() + '/post_req',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData), // フォームデータをJSON形式に変換
        success: function(response) {
            console.log('post_req:', response); // レスポンスをログに表示
        },
        error: function(xhr, status, error) {
            console.error('post_req error:', error); // エラーログを出力
            alert(error); // エラーメッセージを表示
        }
    });
}

// ユーザーの出力履歴を取得し、出力テキストエリアを更新する関数
let lastOutputData = {};
function get_output_log_user() {
    // サーバーからユーザーの出力履歴を取得するAJAXリクエスト
    $.ajax({
        url: $('#core_endpoint').val() + '/get_output_log_user',
        type: 'GET',
        data: { user_id: $('#user_id').val() },
        success: function(data) {
            // データが存在する場合
            if (data !== null) {
                // 受信データと前回データが異なる場合
                if(JSON.stringify(data) !== JSON.stringify(lastOutputData)) {

                    // テキストエリアの内容を更新
                    $('#output_data').val(data.output_data);

                    // アニメーションを追加
                    $('#output_data').addClass('blink-border');

                    // アニメーション終了後にクラスを削除
                    setTimeout(() => {
                        $('#output_data').removeClass('blink-border');
                    }, 2000); // 2秒間アニメーション

                }
                // 最新のデータを保持
                lastOutputData = data;
            }
        },
        error: function(xhr, status, error) { // パラメータを追加
            console.error('get_output_log_user error:', error); // コロンを追加
        }
    });
}

// ドキュメントが読み込まれた時に実行される処理
$(document).ready(function() {
    // 初期表示
    $('#input_files').hide();
    $('#image_img').hide();
    $('#drop_message').show();

    // 画像情報の初期表示と定期更新
    //get_image_info();
    setInterval(get_image_info, 3000); // 3秒ごとにイメージ情報を更新
    //get_input_list();
    setInterval(get_input_list, 3000); // 3秒ごとに入力ファイルリストを更新
    //get_output_log_user();
    setInterval(get_output_log_user, 2000); // 2秒ごとに出力履歴を更新

    // ページ遷移時にlocalStorageから復元
    const storedData = JSON.parse(localStorage.getItem('vision_formData'));
    if (storedData) {
        $('#vision_request').val(storedData.vision_request || '');
    }

    // ページ遷移時にlocalStorageに保存
    window.onbeforeunload = function() {
        var formData = {
            vision_request: $('#vision_request').val(),
        };
        localStorage.setItem('vision_formData', JSON.stringify(formData));
    };

    // ドラッグ&ドロップ機能のセットアップ
    const dropTargets = document.querySelectorAll('[data-drop-target]');
        
    // 各ドロップターゲットにイベントリスナーを設定
    dropTargets.forEach(target => {
        target.addEventListener('dragover', handleDragOver);
        target.addEventListener('dragleave', handleDragLeave);
        target.addEventListener('drop', handleDrop);
    });

    // ドラッグオーバー時の処理
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('drag-over');
    }

    // ドラッグリーブ時の処理
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
    }

    // ドロップ時の処理
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // 結果表示をクリア
            $('#output_data').val('');
            // 画像を2秒間点滅させる
            $('#output_data').addClass('blink-border');
            setTimeout(() => {
                $('#output_data').removeClass('blink-border');
            }, 2000);
            // ドロップされたファイルをサーバーに送信
            post_drop_files(files);
            // 入力ファイルリストを更新
            get_input_list();
        }
    }

    // クリアボタンのクリックイベント
    $('#clear-button').click(function() {
        $('#vision_request').val('');
        // クリア通知をサーバーに送信
        $.ajax({
            url: $('#core_endpoint').val() + '/post_clear',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ user_id: $('#user_id').val() }), // ユーザーIDを送信
            success: function(response) {
                console.log('post_clear:', response); // レスポンスをログに表示
            },
            error: function(xhr, status, error) {
                console.error('post_clear error:', error); // エラーログを出力
            }
        });
    });

    // 送信ボタンのクリックイベント
    $('#submit-button').click(function() {
        const req = $('#vision_request').val().trim();
        if (req) {
            // 結果表示をクリア
            $('#output_data').val('');
            // 画像を2秒間点滅させる
            $('#output_data').addClass('blink-border');
            setTimeout(() => {
                $('#output_data').removeClass('blink-border');
            }, 2000);
            // リクエスト送信
            post_request($('#req_mode').val(), $('#system_text').val(), req, '', '', '');
        }
    });

    // 画像クリックでExec実行する機能を追加
    $('#image_img').click(function() {
        const req = $('#vision_request').val().trim();
        if (req) {
            // 画像を2秒間点滅させる
            $('#image_info').addClass('blink-border');
            setTimeout(() => {
                $('#image_info').removeClass('blink-border');
            }, 2000);
            // 結果表示をクリア
            $('#output_data').val('');
            // 画像を2秒間点滅させる
            $('#output_data').addClass('blink-border');
            setTimeout(() => {
                $('#output_data').removeClass('blink-border');
            }, 2000);
            // リクエスト送信
            post_request($('#req_mode').val(), $('#system_text').val(), req, '', '', '');
        }
    });

});

