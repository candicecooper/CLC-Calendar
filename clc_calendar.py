import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import calendar

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CLC Calendar", page_icon="📅", layout="wide", initial_sidebar_state="collapsed")

# ─── SUPABASE ───────────────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_supabase()

# ─── EVENT TYPES ────────────────────────────────────────────────────────────────
EVENT_TYPES = {
    "Staff Meeting":         {"color": "#1a2e4a", "bg": "#e8edf3", "emoji": "👥"},
    "PAC Meeting":           {"color": "#6d28d9", "bg": "#ede9fe", "emoji": "🏛️"},
    "PD / Professional Dev": {"color": "#065f46", "bg": "#d1fae5", "emoji": "📚"},
    "Team Meeting":          {"color": "#1d4ed8", "bg": "#dbeafe", "emoji": "🤝"},
    "Excursion / Event":     {"color": "#92400e", "bg": "#fef3c7", "emoji": "🎒"},
    "Planned Staff Absence": {"color": "#b91c1c", "bg": "#fee2e2", "emoji": "🏠"},
    "Staff Birthday":        {"color": "#be185d", "bg": "#fce7f3", "emoji": "🎂"},
    "Entry Meeting":         {"color": "#0e7490", "bg": "#cffafe", "emoji": "🚪"},
    "Review Meeting":        {"color": "#c2410c", "bg": "#ffedd5", "emoji": "🔍"},
    "Transition Meeting":    {"color": "#7c3aed", "bg": "#ede9fe", "emoji": "🔄"},
    "TAC Meeting":           {"color": "#b45309", "bg": "#fef3c7", "emoji": "📎"},
    "Student Placement":     {"color": "#374151", "bg": "#f3f4f6", "emoji": "📋"},
    "Other":                 {"color": "#374151", "bg": "#f3f4f6", "emoji": "📌"},
}

# Student meeting types — appear in BOTH normal calendar AND student placement view
STUDENT_MEETING_TYPES = ["Entry Meeting", "Review Meeting", "Transition Meeting", "TAC Meeting"]
# All student-related types
STUDENT_EVENT_TYPES   = STUDENT_MEETING_TYPES + ["Student Placement"]

# Program colour coding
PROGRAM_COLORS = {
    "JP": {"color": "#1d4ed8", "bg": "#dbeafe", "label": "Junior Primary"},
    "PY": {"color": "#15803d", "bg": "#dcfce7", "label": "Primary Years"},
    "SY": {"color": "#a16207", "bg": "#fef9c3", "label": "Senior Years"},
}

