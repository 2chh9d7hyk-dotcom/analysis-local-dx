"""CSSデザインシステム注入モジュール。全ページの先頭で inject_theme() を呼ぶ。"""
import base64 as _b64
import streamlit as st
from PIL import Image as _Image, ImageDraw as _ImageDraw
from src.config import COLORS


def _make_favicon() -> _Image.Image:
    """バーチャートをPIL Image(32×32 RGBA)として生成。st.set_page_config(page_icon=)に渡す。"""
    img = _Image.new("RGBA", (32, 32), (10, 22, 40, 255))
    d = _ImageDraw.Draw(img)
    d.rounded_rectangle([5, 20, 10, 28], radius=2, fill=(37, 99, 235, 255))
    d.rounded_rectangle([13, 14, 18, 28], radius=2, fill=(124, 58, 237, 255))
    d.rounded_rectangle([22, 8, 27, 28], radius=2, fill=(16, 185, 129, 255))
    return img


_FAVICON = _make_favicon()


def _ni(inner: str, color: str) -> str:
    """ナビゲーションアイコン用 base64 SVG data URI。"""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}</svg>'
    )
    return "data:image/svg+xml;base64," + _b64.b64encode(svg.encode()).decode()


_NI_HOME  = _ni('<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', "#2563EB")
_NI_NES   = _ni('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>', "#7C3AED")
_NI_DISC  = _ni('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>', "#D97706")
_NI_DATA  = _ni('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>', "#16A34A")
_NI_CLOSE = _ni('<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>', "#4B5563")


_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

/* ── グローバルリセット ───────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    letter-spacing: 0.02em;
    color: #1F2937;
}

/* ── アプリ背景 ──────────────────────────────────────────── */
.stApp {
    background-color: #F3F4F6 !important;
}

/* ── メインコンテンツエリア ────────────────────────────────── */
.block-container {
    padding: 2rem 2rem 2rem 2rem !important;
    max-width: 1200px !important;
}
/* 末尾の余白を圧縮 */
.block-container > div:last-child {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* ── デフォルトStreamlit要素を非表示 ─────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none; }

/* ── サイドバー ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}
[data-testid="stSidebarNavItems"] {
    gap: 4px;
}

/* ── カードコンポーネント ────────────────────────────────── */
.dx-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}
.dx-card-sm {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    margin-bottom: 12px;
}

