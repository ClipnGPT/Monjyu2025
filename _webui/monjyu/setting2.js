// setting2.js

// 最後の設定値を保持するオブジェクト
let last_addins_setting = null;
let last_engine_models = {
    openrt: null,
    ollama: null,
};
let last_engine_setting = {
    openrt: null,
    ollama: null,
};
let last_live_setting = {
    freeai: null,
    openai: null,
}
let last_webAgent_engine = {
    useBrowser: null,
    modelAPI: null,
}
let last_webAgent_setting = {
    modelName: null,
    maxSteps: null,
}

// サーバーから設定値を取得する関数
function get_addins_setting() {
    // 設定値をサーバーから受信
    $.ajax({
        url: '/get_addins_setting',
        method: 'GET',
        success: function(data) {
            if (JSON.stringify(data) !== last_addins_setting) {
                $('#result_text_save').val(data.result_text_save || '');
                $('#speech_stt_engine').val(data.speech_stt_engine || '');
                $('#speech_tts_engine').val(data.speech_tts_engine || '');
                $('#text_clip_input').val(data.text_clip_input || '');
                $('#text_url_execute').val(data.text_url_execute || '');
                $('#text_pdf_execute').val(data.text_pdf_execute || '');
                $('#image_ocr_execute').val(data.image_ocr_execute || '');
                $('#image_yolo_execute').val(data.image_yolo_execute || '');
                last_addins_setting = JSON.stringify(data);
            }    
        },
        error: function(xhr, status, error) {
            console.error('get_addins_setting error:', error);
        }
    });
}

// サーバーへ設定値を保存する関数
function post_addins_setting() {
    var formData = {};
    formData = {
        result_text_save: $('#result_text_save').val(),
        speech_stt_engine: $('#speech_stt_engine').val(),
        speech_tts_engine: $('#speech_tts_engine').val(),
        text_clip_input: $('#text_clip_input').val(),
        text_url_execute: $('#text_url_execute').val(),
        text_pdf_execute: $('#text_pdf_execute').val(),
        image_ocr_execute: $('#image_ocr_execute').val(),
        image_yolo_execute: $('#image_yolo_execute').val(),
    }
    // 設定値をサーバーに送信
    $.ajax({
        url: '/post_addins_setting',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_addins_setting:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_addins_setting error:', error);
        }
    });
}

// エンジンのmodels情報を取得してコンボボックスを設定する関数
function get_engine_models(engine) {
    $.ajax({
        url: '/get_engine_models',
        method: 'GET',
        data: { engine: engine },
        dataType: 'json',
        async: false, // 同期処理
        success: function(data) {

            // openrt
            if (engine === 'openrt') {
                if (JSON.stringify(data) !== last_engine_models.openrt) {
                    // 既存の選択肢を削除
                    $('#ort_a_model').empty();
                    $('#ort_b_model').empty();
                    $('#ort_v_model').empty();
                    $('#ort_x_model').empty();
                    // 取得した選択肢を設定
                    $('#ort_a_model').append(`<option value="">Auto (自動)</option>`);
                    $('#ort_b_model').append(`<option value="">Auto (自動)</option>`);
                    $('#ort_v_model').append(`<option value="">Auto (自動)</option>`);
                    $('#ort_x_model').append(`<option value="">Auto (自動)</option>`);
                    for (var [key, value] of Object.entries(data)) {
                        $('#ort_a_model').append(`<option value="${key}">${value}</option>`);
                        $('#ort_b_model').append(`<option value="${key}">${value}</option>`);
                        $('#ort_v_model').append(`<option value="${key}">${value}</option>`);
                        $('#ort_x_model').append(`<option value="${key}">${value}</option>`);
                    }
                    last_engine_models.openrt = JSON.stringify(data);
                }
            }

            // ollama
            if (engine === 'ollama') {
                if (JSON.stringify(data) !== last_engine_models.ollama) {
                    // 既存の選択肢を削除
                    $('#olm_a_model').empty();
                    $('#olm_b_model').empty();
                    $('#olm_v_model').empty();
                    $('#olm_x_model').empty();
                    // 取得した選択肢を設定
                    $('#olm_a_model').append(`<option value="">Auto (自動)</option>`);
                    $('#olm_b_model').append(`<option value="">Auto (自動)</option>`);
                    $('#olm_v_model').append(`<option value="">Auto (自動)</option>`);
                    $('#olm_x_model').append(`<option value="">Auto (自動)</option>`);
                    for (var [key, value] of Object.entries(data)) {
                        $('#olm_a_model').append(`<option value="${key}">${value}</option>`);
                        $('#olm_b_model').append(`<option value="${key}">${value}</option>`);
                        $('#olm_v_model').append(`<option value="${key}">${value}</option>`);
                        $('#olm_x_model').append(`<option value="${key}">${value}</option>`);
                    }
                    last_engine_models.ollama = JSON.stringify(data);
                }
            }

        },
        error: function(xhr, status, error) {
            console.error('get_engine_models error:', error);
        }
    });
}

