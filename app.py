import os
import sys

# Add project root to path so modules can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import json
from config.settings import API_PORT

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CARVanta – CAR-T Viability Platform",
    page_icon="◆",
    layout="wide",
)

# ─── Custom CSS – Hospital-Grade Clinical Theme ────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ─────────────────────────────────────────── */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: #1E293B !important;
    }
    .stApp {
        background-color: #F5F7FA;
        color: #1E293B;
    }
    header[data-testid="stHeader"] {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
    }

    /* ── Force dark text on all Streamlit elements ────── */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stText, .stCaption, label, .stWidgetLabel,
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
        color: #1E293B !important;
    }

    /* ── Text inputs & select boxes ─────────────────────── */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] *,
    .stMultiSelect [data-baseweb="select"] *,
    [data-testid="stSelectbox"] *, [data-testid="stMultiSelect"] *,
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        color: #1E293B !important;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .stTextInput input::placeholder {
        color: #94A3B8 !important;
    }

    /* ── Selectbox / Multiselect dropdowns ───────────────── */
    [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-color: #CBD5E1 !important;
    }
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    [data-baseweb="menu"] li, [data-baseweb="menu"] li * {
        color: #1E293B !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: #F1F5F9 !important;
    }
    [data-baseweb="tag"] {
        background-color: #E2E8F0 !important;
        color: #1E293B !important;
    }
    [data-baseweb="tag"] span { color: #1E293B !important; }

    /* ── Sidebar ────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] * {
        color: #1E293B !important;
    }

    /* ── Tabs ───────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button * {
        color: #475569 !important;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] * {
        color: #0077B6 !important;
        font-weight: 600;
    }

    /* ── Expander ───────────────────────────────────────── */
    .streamlit-expanderHeader, .streamlit-expanderHeader *,
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
        color: #1E293B !important;
        font-weight: 500;
    }
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
        color: #334155 !important;
    }

    /* ── Card wrapper ───────────────────────────────────── */
    .clinical-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        color: #1E293B;
    }

    /* ── Section headers ────────────────────────────────── */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #1E293B !important;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #0077B6;
        letter-spacing: -0.01em;
    }

    /* ── Tier badges ────────────────────────────────────── */
    .tier-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.02em;
    }
    .tier-1 { background: #D1FAE5; color: #065F46 !important; }
    .tier-2 { background: #DBEAFE; color: #1E40AF !important; }
    .tier-3 { background: #FEF3C7; color: #92400E !important; }
    .tier-4 { background: #FEE2E2; color: #991B1B !important; }

    /* ── Risk badge ─────────────────────────────────────── */
    .risk-low    { background: #D1FAE5; color: #065F46 !important; padding: 4px 14px; border-radius: 16px; font-weight: 500; font-size: 13px; }
    .risk-mod    { background: #FEF3C7; color: #92400E !important; padding: 4px 14px; border-radius: 16px; font-weight: 500; font-size: 13px; }
    .risk-high   { background: #FEE2E2; color: #991B1B !important; padding: 4px 14px; border-radius: 16px; font-weight: 500; font-size: 13px; }

    /* ── Metric cards ───────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #334155 !important;
    }

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        background-color: #0077B6;
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.01em;
        transition: background-color 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #023E8A;
        color: #FFFFFF !important;
    }
    .stButton > button span { color: #FFFFFF !important; }

    /* ── Selectbox / Multiselect wrapper ─────────────────── */
    [data-testid="stSelectbox"], [data-testid="stMultiSelect"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Divider ─────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 32px 0;
    }

    /* ── Alert overrides ─────────────────────────────────── */
    .stAlert {
        border-radius: 10px;
        font-size: 14px;
    }
    .stAlert p, .stAlert span, .stAlert div {
        color: #1E293B !important;
    }

    /* ── Spinner ─────────────────────────────────────────── */
    .stSpinner > div > span {
        color: #1E293B !important;
    }

    /* ── JSON display ────────────────────────────────────── */
    .stJson {
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }

    /* ── Title area ──────────────────────────────────────── */
    .platform-title {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A !important;
        margin-bottom: 2px;
        letter-spacing: -0.02em;
    }
    .platform-subtitle {
        font-size: 14px;
        color: #64748B !important;
        font-weight: 400;
        margin-bottom: 28px;
    }

    /* ── Comparison item ─────────────────────────────────── */
    .compare-item {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        color: #1E293B !important;
    }
    .compare-item strong {
        color: #0F172A !important;
    }

    /* ── Chart labels ────────────────────────────────────── */
    .stBarChart text, .stLineChart text {
        fill: #1E293B !important;
    }

    /* ── Heatmap cell ────────────────────────────────────── */
    .heatmap-row {
        display: flex;
        align-items: center;
        padding: 6px 12px;
        margin-bottom: 4px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }
    .heatmap-neg { background: #D1FAE5; color: #065F46 !important; }
    .heatmap-low { background: #ECFDF5; color: #065F46 !important; }
    .heatmap-mod { background: #FEF3C7; color: #92400E !important; }
    .heatmap-high { background: #FEE2E2; color: #991B1B !important; }

    /* ── Synergy badge ───────────────────────────────────── */
    .synergy-score {
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .synergy-good { color: #059669 !important; }
    .synergy-ok { color: #D97706 !important; }
    .synergy-bad { color: #DC2626 !important; }

    /* ── Query result ────────────────────────────────────── */
    .query-summary {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        padding: 16px 20px;
        color: #1E40AF !important;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

API_BASE = f"http://127.0.0.1:{API_PORT}"


# ─── Dynamic antigen loading from API ───────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_antigens(search="", limit=50):
    """Fetch antigen names from the API with optional search prefix."""
    try:
        res = requests.get(f"{API_BASE}/antigens", params={"search": search, "limit": limit})
        if res.status_code == 200:
            data = res.json()
            return data.get("antigens", []), data.get("total", 0)
    except requests.ConnectionError:
        pass
    # Comprehensive fallback list of known CAR-T targets
    fallback = [
        "CD19", "BCMA", "CD22", "GPRC5D", "PSMA", "GD2", "GPC3", "FOLR1",
        "CLDN18", "ROR1", "DLL3", "CD70", "CD138", "CAIX", "IL13RA2",
        "HER2", "EGFR", "MESOTHELIN", "CD20", "CD38", "CD33", "FLT3",
        "CD123", "SLAMF7", "B7H3", "MUC1", "EPCAM", "WT1", "NYESO1",
        "NECTIN4", "STEAP1", "PSCA", "TROP2", "CEACAM5", "CCR4",
        "MUC16", "CLEC12A", "CD44V6", "MAGEA4", "PRAME",
    ]
    return fallback, len(fallback)


# ─── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="platform-title">◆ CARVanta</div>', unsafe_allow_html=True)
st.markdown('<div class="platform-subtitle">AI-Augmented Biomarker Intelligence Platform · v4 Adaptive ML-Driven Scoring · Validated Targets + AI-Predicted Cross-Cancer Associations</div>', unsafe_allow_html=True)


# ─── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧬 Navigation")
    page = st.radio(
        "Select Module",
        [
            "🔬 Single Antigen Analysis",
            "⚖️ Antigen Comparison",
            "🧫 Tissue Risk Heatmap",
            "🎯 Multi-Target Synergy",
            "👥 Patient Stratification",
            "🔍 NLP Query Search",
            "💊 Clinical Trials",
            "🏆 Global Leaderboard",
            "📊 Dataset Intelligence",
            "⚙️ System Status",
        ],
        index=0,
    )
    st.divider()
    st.caption("CARVanta v4 · AI-Augmented Platform")
    st.caption("© CARVanta — carvanta.ai")


# ─── Shared: antigen list ───────────────────────────────────────────────────────
antigen_list = []
total_count = 0

if page in ["🔬 Single Antigen Analysis", "🧫 Tissue Risk Heatmap",
            "👥 Patient Stratification", "💊 Clinical Trials"]:
    antigen_list, total_count = fetch_antigens(search="", limit=500)
    st.caption(f"{total_count:,} antigens available")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 – Single Antigen Analysis
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🔬 Single Antigen Analysis":
    st.markdown('<div class="section-header">Single Antigen Evaluation</div>', unsafe_allow_html=True)

    antigen = st.selectbox("Select an antigen", antigen_list, index=0 if antigen_list else None)

    if st.button("Run Evaluation", key="eval_btn"):
        with st.spinner("Running analysis…"):
            response = requests.post(f"{API_BASE}/score", json={"antigen_name": antigen})

        if response.status_code == 200:
            data = response.json()
            rule = data.get("rule_based", {})
            ml = data.get("ml_prediction", {})
            features = data.get("features", {})
            cvs = rule.get("CVS", 0)
            risk = data.get("risk_score", 0)

            # ── Row 1: Core metrics ──────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Core Metrics (v4 Adaptive)</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            adaptive = data.get("adaptive_score", cvs)
            ml_rank = ml.get("ranking_score", 0.5)
            c1.metric("Adaptive Score", f"{adaptive:.3f}")
            c2.metric("Rule-Based CVS", cvs)
            c3.metric("ML Ranking", f"{ml_rank:.3f}")
            c4.metric("Confidence", rule.get("confidence_score"))
            c5.metric("Risk Score", risk)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Data Source Badge ─────────────────────────────────────
            ds_col1, ds_col2, ds_col3 = st.columns(3)
            ds = data.get("data_source", "synthetic")
            sdb = data.get("source_database", "Synthetic")
            evl = data.get("evidence_level", "predicted")
            ds_badge = {
                "real": '<span class="tier-badge tier-1">🟢 REAL — Clinical Evidence</span>',
                "validated": '<span class="tier-badge tier-2">🔵 VALIDATED — Database Confirmed</span>',
                "synthetic": '<span class="tier-badge tier-4">🔴 SYNTHETIC — Training Data</span>',
            }.get(ds, '<span class="tier-badge tier-3">Unknown</span>')
            with ds_col1:
                st.markdown(f'**Data Source:** {ds_badge}', unsafe_allow_html=True)
            with ds_col2:
                st.markdown(f'**Source Database:** `{sdb}`')
            with ds_col3:
                st.markdown(f'**Evidence Level:** `{evl}`')

            # ── Tier + Risk badges ───────────────────────────────────────
            col_tier, col_risk = st.columns(2)
            with col_tier:
                tier = rule.get("tier", "")
                if "Tier 1" in tier:
                    st.markdown('<span class="tier-badge tier-1">Tier 1 – Highly Viable</span>', unsafe_allow_html=True)
                elif "Tier 2" in tier:
                    st.markdown('<span class="tier-badge tier-2">Tier 2 – Promising</span>', unsafe_allow_html=True)
                elif "Tier 3" in tier:
                    st.markdown('<span class="tier-badge tier-3">Tier 3 – Experimental</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="tier-badge tier-4">Tier 4 – High Risk</span>', unsafe_allow_html=True)
            with col_risk:
                if risk < 0.2:
                    st.markdown('<span class="risk-low">Low Risk</span>', unsafe_allow_html=True)
                elif risk < 0.4:
                    st.markdown('<span class="risk-mod">Moderate Risk</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="risk-high">High Risk</span>', unsafe_allow_html=True)

            # ── Decision ─────────────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Clinical Decision</div>', unsafe_allow_html=True)
            dec_col1, dec_col2 = st.columns(2)
            dec_col1.metric("Decision", data.get("decision", "—"))
            dec_col2.metric("Confidence Level", data.get("confidence_label", "—"))
            st.markdown('</div>', unsafe_allow_html=True)

            # ── ML Prediction ────────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Machine Learning Prediction (v4)</div>', unsafe_allow_html=True)
            ml_c1, ml_c2, ml_c3, ml_c4 = st.columns(4)
            viability_label = "Viable" if ml.get("viability") == 1 else "Not Viable"
            ml_c1.metric("Predicted Viability", viability_label)
            ml_c2.metric("ML Confidence", ml.get("confidence"))
            ml_c3.metric("Confidence Level", ml.get("confidence_label"))
            ml_c4.metric("Clinical Success Prob.", f'{ml.get("ranking_score", 0.5):.3f}')
            agreement = data.get("model_agreement", "—")
            if "High agreement" in agreement:
                st.success(f"Model Agreement: {agreement}")
            else:
                st.warning(f"Model Agreement: {agreement}")
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Score Breakdown (Radar Chart) ────────────────────────────
            radar_data = data.get("radar_chart_data", {})
            if radar_data:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)
                st.bar_chart(radar_data)
                # Show numeric values below
                cols = st.columns(len(radar_data))
                for i, (label, value) in enumerate(radar_data.items()):
                    color = "🟢" if value >= 0.75 else "🔵" if value >= 0.55 else "🟡" if value >= 0.40 else "🔴"
                    cols[i].metric(f"{color} {label}", f"{value:.3f}")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Safety Profile ───────────────────────────────────────────
            safety = data.get("safety_profile", {})
            if safety:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Safety Profile</div>', unsafe_allow_html=True)
                sp1, sp2, sp3, sp4 = st.columns(4)
                ner = safety.get("normal_expression_risk", 0)
                sp1.metric("Normal Tissue Risk", f"{ner:.3f}",
                           delta="Safe" if ner < 0.20 else "Caution" if ner < 0.40 else "⚠️ High")
                sp2.metric("Tumor Specificity", f"{safety.get('tumor_specificity', 0):.3f}")
                sp3.metric("Safety Margin", f"{safety.get('safety_margin', 0):.3f}")
                sp4.metric("Therapeutic Index", f"{safety.get('therapeutic_index', 0):.1f}x")
                # AI Safety Insight
                safety_insight = data.get("safety_insight", "")
                if safety_insight:
                    st.markdown(f"**AI Safety Assessment:** {safety_insight}")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Feature Analysis ──────────────────────────────────────────
            importance = data.get("feature_importance", {})
            contrib = data.get("feature_contributions", {})
            if importance or contrib:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Feature Analysis</div>', unsafe_allow_html=True)
                tab1, tab2 = st.tabs(["Feature Importance", "Feature Contributions"])
                with tab1:
                    if importance:
                        st.bar_chart(importance)
                    else:
                        st.info("No feature importance data available.")
                with tab2:
                    if contrib:
                        st.bar_chart(contrib)
                        top_driver = max(contrib, key=contrib.get)
                        risk_driver = min(contrib, key=contrib.get)
                        dc1, dc2 = st.columns(2)
                        dc1.success(f"Strongest driver: **{top_driver}**")
                        dc2.warning(f"Limiting factor: **{risk_driver}**")
                    else:
                        st.info("No contribution data available.")
                st.markdown('</div>', unsafe_allow_html=True)

            # ── AI Insights ──────────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">CARVanta AI Insights (Original Engine v4)</div>', unsafe_allow_html=True)
            insight = data.get("ai_insight", "")
            deep = data.get("deep_insight", "")
            if insight:
                st.markdown(f"**Primary Analysis:**\n\n{insight}")
            if deep:
                with st.expander("🔬 Detailed Feature-Level Analysis"):
                    st.markdown(deep)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Download Report ──────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Download Report</div>', unsafe_allow_html=True)
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                try:
                    text_res = requests.get(f"{API_BASE}/api/report/{antigen}/text")
                    if text_res.status_code == 200:
                        st.download_button(
                            "📄 Download Text Report",
                            data=text_res.text,
                            file_name=f"CARVanta_{antigen}_Report.txt",
                            mime="text/plain",
                        )
                except Exception:
                    st.caption("Report unavailable")
            with dl_col2:
                try:
                    pdf_res = requests.get(f"{API_BASE}/api/report/{antigen}/pdf")
                    if pdf_res.status_code == 200:
                        st.download_button(
                            "📋 Download PDF Report",
                            data=pdf_res.content,
                            file_name=f"CARVanta_{antigen}_Report.pdf",
                            mime="application/pdf",
                        )
                except Exception:
                    st.caption("PDF unavailable")
            st.markdown('</div>', unsafe_allow_html=True)


            # ── Raw data ─────────────────────────────────────────────────
            with st.expander("View Full Feature Breakdown"):
                st.json(features)
        else:
            st.error("Could not reach the CARVanta backend. Ensure the API is running on port 8001.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 – Antigen Comparison
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚖️ Antigen Comparison":
    st.markdown('<div class="section-header">Antigen Comparison</div>', unsafe_allow_html=True)

    all_antigens, _ = fetch_antigens(limit=200)
    compare_antigens = st.multiselect(
        "Select antigens to compare (2+)",
        all_antigens,
        default=["CD19", "BCMA", "HER2"] if all(a in all_antigens for a in ["CD19", "BCMA", "HER2"]) else [],
    )

    col_compare, col_recommend = st.columns(2)
    with col_compare:
        compare_btn = st.button("Compare Selected", key="compare_btn")
    with col_recommend:
        recommend_btn = st.button("AI Recommendation", key="recommend_btn")

    if compare_btn:
        if len(compare_antigens) < 2:
            st.warning("Please select at least two antigens to compare.")
        else:
            with st.spinner("Comparing…"):
                response = requests.post(f"{API_BASE}/batch_score", json={"antigens": compare_antigens})
            if response.status_code == 200:
                results = response.json()
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Comparison Results</div>', unsafe_allow_html=True)
                for item in results:
                    tier = item.get("tier", "—")
                    tier_class = "tier-1" if "Tier 1" in tier else "tier-2" if "Tier 2" in tier else "tier-3" if "Tier 3" in tier else "tier-4"
                    st.markdown(f"""
                    <div class="compare-item">
                        <strong>{item['antigen']}</strong>
                        &nbsp;&nbsp;Score: <strong>{item['CVS']}</strong>
                        &nbsp;&nbsp;Confidence: <strong>{item['confidence_score']}</strong>
                        &nbsp;&nbsp;<span class="tier-badge {tier_class}">{tier}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Bar chart comparison
                chart_data = {item["antigen"]: item["CVS"] for item in results}
                st.bar_chart(chart_data)
            else:
                st.error("Comparison request failed.")

    if recommend_btn:
        if not compare_antigens:
            st.warning("Select antigens first.")
        else:
            with st.spinner("Generating recommendation…"):
                response = requests.post(f"{API_BASE}/recommend", json={"antigens": compare_antigens})
            if response.status_code == 200:
                data = response.json()
                rec = data.get("recommendation", {})
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">AI Recommendation</div>', unsafe_allow_html=True)
                st.metric("Best Antigen", rec.get("best_antigen", "—"))
                st.info(rec.get("reason", ""))
                st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 – Tissue Risk Heatmap (NEW v3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧫 Tissue Risk Heatmap":
    st.markdown('<div class="section-header">🧫 Tissue Risk Heatmap — Off-Tumor Toxicity Prediction</div>', unsafe_allow_html=True)
    st.caption("Predicts off-tumor/on-target toxicity by mapping antigen expression across 17 organ systems using GTEx-modeled normal tissue data.")

    antigen = st.selectbox("Select an antigen", antigen_list, index=0 if antigen_list else None, key="heatmap_antigen")

    if st.button("Generate Heatmap", key="heatmap_btn"):
        with st.spinner("Analyzing tissue expression…"):
            response = requests.get(f"{API_BASE}/api/safety/{antigen}/toxicity")

        if response.status_code == 200:
            data = response.json()

            # ── Summary metrics ──────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Aggregate Toxicity Index", f"{data.get('aggregate_toxicity_index', 0):.3f}")
            sc2.metric("Tissue Risk Score", f"{data.get('tissue_risk_score', 0):.3f}")
            sc3.metric("Organs Analyzed", data.get("organs_analyzed", 0))
            st.caption(f"Data source: {data.get('data_source', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Organ-level heatmap ──────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Organ-Level Risk Map</div>', unsafe_allow_html=True)

            tissue_map = data.get("tissue_risk_map", {})
            for organ, info in tissue_map.items():
                risk_class = info.get("risk_class", "LOW")
                css_class = {
                    "NEGLIGIBLE": "heatmap-neg",
                    "LOW": "heatmap-low",
                    "MODERATE": "heatmap-mod",
                    "HIGH": "heatmap-high",
                }.get(risk_class, "heatmap-low")

                critical_icon = "⚠️ " if info.get("is_critical") and risk_class in ("HIGH", "MODERATE") else ""
                st.markdown(
                    f'<div class="heatmap-row {css_class}">'
                    f'{critical_icon}<strong>{organ}</strong>'
                    f'&nbsp;&nbsp;TPM: {info.get("estimated_tpm", 0):.2f}'
                    f'&nbsp;&nbsp;Risk: {info.get("risk_score", 0):.3f}'
                    f'&nbsp;&nbsp;{risk_class}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Critical organ alerts ────────────────────────────────────
            alerts = data.get("critical_organ_alerts", [])
            if alerts:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">⚠️ Critical Organ Alerts</div>', unsafe_allow_html=True)
                for alert in alerts:
                    if alert.get("severity") == "CRITICAL":
                        st.error(alert.get("message", ""))
                    else:
                        st.warning(alert.get("message", ""))
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Safety recommendation ────────────────────────────────────
            rec = data.get("safety_recommendation", "")
            if rec:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Safety Recommendation</div>', unsafe_allow_html=True)
                if "FAVORABLE" in rec:
                    st.success(rec)
                elif "DANGEROUS" in rec:
                    st.error(rec)
                elif "CAUTION" in rec:
                    st.warning(rec)
                else:
                    st.info(rec)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("Failed to generate toxicity data.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 – Multi-Target Synergy Matrix (NEW v3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎯 Multi-Target Synergy":
    st.markdown('<div class="section-header">🎯 Antigen Synergy Matrix — Multi-Target CAR-T Scoring</div>', unsafe_allow_html=True)
    st.caption("Score multi-antigen CAR-T combinations for complementarity, escape risk reduction, coverage, and aggregate safety.")

    all_antigens, _ = fetch_antigens(limit=200)
    combo_antigens = st.multiselect(
        "Select 2-4 antigens for combination scoring",
        all_antigens,
        default=["CD19", "CD22"] if all(a in all_antigens for a in ["CD19", "CD22"]) else [],
        key="combo_select",
    )

    if st.button("Score Combination", key="synergy_btn"):
        if len(combo_antigens) < 2:
            st.warning("Select at least 2 antigens for combination scoring.")
        elif len(combo_antigens) > 4:
            st.warning("Maximum 4 antigens per combination.")
        else:
            with st.spinner("Computing synergy matrix…"):
                response = requests.post(f"{API_BASE}/api/multi-target", json={"antigens": combo_antigens})

            if response.status_code == 200:
                data = response.json()

                # ── Synergy Score ────────────────────────────────────────
                score = data.get("synergy_score", 0)
                css_class = "synergy-good" if score >= 0.7 else "synergy-ok" if score >= 0.5 else "synergy-bad"
                st.markdown('<div class="clinical-card" style="text-align:center;">', unsafe_allow_html=True)
                st.markdown(f'<div class="synergy-score {css_class}">{score:.3f}</div>', unsafe_allow_html=True)
                st.markdown('<div style="color:#64748B;font-size:14px;margin-top:4px;">Synergy Score</div>', unsafe_allow_html=True)
                verdict = data.get("verdict", "")
                if verdict:
                    st.markdown(f'<div style="margin-top:10px;font-weight:600;">{verdict}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Component breakdown ──────────────────────────────────
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Complementarity", f"{data.get('complementarity_score', 0):.3f}")
                m2.metric("Escape Risk Reduction", f"{data.get('escape_risk_reduction', 0):.3f}")
                m3.metric("Coverage", f"{data.get('coverage_score', 0):.3f}")
                m4.metric("Aggregate Safety", f"{data.get('aggregate_safety', 0):.3f}")
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Per-antigen details ───────────────────────────────────
                per_antigen = data.get("per_antigen", [])
                if per_antigen:
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Per-Antigen Profile</div>', unsafe_allow_html=True)
                    for ag in per_antigen:
                        st.markdown(f"""
                        <div class="compare-item">
                            <strong>{ag.get('antigen', '?')}</strong>
                            &nbsp;&nbsp;CVS: <strong>{ag.get('cvs', 0):.3f}</strong>
                            &nbsp;&nbsp;Safety: <strong>{ag.get('safety', 0):.3f}</strong>
                            &nbsp;&nbsp;Specificity: <strong>{ag.get('specificity', 0):.3f}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── AI Synergy Insight ───────────────────────────────────
                ai_insight = data.get("ai_insight", "")
                recommendation = data.get("recommendation", "")
                if ai_insight or recommendation:
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">CARVanta AI Synergy Analysis</div>', unsafe_allow_html=True)
                    if ai_insight:
                        st.markdown(ai_insight)
                    if recommendation:
                        st.info(f"**Recommendation:** {recommendation}")
                    st.markdown('</div>', unsafe_allow_html=True)

                with st.expander("View Raw Synergy Data"):
                    st.json(data)
            else:
                st.error("Multi-target scoring failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 – Patient Stratification (NEW v3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Patient Stratification":
    st.markdown('<div class="section-header">👥 Biomarker Stratification Engine — Patient Subgroup Analysis</div>', unsafe_allow_html=True)
    st.caption("Identify which patient subgroups would most likely benefit from a specific antigen-targeted CAR-T therapy.")

    antigen = st.selectbox("Select an antigen", antigen_list, index=0 if antigen_list else None, key="strat_antigen")

    all_antigens_full, _ = fetch_antigens(limit=200)
    # Extract cancer types from precomputed data
    cancer_types = ["All", "Breast Cancer", "Lung Adenocarcinoma", "Glioblastoma", "Prostate Cancer",
                    "Colorectal Cancer", "Ovarian Cancer", "Leukemia", "Melanoma", "Liver Cancer",
                    "Renal Cancer", "Gastric Cancer", "Pancreatic Cancer", "Lymphoma", "Myeloma"]
    cancer_type = st.selectbox("Cancer type (optional)", cancer_types, index=0, key="strat_cancer")

    if st.button("Run Stratification", key="strat_btn"):
        with st.spinner("Stratifying patient subgroups…"):
            payload = {"antigen_name": antigen}
            if cancer_type != "All":
                payload["cancer_type"] = cancer_type
            response = requests.post(f"{API_BASE}/api/stratify", json=payload)

        if response.status_code == 200:
            data = response.json()

            # ── Summary ──────────────────────────────────────────────────
            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Stratification Summary</div>', unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Subgroups Found", data.get("n_subgroups", 0))
            sc2.metric("Total Cancer Types", data.get("cancer_types_analyzed", 0))
            sc3.metric("Eligibility Estimate", data.get("overall_eligibility", "N/A"))
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Subgroups ────────────────────────────────────────────────
            subgroups = data.get("subgroups", [])
            if subgroups:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Patient Subgroups</div>', unsafe_allow_html=True)
                for sg in subgroups:
                    expr_level = sg.get("expression_level", "medium")
                    badge_class = "risk-low" if expr_level == "high" else "risk-mod" if expr_level == "medium" else "risk-high"
                    st.markdown(f"""
                    <div class="compare-item">
                        <strong>{sg.get('cancer_type', '?')}</strong>
                        &nbsp;&nbsp;<span class="{badge_class}">{expr_level} expression</span>
                        &nbsp;&nbsp;Prevalence: <strong>{sg.get('prevalence', 'N/A')}</strong>
                        &nbsp;&nbsp;Benefit: <strong>{sg.get('predicted_benefit', 'N/A')}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # ── AI Stratification Insight ─────────────────────────────
            ai_insight = data.get("ai_insight", "")
            if ai_insight:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">CARVanta AI Stratification Analysis</div>', unsafe_allow_html=True)
                st.markdown(ai_insight)
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Recommendation ───────────────────────────────────────────
            rec = data.get("recommendation", "")
            if rec:
                st.info(f"**Recommendations:** {rec}")

            with st.expander("View Full Stratification Data"):
                st.json(data)
        else:
            st.error("Stratification failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 – NLP Query Search (NEW v3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 NLP Query Search":
    st.markdown('<div class="section-header">🔍 CARVanta Query Language — AI-Powered Antigen Search</div>', unsafe_allow_html=True)
    st.caption("Search for antigens using plain English. CARVanta v4 uses cancer-context-aware scoring + semantic NLP for intelligent results.")

    st.markdown("""
    **Example queries:**
    - *Find targets for triple-negative breast cancer with low toxicity*
    - *Show me the best surface antigens for leukemia*
    - *Top 10 highly specific immunogenic targets for melanoma*
    - *Safe CAR-T targets for glioblastoma tier 1 only*
    """)

    query = st.text_input("Enter your query", placeholder="e.g. Find targets for leukemia with low toxicity risk", key="nlp_query")

    if st.button("Search", key="nlp_btn") and query:
        with st.spinner("Processing query with v4 adaptive engine…"):
            response = requests.post(f"{API_BASE}/api/query", json={"query": query})

        if response.status_code == 200:
            data = response.json()
            parsed = data.get("parsed_query", {})
            summary = data.get("summary", "")
            search_method = data.get("search_method", "keyword")

            if summary:
                st.markdown(f'<div class="query-summary">{summary}</div>', unsafe_allow_html=True)

            # ── Search method + parsed filters ────────────────────────────
            with st.expander("Query Interpretation"):
                pc1, pc2, pc3, pc4 = st.columns(4)
                pc1.metric("Cancer Type", parsed.get("cancer_type", "Any"))
                pc2.metric("Safety Preference", parsed.get("safety_preference", "Any"))
                pc3.metric("Tier Filter", f"≤ Tier {parsed.get('tier_filter', 'Any')}" if parsed.get("tier_filter") else "Any")
                pc4.metric("Search Engine", search_method)

            # ── Results ──────────────────────────────────────────────────
            results = data.get("results", [])
            returned = data.get("returned", 0)
            total = data.get("total_matches", 0)

            st.markdown(f"**{returned} results** shown (of {total} total matches)")

            if results:
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                for i, item in enumerate(results[:20], 1):
                    cvs = item.get("CVS", 0)
                    ml_score = item.get("ml_score", 0)
                    blended = item.get("blended_score", cvs)
                    sim = item.get("semantic_similarity", 0)
                    tier = item.get("tier", "—")
                    tier_class = "tier-1" if "Tier 1" in tier else "tier-2" if "Tier 2" in tier else "tier-3" if "Tier 3" in tier else "tier-4"
                    st.markdown(f"""
                    <div class="compare-item">
                        <strong>#{i}&nbsp; {item.get('antigen', '?')}</strong>
                        &nbsp;&nbsp;{item.get('cancer_type', '')}
                        &nbsp;&nbsp;Score: <strong>{blended:.3f}</strong>
                        &nbsp;&nbsp;ML: {ml_score:.3f}
                        &nbsp;&nbsp;<span class="tier-badge {tier_class}">{tier}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No antigens matched your search. Try broadening your query.")
        else:
            st.error("Query failed.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7 – Clinical Trials (NEW v3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💊 Clinical Trials":
    st.markdown('<div class="section-header">💊 Clinical Trials — Real ClinicalTrials.gov Data</div>', unsafe_allow_html=True)
    st.caption("Fetch real clinical trial data for any antigen from ClinicalTrials.gov API.")

    antigen = st.selectbox("Select an antigen", antigen_list, index=0 if antigen_list else None, key="ct_antigen")

    if st.button("Fetch Trials", key="ct_btn"):
        with st.spinner("Fetching from ClinicalTrials.gov…"):
            response = requests.get(f"{API_BASE}/api/clinical-trials/{antigen}")

        if response.status_code == 200:
            data = response.json()

            if data.get("status") == "fetched":
                # ── Summary ──────────────────────────────────────────────
                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Trial Summary</div>', unsafe_allow_html=True)
                tc1, tc2 = st.columns(2)
                tc1.metric("Total Trials", data.get("total_trials", 0))
                tc2.metric("CAR-T Specific Trials", data.get("car_t_trials", 0))
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Phase distribution ───────────────────────────────────
                phases = data.get("phase_distribution", {})
                if phases:
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Phase Distribution</div>', unsafe_allow_html=True)
                    st.bar_chart(phases)
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── Status distribution ──────────────────────────────────
                statuses = data.get("status_distribution", {})
                if statuses:
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Status Distribution</div>', unsafe_allow_html=True)
                    st.bar_chart(statuses)
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── Recent trials ────────────────────────────────────────
                recent = data.get("recent_trials", [])
                if recent:
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Recent Trials</div>', unsafe_allow_html=True)
                    for trial in recent:
                        nct = trial.get("nct_id", "")
                        title = trial.get("title", "Untitled")
                        status = trial.get("status", "Unknown")
                        status_color = "risk-low" if status in ("RECRUITING", "ACTIVE_NOT_RECRUITING") else "risk-mod"
                        st.markdown(f"""
                        <div class="compare-item">
                            <strong>{nct}</strong> &nbsp;—&nbsp; {title}
                            <br><span class="{status_color}">{status}</span>
                            &nbsp; Phases: {', '.join(trial.get('phases', []))}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning(f"Could not fetch trial data: {data.get('status', 'unknown')}")
                if data.get("error"):
                    st.error(data["error"])
        else:
            st.error("Failed to fetch clinical trial data.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8 – Global Leaderboard
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Global Leaderboard":
    st.markdown('<div class="section-header">🏆 Global CAR-T Leaderboard — Adaptive ML-Driven Rankings</div>', unsafe_allow_html=True)
    st.caption("Rankings are computed using the CARVanta v4 Adaptive Score: a blend of rule-based CVS (60%) and ML regression ranker (40%). Select a cancer type to see cancer-specific rankings.")

    lb_col1, lb_col2 = st.columns([2, 1])
    with lb_col1:
        top_n = st.slider("Number of targets to show", 10, 100, 25)
    with lb_col2:
        # Fetch cancer types from API
        try:
            ct_res = requests.get(f"{API_BASE}/api/cancer-types")
            cancer_types = ct_res.json() if ct_res.status_code == 200 else []
        except Exception:
            cancer_types = []
        cancer_filter = st.selectbox(
            "Cancer Type",
            ["All (Global)"] + cancer_types,
            index=0,
            key="lb_cancer",
        )

    if st.button("Load Leaderboard", key="leaderboard_btn"):
        with st.spinner("Computing adaptive rankings…"):
            params = {"top_n": top_n}
            if cancer_filter != "All (Global)":
                params["cancer_type"] = cancer_filter
            res = requests.get(f"{API_BASE}/rank", params=params)

        if res.status_code == 200:
            data = res.json()
            if cancer_filter != "All (Global)":
                st.info(f"Showing **{cancer_filter}**-specific rankings — targets ranked by cancer-specific expression data + ML prediction.")

            st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Top Antigens</div>', unsafe_allow_html=True)
            for i, item in enumerate(data[:top_n], 1):
                inp = item.get("input", {})
                result = item.get("result", {})
                cvs = result.get("CVS", 0)
                ml_score = result.get("ml_score", 0.5)
                tier = result.get("tier", "")
                tier_class = "tier-1" if "Tier 1" in tier else "tier-2" if "Tier 2" in tier else "tier-3" if "Tier 3" in tier else "tier-4"
                st.markdown(f"""
                <div class="compare-item">
                    <strong>#{i} &nbsp; {inp.get('antigen', '?')}</strong>
                    &nbsp;—&nbsp; {inp.get('cancer_type', '')}
                    &nbsp;&nbsp;Score: <strong>{cvs:.3f}</strong>
                    &nbsp;&nbsp;ML: <strong>{ml_score:.3f}</strong>
                    &nbsp;&nbsp;<span class="tier-badge {tier_class}">{tier}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if data:
                best = data[0]
                best_inp = best.get("input", {})
                best_res = best.get("result", {})
                st.success(f"🥇 Top candidate: **{best_inp.get('antigen', '?')}** ({best_inp.get('cancer_type', '')}) — Score: {best_res.get('CVS', 0):.3f}")
        else:
            st.error("Could not load leaderboard.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 9 – Dataset Intelligence (NEW v5)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dataset Intelligence":
    st.markdown('<div class="section-header">📊 Dataset Intelligence — 3-Tier Biomarker Classification</div>', unsafe_allow_html=True)
    st.caption("Separating REAL validated targets from AI-generated training data. This is how CARVanta maintains scientific credibility.")

    if st.button("Load Dataset Analysis", key="di_btn"):
        with st.spinner("Analyzing dataset composition…"):
            try:
                res = requests.get(f"{API_BASE}/api/dataset-intelligence")
                if res.status_code == 200:
                    data = res.json()

                    # ── Overview metrics ────────────────────────────────────
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Database Overview</div>', unsafe_allow_html=True)
                    ov1, ov2, ov3, ov4 = st.columns(4)
                    ov1.metric("Total Rows", f"{data.get('total_rows', 0):,}")
                    ov2.metric("Unique Biomarkers", f"{data.get('unique_biomarkers', 0):,}")
                    ov3.metric("Cancer Types", data.get('cancer_types', 0))
                    tiers = data.get('tiers', {})
                    validated = tiers.get('validated', {})
                    ov4.metric("Validated Targets", validated.get('unique_antigens', 0))
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ── 3-Tier Breakdown ──────────────────────────────────
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">3-Tier Dataset Architecture</div>', unsafe_allow_html=True)

                    # Validated Layer
                    val = tiers.get('validated', {})
                    st.markdown(f"""
                    <div class="compare-item" style="border-left: 4px solid #059669;">
                        <span class="tier-badge tier-1">🟢 Validated Layer</span>
                        &nbsp;&nbsp;<strong>{val.get('unique_antigens', 0)}</strong> unique antigens
                        &nbsp;&nbsp;<strong>{val.get('rows', 0):,}</strong> database rows
                        <br><small style="color:#64748B;">{val.get('description', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    # Predicted Layer
                    pred = tiers.get('predicted', {})
                    st.markdown(f"""
                    <div class="compare-item" style="border-left: 4px solid #D97706;">
                        <span class="tier-badge tier-3">🟡 Predicted Layer</span>
                        &nbsp;&nbsp;AI-predicted cross-cancer associations
                        <br><small style="color:#64748B;">{pred.get('description', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    # Synthetic Layer
                    syn = tiers.get('synthetic', {})
                    st.markdown(f"""
                    <div class="compare-item" style="border-left: 4px solid #DC2626;">
                        <span class="tier-badge tier-4">🔴 Synthetic Layer</span>
                        &nbsp;&nbsp;<strong>{syn.get('unique_antigens', 0):,}</strong> unique antigens
                        &nbsp;&nbsp;<strong>{syn.get('rows', 0):,}</strong> training instances
                        <br><small style="color:#64748B;">{syn.get('description', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ── Credibility Signals ────────────────────────────────
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">Credibility Signals</div>', unsafe_allow_html=True)

                    sdb = data.get('source_databases', {})
                    evl = data.get('evidence_levels', {})

                    cred_col1, cred_col2 = st.columns(2)
                    with cred_col1:
                        st.markdown("**Source Database Breakdown:**")
                        for db, count in sdb.items():
                            if db == "TCGA":
                                st.markdown(f"- 🧬 **{db}**: {count:,} rows")
                            elif db == "UniProt":
                                st.markdown(f"- 🧪 **{db}**: {count:,} rows")
                            elif db == "Literature":
                                st.markdown(f"- 📚 **{db}**: {count:,} rows")
                            else:
                                st.markdown(f"- 🤖 **{db}**: {count:,} rows")
                    with cred_col2:
                        st.markdown("**Evidence Level Breakdown:**")
                        for level, count in evl.items():
                            if level == "clinical":
                                st.markdown(f"- ✅ **{level}**: {count:,} rows")
                            elif level == "preclinical":
                                st.markdown(f"- 🔬 **{level}**: {count:,} rows")
                            else:
                                st.markdown(f"- 🤖 **{level}**: {count:,} rows")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ── Investor Framing ──────────────────────────────────
                    inv = data.get('investor_framing', {})
                    st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="section-header">🚀 {inv.get("headline", "CARVanta")}</div>', unsafe_allow_html=True)

                    st.markdown("**❌ Don't say:** \"We have 100k biomarkers\"")
                    st.markdown("**✅ Instead say:**")
                    quote_text = "We built an AI-augmented biomarker intelligence platform with:"
                    st.markdown(f'<div class="query-summary">{quote_text}</div>', unsafe_allow_html=True)
                    points = inv.get('points', [])
                    for pt in points:
                        st.markdown(f"- **{pt}**")

                    st.divider()
                    st.markdown("**🎯 Investor Pitch Lines:**")
                    pitch_lines = inv.get('pitch_lines', [])
                    for pl in pitch_lines:
                        st.markdown(f'> *"{pl}"*')

                    st.success("👍 That\'s how you turn a \"fake-looking dataset\" into a **deep tech advantage**")
                    st.markdown('</div>', unsafe_allow_html=True)

                else:
                    st.error("Failed to load dataset intelligence.")
            except requests.ConnectionError:
                st.error("Cannot connect to the CARVanta backend at " + API_BASE)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 10 – System Status
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ System Status":
    st.markdown('<div class="section-header">⚙️ System Status</div>', unsafe_allow_html=True)

    if st.button("Check System Health", key="health_btn"):
        try:
            res = requests.get(f"{API_BASE}/health")
            if res.status_code == 200:
                h = res.json()

                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Status", h.get("status", "—"))
                sc2.metric("Version", h.get("version", "—"))
                sc3.metric("Antigens Loaded", h.get("antigen_count", "—"))
                sc4.metric("Cancer Types", h.get("cancer_types", "—"))
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="clinical-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">Engine Details</div>', unsafe_allow_html=True)
                st.metric("Model", h.get("model", "—"))
                st.metric("Total Biomarkers", h.get("total_biomarkers", "—"))
                st.metric("Unique Biomarkers", h.get("unique_biomarkers", "—"))

                # v5: Show tier breakdown
                dt1, dt2, dt3 = st.columns(3)
                dt1.metric("🟢 Validated Targets", h.get("validated_targets", 0))
                dt2.metric("🔴 Predicted (Synthetic)", h.get("predicted_targets", 0))
                dt3.metric("📊 Training Instances", f"{h.get('training_instances', 0):,}")

                features = h.get("features", [])
                if features:
                    st.markdown("**Scoring Features:** " + ", ".join(features))

                new_endpoints = h.get("new_endpoints", [])
                if new_endpoints:
                    st.markdown("**API Endpoints:** " + ", ".join(f"`{e}`" for e in new_endpoints))
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.error("Health check returned a non-200 response.")
        except requests.ConnectionError:
            st.error("Cannot connect to the CARVanta backend at " + API_BASE)

# ─── Footer ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<div style="text-align:center; color:#94A3B8; font-size:12px; padding:12px 0;">'
    'CARVanta v4 · AI-Augmented Biomarker Intelligence Platform · '
    'Validated Targets + AI-Predicted Cross-Cancer Associations + Simulated Training Instances'
    '</div>',
    unsafe_allow_html=True,
)