/* ── メトリクスカード ────────────────────────────────────── */
.metric-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 24px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    text-align: center;
}
.metric-card .metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.02em;
    color: #1F2937;
}
.metric-card .metric-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #6B7280;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 4px;
}
.metric-card .metric-delta {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 6px;
}
.metric-card .metric-delta.positive { color: #22C55E; }
.metric-card .metric-delta.negative { color: #EF4444; }
.metric-card .metric-delta.neutral  { color: #9CA3AF; }

/* ── ヒーローセクション ──────────────────────────────────── */
.hero-section {
    background: linear-gradient(135deg, #0A1628 0%, #0F2756 48%, #2563EB 100%);
    border-radius: 20px;
    padding: 52px 44px;
    color: #FFFFFF;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-section::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -8%;
    width: 480px;
    height: 480px;
    background: radial-gradient(circle, rgba(99,179,237,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-section::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -5%;
    width: 320px;
    height: 320px;
    background: radial-gradient(circle, rgba(147,51,234,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-section h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #FFFFFF !important;
    margin-bottom: 12px;
}
.hero-section p {
    font-size: 1rem;
    font-weight: 300;
    color: rgba(255,255,255,0.85) !important;
    letter-spacing: 0.03em;
    line-height: 1.7;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 500;
    color: rgba(255,255,255,0.9);
    letter-spacing: 0.05em;
    margin-bottom: 16px;
}

/* ── バッジ・ピル ────────────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-online  { background: #EFF6FF; color: #3B82F6; border: 1px solid #BFDBFE; }
.badge-ai-rpa  { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
.badge-data    { background: #ECFEFF; color: #0891B2; border: 1px solid #A5F3FC; }
.badge-positive{ background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0; }
.badge-warning { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-danger  { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

/* ── セクションヘッダー ──────────────────────────────────── */
.section-header {
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #F3F4F6;
}
.section-header h2 {
    font-size: 1.35rem;
    font-weight: 700;
    color: #1F2937;
    letter-spacing: -0.01em;
    margin: 0;
}
.section-header p {
    font-size: 0.875rem;
    color: #6B7280;
    margin: 4px 0 0 0;
    line-height: 1.7;
    letter-spacing: 0.04em;
}

/* ── ソウルカード（3つの魂）────────────────────────────────── */
.soul-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 28px 28px 28px 24px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.soul-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.05);
    transform: translateY(-2px);
}
.soul-card-icon {
    margin-bottom: 18px;
    line-height: 0;
}
.soul-card-title {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.45;
    margin-bottom: 10px;
}
.soul-card-body {
    font-size: 0.875rem;
    color: #4B5563;
    line-height: 1.7;
    letter-spacing: 0.04em;
}

/* ── アラートボックス（新発見） ──────────────────────────── */
.alert-discovery {
    background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
    border: 1px solid #FED7AA;
    border-left: 4px solid #F59E0B;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.alert-discovery .alert-title {
    font-size: 1rem;
    font-weight: 700;
    color: #92400E;
    margin-bottom: 6px;
}
.alert-discovery .alert-body {
    font-size: 0.9rem;
    color: #78350F;
    line-height: 1.6;
}
.alert-future {
    background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    border: 1px solid #BBF7D0;
    border-left: 4px solid #22C55E;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.alert-future .alert-title {
    font-size: 1rem;
    font-weight: 700;
    color: #14532D;
    margin-bottom: 6px;
}
.alert-future .alert-body {
    font-size: 0.9rem;
    color: #166534;
    line-height: 1.6;
}
.alert-churn {
    background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
    border: 1px solid #FECACA;
    border-left: 4px solid #EF4444;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.alert-churn .alert-title {
    font-size: 1rem;
    font-weight: 700;
    color: #7F1D1D;
    margin-bottom: 6px;
}
.alert-churn .alert-body {
    font-size: 0.9rem;
    color: #991B1B;
    line-height: 1.6;
}

/* ── スコアゲージ ────────────────────────────────────────── */
.score-gauge-container {
    text-align: center;
    padding: 8px;
}
.score-value {
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
}
.score-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6B7280;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 4px;
}
.score-bar-track {
    background: #F3F4F6;
    border-radius: 8px;
    height: 8px;
    margin: 12px 0 4px 0;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.6s ease;
}

/* ── ステップインジケーター ──────────────────────────────── */
.step-container {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 8px;
}
.step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #3B82F6;
    color: white;
    font-weight: 700;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.step-content { flex: 1; padding-top: 4px; }

/* ── プログレスバー（優先度） ────────────────────────────── */
.priority-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.priority-highest { background: #FEE2E2; color: #DC2626; }
.priority-high    { background: #FFEDD5; color: #EA580C; }
.priority-medium  { background: #FEF9C3; color: #CA8A04; }
.priority-low     { background: #F0FDF4; color: #16A34A; }

/* ── Streamlitウィジェット微調整 ─────────────────────────── */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
div[data-testid="stMetric"] label {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #6B7280 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #1F2937 !important;
    letter-spacing: -0.02em !important;
}

/* ── タブ ────────────────────────────────────────────────── */
div[data-testid="stTabs"] button {
    font-weight: 500;
    letter-spacing: 0.02em;
    font-size: 0.9rem;
}

/* ── ボタン ──────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
    border: 1px solid #E5E7EB !important;
}
.stButton > button[kind="primary"] {
    background: #3B82F6 !important;
    border-color: #3B82F6 !important;
    color: white !important;
}

/* ── セレクトボックス・インプット ───────────────────────── */
.stSelectbox select, .stTextInput input {
    border-radius: 8px !important;
    border-color: #E5E7EB !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}

/* ── レスポンシブ（モバイル対応） ───────────────────────── */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 1rem 2rem 1rem !important;
    }
    .hero-section {
        padding: 28px 20px;
    }
    .hero-section h1 {
        font-size: 1.4rem;
    }
    .dx-card {
        padding: 16px;
    }
    .metric-card .metric-value {
        font-size: 1.6rem;
    }
}
@media (max-width: 480px) {
    .dx-card { padding: 12px; }
    .hero-section { padding: 20px 16px; }
}

/* ── ダークモード対応（将来用） ──────────────────────────── */
@media (prefers-color-scheme: dark) {
    /* 必要に応じて追加 */
}

/* ── ハンバーガーナビゲーション（CSS-only, ~セレクター）──── */
/* #dx-hbg-wrap を position:fixed にすることで親要素の transform の影響を遮断する */
#dx-hbg-wrap{position:fixed!important;inset:0;z-index:2147483640;pointer-events:none;overflow:visible;}
#dx-hbg-toggle{display:none;}
#dx-hbg-btn{position:absolute;top:16px;right:20px;width:48px;height:48px;border-radius:50%;background:rgba(37,99,235,0.88);border:1.5px solid rgba(255,255,255,0.45);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);box-shadow:0 4px 24px rgba(0,0,0,0.22);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:auto;user-select:none;transition:background .2s,transform .18s;}
#dx-hbg-btn:hover{background:rgba(37,99,235,1);transform:scale(1.06);}
.dx-bar{display:block;width:20px;height:2px;background:rgba(255,255,255,0.95);margin:3.5px 0;border-radius:2px;transition:transform .25s ease,opacity .2s ease;}
#dx-hbg-overlay{position:absolute;inset:0;background:rgba(10,22,40,0.45);backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);opacity:0;pointer-events:none;transition:opacity .3s;}
#dx-hbg-panel{position:absolute;top:0;right:-320px;width:300px;height:100%;background:#fff;border-left:1px solid #E5E7EB;box-shadow:-8px 0 40px rgba(0,0,0,0.14);display:flex;flex-direction:column;overflow:hidden;pointer-events:auto;font-family:'Noto Sans JP',-apple-system,sans-serif;transition:right .35s cubic-bezier(.4,0,.2,1);}
.dx-nav-link{display:flex;align-items:center;gap:14px;padding:14px 24px;text-decoration:none!important;font-size:.9rem;font-weight:500;letter-spacing:.02em;transition:background .14s;}
.dx-nav-link:hover{background:#F0F7FF;}
.dx-nav-icon{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.dx-close{width:32px;height:32px;border-radius:50%;border:1px solid #E5E7EB;background:#F9FAFB;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:.8rem;color:#6B7280;transition:background .14s;pointer-events:auto;}
.dx-close:hover{background:#F3F4F6;}
/* ~ セレクター: checkbox が checked のとき兄弟要素を制御する */
#dx-hbg-toggle:checked ~ #dx-hbg-overlay{opacity:1!important;pointer-events:auto!important;}
#dx-hbg-toggle:checked ~ #dx-hbg-panel{right:0!important;}
#dx-hbg-toggle:checked ~ #dx-hbg-btn .dx-bar:nth-child(1){transform:rotate(45deg) translate(3.5px,4.5px);}
#dx-hbg-toggle:checked ~ #dx-hbg-btn .dx-bar:nth-child(2){opacity:0;transform:scaleX(0);}
#dx-hbg-toggle:checked ~ #dx-hbg-btn .dx-bar:nth-child(3){transform:rotate(-45deg) translate(3.5px,-4.5px);}
</style>
"""


def _make_hamburger_html(municipality_name: str = "大玉村") -> str:
    """CSS-onlyハンバーガーメニューHTMLを生成する。自治体名を動的に埋め込む。"""
    return (
        f'<div id="dx-hbg-wrap">'
        f'<input type="checkbox" id="dx-hbg-toggle">'
        f'<label for="dx-hbg-toggle" id="dx-hbg-overlay"></label>'
        f'<label for="dx-hbg-toggle" id="dx-hbg-btn">'
        f'<span class="dx-bar"></span><span class="dx-bar"></span><span class="dx-bar"></span>'
        f'</label>'
        f'<aside id="dx-hbg-panel">'
        f'<header style="padding:20px 24px 16px;border-bottom:1px solid #F3F4F6;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">'
        f'<div>'
        f'<div style="font-size:.6rem;font-weight:700;color:#9CA3AF;letter-spacing:.12em;text-transform:uppercase;margin-bottom:3px;">NAVIGATION</div>'
        f'<div style="font-size:.9rem;font-weight:700;color:#1F2937;letter-spacing:-.01em;">{municipality_name} DX</div>'
        f'</div>'
        f'<label for="dx-hbg-toggle" class="dx-close">&#x2715;</label>'
        f'</header>'
        f'<nav style="flex:1;padding:8px 0;overflow-y:auto;">'
        f'<a class="dx-nav-link" href="/home">'
        f'<span class="dx-nav-icon" style="background:#EFF6FF;"><img src="{_NI_HOME}" width="17" height="17" alt=""></span>'
        f'<span style="color:#1E3A8A;">ホーム</span></a>'
        f'<a class="dx-nav-link" href="/nes_dashboard">'
        f'<span class="dx-nav-icon" style="background:#F5F3FF;"><img src="{_NI_NES}" width="17" height="17" alt=""></span>'
        f'<span style="color:#4C1D95;">NES重点領域</span></a>'
        f'<a class="dx-nav-link" href="/improvement_proposal">'
        f'<span class="dx-nav-icon" style="background:#FFFBEB;"><img src="{_NI_DISC}" width="17" height="17" alt=""></span>'
        f'<span style="color:#92400E;">新発見と未来提案</span></a>'
        f'<a class="dx-nav-link" href="/data_management">'
        f'<span class="dx-nav-icon" style="background:#F0FDF4;"><img src="{_NI_DATA}" width="17" height="17" alt=""></span>'
        f'<span style="color:#14532D;">データ管理</span></a>'
        f'</nav>'
        f'<footer style="padding:16px 24px;border-top:1px solid #F3F4F6;flex-shrink:0;">'
        f'<div style="font-size:.7rem;color:#9CA3AF;line-height:1.6;letter-spacing:.03em;">'
        f'{municipality_name} × NES重点領域<br>EBPM ダッシュボード v1.0'
        f'</div>'
        f'</footer>'
        f'</aside>'
        f'</div>'
    )


def inject_theme() -> None:
    """全ページ共通のCSSテーマを注入する。各ページの先頭で呼ぶこと。"""
    name = st.session_state.get("active_municipality_name", "大玉村")
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_make_hamburger_html(name), unsafe_allow_html=True)


def set_page_config(title: str, icon: str = "🏛️") -> None:
    """st.set_page_config のラッパー（共通設定付き）。最初のStreamlit呼び出しであること。"""
    st.set_page_config(
        page_title=f"{title} | 大玉村 DX ダッシュボード",
        page_icon=_FAVICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