// サーバーからエンジンの設定値を取得する関数
function get_engine_setting_all(engine) {
    get_engine_setting('openrt');
    get_engine_models('ollama');
    get_engine_setting('ollama');
}
function get_engine_setting(engine) {
    // 設定値をサーバーから受信
    $.ajax({
        url: '/get_engine_setting',
        method: 'GET',
        data: { engine: engine },
        dataType: 'json',
        success: function(data) {

            // openrt
            if (engine === 'openrt') {
                if (JSON.stringify(data) !== last_engine_setting.openrt) {
                    $('#ort_max_wait_sec').val(data.max_wait_sec || '');
                    $('#ort_a_model').val(data.a_model || '');
                    $('#ort_a_use_tools').val(data.a_use_tools || '');
                    $('#ort_b_model').val(data.b_model || '');
                    $('#ort_b_use_tools').val(data.b_use_tools || '');
                    $('#ort_v_model').val(data.v_model || '');
                    $('#ort_v_use_tools').val(data.v_use_tools || '');
                    $('#ort_x_model').val(data.x_model || '');
                    $('#ort_x_use_tools').val(data.x_use_tools || '');
                    last_engine_setting.openrt = JSON.stringify(data);
                }    
            }    

            // ollama
            if (engine === 'ollama') {
                if (JSON.stringify(data) !== last_engine_setting.ollama) {
                    $('#olm_max_wait_sec').val(data.max_wait_sec || '');
                    $('#olm_a_model').val(data.a_model || '');
                    $('#olm_a_use_tools').val(data.a_use_tools || '');
                    $('#olm_b_model').val(data.b_model || '');
                    $('#olm_b_use_tools').val(data.b_use_tools || '');
                    $('#olm_v_model').val(data.v_model || '');
                    $('#olm_v_use_tools').val(data.v_use_tools || '');
                    $('#olm_x_model').val(data.x_model || '');
                    $('#olm_x_use_tools').val(data.x_use_tools || '');
                    last_engine_setting.openrt = JSON.stringify(data);
                }    
            }    

        },
        error: function(xhr, status, error) {
            console.error('get_engine_setting error:', error);
        }
    });
}

// サーバーへ設定値を保存する関数
function post_engine_setting(engine) {
    var formData = {};

    // openrt
    if (engine === 'openrt') {
        formData = {
            engine: 'openrt',
            max_wait_sec: $('#ort_max_wait_sec').val(),
            a_model: $('#ort_a_model').val(),
            a_use_tools: $('#ort_a_use_tools').val(),
            b_model: $('#ort_b_model').val(),
            b_use_tools: $('#ort_b_use_tools').val(),
            v_model: $('#ort_v_model').val(),
            v_use_tools: $('#ort_v_use_tools').val(),
            x_model: $('#ort_x_model').val(),
            x_use_tools: $('#ort_x_use_tools').val(),
        }
    }

    // ollama
    if (engine === 'ollama') {
        formData = {
            engine: 'ollama',
            max_wait_sec: $('#olm_max_wait_sec').val(),
            a_model: $('#olm_a_model').val(),
            a_use_tools: $('#olm_a_use_tools').val(),
            b_model: $('#olm_b_model').val(),
            b_use_tools: $('#olm_b_use_tools').val(),
            v_model: $('#olm_v_model').val(),
            v_use_tools: $('#olm_v_use_tools').val(),
            x_model: $('#olm_x_model').val(),
            x_use_tools: $('#olm_x_use_tools').val(),
        }
    }

    // 設定値をサーバーに送信
    $.ajax({
        url: '/post_engine_setting',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_engine_setting:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_engine_setting error:', error);
        }
    });
}

