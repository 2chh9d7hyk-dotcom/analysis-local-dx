"""再利用可能なUIコンポーネント群。st.markdown経由でHTML/CSSを出力する。"""
from __future__ import annotations
import streamlit as st
from src.config import COLORS, NES_AREAS


def hero_section(title: str, subtitle: str, badge: str | None = None) -> None:
    """ページトップのグラデーションヒーローセクション。"""
    badge_html = f'<div class="hero-badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="hero-section">
            {badge_html}
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, description: str = "") -> None:
    """セクション区切りヘッダー。"""
    desc_html = f'<p>{description}</p>' if description else ""
    st.markdown(
        f"""
        <div class="section-header">
            <h2>{title}</h2>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(
    value: str,
    label: str,
    delta: str | None = None,
    delta_type: str = "neutral",  # "positive" / "negative" / "neutral"
    accent_color: str | None = None,
) -> None:
    """プレミアムメトリクスカード。"""
    delta_html = (
        f'<div class="metric-delta {delta_type}">{delta}</div>' if delta else ""
    )
    color_style = f"color: {accent_color};" if accent_color else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value" style="{color_style}">{value}</div>
            <div class="metric-label">{label}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_card(score: float, label: str, color: str, max_score: float = 100) -> None:
    """スコア表示カード（プログレスバー付き）。"""
    pct = min(score / max_score * 100, 100)
    st.markdown(
        f"""
        <div class="dx-card" style="text-align: center;">
            <div class="score-value" style="color: {color};">{score:.0f}</div>
            <div class="score-label">{label}</div>
            <div class="score-bar-track">
                <div class="score-bar-fill" style="width: {pct}%; background: {color};"></div>
            </div>
            <div style="font-size: 0.72rem; color: #9CA3AF;">{pct:.0f} / 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nes_area_badge(area_key: str) -> str:
    """NES重点領域のバッジHTML文字列を返す（st.markdownに埋め込んで使う）。"""
    area = NES_AREAS.get(area_key, {})
    label = area.get("label", area_key)
    css_class = {
        "online": "badge-online",
        "ai_rpa": "badge-ai-rpa",
        "data": "badge-data",
        "positive": "badge-positive",
    }.get(area_key, "badge-online")
    icon = area.get("icon", "")
    icon_html = f"{icon} " if icon else ""
    return f'<span class="badge {css_class}">{icon_html}{label}</span>'


_SVG_SEARCH = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none"'
    ' stroke="#92400E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' style="display:inline-block;vertical-align:-3px;margin-right:7px;flex-shrink:0;">'
    '<circle cx="11" cy="11" r="8"></circle>'
    '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>'
    '</svg>'
)
_SVG_WARN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none"'
    ' stroke="#7F1D1D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' style="display:inline-block;vertical-align:-3px;margin-right:7px;flex-shrink:0;">'
    '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>'
    '<line x1="12" y1="9" x2="12" y2="13"></line>'
    '<line x1="12" y1="17" x2="12.01" y2="17"></line>'
    '</svg>'
)
_SVG_SPROUT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none"'
    ' stroke="#14532D" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    ' style="display:inline-block;vertical-align:-3px;margin-right:7px;flex-shrink:0;">'
    '<path d="M12 22V12"></path>'
    '<path d="M12 12C12 7 7 4.5 3 6c.5 4 4 7 9 6z"></path>'
    '<path d="M12 12c0-5 5-7.5 9-6-.5 4-4 7-9 6z"></path>'
    '</svg>'
)


def alert_discovery(title: str, body: str) -> None:
    """新発見アラート（オレンジ系）。データから見つかった驚きの事実。"""
    st.markdown(
        f"""
        <div class="alert-discovery">
            <div class="alert-title">{_SVG_SEARCH}{title}</div>
            <div class="alert-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alert_churn(title: str, body: str) -> None:
    """離脱リスクアラート（レッド系）。"""
    st.markdown(
        f"""
        <div class="alert-churn">
            <div class="alert-title">{_SVG_WARN}{title}</div>
            <div class="alert-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alert_future(title: str, body: str) -> None:
    """未来提案アラート（グリーン系）。職員を突き動かすポジティブビジョン。"""
    st.markdown(
        f"""
        <div class="alert-future">
            <div class="alert-title">{_SVG_SPROUT}{title}</div>
            <div class="alert-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_container(content_fn, *args, **kwargs) -> None:
    """カードスタイルのコンテナ内でコンテンツ関数を実行する。"""
    st.markdown('<div class="dx-card">', unsafe_allow_html=True)
    content_fn(*args, **kwargs)
    st.markdown("</div>", unsafe_allow_html=True)


def step_indicator(number: int, title: str, description: str = "") -> None:
    """ステップ番号付きの手順インジケーター。"""
    desc_html = f'<p style="font-size:0.875rem; color:#6B7280; margin:4px 0 0 0;">{description}</p>' if description else ""
    st.markdown(
        f"""
        <div class="step-container">
            <div class="step-number">{number}</div>
            <div class="step-content">
                <strong style="font-size:1rem; color:#1F2937;">{title}</strong>
                {desc_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def priority_badge(level: str) -> str:
    """優先度バッジのHTML文字列。level: 'highest'/'high'/'medium'/'low'"""
    labels = {
        "highest": ("最優先", "priority-highest"),
        "high": ("優先", "priority-high"),
        "medium": ("最適化中", "priority-medium"),
        "low": ("改善検討", "priority-low"),
    }
    label, css = labels.get(level, ("不明", "priority-low"))
    return f'<span class="priority-badge {css}">{label}</span>'


def info_table_row(label: str, value: str, highlight: bool = False) -> str:
    """情報テーブルの行HTML（改行なし単行で返す）。"""
    bg = "background:#F0FDF4;" if highlight else ""
    s1 = "padding:8px 12px;font-size:0.85rem;color:#6B7280;font-weight:500;border-bottom:1px solid #F3F4F6;white-space:nowrap;"
    s2 = "padding:8px 12px;font-size:0.9rem;color:#1F2937;font-weight:600;border-bottom:1px solid #F3F4F6;"
    return f'<tr style="{bg}"><td style="{s1}">{label}</td><td style="{s2}">{value}</td></tr>'


def info_table(rows: list[tuple[str, str, bool]]) -> None:
    """ラベル:値のシンプルな情報テーブル。rows = [(label, value, highlight), ...]"""
    rows_html = "".join(info_table_row(lbl, val, hl) for lbl, val, hl in rows)
    # 改行なし単行HTMLにすることでMarkdownパーサーが </table> を生テキスト扱いするのを防ぐ
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;">{rows_html}</table>',
        unsafe_allow_html=True,
    )


def divider() -> None:
    """細いグレーの区切り線。"""
    st.markdown(
        '<hr style="border: none; border-top: 1px solid #F3F4F6; margin: 24px 0;">',
        unsafe_allow_html=True,
    )


def spacer(height: int = 16) -> None:
    """縦方向の余白。"""
    st.markdown(f'<div style="height: {height}px;"></div>', unsafe_allow_html=True)
