import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import calendar

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CLC Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── SUPABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ─── EVENT TYPE CONFIG ───────────────────────────────────────────────────────────
EVENT_TYPES = {
    "Staff Meeting":         {"color": "#1a2e4a", "bg": "#e8edf3", "emoji": "👥"},
    "PAC Meeting":           {"color": "#6d28d9", "bg": "#ede9fe", "emoji": "🏛️"},
    "PD / Professional Dev": {"color": "#065f46", "bg": "#d1fae5", "emoji": "📚"},
    "Team Meeting":          {"color": "#1d4ed8", "bg": "#dbeafe", "emoji": "🤝"},
    "Excursion / Event":     {"color": "#92400e", "bg": "#fef3c7", "emoji": "🎒"},
    "Planned Staff Absence": {"color": "#b91c1c", "bg": "#fee2e2", "emoji": "🏠"},
    "Other":                 {"color": "#374151", "bg": "#f3f4f6", "emoji": "📌"},
}

# ─── STYLES ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #f8f6f0; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }

.cal-header {
    background: linear-gradient(135deg, #1a2e4a 0%, #2d4a6e 60%, #3a5f8a 100%);
    color: white; padding: 1.75rem 2.5rem; border-radius: 12px;
    margin-bottom: 1rem; display: flex; align-items: center;
    gap: 1.5rem; box-shadow: 0 4px 20px rgba(26,46,74,0.25);
}
.cal-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
.cal-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.95rem; }