// Voiceの情報を取得してコンボボックスを設定する関数
function get_live_voices(engine) {
    $.ajax({
        url: '/get_live_voices',
        method: 'GET',
        data: { engine: engine },
        dataType: 'json',
        async: false, // 同期処理
        success: function(data) {

            // freeai
            if (engine === 'freeai') {
                // 取得した選択肢を設定
                for (var [key, value] of Object.entries(data)) {
                    $('#freeai_voice').append(`<option value="${key}">${value}</option>`);
                }
            }

            // openai
            if (engine === 'openai') {
                // 取得した選択肢を設定
                for (var [key, value] of Object.entries(data)) {
                    $('#openai_voice').append(`<option value="${key}">${value}</option>`);
                }
            }

        },
        error: function(xhr, status, error) {
            console.error('get_live_voices error:', error);
        }
    });
}

// サーバーからLive設定を取得する関数
function get_live_setting_all() {
    get_live_setting('freeai');
    get_live_setting('openai');
}
function get_live_setting(engine) {
    // Live設定をサーバーから受信
    $.ajax({
        url: '/get_live_setting',
        method: 'GET',
        data: { engine: engine },
        dataType: 'json',
        success: function(data) {

            // freeai
            if (engine === 'freeai') {
                if (JSON.stringify(data) !== last_live_setting.freeai) {
                    $('#freeai_voice').val(data.voice || '');
                    $('#freeai_shot_interval_sec').val(data.shot_interval_sec || '');
                    $('#freeai_clip_interval_sec').val(data.clip_interval_sec || '');
                    last_live_setting.freeai = JSON.stringify(data);
                }
            }

            // openai
            if (engine === 'openai') {
                if (JSON.stringify(data) !== last_live_setting.openai) {
                    $('#openai_voice').val(data.voice || '');
                    $('#openai_shot_interval_sec').val(data.shot_interval_sec || '');
                    $('#openai_clip_interval_sec').val(data.clip_interval_sec || '');
                    last_live_setting.openai = JSON.stringify(data);
                }
            }

        },
        error: function(xhr, status, error) {
            console.error('get_live_setting error:', error);
        }
    });
}

// サーバーへLive設定を保存する関数
function post_live_setting(engine) {
    var formData = {};

    // freeai
    if (engine === 'freeai') {
        formData = {
            engine: engine,
            voice: $('#freeai_voice').val(),
            shot_interval_sec: $('#freeai_shot_interval_sec').val(),
            clip_interval_sec: $('#freeai_clip_interval_sec').val(),
        };
    }

    // openai
    if (engine === 'openai') {
        formData = {
            engine: engine,
            voice: $('#openai_voice').val(),
            shot_interval_sec: $('#openai_shot_interval_sec').val(),
            clip_interval_sec: $('#openai_clip_interval_sec').val(),
        };
    }

    // Live設定をサーバーに送信
    $.ajax({
        url: '/post_live_setting',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_live_setting:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_live_setting error:', error);
        }
    });
}

// サーバーからAgent設定を取得する関数
function get_agent_setting_all() {
    get_webAgent_engine();
    get_webAgent_setting( $('#webAgent_modelAPI').val() );
}

