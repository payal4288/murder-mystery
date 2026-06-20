"""
🔍 Murder Mystery Detective — AI-Powered Investigation Game

Main Streamlit application entry point.
Renders the UI based on current game phase and handles user interactions.
"""

import streamlit as st
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration — must be first Streamlit call
st.set_page_config(
    page_title="🔍 Murder Mystery Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Imports (after page config) ──────────────────────────────────
from utils.session_manager import (
    init_session, get_state, get_phase, get_mystery,
    get_score, get_progress,
)
from services.game_service import (
    start_new_case, reveal_clue, interrogate_suspect,
    check_contradictions, submit_accusation,
)
from services.gemini_service import THEME_SEEDS
from services.scoring_service import get_rank, calculate_max_score

# ── Initialise Session ──────────────────────────────────────────
init_session()


# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
def render_sidebar():
    """Render the sidebar with case info, score, and controls."""
    with st.sidebar:
        st.markdown("# 🔍 Murder Mystery")
        st.markdown("##### *AI-Powered Detective Game*")
        st.markdown("---")

        phase = get_phase()

        # ── Start New Case Button ──
        if phase == "not_started":
            st.markdown("### ⚙️ Case Settings")
            theme_choice = st.selectbox(
                "🎨 Case Setting / Theme",
                options=["🎲 Random Theme", "✍️ Custom Theme..."] + THEME_SEEDS,
                key="theme_choice_start",
            )
            selected_theme = None
            if theme_choice == "✍️ Custom Theme...":
                custom_theme = st.text_input(
                    "Enter custom setting/theme:",
                    placeholder="e.g. Victorian train, space station...",
                    key="custom_theme_start",
                )
                if custom_theme.strip():
                    selected_theme = custom_theme.strip()
            elif theme_choice != "🎲 Random Theme":
                selected_theme = theme_choice

            use_offline = st.checkbox(
                "🔌 Offline Mode (Local Case)",
                value=st.session_state.get("use_offline_preference", False),
                help="Play using pre-written offline cases. Bypasses Gemini API rate limits."
            )

            st.markdown("")
            if st.button("🎲 Start New Case", use_container_width=True, type="primary"):
                with st.spinner("🔮 Generating mystery..."):
                    error = start_new_case(selected_theme, use_offline=use_offline)
                if error:
                    st.error(f"⚠️ {error}")
                else:
                    st.rerun()

        # ── Case Info ──
        if phase in ("investigating", "case_closed"):
            mystery = get_mystery()
            if mystery:
                st.markdown("### 📋 Case Info")
                st.markdown(f"**Victim:** {mystery.victim_name}")
                st.markdown(f"**Scene:** {mystery.crime_scene}")
                st.markdown(f"**Cause:** {mystery.cause_of_death}")

                status_emoji = "🔍" if phase == "investigating" else "📁"
                status_text = "Investigating" if phase == "investigating" else "Case Closed"
                if st.session_state.get("is_offline_mode", False):
                    status_text += " (Offline 🔌)"
                st.markdown(f"**Status:** {status_emoji} {status_text}")

                st.markdown("---")

                # ── Score ──
                st.markdown("### 🏆 Detective Score")
                score = get_score()
                max_score = calculate_max_score(
                    len(mystery.clues),
                    len(mystery.suspects),
                    len(mystery.contradictions),
                )
                st.metric("Points", score, help=f"Max possible: {max_score}")
                st.markdown(f"**Rank:** {get_rank(score)}")

                st.markdown("---")

                # ── Progress ──
                state = get_state()
                st.markdown("### 📊 Investigation Progress")

                clues_found = len(state["revealed_clues"])
                clues_total = len(mystery.clues)
                contradictions_found = len(state["discovered_contradictions"])
                contradictions_total = len(mystery.contradictions)
                suspects_talked = len(state["interrogated_suspects"])
                suspects_total = len(mystery.suspects)

                st.markdown(f"🔎 Clues: **{clues_found}/{clues_total}**")
                st.markdown(f"⚡ Contradictions: **{contradictions_found}/{contradictions_total}**")
                st.markdown(f"🗣️ Interrogated: **{suspects_talked}/{suspects_total}**")

                progress = get_progress()
                st.progress(progress, text=f"{int(progress * 100)}% Complete")

                st.markdown("---")

        # ── New Game Button (always available when in game) ──
        if phase in ("investigating", "case_closed"):
            with st.expander("⚙️ Next Case Settings", expanded=False):
                theme_choice = st.selectbox(
                    "🎨 Next Setting / Theme",
                    options=["🎲 Random Theme", "✍️ Custom Theme..."] + THEME_SEEDS,
                    key="theme_choice_new",
                )
                selected_theme = None
                if theme_choice == "✍️ Custom Theme...":
                    custom_theme = st.text_input(
                        "Enter custom setting/theme:",
                        placeholder="e.g. Space colony, medieval castle...",
                        key="custom_theme_new",
                    )
                    if custom_theme.strip():
                        selected_theme = custom_theme.strip()
                elif theme_choice != "🎲 Random Theme":
                    selected_theme = theme_choice

                use_offline = st.checkbox(
                    "🔌 Offline Mode (Local Case)",
                    value=st.session_state.get("use_offline_preference", False),
                    key="offline_choice_new",
                    help="Play using pre-written offline cases. Bypasses Gemini API rate limits."
                )

            if st.button("🔄 New Game", use_container_width=True):
                with st.spinner("🔮 Generating new mystery..."):
                    error = start_new_case(selected_theme, use_offline=use_offline)
                if error:
                    st.error(f"⚠️ {error}")
                else:
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  WELCOME SCREEN
# ═══════════════════════════════════════════════════════════════
def render_welcome():
    """Render the welcome screen when no game is active."""
    st.markdown("""
    <div class="welcome-container">
        <h1>🔍 Murder Mystery Detective</h1>
        <p class="subtitle">Every case is unique. Every clue matters. Can you find the killer?</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎭</div>
            <div class="suspect-name">AI-Generated Mysteries</div>
            <div class="suspect-detail">Every case is uniquely crafted by Gemini AI — no two games are alike.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔎</div>
            <div class="suspect-name">Investigate & Deduce</div>
            <div class="suspect-detail">Examine clues, interrogate suspects, and uncover hidden contradictions.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">⚖️</div>
            <div class="suspect-name">Accuse the Killer</div>
            <div class="suspect-detail">Build your case and make your accusation. One shot — make it count.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.info("👈 Click **Start New Case** in the sidebar to begin your investigation!")


# ═══════════════════════════════════════════════════════════════
#  CRIME SCENE BRIEFING
# ═══════════════════════════════════════════════════════════════
def render_crime_scene():
    """Render the crime scene briefing section."""
    mystery = get_mystery()
    if not mystery:
        return

    if st.session_state.get("is_offline_mode", False):
        st.info("🔌 **Playing in Offline Mode** using a local pre-written case (bypassed Gemini API limits).")

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🔍 Crime Scene Briefing")

    # Case file header
    st.markdown(f"""
    <div class="case-header">
        <h2>📁 Case File — {mystery.victim_name}</h2>
        <p><strong>Victim:</strong> {mystery.victim_name} — {mystery.victim_occupation}<br>
        <strong>Location:</strong> {mystery.crime_scene}<br>
        <strong>Time of Death:</strong> {mystery.time_of_death}<br>
        <strong>Cause of Death:</strong> {mystery.cause_of_death}</p>
    </div>
    """, unsafe_allow_html=True)

    # Backstory and scene
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("#### 📝 Initial Report")
        st.markdown(mystery.initial_report)
    with col2:
        st.markdown("#### 🏛️ Crime Scene")
        st.markdown(mystery.crime_scene_description)
        st.markdown("---")
        st.markdown("#### 👤 About the Victim")
        st.markdown(mystery.victim_backstory)


# ═══════════════════════════════════════════════════════════════
#  SUSPECT CARDS
# ═══════════════════════════════════════════════════════════════
def render_suspects():
    """Render suspect cards with interrogation buttons."""
    mystery = get_mystery()
    if not mystery:
        return

    state = get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🎭 Suspects")

    cols = st.columns(len(mystery.suspects))

    for i, suspect in enumerate(mystery.suspects):
        with cols[i]:
            is_interrogated = suspect.id in state["interrogated_suspects"]
            badge = " ✅" if is_interrogated else ""

            st.markdown(f"""
            <div class="suspect-card">
                <div class="suspect-name">🎭 {suspect.name}{badge}</div>
                <div class="suspect-occupation">{suspect.occupation}</div>
                <div class="suspect-detail"><strong>Relationship:</strong> {suspect.relationship}</div>
                <div class="suspect-detail"><strong>Motive:</strong> {suspect.motive}</div>
            </div>
            """, unsafe_allow_html=True)

            if not is_interrogated:
                if st.button(
                    f"🔎 Interrogate {suspect.name.split()[0]}",
                    key=f"interrogate_{suspect.id}",
                    use_container_width=True,
                ):
                    interrogate_suspect(suspect.id)
                    st.rerun()
            else:
                with st.expander(f"📜 {suspect.name.split()[0]}'s Alibi", expanded=False):
                    st.markdown(f"*\"{suspect.alibi}\"*")


# ═══════════════════════════════════════════════════════════════
#  EVIDENCE LOCKER (CLUES)
# ═══════════════════════════════════════════════════════════════
def render_clues():
    """Render the evidence locker with revealable clues."""
    mystery = get_mystery()
    if not mystery:
        return

    state = get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🗄️ Evidence Locker")
    st.caption("Click on evidence items to examine them and earn investigation points.")

    col1, col2 = st.columns(2)

    for i, clue in enumerate(mystery.clues):
        is_revealed = clue.id in state["revealed_clues"]
        target_col = col1 if i % 2 == 0 else col2

        with target_col:
            if is_revealed:
                # Show revealed clue
                st.markdown(f"""
                <div class="clue-card">
                    <div class="clue-title">✅ {clue.title}</div>
                    <div class="clue-type">📂 {clue.type.replace('_', ' ')}</div>
                    <div class="clue-desc">{clue.description}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Show hidden clue with reveal button
                st.markdown(f"""
                <div class="clue-card" style="opacity: 0.6;">
                    <div class="clue-title">🔒 Evidence #{i + 1}</div>
                    <div class="clue-type">📂 {clue.type.replace('_', ' ')}</div>
                    <div class="clue-desc" style="color: var(--text-muted); font-style: italic;">
                        Click below to examine this evidence...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(
                    f"🔍 Examine Evidence #{i + 1}",
                    key=f"reveal_{clue.id}",
                    use_container_width=True,
                ):
                    reveal_clue(clue.id)
                    st.rerun()

    # ── Check for Contradictions ──
    st.markdown("")
    revealed_count = len(state["revealed_clues"])
    if revealed_count >= 2:
        if st.button(
            "⚡ Analyze Evidence for Contradictions",
            use_container_width=True,
            type="primary",
        ):
            newly_found = check_contradictions()
            if newly_found:
                st.rerun()
            else:
                st.info("🔍 No new contradictions found yet. Keep collecting evidence!")


# ═══════════════════════════════════════════════════════════════
#  INVESTIGATION NOTES
# ═══════════════════════════════════════════════════════════════
def render_investigation_notes():
    """Render discovered contradictions, notes, and score log."""
    mystery = get_mystery()
    if not mystery:
        return

    state = get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 📝 Investigation Notes")

    tab1, tab2, tab3 = st.tabs(["⚡ Contradictions", "📋 Notes", "🏆 Score Log"])

    with tab1:
        discovered = state["discovered_contradictions"]
        if discovered:
            for contradiction in mystery.contradictions:
                if contradiction.id in discovered:
                    st.markdown(f"""
                    <div class="contradiction-found">
                        <div class="contradiction-title">⚡ {contradiction.id.replace('_', ' ').title()}</div>
                        <div class="contradiction-desc">{contradiction.description}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("*No contradictions discovered yet. Examine more clues and analyze the evidence!*")

        # Show hints for undiscovered contradictions
        undiscovered = [
            c for c in mystery.contradictions
            if c.id not in discovered
        ]
        if undiscovered and len(discovered) > 0:
            with st.expander("💡 Hints", expanded=False):
                for c in undiscovered:
                    st.markdown(f"- 💡 *{c.hint}*")

    with tab2:
        notes = state["investigation_notes"]
        if notes:
            for note in notes:
                st.markdown(f"- {note}")
        else:
            st.markdown("*Investigation notes will appear here as you progress.*")

    with tab3:
        score_log = state["score_log"]
        if score_log:
            for action, points in score_log:
                sign = "+" if points >= 0 else ""
                color = "green" if points >= 0 else "red"
                st.markdown(
                    f"- {action}: "
                    f"<span style='color:{color}; font-weight:bold;'>{sign}{points} pts</span>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"**Total: {get_score()} pts**")
        else:
            st.markdown("*Score updates will appear here.*")


# ═══════════════════════════════════════════════════════════════
#  ACCUSATION SECTION
# ═══════════════════════════════════════════════════════════════
def render_accusation():
    """Render the accusation form."""
    mystery = get_mystery()
    if not mystery:
        return

    state = get_state()
    if state["accusation_made"]:
        return

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## ⚖️ Make Your Accusation")
    st.warning("⚠️ **You only get ONE shot.** A correct accusation earns **+100 pts**. A wrong one costs **-50 pts**.")

    suspect_names = {s.name: s.id for s in mystery.suspects}
    selected_name = st.selectbox(
        "Who do you believe is the murderer?",
        options=list(suspect_names.keys()),
        index=None,
        placeholder="Select a suspect...",
    )

    if selected_name:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("⚖️ Submit Accusation", type="primary"):
                st.session_state._confirm_accusation = True
                st.session_state._accused_name = selected_name

        # Confirmation step
        if getattr(st.session_state, "_confirm_accusation", False):
            st.markdown("")
            st.error(f"🔔 **Are you sure you want to accuse {st.session_state._accused_name}?** This cannot be undone!")
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("✅ Yes, I'm sure", type="primary"):
                    accused_name = st.session_state._accused_name
                    accused_id = suspect_names[accused_name]
                    del st.session_state._confirm_accusation
                    del st.session_state._accused_name
                    submit_accusation(accused_id)
                    st.rerun()
            with c2:
                if st.button("❌ Cancel"):
                    del st.session_state._confirm_accusation
                    del st.session_state._accused_name
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  CASE CLOSED SCREEN
# ═══════════════════════════════════════════════════════════════
def render_case_closed():
    """Render the case closed results screen."""
    mystery = get_mystery()
    state = get_state()
    if not mystery or not state["case_closed"]:
        return

    accused_id = state["accused_suspect_id"]
    is_correct = accused_id == mystery.murderer_id

    murderer = next((s for s in mystery.suspects if s.id == mystery.murderer_id), None)
    accused = next((s for s in mystery.suspects if s.id == accused_id), None)

    # ── Result Banner ──
    if is_correct:
        st.markdown(f"""
        <div class="case-closed-banner correct">
            <h2 style="color: var(--success);">🎉 CASE SOLVED!</h2>
            <p style="font-size: 1.2rem; color: var(--text-primary);">
                Brilliant work, Detective! You correctly identified 
                <strong>{murderer.name}</strong> as the murderer.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
    else:
        st.markdown(f"""
        <div class="case-closed-banner wrong">
            <h2 style="color: var(--danger);">❌ WRONG SUSPECT</h2>
            <p style="font-size: 1.2rem; color: var(--text-primary);">
                You accused <strong>{accused.name if accused else 'Unknown'}</strong>, 
                but the real murderer was <strong>{murderer.name if murderer else 'Unknown'}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Solution Narrative ──
    st.markdown("### 📖 The Full Story")
    st.markdown(f"""
    <div class="case-header">
        <p>{mystery.solution_narrative}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── The Murderer ──
    if murderer:
        st.markdown("### 🎭 The Murderer")
        st.markdown(f"""
        <div class="suspect-card">
            <div class="suspect-name">🔴 {murderer.name}</div>
            <div class="suspect-occupation">{murderer.occupation}</div>
            <div class="suspect-detail"><strong>Relationship:</strong> {murderer.relationship}</div>
            <div class="suspect-detail"><strong>Motive:</strong> {murderer.motive}</div>
            <div class="suspect-detail"><strong>Alibi (flawed):</strong> <em>"{murderer.alibi}"</em></div>
        </div>
        """, unsafe_allow_html=True)

    # ── Contradictions Summary ──
    st.markdown("### ⚡ All Contradictions")
    discovered = state["discovered_contradictions"]
    for c in mystery.contradictions:
        found = c.id in discovered
        icon = "✅" if found else "❌ Missed"
        color_class = "contradiction-found" if found else "clue-card"
        st.markdown(f"""
        <div class="{color_class}">
            <div class="contradiction-title">{icon} — {c.id.replace('_', ' ').title()}</div>
            <div class="contradiction-desc">{c.description}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Final Score ──
    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("### 🏆 Final Results")

    score = get_score()
    max_score = calculate_max_score(
        len(mystery.clues),
        len(mystery.suspects),
        len(mystery.contradictions),
    )
    rank = get_rank(score)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Score", f"{score} pts")
    with col2:
        st.metric("Max Possible", f"{max_score} pts")
    with col3:
        st.metric("Detective Rank", rank)

    # ── Score Breakdown ──
    with st.expander("📊 Score Breakdown", expanded=True):
        score_log = state["score_log"]
        if score_log:
            for action, points in score_log:
                sign = "+" if points >= 0 else ""
                color = "green" if points >= 0 else "red"
                st.markdown(
                    f"- {action}: "
                    f"<span style='color:{color}; font-weight:bold;'>{sign}{points} pts</span>",
                    unsafe_allow_html=True,
                )

    # ── Play Again ──
    st.markdown("")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        if st.button("🎲 Start a New Case", use_container_width=True, type="primary"):
            theme_choice = st.session_state.get("theme_choice_new", "🎲 Random Theme")
            selected_theme = None
            if theme_choice == "✍️ Custom Theme...":
                custom_theme = st.session_state.get("custom_theme_new", "")
                if custom_theme.strip():
                    selected_theme = custom_theme.strip()
            elif theme_choice != "🎲 Random Theme":
                selected_theme = theme_choice

            use_offline = st.session_state.get("offline_choice_new", False)
            with st.spinner("🔮 Generating new mystery..."):
                error = start_new_case(selected_theme, use_offline=use_offline)
            if error:
                st.error(f"⚠️ {error}")
            else:
                st.rerun()


# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION ROUTING
# ═══════════════════════════════════════════════════════════════
def main():
    """Main application entry point — routes to the correct phase."""
    render_sidebar()

    phase = get_phase()

    if phase == "not_started":
        render_welcome()

    elif phase == "generating":
        st.markdown("## 🔮 Generating Mystery...")
        st.spinner("Gemini AI is crafting your unique case...")

    elif phase == "investigating":
        render_crime_scene()
        render_suspects()
        render_clues()
        render_investigation_notes()
        render_accusation()

    elif phase == "case_closed":
        render_case_closed()


if __name__ == "__main__":
    main()