/* Month grid */
.month-grid { width: 100%; border-collapse: collapse; }
.month-grid th {
    background: #1a2e4a; color: white; padding: 0.6rem;
    text-align: center; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.5px;
}
.month-grid td {
    border: 1px solid #e8e4d9; vertical-align: top;
    padding: 0.4rem; min-height: 90px; background: white; width: 14.28%;
}
.month-grid td.today { background: #fffbeb; border: 2px solid #d4af37; }
.month-grid td.other-month { background: #f8f6f0; }
.day-num { font-size: 0.8rem; font-weight: 600; color: #1a2e4a; margin-bottom: 0.2rem; }
.day-num.today-num { background: #1a2e4a; color: white; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; }
.cal-event {
    font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 4px;
    margin-bottom: 0.15rem; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; display: block;
}

/* Week view */
.week-col { background: white; border-radius: 8px; padding: 0.75rem; min-height: 180px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
.week-day-header { font-weight: 700; font-size: 0.82rem; color: #1a2e4a; border-bottom: 2px solid #e8e4d9; padding-bottom: 0.4rem; margin-bottom: 0.5rem; }
.week-day-header.today-header { color: #d4af37; }

/* Event cards */
.event-card {
    border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.6rem;
    border-left: 4px solid; box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.event-card h4 { margin: 0 0 0.2rem; font-size: 0.92rem; }
.event-card .meta { font-size: 0.78rem; color: #666; }

.info-box {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 0.75rem 1rem; font-size: 0.88rem; color: #1e40af; margin-bottom: 1rem;
}
.legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }

hr { border: none; border-top: 1px solid #e8e4d9; margin: 1rem 0; }
.stButton>button { border-radius: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ─── DB HELPERS ─────────────────────────────────────────────────────────────────
def db_events(start_date=None, end_date=None):
    q = supabase.table("clc_events").select("*").order("event_date").order("start_time")
    if start_date:
        q = q.gte("event_date", str(start_date))
    if end_date:
        q = q.lte("event_date", str(end_date))
    return q.execute().data

def db_pac_meetings():
    try:
        return supabase.table("pac_meetings").select("*").order("meeting_date").execute().data
    except:
        return []

def fmt_date(d):
    if not d: return "—"
    try: return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%-d %B %Y")
    except: return str(d)[:10]

def fmt_time(t):
    if not t: return ""
    try: return datetime.strptime(str(t)[:5], "%H:%M").strftime("%-I:%M %p")
    except: return str(t)[:5]

# ─── ADMIN CHECK ────────────────────────────────────────────────────────────────
def check_admin():
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    return st.session_state.is_admin

# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cal-header">
  <div style="font-size:3rem">📅</div>
  <div>
    <h1>CLC Communal Calendar</h1>
    <p>Cowandilla Learning Centre — Staff Events, Meetings &amp; Absences</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── ADMIN LOGIN ────────────────────────────────────────────────────────────────
if not check_admin():
    with st.expander("🔐 Admin Login (required to delete events)", expanded=False):
        col_pw, col_btn = st.columns([3,1])
        with col_pw:
            pw = st.text_input("Password", type="password", key="admin_pw",
                               label_visibility="collapsed", placeholder="Admin password")
        with col_btn:
            if st.button("Sign In", use_container_width=True, type="primary"):
                if pw == st.secrets.get("CAL_ADMIN_PASSWORD", "CLC2026"):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
else:
    col_a, col_b = st.columns([5,1])
    with col_a:
        st.success("🔓 Admin mode active — you can delete events.")
    with col_b:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

# ─── LEGEND ─────────────────────────────────────────────────────────────────────
legend_html = "<div style='display:flex;flex-wrap:wrap;gap:0.75rem;margin-bottom:1rem;'>"
for etype, cfg in EVENT_TYPES.items():
    legend_html += f"<span style='font-size:0.78rem;'><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{cfg['color']};margin-right:4px;vertical-align:middle;'></span>{cfg['emoji']} {etype}</span>"
legend_html += "</div>"
st.markdown(legend_html, unsafe_allow_html=True)

# ─── ADD EVENT FORM ──────────────────────────────────────────────────────────────
with st.expander("➕ Add Event", expanded=False):
    with st.form("add_event", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            ev_title = st.text_input("Event title *")
            ev_type = st.selectbox("Event type", list(EVENT_TYPES.keys()))
        with col2:
            ev_date = st.date_input("Date *", value=date.today())
            ev_end_date = st.date_input("End date (multi-day events)", value=date.today())
        with col3:
            ev_start = st.time_input("Start time (optional)", value=None)
            ev_end = st.time_input("End time (optional)", value=None)
        col4, col5 = st.columns(2)
        with col4:
            ev_location = st.text_input("Location")
        with col5:
            ev_who = st.text_input("Added by *")
        ev_notes = st.text_area("Notes (optional)", height=68)

        if st.form_submit_button("📅 Add to Calendar", type="primary", use_container_width=True):
            if ev_title.strip() and ev_who.strip():
                supabase.table("clc_events").insert({
                    "title": ev_title.strip(),
                    "event_type": ev_type,
                    "event_date": str(ev_date),
                    "end_date": str(ev_end_date) if ev_end_date != ev_date else None,
                    "start_time": str(ev_start) if ev_start else None,
                    "end_time": str(ev_end) if ev_end else None,
                    "location": ev_location.strip(),
                    "added_by": ev_who.strip(),
                    "notes": ev_notes.strip(),
                }).execute()
                st.success(f"✅ '{ev_title}' added to calendar!")
                st.rerun()
            else:
                st.warning("Please enter an event title and your name.")

st.markdown("")

# ─── NAVIGATION ─────────────────────────────────────────────────────────────────
# Month navigation state
if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = date.today().month
if "cal_week_start" not in st.session_state:
    today = date.today()
    st.session_state.cal_week_start = today - timedelta(days=today.weekday())  # Monday

tab_month, tab_week, tab_list = st.tabs(["🗓️ Month View", "📋 Week View", "📃 List / Agenda"])

# ════════════════════════════════════════════════════════════════════════════════
# MONTH VIEW
# ════════════════════════════════════════════════════════════════════════════════
with tab_month:
    # Nav
    col_prev, col_title, col_next, col_today = st.columns([1,3,1,1])
    with col_prev:
        if st.button("◀ Prev", use_container_width=True, key="m_prev"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with col_title:
        mn = datetime(st.session_state.cal_year, st.session_state.cal_month, 1)
        st.markdown(f"<h3 style='text-align:center;margin:0;color:#1a2e4a;'>{mn.strftime('%B %Y')}</h3>", unsafe_allow_html=True)
    with col_next:
        if st.button("Next ▶", use_container_width=True, key="m_next"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()
    with col_today:
        if st.button("Today", use_container_width=True, key="m_today"):
            st.session_state.cal_year = date.today().year
            st.session_state.cal_month = date.today().month
            st.rerun()

    # Fetch events for this month
    year = st.session_state.cal_year
    month = st.session_state.cal_month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    events = db_events(first_day - timedelta(days=7), last_day + timedelta(days=7))

    # Also get PAC meetings
    pac = db_pac_meetings()
    for p in pac:
        if p.get("meeting_date"):
            events.append({
                "title": f"{p.get('meeting_type','Ordinary')} PAC Meeting",
                "event_type": "PAC Meeting",
                "event_date": p["meeting_date"],
                "start_time": p.get("start_time"),
                "location": p.get("location",""),
                "added_by": "PAC System",
                "notes": f"Chair: {p.get('chair','—')}",
                "id": f"pac_{p['id']}"
            })

    # Build events by date dict
    events_by_date = {}
    for ev in events:
        d = str(ev.get("event_date",""))[:10]
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(ev)

    # Build calendar grid HTML
    cal = calendar.monthcalendar(year, month)
    today_str = str(date.today())

    html = "<table class='month-grid'><tr>"
    for day_name in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
        html += f"<th>{day_name}</th>"
    html += "</tr>"

    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td class='other-month'></td>"
            else:
                d = date(year, month, day)
                d_str = str(d)
                is_today = d_str == today_str
                cell_class = "today" if is_today else ""
                num_class = "today-num" if is_today else ""
                html += f"<td class='{cell_class}'>"
                html += f"<div class='day-num'><span class='{num_class}'>{day}</span></div>"
                for ev in events_by_date.get(d_str, [])[:4]:
                    cfg = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
                    bg = cfg["bg"]; fg = cfg["color"]; em = cfg["emoji"]; ti = ev.get("title","")
                    html += f"<span class='cal-event' style='background:{bg};color:{fg};' title='{ti}'>{em} {ti}</span>"
                extra = len(events_by_date.get(d_str, [])) - 4
                if extra > 0:
                    html += f"<span style='font-size:0.68rem;color:#888;'>+{extra} more</span>"
                html += "</td>"
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# WEEK VIEW
# ════════════════════════════════════════════════════════════════════════════════
with tab_week:
    week_start = st.session_state.cal_week_start
    week_end = week_start + timedelta(days=6)

    col_prev2, col_wtitle, col_next2, col_today2 = st.columns([1,3,1,1])
    with col_prev2:
        if st.button("◀ Prev", use_container_width=True, key="w_prev"):
            st.session_state.cal_week_start -= timedelta(weeks=1)
            st.rerun()
    with col_wtitle:
        st.markdown(f"<h3 style='text-align:center;margin:0;color:#1a2e4a;'>{fmt_date(week_start)} – {fmt_date(week_end)}</h3>", unsafe_allow_html=True)
    with col_next2:
        if st.button("Next ▶", use_container_width=True, key="w_next"):
            st.session_state.cal_week_start += timedelta(weeks=1)
            st.rerun()
    with col_today2:
        if st.button("Today", use_container_width=True, key="w_today"):
            today = date.today()
            st.session_state.cal_week_start = today - timedelta(days=today.weekday())
            st.rerun()

    events = db_events(week_start, week_end)
    pac = db_pac_meetings()
    for p in pac:
        if p.get("meeting_date"):
            d = str(p["meeting_date"])[:10]
            if str(week_start) <= d <= str(week_end):
                events.append({
                    "title": f"{p.get('meeting_type','Ordinary')} PAC Meeting",
                    "event_type": "PAC Meeting",
                    "event_date": p["meeting_date"],
                    "start_time": p.get("start_time"),
                    "location": p.get("location",""),
                    "added_by": "PAC System",
                    "notes": f"Chair: {p.get('chair','—')}",
                    "id": f"pac_{p['id']}"
                })

    events_by_date = {}
    for ev in events:
        d = str(ev.get("event_date",""))[:10]
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(ev)

    cols = st.columns(7)
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    today_str = str(date.today())

    for i, col in enumerate(cols):
        d = week_start + timedelta(days=i)
        d_str = str(d)
        is_today = d_str == today_str
        header_style = "today-header" if is_today else ""
        with col:
            st.markdown(f"""
            <div class="week-col">
              <div class="week-day-header {header_style}">
                {day_names[i]}<br>
                <span style="font-size:1.1rem;">{'📍 ' if is_today else ''}{d.day}</span>
              </div>
            """, unsafe_allow_html=True)

            day_events = events_by_date.get(d_str, [])
            if day_events:
                for ev in day_events:
                    cfg = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
                    time_str = fmt_time(ev.get("start_time")) if ev.get("start_time") else ""
                    st.markdown(f"""
                    <div style="background:{cfg['bg']};border-left:3px solid {cfg['color']};border-radius:6px;padding:0.4rem 0.5rem;margin-bottom:0.4rem;font-size:0.75rem;">
                      <div style="font-weight:600;color:{cfg['color']};">{cfg['emoji']} {ev.get('title','')}</div>
                      {f"<div style='color:#666;'>{time_str}</div>" if time_str else ""}
                      {f"<div style='color:#888;'>📍 {ev.get('location','')}</div>" if ev.get('location') else ""}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#ccc;font-size:0.75rem;text-align:center;padding-top:1rem;'>—</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# LIST / AGENDA VIEW
# ════════════════════════════════════════════════════════════════════════════════
with tab_list:
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        list_start = st.date_input("From", value=date.today(), key="list_start")
    with col_filter2:
        list_end = st.date_input("To", value=date.today() + timedelta(weeks=8), key="list_end")
    with col_filter3:
        type_filter = st.multiselect("Filter by type", list(EVENT_TYPES.keys()), default=list(EVENT_TYPES.keys()), key="type_filter")

    events = db_events(list_start, list_end)

    # Add PAC meetings
    pac = db_pac_meetings()
    for p in pac:
        if p.get("meeting_date"):
            d = str(p["meeting_date"])[:10]
            if str(list_start) <= d <= str(list_end):
                events.append({
                    "title": f"{p.get('meeting_type','Ordinary')} PAC Meeting",
                    "event_type": "PAC Meeting",
                    "event_date": p["meeting_date"],
                    "start_time": p.get("start_time"),
                    "location": p.get("location",""),
                    "added_by": "PAC System",
                    "notes": f"Chair: {p.get('chair','—')}",
                    "id": f"pac_{p['id']}"
                })

    events = [e for e in events if e.get("event_type") in type_filter]
    events.sort(key=lambda x: (str(x.get("event_date","")), str(x.get("start_time",""))))

    if not events:
        st.markdown('<div class="info-box">No events in this date range.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(events)} event{'s' if len(events) != 1 else ''} found**")
        st.markdown("---")

        current_date = None
        for ev in events:
            ev_date = str(ev.get("event_date",""))[:10]
            if ev_date != current_date:
                current_date = ev_date
                try:
                    d_obj = datetime.strptime(ev_date, "%Y-%m-%d").date()
                    is_today = d_obj == date.today()
                    day_label = f"📍 **TODAY** — {d_obj.strftime('%A %-d %B %Y')}" if is_today else f"**{d_obj.strftime('%A %-d %B %Y')}**"
                    st.markdown(day_label)
                except:
                    st.markdown(f"**{ev_date}**")

            cfg = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
            time_str = ""
            if ev.get("start_time"):
                time_str = fmt_time(ev["start_time"])
                if ev.get("end_time"):
                    time_str += f" – {fmt_time(ev['end_time'])}"

            col_ev, col_del = st.columns([6,1])
            with col_ev:
                st.markdown(f"""
                <div class="event-card" style="background:{cfg['bg']};border-left-color:{cfg['color']};">
                  <h4 style="color:{cfg['color']};">{cfg['emoji']} {ev.get('title','')}</h4>
                  <div class="meta">
                    <span style="background:{cfg['color']};color:white;font-size:0.68rem;padding:0.1rem 0.4rem;border-radius:10px;">{ev.get('event_type','')}</span>
                    {f" &nbsp;⏰ {time_str}" if time_str else ""}
                    {f" &nbsp;📍 {ev.get('location','')}" if ev.get('location') else ""}
                    {f" &nbsp;👤 {ev.get('added_by','')}" if ev.get('added_by') else ""}
                  </div>
                  {f"<div style='font-size:0.8rem;color:#555;margin-top:0.3rem;'>{ev.get('notes','')}</div>" if ev.get('notes') else ""}
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                ev_id = ev.get("id","")
                if check_admin() and not str(ev_id).startswith("pac_"):
                    st.write("")
                    if st.button("🗑️", key=f"del_ev_{ev_id}", help="Delete event"):
                        supabase.table("clc_events").delete().eq("id", ev_id).execute()
                        st.rerun()

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;color:#999;font-size:0.8rem;">
  Cowandilla Learning Centre · Communal Staff Calendar
</div>
""", unsafe_allow_html=True)