// サーバーからwebAgent engine設定を取得する関数
function get_webAgent_engine() {
    // webAgent API設定をサーバーから受信
    $.ajax({
        url: '/get_webAgent_engine',
        method: 'GET',
        dataType: 'json',
        success: function(data) {

            if (JSON.stringify(data) !== last_webAgent_engine) {
                $('#webAgent_useBrowser').val(data.useBrowser || '');
                $('#webAgent_modelAPI').val(data.modelAPI || '');
                const element = document.getElementById("webAgent_modelName");
                for (let i=element.length-1;i >= 0; i--) {
                   element.remove( i );
                }
                $('#webAgent_modelName').append(`<option value="">Auto (自動)</option>`);
                for (var [key, value] of Object.entries(data.modelNames)) {
                    $('#webAgent_modelName').append(`<option value="${key}">${value}</option>`);
                }
                $('#webAgent_modelName').val('');
                $('#webAgent_maxSteps').val('');
                last_webAgent_setting = {
                    modelName: null,
                    maxSteps: null,
                }
                last_webAgent_engine = JSON.stringify(data);
            }

        },
        error: function(xhr, status, error) {
            console.error('get_webAgent_engine error:', error);
        }
    });
}

// サーバーからwebAgent設定を取得する関数
function get_webAgent_setting(modelAPI) {
    // webAgent設定をサーバーから受信
    $.ajax({
        url: '/get_webAgent_setting',
        method: 'GET',
        data: { modelAPI: modelAPI },
        dataType: 'json',
        success: function(data) {

            if (JSON.stringify(data) !== last_webAgent_setting) {
                $('#webAgent_modelName').val(data.modelName || '');
                $('#webAgent_maxSteps').val(data.maxSteps || '');
                last_webAgent_setting = JSON.stringify(data);
            }

        },
        error: function(xhr, status, error) {
            console.error('get_webAgent_setting error:', error);
        }
    });
}

// サーバーへwebAgent engine設定を保存する関数
function post_webAgent_engine() {
    var formData = {};

    formData = {
        useBrowser: $('#webAgent_useBrowser').val(),
        modelAPI: $('#webAgent_modelAPI').val(),
    };

    // webAgent設定をサーバーに送信
    $.ajax({
        url: '/post_webAgent_engine',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_webAgent_engine:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_webAgent_engine error:', error);
        }
    });
}

// サーバーへwebAgent setting設定を保存する関数
function post_webAgent_setting(modelAPI) {
    var formData = {};

    formData = {
        modelAPI: modelAPI,
        modelName: $('#webAgent_modelName').val(),
        maxSteps:  $('#webAgent_maxSteps').val(),
    };

    // webAgent設定をサーバーに送信
    $.ajax({
        url: '/post_webAgent_setting',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_webAgent_setting:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_webAgent_setting error:', error);
        }
    });
}

// Reactを差し替える関数
function post_set_react(filename) {
    var formData = {};
    formData = {
        filename: filename,
    }
    // 設定値をサーバーに送信
    $.ajax({
        url: '/post_set_react',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_set_react:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_set_react error:', error);
        }
    });
}

