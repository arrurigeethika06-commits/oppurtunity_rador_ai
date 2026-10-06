from datetime import datetime

import streamlit as st

from app.db.connection import initialize_database
from app.db.crud import fetch_all_opportunities, fetch_all_users


CATEGORY_FILTERS = {
    "Internships": {"Internship"},
    "Jobs": {"Private Job", "Government Job"},
    "Government Exams": {
        "Government Examination",
        "Competitive Examination",
        "Entrance Examination",
    },
    "Scholarships": {"Scholarship", "Fellowship"},
    "Competitions": {
        "Coding Competition",
        "Hackathon",
        "Technical Event",
        "Workshop/Seminar",
    },
    "Hackathons": {"Hackathon"},
}
KNOWN_CATEGORIES = set().union(*CATEGORY_FILTERS.values())


def _is_real_opportunity(opportunity):
    tags = {
        tag.strip().casefold()
        for tag in (opportunity.get("tags") or "").split(",")
        if tag.strip()
    }
    return "demo" not in tags and opportunity.get("verification_status") != "rejected"


def _matches_search(opportunity, query):
    searchable_fields = (
        "title",
        "organization",
        "category",
        "description",
        "eligibility",
        "location",
    )
    return not query or any(
        query in str(opportunity.get(field) or "").casefold()
        for field in searchable_fields
    )


def _format_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
        return parsed.strftime("%b %d, %Y")
    return parsed.strftime("%b %d, %Y %I:%M %p %Z").strip()


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Opportunity Radar AI",
    page_icon="🎯",
    layout="wide"
)

# -----------------------------
# INITIALIZE DATABASE
# -----------------------------
try:
    initialize_database()
except Exception as e:
    st.error(f"Database initialization failed: {e}")


# -----------------------------
# HEADER
# -----------------------------
st.title("🎯 Opportunity Radar AI")
st.subheader("Your One-Stop Platform for Opportunities")

st.write(
    "Find and track internships, jobs, exams, scholarships, "
    "competitions and other opportunities in one place."
)

st.divider()


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("🔎 Search & Filter")

category = st.sidebar.selectbox(
    "Opportunity Category",
    [
        "All",
        "Internships",
        "Jobs",
        "Government Exams",
        "Scholarships",
        "Competitions",
        "Hackathons",
        "Other"
    ]
)

search = st.sidebar.text_input(
    "Search Opportunity"
)

try:
    real_opportunities = [
        opportunity
        for opportunity in fetch_all_opportunities()
        if _is_real_opportunity(opportunity)
    ]
except Exception as e:
    real_opportunities = []
    st.error(f"Unable to load opportunities from the database: {e}")


# -----------------------------
# DASHBOARD
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📢 Opportunities", len(real_opportunities))

with col2:
    st.metric(
        "💼 Internships",
        sum(item.get("category") == "Internship" for item in real_opportunities),
    )

with col3:
    st.metric(
        "🏆 Competitions",
        sum(
            item.get("category") in CATEGORY_FILTERS["Competitions"]
            for item in real_opportunities
        ),
    )

with col4:
    st.metric(
        "📝 Exams",
        sum(
            item.get("category") in CATEGORY_FILTERS["Government Exams"]
            for item in real_opportunities
        ),
    )


st.divider()


# -----------------------------
# OPPORTUNITIES
# -----------------------------
st.header("📌 Latest Opportunities")
if category == "All":
    filtered_opportunities = real_opportunities
elif category == "Other":
    filtered_opportunities = [
        opportunity
        for opportunity in real_opportunities
        if opportunity.get("category") not in KNOWN_CATEGORIES
    ]
else:
    selected_categories = CATEGORY_FILTERS[category]
    filtered_opportunities = [
        opportunity
        for opportunity in real_opportunities
        if opportunity.get("category") in selected_categories
    ]

search_query = search.strip().casefold()
filtered_opportunities = [
    opportunity
    for opportunity in filtered_opportunities
    if _matches_search(opportunity, search_query)
]

if not real_opportunities:
    st.info("No collected opportunities yet. Run the government collector to add verified opportunities.")
elif not filtered_opportunities:
    st.info("No opportunities match the selected search and category filters.")
else:
    for opportunity in filtered_opportunities:
        st.markdown("---")
        st.subheader(opportunity.get("title") or "Untitled opportunity")
        st.write(f"**Organization:** {opportunity.get('organization') or 'Not provided'}")
        st.write(f"**Category:** {opportunity.get('category') or 'Not provided'}")

        description = opportunity.get("description")
        if description:
            st.write(description)

        deadline = (
            opportunity.get("application_deadline")
            or opportunity.get("registration_deadline")
            or opportunity.get("event_date")
            or opportunity.get("exam_date")
        )
        formatted_deadline = _format_date(deadline)
        if formatted_deadline:
            st.write(f"**Deadline:** {formatted_deadline}")

        published_date = _format_date(opportunity.get("published_at"))
        if published_date:
            st.write(f"**Published:** {published_date}")

        with st.container(horizontal=True):
            apply_url = opportunity.get("application_url")
            if apply_url:
                st.link_button("Apply Now", apply_url)

            source_url = opportunity.get("source_url") or opportunity.get("official_url")
            if source_url:
                st.link_button("Source", source_url)


# -----------------------------
# DATABASE TEST
# -----------------------------
st.divider()

st.header("🗄️ Database Status")

try:
    users = fetch_all_users()

    st.success("✅ Database connected successfully!")

    st.write(f"Registered users: **{len(users)}**")

except Exception as e:
    st.error(f"Database connection error: {e}")


# -----------------------------
# FOOTER
# -----------------------------
st.divider()

st.caption(
    "Opportunity Radar AI • Built to bring opportunities into one platform 🚀"
)