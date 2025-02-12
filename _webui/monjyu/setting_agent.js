// setting_agent.js

// 最後の設定値を保持するオブジェクト
let last_agent_engine = {
    webAgent: null,
    researchAgent: null,
}
let last_agent_setting = {
    webAgent: null,
    researchAgent: null,
}

// サーバーからAgent設定を取得する関数
function get_agent_setting_all() {
    get_agent_engine( 'webAgent');
    get_agent_setting('webAgent');
    get_agent_engine( 'researchAgent');
    get_agent_setting('researchAgent');
}

// サーバーからengine設定を取得する関数
function get_agent_engine(agent) {
    // engine設定をサーバーから受信
    $.ajax({
        url: '/get_agent_engine',
        method: 'GET',
        data: { agent: agent },
        dataType: 'json',
        success: function(data) {

            // webAgent
            if (agent === 'webAgent') {
                if (JSON.stringify(data) !== last_agent_engine.webAgent) {
                    $('#webAgent_engine').val(data.engine || '');
                    $('#webAgent_model').empty();
                    $('#webAgent_model').append(`<option value="">Auto (自動)</option>`);
                    for (var [key, value] of Object.entries(data.models)) {
                        $('#webAgent_model').append(`<option value="${key}">${value}</option>`);
                    }
                    last_agent_engine.webAgent = JSON.stringify(data);
                }
            }

            // researchAgent
            if (agent === 'researchAgent') {
                if (JSON.stringify(data) !== last_agent_engine.researchAgent) {
                    $('#researchAgent_engine').val(data.engine || '');
                    $('#researchAgent_model').empty();
                    $('#researchAgent_model').append(`<option value="">Auto (自動)</option>`);
                    for (var [key, value] of Object.entries(data.models)) {
                        $('#researchAgent_model').append(`<option value="${key}">${value}</option>`);
                    }
                    last_agent_engine.researchAgent = JSON.stringify(data);
                }
            }

        },
        error: function(xhr, status, error) {
            console.error('get_agent_engine error:', error);
        }
    });
}

// サーバーからAgent設定を取得する関数
function get_agent_setting(agent) {
    // Agent設定をサーバーから受信
    $.ajax({
        url: '/get_agent_setting',
        method: 'GET',
        data: { agent: agent },
        dataType: 'json',
        success: function(data) {

            // webAgent
            if (agent === 'webAgent') {
                if (JSON.stringify(data) !== last_agent_setting.webAgent) {
                    $('#webAgent_model').val(data.model || '');
                    $('#webAgent_max_step').val(data.max_step || '');
                    $('#webAgent_browser').val(data.browser || '');
                    last_agent_setting.webAgent = JSON.stringify(data);
                }
            }

            // researchAgent
            if (agent === 'researchAgent') {
                if (JSON.stringify(data) !== last_agent_setting.researchAgent) {
                    $('#researchAgent_model').val(data.model || '');
                    $('#researchAgent_max_step').val(data.max_step || '');
                    $('#researchAgent_browser').val(data.browser || '');
                    last_agent_setting.researchAgent = JSON.stringify(data);
                }
            }

        },
        error: function(xhr, status, error) {
            console.error('get_agent_setting error:', error);
        }
    });
}

// サーバーへengine設定を保存する関数
function post_agent_engine(agent) {
    var formData = {};

    // webAgent
    if (agent === 'webAgent') {
        formData = {
            agent: agent,
            engine: $('#webAgent_engine').val(),
        };
    }

    // researchAgent
    if (agent === 'researchAgent') {
        formData = {
            agent: agent,
            engine: $('#researchAgent_engine').val(),
        };
    }

    // engine設定をサーバーに送信
    $.ajax({
        url: '/post_agent_engine',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_agent_engine:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_agent_engine error:', error);
        }
    });
}

