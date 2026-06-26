"""庁内職員専用エリアの簡易認証ゲート。"""
from __future__ import annotations
import streamlit as st

_SESSION_KEY = "staff_authenticated"
_DEFAULT_PW = "demo1234"


def _correct_password() -> str:
    try:
        return st.secrets.get("STAFF_PASSWORD", _DEFAULT_PW)
    except Exception:
        return _DEFAULT_PW


def is_authenticated() -> bool:
    return bool(st.session_state.get(_SESSION_KEY))


def login_gate() -> bool:
    """未認証ならログインフォームを表示して False を返す。認証済みなら True。"""
    if is_authenticated():
        return True

    st.markdown(
        '<div style="height:48px;"></div>',
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            '<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:16px;'
            'padding:40px 36px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.08);">'
            '<div style="font-size:2.5rem;margin-bottom:12px;">🔒</div>'
            '<div style="font-size:1.25rem;font-weight:700;color:#1F2937;margin-bottom:8px;">庁内職員専用エリア</div>'
            '<div style="font-size:0.85rem;color:#6B7280;line-height:1.6;margin-bottom:24px;">'
            '市民の行動ログ・行政内部データを含むこのページは<br>職員認証が必要です。</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        password = st.text_input(
            "パスワード",
            type="password",
            placeholder="パスワードを入力してください",
            label_visibility="collapsed",
        )
        if st.button("ログイン", type="primary", use_container_width=True):
            if password == _correct_password():
                st.session_state[_SESSION_KEY] = True
                st.rerun()
            else:
                st.error("パスワードが正しくありません")
        st.caption("デモ用パスワード: **demo1234**　｜　本番環境では Secrets で STAFF_PASSWORD を設定")

    return False


def logout_button() -> None:
    """ログアウトボタンをサイドバーに追加する（認証済み時のみ呼ぶ）。"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.75rem;color:#6B7280;margin-bottom:4px;">🔓 職員モードでログイン中</div>',
            unsafe_allow_html=True,
        )
        if st.button("ログアウト", use_container_width=True):
            st.session_state[_SESSION_KEY] = False
            st.rerun()
