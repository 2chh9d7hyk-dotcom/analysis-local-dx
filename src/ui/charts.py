"""Plotlyチャートファクトリー。デザインシステムに準拠したスタイル統一チャートを生成する。"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.config import COLORS, NES_AREAS

# ── 共通レイアウト設定 ─────────────────────────────────────────

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family="'Noto Sans JP', -apple-system, sans-serif",
        color=COLORS["text_main"],
        size=12,
    ),
    margin=dict(l=16, r=16, t=32, b=16),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        gridcolor="#F3F4F6",
        gridwidth=1,
        showgrid=False,
        zeroline=False,
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color=COLORS["text_sub"]),
    ),
    yaxis=dict(
        gridcolor="#F3F4F6",
        gridwidth=1,
        showgrid=True,
        zeroline=False,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color=COLORS["text_sub"]),
    ),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#E5E7EB",
        font=dict(family="'Noto Sans JP', sans-serif", size=12, color=COLORS["text_main"]),
    ),
)


def _apply_base(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(height=height, **_BASE_LAYOUT)
    return fig


# ── チャートファクトリー関数 ────────────────────────────────────

def line_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str],
    labels: dict[str, str] | None = None,
    colors: list[str] | None = None,
    title: str = "",
    height: int = 340,
    area: bool = True,
) -> go.Figure:
    """折れ線（+エリアグラデーション）グラフ。スペック: 線幅3px以上、グラデーション塗り。"""
    _colors = colors or [
        COLORS["online"], COLORS["ai_rpa"], COLORS["data"], COLORS["positive"]
    ]
    _labels = labels or {}
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        color = _colors[i % len(_colors)]
        fill_color = color.replace(")", ", 0.12)").replace("rgb(", "rgba(")
        # hex → rgba 変換
        if color.startswith("#"):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            fill_color = f"rgba({r},{g},{b},0.10)"

        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[col],
                mode="lines+markers",
                name=_labels.get(col, col),
                line=dict(color=color, width=3, shape="spline"),
                marker=dict(size=7, color=color, line=dict(color="white", width=2)),
                fill="tozeroy" if area else "none",
                fillcolor=fill_color if area else None,
                hovertemplate=f"<b>{_labels.get(col, col)}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.update_layout(title=dict(text=title, font=dict(size=14, weight="bold"), x=0))
    return _apply_base(fig, height)


def radar_chart(
    categories: list[str],
    values_list: list[tuple[str, list[float], str]],
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """レーダーチャート。values_list = [(name, values, color), ...]"""
    fig = go.Figure()
    for name, values, color in values_list:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor=f"rgba({r},{g},{b},0.10)",
                line=dict(color=color, width=3),
                name=name,
                marker=dict(size=8, color=color),
                hovertemplate="<b>%{theta}</b><br>スコア: %{r:.1f}<extra></extra>",
            )
        )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=True,
                tickfont=dict(size=10, color=COLORS["text_muted"]),
                gridcolor="#E5E7EB",
                linecolor="#E5E7EB",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=COLORS["text_sub"], family="'Noto Sans JP'"),
                linecolor="#E5E7EB",
                gridcolor="#F3F4F6",
            ),
        ),
        title=dict(text=title, font=dict(size=14, weight="bold"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Noto Sans JP', sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        ),
        height=height,
        margin=dict(l=32, r=32, t=48, b=32),
    )
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str = COLORS["online"],
    title: str = "",
    height: int = 340,
    horizontal: bool = False,
    text_auto: bool = True,
) -> go.Figure:
    """棒グラフ（縦/横）。"""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fill_color = f"rgba({r},{g},{b},0.85)"

    if horizontal:
        fig = go.Figure(
            go.Bar(
                y=df[x], x=df[y], orientation="h",
                marker=dict(
                    color=fill_color,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                ),
                text=df[y].round(1) if text_auto else None,
                textposition="outside",
                hovertemplate=f"<b>%{{y}}</b><br>{y}: %{{x:.1f}}<extra></extra>",
            )
        )
        fig.update_layout(xaxis=dict(showgrid=True), yaxis=dict(showgrid=False))
    else:
        fig = go.Figure(
            go.Bar(
                x=df[x], y=df[y],
                marker=dict(
                    color=fill_color,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                ),
                text=df[y].round(1) if text_auto else None,
                textposition="outside",
                hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y:.1f}}<extra></extra>",
            )
        )

    fig.update_traces(marker_cornerradius=6)
    fig.update_layout(title=dict(text=title, font=dict(size=14, weight="bold"), x=0))
    return _apply_base(fig, height)


def grouped_bar_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str],
    labels: dict[str, str] | None = None,
    colors: list[str] | None = None,
    title: str = "",
    height: int = 360,
) -> go.Figure:
    """グループ棒グラフ。"""
    _colors = colors or [COLORS["online"], COLORS["ai_rpa"], COLORS["data"], COLORS["positive"]]
    _labels = labels or {}
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        color = _colors[i % len(_colors)]
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fig.add_trace(
            go.Bar(
                x=df[x], y=df[col],
                name=_labels.get(col, col),
                marker=dict(color=f"rgba({r},{g},{b},0.85)"),
                hovertemplate=f"<b>{_labels.get(col, col)}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.update_traces(marker_cornerradius=4)
    fig.update_layout(
        barmode="group",
        title=dict(text=title, font=dict(size=14, weight="bold"), x=0),
    )
    return _apply_base(fig, height)


def donut_chart(
    labels: list[str],
    values: list[float],
    colors: list[str] | None = None,
    title: str = "",
    height: int = 320,
    center_text: str = "",
) -> go.Figure:
    """ドーナツグラフ。"""
    _colors = colors or [COLORS["online"], COLORS["ai_rpa"], COLORS["data"], COLORS["positive"], COLORS["warning"]]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(
                colors=_colors[: len(labels)],
                line=dict(color="#FFFFFF", width=3),
            ),
            textinfo="label+percent",
            textfont=dict(size=11, family="'Noto Sans JP', sans-serif"),
            hovertemplate="<b>%{label}</b><br>%{value:.0f} (%{percent})<extra></extra>",
        )
    )
    if center_text:
        fig.add_annotation(
            x=0.5, y=0.5, text=center_text,
            font=dict(size=14, weight="bold", color=COLORS["text_main"]),
            showarrow=False,
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight="bold"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Noto Sans JP', sans-serif"),
        legend=dict(orientation="v", x=1, y=0.5),
        height=height,
        margin=dict(l=16, r=16, t=40, b=16),
    )
    return fig


def scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    color_col: str | None = None,
    size_col: str | None = None,
    hover_name: str | None = None,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    height: int = 380,
) -> go.Figure:
    """散布図。クロス分析・RFMセグメント表示に使用。"""
    fig = px.scatter(
        df, x=x, y=y,
        color=color_col, size=size_col,
        hover_name=hover_name,
        color_discrete_sequence=[
            COLORS["online"], COLORS["ai_rpa"], COLORS["data"],
            COLORS["positive"], COLORS["warning"], COLORS["danger"],
        ],
        labels={x: x_label or x, y: y_label or y},
        title=title,
    )
    fig.update_traces(
        marker=dict(line=dict(color="white", width=1.5)),
        selector=dict(mode="markers"),
    )
    fig.update_layout(
        title=dict(font=dict(size=14, weight="bold"), x=0),
    )
    return _apply_base(fig, height)


def heatmap(
    z: list[list[float]],
    x_labels: list[str],
    y_labels: list[str],
    title: str = "",
    height: int = 360,
    colorscale: str = "Blues",
) -> go.Figure:
    """ヒートマップ（バスケット分析の共起マトリクスなどに使用）。"""
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            showscale=True,
            hovertemplate="<b>%{y} × %{x}</b><br>値: %{z:.3f}<extra></extra>",
            texttemplate="%{z:.2f}",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight="bold"), x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Noto Sans JP', sans-serif"),
        height=height,
        margin=dict(l=120, r=16, t=48, b=80),
        xaxis=dict(tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
    )
    return fig


def stacked_bar_time_allocation(
    df: pd.DataFrame,
    x: str = "target_year",
    height: int = 340,
) -> go.Figure:
    """職員の時間配分積み上げ棒グラフ（専用）。"""
    fig = go.Figure()
    # 定型業務（赤系）
    r, g, b = int(COLORS["danger"][1:3], 16), int(COLORS["danger"][3:5], 16), int(COLORS["danger"][5:7], 16)
    fig.add_trace(go.Bar(
        x=df[x], y=df["routine_hours"],
        name="定型的な予定外作業",
        marker=dict(color=f"rgba({r},{g},{b},0.75)"),
        hovertemplate="<b>定型業務</b><br>%{x}年: %{y:.0f}時間/月<extra></extra>",
    ))
    # クリエイティブ業務（緑系）
    r2, g2, b2 = int(COLORS["positive"][1:3], 16), int(COLORS["positive"][3:5], 16), int(COLORS["positive"][5:7], 16)
    fig.add_trace(go.Bar(
        x=df[x], y=df["creative_hours"],
        name="クリエイティブな業務",
        marker=dict(color=f"rgba({r2},{g2},{b2},0.80)"),
        hovertemplate="<b>創造業務</b><br>%{x}年: %{y:.0f}時間/月<extra></extra>",
    ))
    fig.update_traces(marker_cornerradius=4)
    fig.update_layout(
        barmode="stack",
        title=dict(text="職員の時間配分推移（月間・人平均）", font=dict(size=14, weight="bold"), x=0),
        yaxis_title="時間/月",
    )
    return _apply_base(fig, height)