# ─── STYLES ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #f0f2f6; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1300px; }
.cal-header {
    background: linear-gradient(135deg, #1a2e4a 0%, #2d4a6e 60%, #3a5f8a 100%);
    color: white; padding: 1.25rem 2rem; border-radius: 12px;
    margin-bottom: 1rem; display: flex; align-items: center;
    gap: 1.5rem; box-shadow: 0 4px 20px rgba(26,46,74,0.25);
}
.cal-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.cal-header p  { margin: 0.2rem 0 0; opacity: 0.75; font-size: 0.88rem; }
.month-grid { width: 100%; border-collapse: collapse; table-layout: fixed; }
.month-grid th { background: #1a2e4a; color: white; padding: 0.5rem; text-align: center; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.5px; }
.month-grid td { border: 1px solid #dde; vertical-align: top; padding: 0.35rem; background: white; width: 14.28%; min-height: 80px; }
.month-grid td.today-cell   { background: #fffbeb; border: 2px solid #d4af37; }
.month-grid td.selected-cell { background: #dbeafe !important; border: 2px solid #1a2e4a !important; }
.month-grid td.other-month  { background: #f8f8fb; }
.day-num { font-size: 0.78rem; font-weight: 600; color: #1a2e4a; margin-bottom: 0.15rem; }
.today-badge { background: #1a2e4a; color: white; border-radius: 50%; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.72rem; }
.cal-chip { font-size: 0.66rem; padding: 0.1rem 0.35rem; border-radius: 3px; margin-bottom: 0.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.week-col { background: white; border-radius: 10px; padding: 0.6rem 0.5rem; min-height: 180px; box-shadow: 0 1px 6px rgba(0,0,0,0.07); border-top: 3px solid #e0e0e0; }
.week-day-label { font-size: 0.72rem; color: #888; text-transform: uppercase; font-weight: 600; }
.week-day-num   { font-size: 1.2rem; font-weight: 700; color: #1a2e4a; line-height: 1.2; }
.today-strip { background: linear-gradient(90deg,#fffbeb,#fef9e7); border: 1px solid #d4af37; border-radius: 10px; padding: 0.65rem 1.2rem; margin-bottom: 0.75rem; display:flex; align-items:center; gap:1rem; flex-wrap:wrap; }
.ts-date { font-weight: 700; font-size: 0.95rem; color: #92400e; }
.ev-card { border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; border-left: 4px solid; font-size: 0.85rem; }
.ev-card h4 { margin: 0 0 0.15rem; font-size: 0.88rem; }
.ev-card .meta { font-size: 0.74rem; color: #666; }
.info-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.84rem; color: #1e40af; margin-bottom: 0.75rem; }
.add-prompt { background: #f0fdf4; border: 2px dashed #86efac; border-radius: 10px; padding: 0.8rem 1rem; font-size: 0.85rem; color: #15803d; margin-bottom: 0.75rem; text-align: center; font-weight: 500; }
hr { border: none; border-top: 1px solid #eaecf0; margin: 0.75rem 0; }
.stButton>button { border-radius: 7px; font-weight: 500; }
.prog-badge { font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 12px; display: inline-block; margin-right: 0.3rem; }
.student-card { border-radius: 10px; padding: 0.7rem 1rem; margin-bottom: 0.5rem; border-left: 5px solid; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ───────────────────────────────────────────────────────────────
today = date.today()
for k, v in [("cal_year", today.year), ("cal_month", today.month),
              ("cal_week_start", today - timedelta(days=today.weekday())),
              ("selected_date", today), ("is_admin", False), ("edit_event_id", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── DB HELPERS ─────────────────────────────────────────────────────────────────
def db_events(start_date=None, end_date=None):
    q = supabase.table("clc_events").select("*").order("event_date").order("start_time")
    if start_date: q = q.gte("event_date", str(start_date))
    if end_date:   q = q.lte("event_date", str(end_date))
    return q.execute().data

def db_events_all():
    return supabase.table("clc_events").select("*").order("event_date").execute().data

def db_pac():
    try: return supabase.table("pac_meetings").select("*").order("meeting_date").execute().data
    except: return []

def pac_events(pac_list, d_from=None, d_to=None):
    out = []
    for p in pac_list:
        if not p.get("meeting_date"): continue
        d = str(p["meeting_date"])[:10]
        if d_from and d < str(d_from): continue
        if d_to   and d > str(d_to):   continue
        out.append({"title": f"{p.get('meeting_type','Ordinary')} PAC Meeting",
                    "event_type": "PAC Meeting", "event_date": p["meeting_date"],
                    "start_time": p.get("start_time"), "location": p.get("location",""),
                    "added_by": "PAC System", "notes": f"Chair: {p.get('chair','—')}",
                    "id": f"pac_{p['id']}"})
    return out

def ev_index(events):
    idx = {}
    for ev in events:
        idx.setdefault(str(ev.get("event_date",""))[:10], []).append(ev)
    return idx

def fmt_date(d):
    try: return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%-d %B %Y")
    except: return str(d)[:10]

def fmt_time(t):
    if not t: return ""
    try: return datetime.strptime(str(t)[:5], "%H:%M").strftime("%-I:%M %p")
    except: return str(t)[:5]

def select_day(d):
    st.session_state.selected_date = d
    st.session_state.edit_event_id = None

def save_event(d):
    supabase.table("clc_events").insert({
        "title": d["title"].strip(), "event_type": d["etype"],
        "event_date": str(d["ev_date"]),
        "end_date": str(d["end_date"]) if d["end_date"] and d["end_date"] != d["ev_date"] else None,
        "start_time": str(d["start_t"]) if d["start_t"] else None,
        "end_time": str(d["end_t"]) if d["end_t"] else None,
        "location": d["location"].strip(), "added_by": d["who"].strip(), "notes": d["notes"].strip(),
        "program": d.get("program",""), "student_initials": d.get("student_initials",""),
    }).execute()

def upd_event(ev_id, d):
    supabase.table("clc_events").update({
        "title": d["title"].strip(), "event_type": d["etype"],
        "event_date": str(d["ev_date"]),
        "end_date": str(d["end_date"]) if d["end_date"] and d["end_date"] != d["ev_date"] else None,
        "start_time": str(d["start_t"]) if d["start_t"] else None,
        "end_time": str(d["end_t"]) if d["end_t"] else None,
        "location": d["location"].strip(), "added_by": d["who"].strip(), "notes": d["notes"].strip(),
        "program": d.get("program",""), "student_initials": d.get("student_initials",""),
    }).eq("id", ev_id).execute()

def del_event(ev_id):
    supabase.table("clc_events").delete().eq("id", ev_id).execute()

# ─── EVENT FORM ──────────────────────────────────────────────────────────────────
def event_form(key, default_date=None, existing=None, label="📅 Save Event"):
    ev = existing or {}
    d0 = default_date or today
    is_student = ev.get("event_type") in STUDENT_EVENT_TYPES

    with st.form(key, clear_on_submit=(existing is None)):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Event title *", value=ev.get("title",""),
                                  placeholder="e.g. Staff meeting, J.S. Entry Meeting")
            etype = st.selectbox("Type", list(EVENT_TYPES.keys()),
                                 index=list(EVENT_TYPES.keys()).index(ev.get("event_type","Other"))
                                 if ev.get("event_type") in EVENT_TYPES else len(EVENT_TYPES)-1)
            who = st.text_input("Added by *", value=ev.get("added_by",""), placeholder="Your name")
        with c2:
            ev_date  = st.date_input("Date *",
                                     value=datetime.strptime(str(ev.get("event_date",d0))[:10],"%Y-%m-%d").date()
                                     if ev.get("event_date") else d0)
            end_date = st.date_input("End date (leave same for single day)", value=ev_date)
            location = st.text_input("Location", value=ev.get("location",""))

        # Student-specific fields — shown when student event type selected
        st.markdown("**Student details** *(fill in for Entry/Review/Transition/Placement events)*")
        sc1, sc2 = st.columns(2)
        with sc1:
            student_initials = st.text_input("Student initials (privacy)",
                                             value=ev.get("student_initials",""),
                                             placeholder="e.g. J.S.")
        with sc2:
            prog_opts = ["", "JP", "PY", "SY"]
            prog_val  = ev.get("program","") or ""
            program   = st.selectbox("Program", prog_opts,
                                     index=prog_opts.index(prog_val) if prog_val in prog_opts else 0)

        c3, c4 = st.columns(2)
        with c3: start_t = st.time_input("Start time (optional)", value=None)
        with c4: end_t   = st.time_input("End time (optional)",   value=None)
        notes = st.text_area("Notes", value=ev.get("notes",""), height=64)
        ok = st.form_submit_button(label, type="primary", use_container_width=True)
        if ok:
            if not title.strip() or not who.strip():
                st.warning("Event title and 'Added by' are required.")
                return False, {}
            return True, dict(title=title, etype=etype, ev_date=ev_date, end_date=end_date,
                              start_t=start_t, end_t=end_t, location=location, who=who,
                              notes=notes, program=program, student_initials=student_initials)
    return False, {}

# ─── RENDER EVENT CARD ──────────────────────────────────────────────────────────
def render_event_card(ev, key_prefix, allow_edit=True):
    cfg  = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
    tr   = fmt_time(ev.get("start_time",""))
    if ev.get("end_time"): tr += f" – {fmt_time(ev['end_time'])}"
    eid  = ev.get("id",""); pac = str(eid).startswith("pac_")
    prog = ev.get("program","")
    init = ev.get("student_initials","")

    # For student events, use program colour
    if prog and ev.get("event_type") in STUDENT_EVENT_TYPES:
        pc = PROGRAM_COLORS.get(prog, {})
        cfg = {"color": pc.get("color", cfg["color"]), "bg": pc.get("bg", cfg["bg"]), "emoji": cfg["emoji"]}

    prog_html = ""
    if prog:
        pc = PROGRAM_COLORS.get(prog,{})
        prog_html = f'<span style="background:{pc.get("bg","#f3f4f6")};color:{pc.get("color","#374151")};font-size:0.68rem;font-weight:700;padding:0.1rem 0.5rem;border-radius:10px;margin-right:4px;">{prog}</span>'
    init_html = f'<span style="font-weight:700;"> {init}</span>' if init else ""

    cc1, cc2, cc3 = st.columns([6,1,1])
    with cc1:
        st.markdown(
            f'<div class="ev-card" style="background:{cfg["bg"]};border-left-color:{cfg["color"]};">'
            f'<h4 style="color:{cfg["color"]};">{cfg["emoji"]} {ev.get("title","")}{init_html}</h4>'
            f'<div class="meta">'
            f'{prog_html}'
            f'<span style="background:{cfg["color"]};color:white;font-size:0.68rem;padding:0.1rem 0.4rem;border-radius:10px;">{ev.get("event_type","")}</span>'
            f'{(" ⏰ "+tr) if tr else ""}'
            f'{(" 📍 "+ev.get("location","")) if ev.get("location") else ""}'
            f'{(" 👤 "+ev.get("added_by","")) if ev.get("added_by") else ""}'
            f'</div>'
            f'{("<div style=\"font-size:0.78rem;color:#555;margin-top:0.25rem;\">"+ev.get("notes","")+"</div>") if ev.get("notes") else ""}'
            f'</div>', unsafe_allow_html=True)
    with cc2:
        # All staff can edit student meeting dates; admin can edit everything
        can_edit = (st.session_state.is_admin or ev.get("event_type") in STUDENT_EVENT_TYPES) and not pac
        if can_edit and allow_edit:
            st.write("")
            if st.button("✏️", key=f"{key_prefix}_e_{eid}", help="Edit"):
                st.session_state.edit_event_id = eid if st.session_state.edit_event_id!=eid else None
                st.rerun()
    with cc3:
        if st.session_state.is_admin and not pac and allow_edit:
            st.write("")
            if st.button("🗑️", key=f"{key_prefix}_d_{eid}", help="Delete"):
                del_event(eid); st.session_state.edit_event_id=None; st.rerun()

    if st.session_state.edit_event_id == eid and not pac and allow_edit:
        st.markdown("**✏️ Edit event:**")
        ok, data = event_form(f"{key_prefix}_ef_{eid}", existing=ev, label="💾 Save Changes")
        if ok:
            upd_event(eid, data); st.session_state.edit_event_id=None
            st.success("Updated!"); st.rerun()

# ─── HEADER ─────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([4, 1])
with hc1:
    st.markdown("""
    <div class="cal-header">
      <div style="font-size:2.5rem">📅</div>
      <div>
        <h1>CLC Communal Calendar</h1>
        <p>Cowandilla Learning Centre — click any day to view or add events</p>
      </div>
    </div>""", unsafe_allow_html=True)
with hc2:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if not st.session_state.is_admin:
        with st.expander("🔐 Admin"):
            pw = st.text_input("", type="password", key="admin_pw", placeholder="Admin password")
            if st.button("Sign In", type="primary", use_container_width=True):
                if pw == st.secrets.get("CAL_ADMIN_PASSWORD","CLC2026"):
                    st.session_state.is_admin = True; st.rerun()
                else: st.error("Incorrect password")
    else:
        st.success("🔓 Admin active")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.is_admin = False; st.rerun()

# ─── TODAY STRIP ────────────────────────────────────────────────────────────────
t_evs = db_events(today, today) + pac_events(db_pac(), today, today)
t_evs.sort(key=lambda x: str(x.get("start_time","")))
chips = []
for ev in t_evs:
    cfg = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
    prog = ev.get("program","")
    if prog and ev.get("event_type") in STUDENT_EVENT_TYPES:
        pc = PROGRAM_COLORS.get(prog,{})
        cfg = {"color": pc.get("color",cfg["color"]), "bg": pc.get("bg",cfg["bg"]), "emoji": cfg["emoji"]}
    t   = fmt_time(ev.get("start_time",""))
    init = ev.get("student_initials","")
    label = ev.get("title","") + (f" ({init})" if init else "")
    chips.append(f'<span style="background:{cfg["bg"]};color:{cfg["color"]};border-radius:6px;padding:0.2rem 0.6rem;font-size:0.78rem;font-weight:500;">{cfg["emoji"]} {label}{("  "+t) if t else ""}</span>')
ev_strip = " &nbsp;".join(chips) if chips else '<span style="color:#999;font-size:0.82rem;">No events scheduled today</span>'
st.markdown(f'<div class="today-strip"><div class="ts-date">📍 Today — {today.strftime("%A %-d %B %Y")}</div><div style="display:flex;flex-wrap:wrap;gap:0.4rem;">{ev_strip}</div></div>', unsafe_allow_html=True)

# ─── TABS ───────────────────────────────────────────────────────────────────────
tab_month, tab_week, tab_list, tab_students = st.tabs(["🗓️ Month", "📋 Week", "📃 Agenda", "👨‍🎓 Students"])

# ═══════════════ MONTH VIEW ════════════════════════════════════════════════════
with tab_month:
    cp, ct, cn, ctod = st.columns([1,3,1,1])
    with cp:
        if st.button("◀ Prev", use_container_width=True, key="m_prev"):
            if st.session_state.cal_month == 1: st.session_state.cal_month=12; st.session_state.cal_year-=1
            else: st.session_state.cal_month-=1
            st.rerun()
    with ct:
        mn = datetime(st.session_state.cal_year, st.session_state.cal_month, 1)
        st.markdown(f"<h3 style='text-align:center;margin:0;color:#1a2e4a;'>{mn.strftime('%B %Y')}</h3>", unsafe_allow_html=True)
    with cn:
        if st.button("Next ▶", use_container_width=True, key="m_next"):
            if st.session_state.cal_month == 12: st.session_state.cal_month=1; st.session_state.cal_year+=1
            else: st.session_state.cal_month+=1
            st.rerun()
    with ctod:
        if st.button("Today", use_container_width=True, key="m_today"):
            st.session_state.cal_year=today.year; st.session_state.cal_month=today.month
            select_day(today); st.rerun()

    yr, mo = st.session_state.cal_year, st.session_state.cal_month
    fd = date(yr, mo, 1)
    ld = date(yr, mo, calendar.monthrange(yr, mo)[1])
    evs  = db_events(fd-timedelta(days=7), ld+timedelta(days=7))
    evs += pac_events(db_pac(), fd-timedelta(days=7), ld+timedelta(days=7))
    idx  = ev_index(evs)
    ts   = str(today)
    ss   = str(st.session_state.selected_date)

    html = "<table class='month-grid'><tr>"
    for dn in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]: html += f"<th>{dn}</th>"
    html += "</tr>"
    for week in calendar.monthcalendar(yr, mo):
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td class='other-month'>&nbsp;</td>"; continue
            d = date(yr, mo, day); ds = str(d)
            cls = "today-cell" if ds==ts else ""
            if ds == ss: cls = "selected-cell"
            nbadge = f"<span class='today-badge'>{day}</span>" if ds==ts else str(day)
            html += f"<td class='{cls}'><div class='day-num'>{nbadge}</div>"
            for ev in idx.get(ds,[])[:3]:
                etype = ev.get("event_type","Other")
                prog  = ev.get("program","")
                if prog and etype in STUDENT_EVENT_TYPES:
                    pc  = PROGRAM_COLORS.get(prog,{})
                    cbg = pc.get("bg","#f3f4f6"); ccol = pc.get("color","#374151")
                    emoji = EVENT_TYPES.get(etype,EVENT_TYPES["Other"])["emoji"]
                else:
                    cfg   = EVENT_TYPES.get(etype, EVENT_TYPES["Other"])
                    cbg   = cfg["bg"]; ccol = cfg["color"]; emoji = cfg["emoji"]
                init  = ev.get("student_initials","")
                title = (init if init else ev.get("title",""))
                html += f"<span class='cal-chip' style='background:{cbg};color:{ccol};'>{emoji} {title}</span>"
            ex = len(idx.get(ds,[]))-3
            if ex>0: html += f"<span style='font-size:0.65rem;color:#888;'>+{ex} more</span>"
            html += "</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    # Day picker — this week
    st.markdown("<div style='margin-top:0.6rem;font-size:0.8rem;color:#666;font-weight:600;'>👇 Select a day to view or add events:</div>", unsafe_allow_html=True)
    wk_mon = today - timedelta(days=today.weekday())
    pick_cols = st.columns(7)
    for i, dn in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        d = wk_mon + timedelta(days=i)
        is_sel = str(d) == ss
        with pick_cols[i]:
            lbl = f"**{dn} {d.day}**" if is_sel else f"{dn} {d.day}"
            if st.button(lbl, key=f"mp_{i}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                select_day(d); st.rerun()

    # Jump to any date
    jumped = st.date_input("Or jump to any date:", value=st.session_state.selected_date, key="m_jump")
    if jumped != st.session_state.selected_date:
        select_day(jumped); st.session_state.cal_year=jumped.year; st.session_state.cal_month=jumped.month; st.rerun()

    # ── Day panel ──
    sel = st.session_state.selected_date
    d_evs = db_events(sel, sel) + pac_events(db_pac(), sel, sel)
    d_evs.sort(key=lambda x: str(x.get("start_time","")))
    st.markdown(f"---\n### {'📍 ' if sel==today else ''}{sel.strftime('%A %-d %B %Y')}")

    if not d_evs:
        st.markdown('<div class="add-prompt">📭 No events on this day — use the form below to add one</div>', unsafe_allow_html=True)
    for ev in d_evs:
        render_event_card(ev, "m")

    with st.expander(f"➕ Add event on {sel.strftime('%-d %B')}", expanded=(not d_evs)):
        ok, data = event_form(f"madd_{str(sel)}", default_date=sel)
        if ok: save_event(data); st.success(f"✅ '{data['title']}' added!"); st.rerun()

# ═══════════════ WEEK VIEW ═════════════════════════════════════════════════════
with tab_week:
    ws = st.session_state.cal_week_start
    we = ws + timedelta(days=6)
    wp, wt, wn, wtod = st.columns([1,3,1,1])
    with wp:
        if st.button("◀ Prev", use_container_width=True, key="w_prev"):
            st.session_state.cal_week_start -= timedelta(weeks=1); st.rerun()
    with wt:
        st.markdown(f"<h3 style='text-align:center;margin:0;color:#1a2e4a;'>{fmt_date(ws)} – {fmt_date(we)}</h3>", unsafe_allow_html=True)
    with wn:
        if st.button("Next ▶", use_container_width=True, key="w_next"):
            st.session_state.cal_week_start += timedelta(weeks=1); st.rerun()
    with wtod:
        if st.button("Today", use_container_width=True, key="w_today"):
            st.session_state.cal_week_start = today-timedelta(days=today.weekday()); select_day(today); st.rerun()

    wevs  = db_events(ws, we) + pac_events(db_pac(), ws, we)
    widx  = ev_index(wevs)
    ts    = str(today)
    ss    = str(st.session_state.selected_date)
    dnames= ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    wcols = st.columns(7)
    for i, wc in enumerate(wcols):
        d    = ws + timedelta(days=i); ds = str(d)
        itod = ds==ts; isel = ds==ss
        top  = "#d4af37" if itod else ("#1a2e4a" if isel else "#e0e0e0")
        bg   = "#fffef5" if itod else "white"
        with wc:
            st.markdown(f'<div class="week-col" style="border-top:3px solid {top};background:{bg};"><div class="week-day-label">{dnames[i]}</div><div class="week-day-num" style="color:{"#d4af37" if itod else "#1a2e4a"};">{d.day}</div>', unsafe_allow_html=True)
            for ev in widx.get(ds,[]):
                etype = ev.get("event_type","Other")
                prog  = ev.get("program","")
                if prog and etype in STUDENT_EVENT_TYPES:
                    pc  = PROGRAM_COLORS.get(prog,{})
                    cbg = pc.get("bg","#f3f4f6"); ccol = pc.get("color","#374151")
                    emoji = EVENT_TYPES.get(etype,EVENT_TYPES["Other"])["emoji"]
                else:
                    cfg   = EVENT_TYPES.get(etype, EVENT_TYPES["Other"])
                    cbg   = cfg["bg"]; ccol = cfg["color"]; emoji = cfg["emoji"]
                t     = fmt_time(ev.get("start_time",""))
                init  = ev.get("student_initials","")
                title = (init if init else ev.get("title",""))
                st.markdown(f'<div style="background:{cbg};border-left:3px solid {ccol};border-radius:5px;padding:0.25rem 0.4rem;margin-bottom:0.3rem;font-size:0.72rem;"><span style="font-weight:600;color:{ccol};">{emoji} {title}</span>{("<br><span style=\"color:#666;\">"+t+"</span>") if t else ""}{("<br><span style=\"color:#888;\">📍 "+ev.get("location","")+"</span>") if ev.get("location") else ""}</div>', unsafe_allow_html=True)
            if not widx.get(ds,[]):
                st.markdown("<div style='color:#ccc;font-size:0.75rem;text-align:center;padding:0.5rem 0;'>—</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            btnlbl = "✅ Selected" if isel else "📝 Add/View"
            if st.button(btnlbl, key=f"wsel_{i}", use_container_width=True, type="primary" if isel else "secondary"):
                select_day(d); st.rerun()

    st.markdown("---")
    sel = st.session_state.selected_date
    d_evs = db_events(sel, sel) + pac_events(db_pac(), sel, sel)
    d_evs.sort(key=lambda x: str(x.get("start_time","")))
    st.markdown(f"### {'📍 ' if sel==today else ''}{sel.strftime('%A %-d %B %Y')}")

    if not d_evs:
        st.markdown('<div class="add-prompt">📭 No events on this day — use the form below to add one</div>', unsafe_allow_html=True)
    for ev in d_evs:
        render_event_card(ev, "w")

    with st.expander(f"➕ Add event on {sel.strftime('%-d %B')}", expanded=(not d_evs)):
        ok, data = event_form(f"wadd_{str(sel)}", default_date=sel)
        if ok: save_event(data); st.success(f"✅ '{data['title']}' added!"); st.rerun()

# ═══════════════ AGENDA VIEW ══════════════════════════════════════════════════
with tab_list:
    lc1, lc2, lc3 = st.columns(3)
    with lc1: ls = st.date_input("From", value=today, key="ls")
    with lc2: le = st.date_input("To",   value=today+timedelta(weeks=8), key="le")
    with lc3: tf = st.multiselect("Filter type", list(EVENT_TYPES.keys()), default=list(EVENT_TYPES.keys()), key="tf")

    with st.expander("➕ Add New Event"):
        ok, data = event_form("ladd")
        if ok: save_event(data); st.success(f"✅ '{data['title']}' added!"); st.rerun()

    st.markdown("---")
    levs  = db_events(ls, le) + pac_events(db_pac(), ls, le)
    levs  = [e for e in levs if e.get("event_type") in tf]
    levs.sort(key=lambda x: (str(x.get("event_date","")), str(x.get("start_time",""))))

    if not levs:
        st.markdown('<div class="info-box">No events in this date range.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(levs)} event{'s' if len(levs)!=1 else ''} found**")
        cur_d = None
        for ev in levs:
            eds = str(ev.get("event_date",""))[:10]
            if eds != cur_d:
                cur_d = eds
                try:
                    do = datetime.strptime(eds,"%Y-%m-%d").date()
                    lbl = f"📍 **TODAY — {do.strftime('%A %-d %B %Y')}**" if do==today else f"**{do.strftime('%A %-d %B %Y')}**"
                    st.markdown(lbl)
                except: st.markdown(f"**{eds}**")
            render_event_card(ev, "l")

# ═══════════════ STUDENTS VIEW ════════════════════════════════════════════════
with tab_students:
    st.markdown("### 👨‍🎓 Student Placements & Meetings")
    st.markdown("""
    <div style="background:#f8faff;border:1px solid #c7d7f0;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.84rem;color:#374151;">
    Student names are stored as <strong>initials only</strong> for privacy. &nbsp;
    Colour coding:&nbsp;
    <span style="background:#dbeafe;color:#1d4ed8;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">JP</span> Junior Primary &nbsp;
    <span style="background:#dcfce7;color:#15803d;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">PY</span> Primary Years &nbsp;
    <span style="background:#fef9c3;color:#a16207;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">SY</span> Senior Years &nbsp;
    &nbsp;|&nbsp; ✏️ <strong>All staff</strong> can edit student dates.
    </div>
    """, unsafe_allow_html=True)

    # ── Sub-tabs ──
    st_gantt, st_meetings, st_transition = st.tabs(["📊 Placement Timeline", "📋 Meetings List", "🔀 Transition Schedule"])

    # ════════ PLACEMENT TIMELINE (GANTT STRIP) ════════
    with st_gantt:

        g1, g2, g3 = st.columns(3)
        with g1: g_from = st.date_input("From", value=today - timedelta(days=today.weekday()), key="g_from")
        with g2: g_to   = st.date_input("To",   value=today + timedelta(weeks=8), key="g_to")
        with g3: g_prog = st.multiselect("Program", ["JP","PY","SY"], default=["JP","PY","SY"], key="g_prog")

        # Add student placement form
        with st.expander("➕ Add Student Placement"):
            with st.form("sg_add_form", clear_on_submit=True):
                sa1, sa2 = st.columns(2)
                with sa1:
                    s_initials = st.text_input("Student initials *", placeholder="e.g. J.S.")
                    s_program  = st.selectbox("Program *", ["", "JP", "PY", "SY"])
                    s_who      = st.text_input("Added by *", placeholder="Your name")
                with sa2:
                    s_start = st.date_input("Start date *", value=today, key="sg_start")
                    s_end   = st.date_input("End date *",   value=today + timedelta(weeks=10), key="sg_end")
                    s_notes = st.text_area("Notes (optional)", height=96)
                s_ok = st.form_submit_button("✅ Add Placement", type="primary", use_container_width=True)
                if s_ok:
                    if not s_initials.strip():
                        st.warning("Please enter student initials.")
                    elif not s_program:
                        st.warning("Please select a program.")
                    elif not s_who.strip():
                        st.warning("Please enter your name.")
                    else:
                        supabase.table("clc_events").insert({
                            "title": f"Student Placement — {s_initials.strip()}",
                            "event_type": "Student Placement",
                            "event_date": str(s_start),
                            "end_date": str(s_end) if s_end != s_start else None,
                            "start_time": None, "end_time": None,
                            "location": "", "added_by": s_who.strip(),
                            "notes": s_notes.strip(),
                            "program": s_program,
                            "student_initials": s_initials.strip(),
                        }).execute()
                        st.success(f"✅ Placement added for {s_initials.strip()}!")
                        st.rerun()

        st.markdown("---")

        # Fetch all placements and meetings in range
        g_range_start = g_from - timedelta(days=30)  # fetch wider to catch placements that started earlier
        g_range_end   = g_to   + timedelta(days=30)
        all_g_evs = db_events(g_range_start, g_range_end)

        placements = [e for e in all_g_evs
                      if e.get("event_type") == "Student Placement"
                      and e.get("program","") in g_prog]
        meetings   = [e for e in all_g_evs
                      if e.get("event_type") in STUDENT_MEETING_TYPES]

        if not placements:
            st.markdown('<div class="info-box">No student placements found. Add one above.</div>', unsafe_allow_html=True)
        else:
            # Build list of days to show as columns (Mon–Fri only, within range)
            days = []
            d = g_from
            while d <= g_to:
                if d.weekday() < 5:  # Mon–Fri only
                    days.append(d)
                d += timedelta(days=1)

            if len(days) > 60:
                st.warning("Date range is very wide — showing up to 60 school days. Narrow the range for best results.")
                days = days[:60]

            # Build meeting lookup by student_initials and date
            meeting_lookup = {}  # (initials, date_str) -> list of meeting types
            for m in meetings:
                init = m.get("student_initials","")
                mdate = str(m.get("event_date",""))[:10]
                if init:
                    key = (init, mdate)
                    meeting_lookup.setdefault(key, []).append(m.get("event_type",""))

            # Meeting dot colours
            MEETING_DOTS = {
                "Entry Meeting":      {"dot": "#0e7490", "label": "E"},
                "Review Meeting":     {"dot": "#c2410c", "label": "R"},
                "Transition Meeting": {"dot": "#7c3aed", "label": "T"},
                "TAC Meeting":        {"dot": "#b45309", "label": "TAC"},
            }

            # Group placements by program for display
            prog_order = ["JP", "PY", "SY"]
            placements.sort(key=lambda x: (prog_order.index(x.get("program","JP")) if x.get("program") in prog_order else 3,
                                           str(x.get("event_date",""))))

            # Build Gantt HTML table
            # Header row: dates
            # Limit column header to show day number only, month on change
            CELL_W = max(22, min(36, 1100 // max(len(days),1)))

            html = f"""
<style>
.gantt-wrap {{overflow-x:auto;}}
.gantt-table {{border-collapse:collapse;font-family:'Inter',sans-serif;font-size:0.72rem;}}
.gantt-table th {{background:#1a2e4a;color:white;padding:3px 4px;text-align:center;min-width:{CELL_W}px;white-space:nowrap;border:1px solid #2d4a6e;}}
.gantt-table td {{border:1px solid #e5e7eb;padding:2px;text-align:center;height:30px;min-width:{CELL_W}px;background:white;}}
.gantt-table .row-label {{text-align:left;padding:4px 10px;font-weight:700;white-space:nowrap;min-width:90px;background:#f8fafc;border:1px solid #e5e7eb;position:sticky;left:0;z-index:2;}}
.gantt-table .prog-head {{text-align:left;padding:5px 10px;font-size:0.75rem;font-weight:800;letter-spacing:0.05em;text-transform:uppercase;border:1px solid #e5e7eb;}}
.gantt-bar {{border-radius:4px;height:22px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;color:white;position:relative;}}
.gantt-dot {{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;color:white;font-size:0.6rem;font-weight:800;margin:1px;}}
.gantt-today {{background:#fffbeb!important;border-left:2px solid #d4af37!important;border-right:2px solid #d4af37!important;}}
.gantt-weekend {{background:#f9fafb!important;}}
</style>
<div class="gantt-wrap">
<table class="gantt-table">
<tr>
  <th class="row-label" style="position:sticky;left:0;z-index:3;">Student</th>
"""
            # Date headers
            prev_month = None
            for d in days:
                is_today = d == today
                month_lbl = d.strftime("%b") if d.month != prev_month else ""
                prev_month = d.month
                bg = "#d4af37" if is_today else "#1a2e4a"
                html += f'<th style="background:{bg};">{month_lbl}<br>{d.day}<br><span style="font-weight:400;opacity:0.7;">{d.strftime("%a")[0]}</span></th>'
            html += "</tr>"

            cur_prog = None
            for pl in placements:
                prog = pl.get("program","")
                pc   = PROGRAM_COLORS.get(prog, {"color":"#374151","bg":"#f3f4f6"})
                init = pl.get("student_initials","") or pl.get("title","?")

                # Program group header row
                if prog != cur_prog:
                    cur_prog = prog
                    prog_bg  = pc["bg"]; prog_col = pc["color"]
                    html += f'<tr><td class="prog-head" colspan="{len(days)+1}" style="background:{prog_bg};color:{prog_col};">{prog} — {PROGRAM_COLORS.get(prog,{}).get("label","")}</td></tr>'

                pl_start = datetime.strptime(str(pl.get("event_date",""))[:10], "%Y-%m-%d").date()
                pl_end_raw = pl.get("end_date") or pl.get("event_date")
                pl_end   = datetime.strptime(str(pl_end_raw)[:10], "%Y-%m-%d").date()

                html += f'<tr><td class="row-label"><span style="color:{pc["color"]};font-weight:700;">{init}</span><br><span style="font-size:0.65rem;color:#888;">{pl_start.strftime("%-d %b")} – {pl_end.strftime("%-d %b")}</span></td>'

                for d in days:
                    is_today_col = d == today
                    in_placement = pl_start <= d <= pl_end
                    ds = str(d)
                    mtypes = meeting_lookup.get((init, ds), [])

                    td_cls = "gantt-today" if is_today_col else ""

                    if in_placement:
                        if mtypes:
                            # Show meeting dots on placement bar
                            dots_html = ""
                            for mt in mtypes:
                                dot_cfg = MEETING_DOTS.get(mt, {"dot":"#374151","label":"?"})
                                dots_html += f'<span class="gantt-dot" style="background:{dot_cfg["dot"]};" title="{mt}">{dot_cfg["label"]}</span>'
                            html += f'<td class="{td_cls}" style="background:{pc["bg"]}"><div class="gantt-bar" style="background:{pc["color"]};">{dots_html}</div></td>'
                        else:
                            # Solid placement bar
                            html += f'<td class="{td_cls}" style="background:{pc["bg"]};"><div class="gantt-bar" style="background:{pc["color"]};opacity:0.85;">·</div></td>'
                    else:
                        # Outside placement — show meeting dots even if not placed (edge case)
                        if mtypes:
                            dots_html = "".join([f'<span class="gantt-dot" style="background:{MEETING_DOTS.get(mt,{}).get("dot","#374151")};" title="{mt}">{MEETING_DOTS.get(mt,{}).get("label","?")}</span>' for mt in mtypes])
                            html += f'<td class="{td_cls}">{dots_html}</td>'
                        else:
                            html += f'<td class="{td_cls}"></td>'
                html += "</tr>"

            html += "</table></div>"

            # Legend
            html += """
<div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.5rem;font-size:0.75rem;align-items:center;">
<strong>Meeting markers:</strong>
<span style="background:#0e7490;color:white;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:0.65rem;">E</span> Entry &nbsp;
<span style="background:#c2410c;color:white;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:0.65rem;">R</span> Review &nbsp;
<span style="background:#7c3aed;color:white;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:0.65rem;">T</span> Transition &nbsp;
<span style="background:#b45309;color:white;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:0.65rem;font-size:0.55rem;">TAC</span> TAC
</div>"""

            st.markdown(html, unsafe_allow_html=True)

            # Edit placements
            st.markdown("---")
            st.markdown("**✏️ Edit a placement:**")
            for pl in placements:
                eid  = pl.get("id","")
                init = pl.get("student_initials","")
                prog = pl.get("program","")
                pc   = PROGRAM_COLORS.get(prog, {"color":"#374151","bg":"#f3f4f6"})
                pl_start = str(pl.get("event_date",""))[:10]
                pl_end   = str(pl.get("end_date") or pl.get("event_date",""))[:10]

                ec1, ec2 = st.columns([6,1])
                with ec1:
                    st.markdown(f'<div style="background:{pc["bg"]};border-left:4px solid {pc["color"]};border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:4px;"><span style="background:{pc["color"]};color:white;font-size:0.7rem;font-weight:700;padding:0.1rem 0.4rem;border-radius:8px;">{prog}</span> <strong>{init}</strong> <span style="color:#888;font-size:0.78rem;">{pl_start} → {pl_end}</span></div>', unsafe_allow_html=True)
                with ec2:
                    if st.button("✏️", key=f"sg_e_{eid}"):
                        st.session_state.edit_event_id = eid if st.session_state.edit_event_id != eid else None
                        st.rerun()

                if st.session_state.edit_event_id == eid:
                    with st.form(f"sg_ef_{eid}", clear_on_submit=False):
                        ea1, ea2 = st.columns(2)
                        with ea1:
                            e_initials = st.text_input("Student initials *", value=pl.get("student_initials",""))
                            prog_opts  = ["", "JP", "PY", "SY"]
                            e_program  = st.selectbox("Program *", prog_opts,
                                                      index=prog_opts.index(pl.get("program","")) if pl.get("program","") in prog_opts else 0)
                            e_who = st.text_input("Added by *", value=pl.get("added_by",""))
                        with ea2:
                            e_start = st.date_input("Start date *",
                                                    value=datetime.strptime(str(pl.get("event_date",today))[:10],"%Y-%m-%d").date(),
                                                    key=f"sge_s_{eid}")
                            e_end_raw = pl.get("end_date") or pl.get("event_date", today)
                            e_end = st.date_input("End date *",
                                                  value=datetime.strptime(str(e_end_raw)[:10],"%Y-%m-%d").date(),
                                                  key=f"sge_e_{eid}")
                            e_notes = st.text_area("Notes", value=pl.get("notes",""), height=80)
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            supabase.table("clc_events").update({
                                "title": f"Student Placement — {e_initials.strip()}",
                                "event_type": "Student Placement",
                                "event_date": str(e_start),
                                "end_date": str(e_end) if e_end != e_start else None,
                                "start_time": None, "end_time": None,
                                "location": "", "added_by": e_who.strip(),
                                "notes": e_notes.strip(),
                                "program": e_program,
                                "student_initials": e_initials.strip(),
                            }).eq("id", eid).execute()
                            st.session_state.edit_event_id = None
                            st.success("Updated!"); st.rerun()
                    if st.session_state.is_admin:
                        if st.button("🗑️ Delete this placement", key=f"sg_del_{eid}", type="secondary"):
                            del_event(eid); st.rerun()

    # ════════ MEETINGS LIST ════════
    with st_meetings:
        ml1, ml2, ml3 = st.columns(3)
        with ml1: m_from = st.date_input("From", value=today, key="m_from")
        with ml2: m_to   = st.date_input("To",   value=today+timedelta(weeks=12), key="m_to")
        with ml3: m_prog = st.multiselect("Program", ["JP","PY","SY"], default=["JP","PY","SY"], key="m_prog_f")

        m_types = st.multiselect("Meeting type", STUDENT_MEETING_TYPES, default=STUDENT_MEETING_TYPES, key="m_type_f")

        # Add student meeting
        with st.expander("➕ Add Student Meeting"):
            with st.form("sm_add_form", clear_on_submit=True):
                sma1, sma2 = st.columns(2)
                with sma1:
                    sm_type     = st.selectbox("Meeting type *", STUDENT_MEETING_TYPES)
                    sm_initials = st.text_input("Student initials *", placeholder="e.g. J.S.")
                    sm_program  = st.selectbox("Program *", ["", "JP", "PY", "SY"])
                    sm_who      = st.text_input("Added by *", placeholder="Your name")
                with sma2:
                    sm_date  = st.date_input("Meeting date *", value=today, key="sm_date")
                    sm_time  = st.time_input("Time (optional)", value=None)
                    sm_loc   = st.text_input("Location (optional)")
                    sm_notes = st.text_area("Notes (optional)", height=80)
                sm_ok = st.form_submit_button("✅ Add Meeting", type="primary", use_container_width=True)
                if sm_ok:
                    if not sm_initials.strip():
                        st.warning("Please enter student initials.")
                    elif not sm_program:
                        st.warning("Please select a program.")
                    elif not sm_who.strip():
                        st.warning("Please enter your name.")
                    else:
                        supabase.table("clc_events").insert({
                            "title": f"{sm_type} — {sm_initials.strip()}",
                            "event_type": sm_type,
                            "event_date": str(sm_date),
                            "end_date": None,
                            "start_time": str(sm_time) if sm_time else None,
                            "end_time": None,
                            "location": sm_loc.strip(),
                            "added_by": sm_who.strip(),
                            "notes": sm_notes.strip(),
                            "program": sm_program,
                            "student_initials": sm_initials.strip(),
                        }).execute()
                        st.success(f"✅ {sm_type} added for {sm_initials.strip()}!")
                        st.rerun()

        st.markdown("---")

        m_evs = db_events(m_from, m_to)
        m_evs = [e for e in m_evs
                 if e.get("event_type") in m_types
                 and e.get("program","") in m_prog]
        m_evs.sort(key=lambda x: (str(x.get("event_date","")), str(x.get("start_time",""))))

        if not m_evs:
            st.markdown('<div class="info-box">No student meetings found in this date range. Add one above.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(m_evs)} meeting{'s' if len(m_evs)!=1 else ''} found**")
            cur_d = None
            for ev in m_evs:
                eds = str(ev.get("event_date",""))[:10]
                if eds != cur_d:
                    cur_d = eds
                    try:
                        do  = datetime.strptime(eds,"%Y-%m-%d").date()
                        lbl = f"📍 **TODAY — {do.strftime('%A %-d %B %Y')}**" if do==today else f"**{do.strftime('%A %-d %B %Y')}**"
                        st.markdown(lbl)
                    except: st.markdown(f"**{eds}**")

                prog = ev.get("program","")
                pc   = PROGRAM_COLORS.get(prog, {"color":"#374151","bg":"#f3f4f6"})
                cfg  = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
                tr   = fmt_time(ev.get("start_time",""))
                eid  = ev.get("id","")
                init = ev.get("student_initials","")

                mc1, mc2, mc3 = st.columns([6,1,1])
                with mc1:
                    st.markdown(
                        f'<div class="student-card" style="background:{pc["bg"]};border-left-color:{cfg["color"]};">'
                        f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">'
                        f'<span style="background:{pc["color"]};color:white;font-size:0.7rem;font-weight:700;padding:0.1rem 0.45rem;border-radius:8px;">{prog}</span>'
                        f'<span style="background:{cfg["color"]};color:white;font-size:0.7rem;padding:0.1rem 0.45rem;border-radius:8px;">{cfg["emoji"]} {ev.get("event_type","")}</span>'
                        f'<strong style="color:#1a2e4a;">{init}</strong>'
                        f'</div>'
                        f'<div style="font-size:0.78rem;color:#555;">'
                        f'{(" ⏰ "+tr) if tr else ""}'
                        f'{(" 📍 "+ev.get("location","")) if ev.get("location") else ""}'
                        f'{(" 👤 "+ev.get("added_by","")) if ev.get("added_by") else ""}'
                        f'</div>'
                        f'{("<div style=\"font-size:0.78rem;color:#666;margin-top:0.2rem;\">"+ev.get("notes","")+"</div>") if ev.get("notes") else ""}'
                        f'</div>', unsafe_allow_html=True)
                with mc2:
                    st.write("")
                    if st.button("✏️", key=f"sm_e_{eid}"):
                        st.session_state.edit_event_id = eid if st.session_state.edit_event_id != eid else None
                        st.rerun()
                with mc3:
                    if st.session_state.is_admin:
                        st.write("")
                        if st.button("🗑️", key=f"sm_d_{eid}"):
                            del_event(eid); st.rerun()

                if st.session_state.edit_event_id == eid:
                    st.markdown("**✏️ Edit meeting:**")
                    with st.form(f"sm_ef_{eid}", clear_on_submit=False):
                        ef1, ef2 = st.columns(2)
                        with ef1:
                            etype_opts = STUDENT_MEETING_TYPES
                            e_mtype    = st.selectbox("Meeting type *", etype_opts,
                                                      index=etype_opts.index(ev.get("event_type")) if ev.get("event_type") in etype_opts else 0)
                            e_init     = st.text_input("Student initials *", value=ev.get("student_initials",""))
                            prog_opts  = ["", "JP", "PY", "SY"]
                            e_prog     = st.selectbox("Program *", prog_opts,
                                                      index=prog_opts.index(ev.get("program","")) if ev.get("program","") in prog_opts else 0)
                            e_who_m    = st.text_input("Added by *", value=ev.get("added_by",""))
                        with ef2:
                            e_mdate = st.date_input("Date *",
                                                    value=datetime.strptime(str(ev.get("event_date",today))[:10],"%Y-%m-%d").date(),
                                                    key=f"sme_d_{eid}")
                            e_mtime = st.time_input("Time (optional)", value=None, key=f"sme_t_{eid}")
                            e_mloc  = st.text_input("Location", value=ev.get("location",""))
                            e_mnotes= st.text_area("Notes", value=ev.get("notes",""), height=80)
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            supabase.table("clc_events").update({
                                "title": f"{e_mtype} — {e_init.strip()}",
                                "event_type": e_mtype,
                                "event_date": str(e_mdate),
                                "end_date": None,
                                "start_time": str(e_mtime) if e_mtime else None,
                                "end_time": None,
                                "location": e_mloc.strip(),
                                "added_by": e_who_m.strip(),
                                "notes": e_mnotes.strip(),
                                "program": e_prog,
                                "student_initials": e_init.strip(),
                            }).eq("id", eid).execute()
                            st.session_state.edit_event_id = None
                            st.success("Updated!"); st.rerun()


    # ════════ TRANSITION SCHEDULE ════════
    with st_transition:
        st.markdown("### 🔀 Student Transition Schedules")
        st.markdown("""
        <div style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.84rem;color:#374151;">
        Record the days and times a student attends their mainstream school during transition.
        Each row is one week — enter the times they are <strong>at mainstream</strong> each day.
        Leave a day blank if they are at CLC all day that day.
        </div>
        """, unsafe_allow_html=True)

        # ── Helpers for transition table ──
        DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        DAY_KEYS = ["mon", "tue", "wed", "thu", "fri"]

        def db_transitions(initials=None):
            try:
                q = supabase.table("student_transitions").select("*").order("week_start_date").order("student_initials")
                if initials:
                    q = q.eq("student_initials", initials)
                return q.execute().data or []
            except Exception as e:
                st.error(f"Could not load transition data. Have you run the SQL migration? ({e})")
                return []

        def save_transition(d):
            supabase.table("student_transitions").insert(d).execute()

        def upd_transition(tid, d):
            supabase.table("student_transitions").update(d).eq("id", tid).execute()

        def del_transition(tid):
            supabase.table("student_transitions").delete().eq("id", tid).execute()

        def fmt_time_short(t):
            if not t: return ""
            try: return datetime.strptime(str(t)[:5], "%H:%M").strftime("%-I:%M%p").lower()
            except: return str(t)[:5]

        # ── Filters ──
        tr1, tr2, tr3 = st.columns(3)
        with tr1:
            tr_prog = st.multiselect("Program", ["JP","PY","SY"], default=["JP","PY","SY"], key="tr_prog")
        with tr2:
            # Get distinct students from transitions for filter
            all_trans = db_transitions()
            all_inits = sorted(set(t.get("student_initials","") for t in all_trans if t.get("student_initials")))
            tr_student = st.selectbox("Filter by student", ["All"] + all_inits, key="tr_student")
        with tr3:
            tr_term = st.selectbox("Filter by term", ["All", "Term 1", "Term 2", "Term 3", "Term 4"], key="tr_term")

        # ── Add new transition week ──
        with st.expander("➕ Add Transition Week"):
            with st.form("tr_add_form", clear_on_submit=True):
                tf1, tf2 = st.columns(2)
                with tf1:
                    tr_initials  = st.text_input("Student initials *", placeholder="e.g. J.S.")
                    tr_program_s = st.selectbox("Program *", ["", "JP", "PY", "SY"], key="tr_prog_add")
                    tr_school    = st.text_input("Mainstream school name", placeholder="e.g. Cowandilla Primary")
                    tr_added_by  = st.text_input("Added by *", placeholder="Your name")
                with tf2:
                    tr_term_val  = st.selectbox("Term *", ["Term 1", "Term 2", "Term 3", "Term 4"], key="tr_term_add")
                    tr_week_lbl  = st.text_input("Week label *", placeholder="e.g. Week 3")
                    tr_week_date = st.date_input("Week start date (Monday) *", value=today - timedelta(days=today.weekday()), key="tr_week_date")
                    tr_notes     = st.text_area("Notes (optional)", height=60)

                st.markdown("**Times at mainstream school** *(leave blank = at CLC all day)*")
                day_cols = st.columns(5)
                tr_times = {}
                for i, (day, dk) in enumerate(zip(DAYS, DAY_KEYS)):
                    with day_cols[i]:
                        st.markdown(f"**{day[:3]}**")
                        tr_times[f"{dk}_start"] = st.time_input(f"From", value=None, key=f"tr_{dk}_s")
                        tr_times[f"{dk}_end"]   = st.time_input(f"To",   value=None, key=f"tr_{dk}_e")

                tr_ok = st.form_submit_button("✅ Save Transition Week", type="primary", use_container_width=True)
                if tr_ok:
                    if not tr_initials.strip():
                        st.warning("Please enter student initials.")
                    elif not tr_program_s:
                        st.warning("Please select a program.")
                    elif not tr_added_by.strip():
                        st.warning("Please enter your name.")
                    elif not tr_week_lbl.strip():
                        st.warning("Please enter a week label.")
                    else:
                        row = {
                            "student_initials": tr_initials.strip(),
                            "program": tr_program_s,
                            "mainstream_school": tr_school.strip(),
                            "term": tr_term_val,
                            "week_label": tr_week_lbl.strip(),
                            "week_start_date": str(tr_week_date),
                            "notes": tr_notes.strip(),
                            "added_by": tr_added_by.strip(),
                        }
                        for dk in DAY_KEYS:
                            s = tr_times.get(f"{dk}_start")
                            e = tr_times.get(f"{dk}_end")
                            row[f"{dk}_start"] = str(s) if s else None
                            row[f"{dk}_end"]   = str(e) if e else None
                        save_transition(row)
                        st.success(f"✅ Transition week saved for {tr_initials.strip()}!")
                        st.rerun()

        st.markdown("---")

        # ── Fetch and filter ──
        disp_trans = db_transitions(initials=None if tr_student == "All" else tr_student)
        if tr_prog != ["JP","PY","SY"]:
            disp_trans = [t for t in disp_trans if t.get("program","") in tr_prog]
        if tr_term != "All":
            disp_trans = [t for t in disp_trans if t.get("term","") == tr_term]

        if not disp_trans:
            st.markdown('<div class="info-box">No transition schedules found. Add one above.</div>', unsafe_allow_html=True)
        else:
            # Group by student
            from collections import defaultdict
            by_student = defaultdict(list)
            for t in disp_trans:
                by_student[t.get("student_initials","?")].append(t)

            for init, weeks in by_student.items():
                prog = weeks[0].get("program","")
                pc   = PROGRAM_COLORS.get(prog, {"color":"#374151","bg":"#f3f4f6"})
                school = weeks[0].get("mainstream_school","")

                # Student header
                st.markdown(
                    f'<div style="background:{pc["bg"]};border-left:4px solid {pc["color"]};border-radius:10px;'
                    f'padding:0.6rem 1rem;margin:1rem 0 0.5rem;display:flex;align-items:center;gap:0.75rem;">'
                    f'<span style="background:{pc["color"]};color:white;font-size:0.75rem;font-weight:700;'
                    f'padding:0.2rem 0.55rem;border-radius:8px;">{prog}</span>'
                    f'<strong style="font-size:1rem;color:{pc["color"]};">🔀 {init}</strong>'
                    f'{"<span style=\"font-size:0.82rem;color:#666;\">→ "+school+"</span>" if school else ""}'
                    f'</div>', unsafe_allow_html=True)

                # Build timetable HTML grid
                html = """
<style>
.tr-grid{border-collapse:collapse;width:100%;font-family:'Inter',sans-serif;margin-bottom:1rem;}
.tr-grid th{background:#4a7c59;color:white;padding:6px 10px;font-size:0.78rem;font-weight:600;text-align:center;border:1px solid #3a6347;}
.tr-grid th.row-h{background:#2d5a3d;text-align:left;min-width:90px;}
.tr-grid td{border:1px solid #d1d5db;padding:6px 8px;font-size:0.78rem;text-align:center;background:white;vertical-align:middle;}
.tr-grid td.label-cell{background:#f0f7f2;font-weight:600;color:#2d5a3d;text-align:left;white-space:nowrap;}
.tr-grid td.has-time{background:#d1fae5;color:#065f46;font-weight:600;}
.tr-grid td.no-time{background:#f9fafb;color:#9ca3af;font-size:0.72rem;}
.tr-grid tr.week-divider td{border-top:2px solid #6b9e7a;}
</style>
<table class="tr-grid">
<tr>
  <th class="row-h">Term / Week</th>
  <th>Monday</th><th>Tuesday</th><th>Wednesday</th><th>Thursday</th><th>Friday</th>
</tr>"""
                cur_term = None
                for idx_w, week in enumerate(weeks):
                    trm  = week.get("term","")
                    wlbl = week.get("week_label","")
                    tid  = week.get("id","")
                    # Week date labels row
                    wdate = week.get("week_start_date","")
                    try:
                        wmon = datetime.strptime(wdate[:10], "%Y-%m-%d").date()
                        date_cells = "".join([
                            f'<td style="font-size:0.7rem;color:#888;background:#fafafa;">{(wmon+timedelta(days=i)).strftime("%-d %b")}</td>'
                            for i in range(5)])
                    except:
                        date_cells = "<td colspan='5'></td>"

                    # Term header row
                    if trm != cur_term:
                        cur_term = trm
                        html += f'<tr><td class="label-cell" colspan="6" style="background:#2d5a3d;color:white;font-size:0.8rem;letter-spacing:0.05em;text-transform:uppercase;">{trm}</td></tr>'

                    # Week label + dates
                    html += f'<tr class="{"week-divider" if idx_w>0 else ""}"><td class="label-cell" rowspan="2">{wlbl}</td>{date_cells}</tr>'

                    # Time cells row
                    html += "<tr>"
                    for dk in DAY_KEYS:
                        s = fmt_time_short(week.get(f"{dk}_start"))
                        e = fmt_time_short(week.get(f"{dk}_end"))
                        if s and e:
                            html += f'<td class="has-time">{s}–{e}</td>'
                        elif s:
                            html += f'<td class="has-time">{s}</td>'
                        else:
                            html += '<td class="no-time">CLC</td>'
                    html += "</tr>"

                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

                # Notes
                if weeks[0].get("notes"):
                    st.caption(f"📝 {weeks[0]['notes']}")

                # Edit / delete controls per week
                with st.expander(f"✏️ Edit / delete weeks for {init}"):
                    for week in weeks:
                        tid   = week.get("id","")
                        wlbl  = week.get("week_label","")
                        wdate = week.get("week_start_date","")
                        ec1, ec2, ec3 = st.columns([4,1,1])
                        with ec1:
                            st.markdown(f"**{week.get('term','')} · {wlbl}** — {wdate}")
                        with ec2:
                            if st.button("✏️", key=f"tr_ed_{tid}"):
                                st.session_state.edit_event_id = tid if st.session_state.edit_event_id != tid else None
                                st.rerun()
                        with ec3:
                            if st.session_state.is_admin:
                                if st.button("🗑️", key=f"tr_del_{tid}"):
                                    del_transition(tid); st.rerun()

                        if st.session_state.edit_event_id == tid:
                            with st.form(f"tr_ef_{tid}", clear_on_submit=False):
                                ef1, ef2 = st.columns(2)
                                with ef1:
                                    e_init_tr   = st.text_input("Student initials *", value=week.get("student_initials",""))
                                    prog_opts   = ["", "JP", "PY", "SY"]
                                    e_prog_tr   = st.selectbox("Program *", prog_opts,
                                                               index=prog_opts.index(week.get("program","")) if week.get("program","") in prog_opts else 0)
                                    e_school_tr = st.text_input("Mainstream school", value=week.get("mainstream_school",""))
                                    e_by_tr     = st.text_input("Added by *", value=week.get("added_by",""))
                                with ef2:
                                    e_term_tr   = st.selectbox("Term *", ["Term 1","Term 2","Term 3","Term 4"],
                                                               index=["Term 1","Term 2","Term 3","Term 4"].index(week.get("term","Term 1")) if week.get("term") in ["Term 1","Term 2","Term 3","Term 4"] else 0)
                                    e_wlbl_tr   = st.text_input("Week label *", value=week.get("week_label",""))
                                    try:
                                        e_wdate_tr = st.date_input("Week start date *",
                                                                   value=datetime.strptime(week.get("week_start_date","")[:10],"%Y-%m-%d").date(),
                                                                   key=f"tr_wd_{tid}")
                                    except:
                                        e_wdate_tr = st.date_input("Week start date *", value=today, key=f"tr_wd_{tid}")
                                    e_notes_tr  = st.text_area("Notes", value=week.get("notes",""), height=50)

                                st.markdown("**Times at mainstream**")
                                eday_cols = st.columns(5)
                                e_tr_times = {}
                                for i, (day, dk) in enumerate(zip(DAYS, DAY_KEYS)):
                                    with eday_cols[i]:
                                        st.markdown(f"**{day[:3]}**")
                                        existing_s = week.get(f"{dk}_start")
                                        existing_e = week.get(f"{dk}_end")
                                        e_tr_times[f"{dk}_start"] = st.time_input(f"From", value=None, key=f"tr_e{dk}s_{tid}")
                                        e_tr_times[f"{dk}_end"]   = st.time_input(f"To",   value=None, key=f"tr_e{dk}e_{tid}")

                                if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                                    upd_row = {
                                        "student_initials": e_init_tr.strip(),
                                        "program": e_prog_tr,
                                        "mainstream_school": e_school_tr.strip(),
                                        "term": e_term_tr,
                                        "week_label": e_wlbl_tr.strip(),
                                        "week_start_date": str(e_wdate_tr),
                                        "notes": e_notes_tr.strip(),
                                        "added_by": e_by_tr.strip(),
                                    }
                                    for dk in DAY_KEYS:
                                        s = e_tr_times.get(f"{dk}_start")
                                        e_val = e_tr_times.get(f"{dk}_end")
                                        upd_row[f"{dk}_start"] = str(s) if s else None
                                        upd_row[f"{dk}_end"]   = str(e_val) if e_val else None
                                    upd_transition(tid, upd_row)
                                    st.session_state.edit_event_id = None
                                    st.success("Updated!"); st.rerun()

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem;color:#aaa;font-size:0.76rem;">
Cowandilla Learning Centre · Communal Staff Calendar · Events auto-sync to Daily Bulletin
</div>""", unsafe_allow_html=True)
