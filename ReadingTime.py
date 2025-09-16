import math
from datetime import timedelta

import streamlit as st


def minutes_to_hms(total_min: float):
    total_sec = int(round(total_min * 60))
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return h, m, s

def format_duration(total_min: float) -> str:
    h, m, s = minutes_to_hms(total_min)
    parts = []
    if h:
        parts.append(f"{h} h")
    if m:
        parts.append(f"{m} min")
    if not h and not m:
        parts.append(f"{s} s")
    return " ".join(parts)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def safe_div(a, b, default=0.0):
    return a / b if b else default

import streamlit as st

# ... ton st.set_page_config(...)

# Masquer éléments Streamlit (header/menu/footer + badges/contrôles Cloud)
st.markdown("""
<style>
/* Header/menu/footer */
header[data-testid="stHeader"] { display:none; }
div[data-testid="stToolbar"] { visibility:hidden; height:0; }
#MainMenu { visibility:hidden; }
footer { visibility:hidden; }

/* Badge "viewer" Streamlit (bas droite) */
div[class^="viewerBadge_"], div[class*="viewerBadge_"] { display:none !important; }

/* Bouton flottant de déploiement/gestion sur Streamlit Cloud */
div[data-testid="stDeployButton"] { display:none !important; }

/* (Optionnel) Ultrafallback : cache tout élément fixé en bas à droite.
   Commente cette règle si elle cache un autre widget dont tu as besoin. */
.stApp [style*="position: fixed"][style*="bottom: 0px"][style*="right: 0px"] {
  display:none !important;
}

/* Réduit le padding haut quand le header est masqué */
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


st.set_page_config(
    page_title="Estimateur de temps de lecture",
    page_icon="📚",
    layout="centered",
)

st.markdown(
    """
    # 📚 Estimateur de temps de lecture  
    Donnez votre **rythme sur les premiers chapitres**, et obtenez une **estimation** pour toute l'œuvre.

    *Astuce :* si vous lisez un manga/BD/Roman avec des chapitres très inégaux, utilisez l’onglet **Pages**.
    
    """
)

st.write("Gio va pouvoir optimiser son temps pour en allouer plus + au sauvetage de vie en cardiologie.")

with st.sidebar:
    st.header("⚙️ Options")
    oeuvre_type = st.selectbox(
        "Type d'œuvre",
        ["Manga", "BD", "Roman", "Light Novel", "Autre"],
        index=0,
        help="Ne change pas la formule, mais personnalise quelques textes.",
    )
    buffer_pct = st.slider(
        "Marge d'incertitude ± (%)",
        min_value=0,
        max_value=50,
        value=15,
        step=1,
        help="Ajoute une fourchette autour de l'estimation (variations de densité, fatigue, etc.).",
    )
    pause_per_chapter = st.number_input(
        "Temps de pause par chapitre (min)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5,
        help="Optionnel : petits breaks, notes, etc.",
    )
    minutes_per_day = st.slider(
        "Temps de lecture prévu par jour (min)",
        min_value=10,
        max_value=300,
        value=30,
        step=5,
        help="Pour convertir l’estimation en nombre de jours/semaines.",
    )

tabs = st.tabs(["Chapitres", "Pages"])

# ---------- Onglet Chapitres ----------
with tabs[0]:
    st.subheader("Estimation par chapitres")
    mode = st.radio(
        "Je fournis…",
        ["Mon temps total pour N chapitres", "Ma moyenne par chapitre"],
        horizontal=True,
    )

    colA, colB = st.columns(2)

    if mode == "Mon temps total pour N chapitres":
        with colA:
            sample_chapters = st.number_input(
                "Nombre de chapitres lus (échantillon)",
                min_value=1,
                value=5,
                step=1,
            )
        with colB:
            h = st.number_input("Heures (sur l’échantillon)", min_value=0, value=1, step=1)
            m = st.number_input("Minutes (sur l’échantillon)", min_value=0, max_value=59, value=0, step=1)
        sample_total_min = h * 60 + m
        avg_min_per_chapter = safe_div(sample_total_min, sample_chapters)
        st.caption(
            f"💡 Moyenne calculée : **{format_duration(avg_min_per_chapter)}** par chapitre (pauses non incluses)."
        )
    else:
        avg_min_per_chapter = st.number_input(
            "Ma moyenne par chapitre (min)",
            min_value=0.1,
            value=6.0,
            step=0.5,
        )

    # Total chapitres
    st.markdown("#### Combien de chapitres au total ?")
    mode_total = st.radio(
        "Méthode",
        ["Je connais le nombre total", "Je connais les volumes × chapitres/volume"],
        horizontal=True,
    )

    if mode_total == "Je connais le nombre total":
        total_chapters = st.number_input(
            "Nombre total de chapitres de l'œuvre",
            min_value=1,
            value=100,
            step=1,
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            volumes = st.number_input("Nombre de volumes", min_value=1, value=10, step=1)
        with col2:
            ch_per_vol = st.number_input("Chapitres par volume (moyenne)", min_value=1.0, value=10.0, step=0.5)
        total_chapters = int(round(volumes * ch_per_vol))

    # Calcul principal
    avg_with_pause = avg_min_per_chapter + pause_per_chapter
    total_min = avg_with_pause * total_chapters

    low = total_min * (1 - buffer_pct / 100.0)
    high = total_min * (1 + buffer_pct / 100.0)

    # Affichage résultats
    st.markdown("---")
    st.markdown("### Résultats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Moyenne / chapitre", format_duration(avg_with_pause))
    c2.metric("Chapitres totaux", f"{total_chapters}")
    c3.metric("Temps estimé", format_duration(total_min))

    st.progress(clamp(total_chapters / max(total_chapters, 1), 0, 1), text="Progression potentielle…")  # purely decorative

    st.markdown(
        f"**Fourchette avec marge ±{buffer_pct}%** : {format_duration(low)} ⟶ **{format_duration(high)}**"
    )

    # Projection en jours/semaines selon minutes/jour
    days = total_min / minutes_per_day if minutes_per_day > 0 else math.inf
    weeks = days / 7
    st.info(
        f"📅 Au rythme de **{minutes_per_day} min/jour**, comptez environ **{days:.1f} jours** (~{weeks:.1f} semaines)."
    )

# ---------- Onglet Pages ----------
with tabs[1]:
    st.subheader("Estimation par pages")
    st.caption("Utile si vos chapitres ont des longueurs très inégales.")

    col1, col2 = st.columns(2)
    with col1:
        pages_read = st.number_input("Pages lues (échantillon)", min_value=1, value=60, step=1)
    with col2:
        h2 = st.number_input("Heures sur l’échantillon", min_value=0, value=1, step=1, key="h_pages")
        m2 = st.number_input("Minutes sur l’échantillon", min_value=0, max_value=59, value=0, step=1, key="m_pages")
    total_min_sample = h2 * 60 + m2

    speed_min_per_page = safe_div(total_min_sample, pages_read, default=0.0)  # min par page
    st.caption(f"💡 Moyenne calculée : **{speed_min_per_page:.2f} min/page** (pauses non incluses).")

    total_pages = st.number_input("Nombre total de pages de l'œuvre", min_value=1, value=1200, step=10)
    avg_with_pause_page = speed_min_per_page + (pause_per_chapter / max(1, st.session_state.get('_dummy_pages_per_chapter', 30)))
    # Note: ci-dessus, on répartit la pause au prorata de ~30 pages/chapitre par défaut, pour ne pas ignorer totalement la pause.

    total_min_pages = total_pages * avg_with_pause_page
    low_p = total_min_pages * (1 - buffer_pct / 100.0)
    high_p = total_min_pages * (1 + buffer_pct / 100.0)

    st.markdown("---")
    colp1, colp2 = st.columns(2)
    colp1.metric("Moyenne / page", f"{speed_min_per_page:.2f} min")
    colp2.metric("Temps estimé", format_duration(total_min_pages))
    st.markdown(
        f"**Fourchette ±{buffer_pct}%** : {format_duration(low_p)} ⟶ **{format_duration(high_p)}**"
    )

    days_p = total_min_pages / minutes_per_day if minutes_per_day > 0 else math.inf
    weeks_p = days_p / 7
    st.info(
        f"📅 Au rythme de **{minutes_per_day} min/jour**, comptez environ **{days_p:.1f} jours** (~{weeks_p:.1f} semaines)."
    )