// サーバーへAgent設定を保存する関数
function post_agent_setting(agent) {
    var formData = {};

    // webAgent
    if (agent === 'webAgent') {
        formData = {
            agent: agent,
            engine: $('#webAgent_engine').val(),
            model: $('#webAgent_model').val(),
            max_step:  $('#webAgent_max_step').val(),
            browser:  $('#webAgent_browser').val(),
        };
    }

    // webAgent
    if (agent === 'researchAgent') {
        formData = {
            agent: agent,
            engine: $('#researchAgent_engine').val(),
            model: $('#researchAgent_model').val(),
            max_step:  $('#researchAgent_max_step').val(),
            browser:  $('#researchAgent_browser').val(),
        };
    }

    // webAgent設定をサーバーに送信
    $.ajax({
        url: '/post_agent_setting',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            console.log('post_agent_setting:', response);
        },
        error: function(xhr, status, error) {
            console.error('post_agent_setting error:', error);
        }
    });
}

// Agent出力(text)
function post_webAgent_request(request_text) {
    $.ajax({
        url: $('#core_endpoint').val() + '/post_webAgent_request',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ request_text: request_text }),
        success: function(response) {
            console.log('post_webAgent_request:', response); // レスポンスをログに表示
        },
        error: function(xhr, status, error) {
            console.error('post_webAgent_request error:', error); // エラーログを出力
        }
    });
}
function post_researchAgent_request(request_text) {
    $.ajax({
        url: $('#core_endpoint').val() + '/post_researchAgent_request',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ request_text: request_text }),
        success: function(response) {
            console.log('post_researchAgent_request:', response); // レスポンスをログに表示
        },
        error: function(xhr, status, error) {
            console.error('post_researchAgent_request error:', error); // エラーログを出力
        }
    });
}

// ドキュメントが読み込まれた時に実行される処理
$(document).ready(function() {

    // ページ遷移時にlocalStorageから復元
    const storedData = JSON.parse(localStorage.getItem('setting_agent_formData'));
    if (storedData) {
        // ページ開始時に保存されたタブを復元
        var activeTab = storedData.activeTab || 'reset';
        $('.tab-content').removeClass('active');
        $('.tab-header button').removeClass('active');
        $('#' + activeTab).addClass('active');
        $('.tab-header button[data-target="' + activeTab + '"]').addClass('active');
        // 入力欄
        $('#webAgent_request').val(storedData.webAgent_request || '');
        $('#researchAgent_request').val(storedData.researchAgent_request || '');
    }

    // ページ遷移時にlocalStorageに保存
    window.onbeforeunload = function() {
        var formData = {
            // ページ遷移時にlocalStorageに保存
            activeTab: $('.tab-header button.active').data('target'),
            // 入力欄
            webAgent_request: $('#webAgent_request').val(),
            researchAgent_request: $('#researchAgent_request').val(),
        };
        localStorage.setItem('setting_agent_formData', JSON.stringify(formData));
    };

    // 定期的に設定値を取得する処理
    setInterval(get_agent_setting_all, 3000);

    $('#webAgent_engine').change(function() {
        post_agent_engine('webAgent');
    });
    $('#webAgent_model, #webAgent_max_step, #webAgent_browser').change(function() {
        post_agent_setting('webAgent');
    });
    
    $('#researchAgent_engine').change(function() {
        post_agent_engine('researchAgent');
    });
    $('#researchAgent_model, #researchAgent_max_step, #researchAgent_browser').change(function() {
        post_agent_setting('researchAgent');
    });

    $('#webAgent-button').click(function() {
        post_webAgent_request( $('#webAgent_request').val() );
        // アニメーション(2秒)
        $('#webAgent_request').addClass('blink-border');
        setTimeout(() => {
            $('#webAgent_request').removeClass('blink-border');
        }, 2000);
    });
    $('#researchAgent-button').click(function() {
        post_researchAgent_request( $('#researchAgent_request').val() );
        // アニメーション(2秒)
        $('#researchAgent_request').addClass('blink-border');
        setTimeout(() => {
            $('#researchAgent_request').removeClass('blink-border');
        }, 2000);
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
