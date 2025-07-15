import streamlit as st

def show_mascot_reaction(reaction_type: str, message: str):
    colors = {
        "success": "#d4edda",
        "error": "#f8d7da",
        "info": "#fff3cd",
        "chat": "#d1ecf1"
    }
    border_colors = {
        "success": "#28a745",
        "error": "#dc3545",
        "info": "#ffc107",
        "chat": "#17a2b8"
    }
    emoji = {
        "success": "✅",
        "error": "❌",
        "info": "💡",
        "chat": "💬"
    }

    bg_color = colors.get(reaction_type, "#eeeeee")
    border_color = border_colors.get(reaction_type, "#888888")
    icon = emoji.get(reaction_type, "ℹ️")

    st.markdown(f"""
    <div style='
        position: fixed;
        bottom: 190px;
        right: 180px;
        background: {bg_color};
        padding: 12px 18px;
        border-radius: 12px;
        border-left: 6px solid {border_color};
        font-weight: 500;
        font-size: 0.95rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        z-index: 999;
        animation: fadeIn 1s ease-in-out;
    '>
    {icon} {message}
    </div>

    <style>
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    """, unsafe_allow_html=True)
