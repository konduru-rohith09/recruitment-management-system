import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy.orm import Session

from src.database import SessionLocal, init_db
from src.models import (
    Department,
    JobRequisition,
    Application,
    Interview,
    Feedback,
    Offer,
    AnomalyRecord,
    RequisitionStatus,
    ApplicationStage,
    InterviewStatus,
    OfferStatus,
)
from src.metrics import MetricsCalculator
from src.audit import AuditService
from src.validation import DataValidator

# Page Configuration
st.set_page_config(
    page_title="Recruitment Management & Workflow Intelligence Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        margin: 8px 0 0 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_session():
    init_db()
    return SessionLocal()


def load_departments(db: Session):
    return db.query(Department).all()


def load_anomalies(db: Session):
    return db.query(AnomalyRecord).order_by(AnomalyRecord.detected_at.desc()).all()


def main():
    db = get_database_session()

    # Sidebar Filters
    st.sidebar.image("https://img.icons8.com/fluency/96/recruitment.png", width=64)
    st.sidebar.title("Talent Intelligence")
    st.sidebar.caption("Enterprise Workflow & Compliance")

    departments = load_departments(db)
    dept_options = {"All Departments": None}
    for d in departments:
        dept_options[f"{d.name} ({d.code})"] = d.id

    selected_dept_label = st.sidebar.selectbox("Filter by Department", list(dept_options.keys()))
    selected_dept_id = dept_options[selected_dept_label]

    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh Data & Rescan Anomalies"):
        AuditService.scan_for_anomalies(db)
        st.sidebar.success("Audit scan complete!")
        st.rerun()

    # Title & Subtitle
    st.title("🎯 Recruitment Management & Workflow Analytics")
    st.caption("Real-time pipeline metrics, automated lifecycle compliance, and audit anomaly detection.")

    # Compute Metrics Live from Persisted Source Data
    metrics = MetricsCalculator.compute_all_metrics(db=db, department_id=selected_dept_id)

    # 1. Top Level KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Requisitions</h3>
            <p>{metrics['overview']['total_requisitions']:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Active Applications</h3>
            <p>{metrics['overview']['total_applications']:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Screening Pass Rate</h3>
            <p>{metrics['screening']['screening_pass_rate_pct']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Offer Acceptance</h3>
            <p>{metrics['offers']['offer_acceptance_rate_pct']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        anom_count = metrics['anomalies']['total_count']
        anom_color = "#ef4444" if anom_count > 0 else "#22c55e"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Anomalies Flagged</h3>
            <p style="color: {anom_color};">{anom_count}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Dashboard Tabs
    tab_funnel, tab_requisitions, tab_interviews, tab_anomalies, tab_validation = st.tabs([
        "📊 Hiring Funnel",
        "📋 Requisitions & Stages",
        "🎙️ Interviews & Feedback",
        "🚨 Anomaly Center (5 Scenarios)",
        "✅ Data Validation Audit",
    ])

    # TAB 1: Hiring Funnel
    with tab_funnel:
        st.subheader("Talent Acquisition Funnel Progression")
        stages_data = metrics['applications_by_stage']

        funnel_order = [
            "APPLIED", "SCREENING", "INTERVIEW", "DECISION_PENDING",
            "OFFER_PENDING_APPROVAL", "OFFERED", "ACCEPTED"
        ]
        funnel_counts = [stages_data.get(stage, 0) for stage in funnel_order]

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_order,
            x=funnel_counts,
            textinfo="value+percent initial",
            marker={"color": ["#38bdf8", "#60a5fa", "#818cf8", "#a78bfa", "#c084fc", "#f472b6", "#4ade80"]}
        ))
        fig_funnel.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            st.metric("Avg Screening Score", f"{metrics['screening']['average_screening_score']:.1f} / 100")
        with cf2:
            st.metric("Avg Time to Decision", f"{metrics['funnel_rates']['avg_time_to_decision_days']} Days")
        with cf3:
            st.metric("Withdrawal Rate", f"{metrics['funnel_rates']['withdrawal_rate_pct']:.1f}%")

    # TAB 2: Requisitions & Stages
    with tab_requisitions:
        st.subheader("Requisition Status and Application Distributions")
        c1, c2 = st.columns(2)

        with c1:
            st.write("##### Requisitions by Status")
            req_status = metrics['requisitions_by_status']
            if req_status:
                df_req_st = pd.DataFrame(list(req_status.items()), columns=["Status", "Count"])
                fig_req = px.pie(
                    df_req_st, names="Status", values="Count",
                    hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_req.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
                st.plotly_chart(fig_req, use_container_width=True)
            else:
                st.info("No requisition records found.")

        with c2:
            st.write("##### Applications by Current Lifecycle Stage")
            app_stages = metrics['applications_by_stage']
            if app_stages:
                df_app_st = pd.DataFrame(list(app_stages.items()), columns=["Stage", "Count"]).sort_values(by="Count", ascending=True)
                fig_bar = px.bar(
                    df_app_st, x="Count", y="Stage", orientation="h",
                    color="Count", color_continuous_scale="Blues"
                )
                fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No applications found.")

    # TAB 3: Interviews & Feedback
    with tab_interviews:
        st.subheader("Interview Pipeline Health & Scorecard Compliance")
        i1, i2, i3, i4 = st.columns(4)
        with i1:
            st.metric("Total Interviews", f"{metrics['interviews']['total_interviews']:,}")
        with i2:
            st.metric("Completed Interviews", f"{metrics['interviews']['completed_interviews']:,}")
        with i3:
            st.metric("Interview Completion Rate", f"{metrics['interviews']['interview_completion_rate_pct']:.1f}%")
        with i4:
            st.metric("Scorecard Feedback Rate", f"{metrics['interviews']['feedback_completion_rate_pct']:.1f}%")

        # Feedback recommendations breakdown
        feedbacks = db.query(Feedback).all()
        if feedbacks:
            fb_df = pd.DataFrame([{
                "Technical Rating": f.technical_rating,
                "Communication": f.communication_rating,
                "Problem Solving": f.problem_solving_rating,
                "Overall Score": f.overall_score,
                "Recommendation": f.recommendation.value if hasattr(f.recommendation, "value") else str(f.recommendation),
            } for f in feedbacks])

            rec_counts = fb_df["Recommendation"].value_counts().reset_index()
            rec_counts.columns = ["Recommendation", "Count"]

            fig_rec = px.bar(
                rec_counts, x="Recommendation", y="Count",
                color="Recommendation", color_discrete_sequence=px.colors.qualitative.Safe,
                title="Interviewer Recommendation Breakdown"
            )
            fig_rec.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_rec, use_container_width=True)

    # TAB 4: Anomaly Center
    with tab_anomalies:
        st.subheader("Automated Anomaly Detection & Policy Enforcement")
        st.write("Live compliance monitoring for all 5 enterprise audit scenarios:")

        anomalies = load_anomalies(db)
        if anomalies:
            anom_data = [{
                "Issue ID": a.issue_id,
                "Scenario Type": a.issue_type,
                "Entity Type": a.affected_entity_type,
                "Record ID": a.affected_record_id,
                "Severity": a.severity.value if hasattr(a.severity, "value") else str(a.severity),
                "Detection Result": a.detection_result.value if hasattr(a.detection_result, "value") else str(a.detection_result),
                "Explanation": a.explanation,
                "Recommended Corrective Action": a.recommended_action,
            } for a in anomalies]
            df_anom = pd.DataFrame(anom_data)

            # Severity filter
            sev_filter = st.multiselect("Filter by Severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH", "MEDIUM"])
            filtered_df = df_anom[df_anom["Severity"].isin(sev_filter)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            st.write("##### Detailed Corrective Actions")
            for idx, row in filtered_df.iterrows():
                with st.expander(f"⚠️ [{row['Severity']}] {row['Issue ID']} - {row['Scenario Type']} (Target: {row['Record ID']})"):
                    st.markdown(f"**Explanation:** {row['Explanation']}")
                    st.markdown(f"**Policy Mandate:** {row['Detection Result']}")
                    st.info(f"💡 **Recommended Action:** {row['Recommended Corrective Action']}")
        else:
            st.success("No policy violations or scheduling anomalies detected in the current database.")

    # TAB 5: Data Validation Audit
    with tab_validation:
        st.subheader("System Data Validation & Integrity Checks")
        report_file = "reports/validation_summary.json"

        if st.button("🧪 Re-run Full Data Validation Suite"):
            res = DataValidator.run_all_validations(db, export_report_path=report_file)
            st.success(f"Validation finished! Total checks: {res['total_checks']}, Passed: {res['passed_checks']}")

        if os.path.exists(report_file):
            with open(report_file, "r", encoding="utf-8") as f:
                val_data = json.load(f)

            v1, v2, v3 = st.columns(3)
            with v1:
                st.metric("Total Validation Checks", val_data["total_checks"])
            with v2:
                st.metric("Checks Passed", val_data["passed_checks"], delta="100%" if val_data["failed_checks"] == 0 else "-")
            with v3:
                st.metric("Failed Checks", val_data["failed_checks"])

            df_chk = pd.DataFrame(val_data["checks"])
            st.dataframe(df_chk, use_container_width=True, hide_index=True)
        else:
            st.info("Validation report not yet generated. Click the button above to run validations.")


if __name__ == "__main__":
    main()