// ドキュメントが読み込まれた時に実行される処理
$(document).ready(function() {

    // ページ遷移時にlocalStorageから復元
    const storedData = JSON.parse(localStorage.getItem('setting2_formData'));
    if (storedData) {
        // ページ開始時に保存されたタブを復元
        var activeTab = storedData.activeTab || 'reset';
        $('.tab-content').removeClass('active');
        $('.tab-header button').removeClass('active');
        $('#' + activeTab).addClass('active');
        $('.tab-header button[data-target="' + activeTab + '"]').addClass('active');
    }

    // ページ遷移時にlocalStorageに保存
    window.onbeforeunload = function() {
        var formData = {
            // ページ遷移時にlocalStorageに保存
            activeTab: $('.tab-header button.active').data('target')
        };
        localStorage.setItem('setting2_formData', JSON.stringify(formData)); // localStorageに保存
    };

    // エンジンのmodels設定を取得
    get_engine_models('openrt');
    get_engine_models('ollama');

    // Liveのvoices設定を取得
    get_live_voices('freeai');
    get_live_voices('openai');

    // 定期的に設定値を取得する処理
    setInterval(get_addins_setting, 3000);
    setInterval(get_engine_setting_all, 3100);
    setInterval(get_live_setting_all, 3200);
    setInterval(get_agent_setting_all, 3300);

    $('#result_text_save, #speech_stt_engine, #speech_tts_engine, #text_clip_input, #text_url_execute, #text_pdf_execute, #image_ocr_execute, #image_yolo_execute').change(function() {
        post_addins_setting();
    });
    $('#ort_max_wait_sec, #ort_a_model, #ort_a_use_tools, #ort_b_model, #ort_b_use_tools, #ort_v_model, #ort_v_use_tools, #ort_x_model, #ort_x_use_tools').change(function() {
        post_engine_setting('openrt');
    });
    $('#ort-a2bvx-button').click(function() {
        $('#ort_b_model').val( $('#ort_a_model').val() );
        $('#ort_b_use_tools').val( $('#ort_a_use_tools').val() );
        $('#ort_v_model').val( $('#ort_a_model').val() );
        $('#ort_v_use_tools').val( $('#ort_a_use_tools').val() );
        $('#ort_x_model').val( $('#ort_a_model').val() );
        $('#ort_x_use_tools').val( $('#ort_a_use_tools').val() );
        post_engine_setting('openrt');
    });
    $('#olm_max_wait_sec, #olm_a_model, #olm_a_use_tools, #olm_b_model, #olm_b_use_tools, #olm_v_model, #olm_v_use_tools, #olm_x_model, #olm_x_use_tools').change(function() {
        post_engine_setting('ollama');
    });
    $('#olm-a2bvx-button').click(function() {
        $('#olm_b_model').val( $('#olm_a_model').val() );
        $('#olm_b_use_tools').val( $('#olm_a_use_tools').val() );
        $('#olm_v_model').val( $('#olm_a_model').val() );
        $('#olm_v_use_tools').val( $('#olm_a_use_tools').val() );
        $('#olm_x_model').val( $('#olm_a_model').val() );
        $('#olm_x_use_tools').val( $('#olm_a_use_tools').val() );
        post_engine_setting('ollama');
    });
    $('#freeai_voice, #freeai_shot_interval_sec, #freeai_clip_interval_sec').change(function() {
        post_live_setting('freeai');
    });
    $('#openai_voice, #openai_shot_interval_sec, #openai_clip_interval_sec').change(function() {
        post_live_setting('openai');
    });
    $('#webAgent_useBrowser, #webAgent_modelAPI').change(function() {
        post_webAgent_engine();
        get_agent_setting_all();
    });
    $('#webAgent_modelName, #webAgent_maxSteps').change(function() {
        post_webAgent_setting( $('#webAgent_modelAPI').val() );
    });
    
    // リセットボタンのクリックイベント
    $('#reset-button').click(function() {
        if (confirm("全ての設定をリセットしますか?")) {
            // リセット処理を実行
            $.ajax({
                url: $('#core_endpoint').val() + '/post_reset',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ user_id: $('#user_id').val() }),
                success: function(response) {
                    console.log('post_reset:', response);
                },
                error: function(xhr, status, error) {
                    console.error('post_reset error:', error);
                }
            });
        }
    });
    
    $('#react-halloWorld').click(function() {
        post_set_react('react-sample-halloWorld.zip');
    });
    $('#react-realtimeConsole').click(function() {
        post_set_react('openai-realtime-console-main.zip');
    });

    // タブ切り替え処理
    $('.frame-tab .tab-header button').click(function() {
        var target = $(this).data('target');
        var frame = $(this).closest('.frame-tab');
        frame.find('.tab-header button').removeClass('active');
        $(this).addClass('active');
        frame.find('.tab-content').removeClass('active');
        frame.find('#' + target).addClass('active');
    });

});
