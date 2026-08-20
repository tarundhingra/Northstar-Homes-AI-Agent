import streamlit as st
import requests
import uuid

# FastAPI backend url
API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Northstar Homes — Sales Agent Zara", page_icon="🏠")

st.title("🏠 Northstar Homes — Sales Assistant")
st.caption("Chat with Zara regarding Northstar One, Sector 79 Gurugram")

# session state setup
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []
    # greet on launch
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm Zara from Northstar Homes. How can I help you find your ideal home in Gurugram today?"
    })

if "analytics_result" not in st.session_state:
    st.session_state.analytics_result = None

# sidebar controls
st.sidebar.header("Conversation Controls")
st.sidebar.text(f"Session: {st.session_state.session_id[:8]}...")

simulate_fail = st.sidebar.checkbox("Simulate Booking Failure", value=False, help="Forces the site visit booking action to fail so you can test error recovery.")

if st.sidebar.button("End Conversation & View Analytics"):
    with st.spinner("Analyzing conversation transcript..."):
        try:
            res = requests.post(
                f"{API_BASE_URL}/end-session",
                json={"session_id": st.session_state.session_id},
                timeout=15
            )
            if res.status_code == 200:
                st.session_state.analytics_result = res.json().get("analytics", {})
            else:
                st.sidebar.error("Failed to generate analytics from backend.")
        except Exception as err:
            st.sidebar.error(f"Cannot reach backend: {err}")

if st.sidebar.button("Reset Conversation"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm Zara from Northstar Homes. How can I help you find your ideal home in Gurugram today?"
    }]
    st.session_state.analytics_result = None
    st.rerun()

# display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# chat input
user_input = st.chat_input("Type your message in English, Hindi, or Hinglish...")

if user_input:
    # render user bubble immediately
    st.session_state.analytics_result = None
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # send to fastapi
    payload = {
        "session_id": st.session_state.session_id,
        "message": user_input,
        "force_booking_fail": simulate_fail
    }

    try:
        resp = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=20)
        if resp.status_code == 200:
            bot_reply = resp.json().get("reply", "No reply received.")
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            with st.chat_message("assistant"):
                st.write(bot_reply)
        else:
            error_msg = f"Backend error: {resp.status_code}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.write(error_msg)
    except Exception as e:
        err_str = f"Could not connect to FastAPI server at {API_BASE_URL}. Ensure uvicorn is running."
        st.session_state.messages.append({"role": "assistant", "content": err_str})
        with st.chat_message("assistant"):
            st.write(err_str)

# display analytics section if computed
if st.session_state.analytics_result:
    st.divider()
    st.subheader("📊 Lead Analytics & Call Summary")
    
    analytics = st.session_state.analytics_result
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Lead Interest:** {str(analytics.get('interest_level')).upper()}")
        st.write(f"**Configuration Interest:** {analytics.get('configuration_interest')}")
        st.write(f"**Budget Mentioned:** {analytics.get('budget_mentioned') or 'Not stated'}")
        st.write(f"**Language Detected:** {analytics.get('preferred_language')}")

    with col2:
        st.write(f"**Site Visit Status:** {analytics.get('site_visit_status')}")
        st.write(f"**Follow-up Required:** {'Yes' if analytics.get('follow_up_required') else 'No'}")
        st.write(f"**Opted Out:** {'Yes' if analytics.get('opted_out') else 'No'}")
        st.write(f"**Objections Raised:** {', '.join(analytics.get('objections_raised', [])) if analytics.get('objections_raised') else 'None'}")

    st.info(f"**Summary:** {analytics.get('summary', 'No summary generated.')}")
    
    with st.expander("View Raw JSON Output"):
        st.json(analytics)