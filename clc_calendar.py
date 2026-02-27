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
    "Student Placement":     {"color": "#374151", "bg": "#f3f4f6", "emoji": "📋"},
    "Other":                 {"color": "#374151", "bg": "#f3f4f6", "emoji": "📌"},
}

# Student event types (use initials, program colour coding)
STUDENT_EVENT_TYPES = ["Entry Meeting", "Review Meeting", "Transition Meeting", "Student Placement"]

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
    st.markdown("### 👨‍🎓 Student Meetings & Placements")
    st.markdown("""
    <div style="background:#f8faff;border:1px solid #c7d7f0;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.84rem;color:#374151;">
    Student names are stored as <strong>initials only</strong> for privacy. 
    Colour coding: 
    <span style="background:#dbeafe;color:#1d4ed8;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">JP</span> Junior Primary &nbsp;
    <span style="background:#dcfce7;color:#15803d;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">PY</span> Primary Years &nbsp;
    <span style="background:#fef9c3;color:#a16207;font-weight:700;padding:0.15rem 0.5rem;border-radius:8px;">SY</span> Senior Years
    <br><br>✏️ <strong>All staff</strong> can update student meeting dates using the edit button.
    </div>
    """, unsafe_allow_html=True)

    # Filters
    sc1, sc2, sc3 = st.columns(3)
    with sc1: s_from = st.date_input("From", value=today, key="s_from")
    with sc2: s_to   = st.date_input("To",   value=today+timedelta(weeks=16), key="s_to")
    with sc3:
        prog_filter = st.multiselect("Program", ["JP","PY","SY"], default=["JP","PY","SY"], key="s_prog")

    type_filter = st.multiselect("Meeting type", STUDENT_EVENT_TYPES, default=STUDENT_EVENT_TYPES, key="s_type")

    # Add new student event
    with st.expander("➕ Add Student Meeting / Placement"):
        ok, data = event_form("s_add", default_date=today)
        if ok:
            if data.get("etype") not in STUDENT_EVENT_TYPES:
                st.warning("Please select a student event type (Entry Meeting, Review Meeting, Transition Meeting, or Student Placement).")
            elif not data.get("student_initials","").strip():
                st.warning("Please enter student initials.")
            elif not data.get("program",""):
                st.warning("Please select a program (JP/PY/SY).")
            else:
                save_event(data); st.success(f"✅ Added!"); st.rerun()

    st.markdown("---")

    # Fetch and filter
    all_evs = db_events(s_from, s_to)
    s_evs   = [e for e in all_evs
               if e.get("event_type") in type_filter
               and e.get("event_type") in STUDENT_EVENT_TYPES
               and e.get("program","") in prog_filter]
    s_evs.sort(key=lambda x: (str(x.get("event_date","")), x.get("program",""), str(x.get("start_time",""))))

    if not s_evs:
        st.markdown('<div class="info-box">No student events found in this date range.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(s_evs)} event{'s' if len(s_evs)!=1 else ''} found**")
        cur_d = None
        for ev in s_evs:
            eds = str(ev.get("event_date",""))[:10]
            if eds != cur_d:
                cur_d = eds
                try:
                    do = datetime.strptime(eds,"%Y-%m-%d").date()
                    lbl = f"📍 **TODAY — {do.strftime('%A %-d %B %Y')}**" if do==today else f"**{do.strftime('%A %-d %B %Y')}**"
                    st.markdown(lbl)
                except: st.markdown(f"**{eds}**")

            prog = ev.get("program","")
            pc   = PROGRAM_COLORS.get(prog, {"color":"#374151","bg":"#f3f4f6","label":""})
            cfg  = EVENT_TYPES.get(ev.get("event_type","Other"), EVENT_TYPES["Other"])
            tr   = fmt_time(ev.get("start_time",""))
            if ev.get("end_time"): tr += f" – {fmt_time(ev['end_time'])}"
            eid  = ev.get("id","")
            init = ev.get("student_initials","")

            cc1, cc2 = st.columns([7,1])
            with cc1:
                st.markdown(
                    f'<div class="student-card" style="background:{pc["bg"]};border-left-color:{pc["color"]};">'
                    f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem;">'
                    f'<span style="background:{pc["color"]};color:white;font-size:0.72rem;font-weight:700;padding:0.15rem 0.55rem;border-radius:10px;">{prog}</span>'
                    f'<span style="font-weight:700;font-size:0.95rem;color:{pc["color"]};">{cfg["emoji"]} {init or ev.get("title","")}</span>'
                    f'<span style="background:{pc["bg"]};border:1px solid {pc["color"]};color:{pc["color"]};font-size:0.7rem;padding:0.1rem 0.4rem;border-radius:8px;">{ev.get("event_type","")}</span>'
                    f'</div>'
                    f'<div style="font-size:0.78rem;color:#555;">'
                    f'{(" ⏰ "+tr) if tr else ""}'
                    f'{(" 📍 "+ev.get("location","")) if ev.get("location") else ""}'
                    f'{(" 👤 "+ev.get("added_by","")) if ev.get("added_by") else ""}'
                    f'</div>'
                    f'{("<div style=\"font-size:0.78rem;color:#555;margin-top:0.2rem;\">"+ev.get("notes","")+"</div>") if ev.get("notes") else ""}'
                    f'</div>', unsafe_allow_html=True)
            with cc2:
                st.write("")
                if st.button("✏️", key=f"s_e_{eid}", help="Edit date/details"):
                    st.session_state.edit_event_id = eid if st.session_state.edit_event_id!=eid else None
                    st.rerun()

            if st.session_state.edit_event_id == eid:
                st.markdown("**✏️ Edit student event:**")
                ok, data = event_form(f"s_ef_{eid}", existing=ev, label="💾 Save Changes")
                if ok:
                    upd_event(eid, data); st.session_state.edit_event_id=None
                    st.success("Updated!"); st.rerun()

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem;color:#aaa;font-size:0.76rem;">
Cowandilla Learning Centre · Communal Staff Calendar · Events auto-sync to Daily Bulletin
</div>""", unsafe_allow_html=True)
