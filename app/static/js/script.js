/* 全自動議事録生成アプリ JavaScript */

// ページロード時の処理
document.addEventListener('DOMContentLoaded', function() {
    // フラッシュメッセージの自動非表示
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // Bootstrapのalertインスタンスを取得して閉じる
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        });
    }, 5000); // 5秒後に非表示
    
    // ページ遷移時のローディング表示（必要に応じて）
    const links = document.querySelectorAll('a:not([target="_blank"])');
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // 同じページ内のアンカーリンクは除外
            if (this.getAttribute('href').startsWith('#')) {
                return true;
            }
            
            // 処理に時間がかかる場合のローディング表示
            // showLoading();
        });
    });
    
    // フォーム送信時のバリデーション
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// ローディング表示
function showLoading() {
    // 既存のローディング表示があれば削除
    hideLoading();
    
    // ローディング表示の要素を作成
    const loadingEl = document.createElement('div');
    loadingEl.id = 'page-loading';
    loadingEl.innerHTML = `
        <div class="loading-wrapper">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">処理中...</p>
        </div>
    `;
    
    // スタイルを設定
    loadingEl.style.position = 'fixed';
    loadingEl.style.top = '0';
    loadingEl.style.left = '0';
    loadingEl.style.width = '100%';
    loadingEl.style.height = '100%';
    loadingEl.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
    loadingEl.style.display = 'flex';
    loadingEl.style.justifyContent = 'center';
    loadingEl.style.alignItems = 'center';
    loadingEl.style.zIndex = '9999';
    
    // bodyに追加
    document.body.appendChild(loadingEl);
}

// ローディング非表示
function hideLoading() {
    const loadingEl = document.getElementById('page-loading');
    if (loadingEl) {
        loadingEl.remove();
    }
}

// テーブル行のクリックイベント（詳細表示など）
function setupTableRowClick() {
    const tableRows = document.querySelectorAll('table tbody tr[data-id]');
    tableRows.forEach(function(row) {
        row.addEventListener('click', function(e) {
            // リンクやボタンがクリックされた場合は何もしない
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || 
                e.target.closest('a') || e.target.closest('button')) {
                return;
            }
            
            // 行のデータIDを取得
            const id = this.getAttribute('data-id');
            if (id) {
                // 詳細ページへの遷移など
                // window.location.href = `/results/detail/${id}`;
            }
        });
    });
}

// クリップボードへのコピー機能
function copyToClipboard(text, successCallback) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(function() {
                if (typeof successCallback === 'function') {
                    successCallback();
                }
            })
            .catch(function(err) {
                console.error('クリップボードへのコピーに失敗しました:', err);
            });
    } else {
        // フォールバック（古いブラウザ対応）
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.top = '0';
        textArea.style.left = '0';
        textArea.style.width = '2em';
        textArea.style.height = '2em';
        textArea.style.padding = '0';
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';
        textArea.style.background = 'transparent';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful && typeof successCallback === 'function') {
                successCallback();
            }
        } catch (err) {
            console.error('クリップボードへのコピーに失敗しました:', err);
        }
        
        document.body.removeChild(textArea);
    }
}

// 日時のフォーマット
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 文字列の省略表示
function truncateText(text, maxLength = 50) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    
    return text.substring(0, maxLength) + '...';
} 