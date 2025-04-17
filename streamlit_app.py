# turtelrede_app.py
import streamlit as st
import json
import os
from datetime import datetime as dt

DATA_DIR = "data"
CHORES_FILE = os.path.join(DATA_DIR, "chores.json")
PEOPLE_FILE = os.path.join(DATA_DIR, "people.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def load_json(filepath):
    if not os.path.exists(filepath):
        default = [] if "history" in filepath or "chores" in filepath else {}
        save_json(filepath, default)
        return default
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            default = [] if "history" in filepath or "chores" in filepath else {}
            save_json(filepath, default)
            return default
        return json.loads(content)

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

chores = load_json(CHORES_FILE)
people = load_json(PEOPLE_FILE)
history = load_json(HISTORY_FILE)

# --- Init ---
st.title("🪺 TurtelredeTjanser")

if "selected_person" not in st.session_state:
    st.session_state.selected_person = None

if "edit_chore" not in st.session_state:
    st.session_state.edit_chore = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# --- Person galleri ---
st.subheader("👥 Hvem er du?")
cols = st.columns(len(people))
for i, (person, pdata) in enumerate(people.items()):
    with cols[i]:
        is_selected = st.session_state.selected_person == person
        btn_label = f"{person} ({pdata['points']}🪙)"
        btn_style = "primary" if is_selected else "secondary"
        if st.button(btn_label, key=f"person_{i}", type=btn_style):
            st.session_state.selected_person = person
            st.session_state.edit_chore = None  # Luk evt. åben modal
            st.session_state.edit_mode = False
            st.rerun()
        recent_tasks = [h for h in reversed(history) if h["person"] == person][:3]
        for h in recent_tasks:
            ts = dt.fromisoformat(h["timestamp"])
            days_ago = (dt.now().date() - ts.date()).days
            if days_ago == 0:
                ago = "i dag"
            elif days_ago == 1:
                ago = "i går"
            else:
                ago = f"for {days_ago} dage siden"
            st.caption(f"✔️ {h['chore']} ({ago})")

if not st.session_state.selected_person:
    st.info("Vælg en person for at fortsætte")
    st.stop()

# --- Vis tjanser ---
st.subheader("🧹 Tjanser")
AREA_OPTIONS = ["Stue", "Køkken", "Bad", "Soveværelse", "Hjem", "Andet"]
FREQ_OPTIONS = {
    "Dagligt": 1,
    "Ugentligt": 7,
    "Hver anden uge": 14,
    "Hver tredje uge": 21,
    "Månedligt": 30,
    "Kvartalsvist": 90,
    "Halvårligt": 182,
    "Årligt": 365
}

chores_by_area = {}
for chore in chores:
    area = chore.get("area", "Andet")
    chores_by_area.setdefault(area, []).append(chore)

for area, chores_list in chores_by_area.items():
    st.markdown(f"### {area}")
    chores_list.sort(key=lambda c: (dt.now() - dt.fromisoformat(c.get("last_done") or "2000-01-01T00:00:00")).days - c["frequency_days"], reverse=True)
    for i, chore in enumerate(chores_list):
        last_done = dt.fromisoformat(chore.get("last_done") or "2000-01-01T00:00:00")
        days_since = (dt.now() - last_done).days
        freq = chore["frequency_days"]
        due_in = freq - days_since

        if freq <= 6:
            yellow_threshold = 1
        elif freq <= 29:
            yellow_threshold = 3
        elif freq <= 180:
            yellow_threshold = 5
        else:
            yellow_threshold = 10

        if days_since > freq:
            color = "🔴"
        elif due_in <= yellow_threshold:
            color = "🟡"
        else:
            color = "🟢"

        label = f"{color} {chore['name']} ({chore['points']}🪙)"
        btn_style = "secondary"  # Modal popup gør farvemarkering unødvendig
        if st.button(label, key=f"open_{area}_{i}", type=btn_style):
            st.session_state.edit_chore = chore["name"]
            st.session_state.edit_mode = False
            st.rerun()  # Sørg for at modal åbner den korrekte

# --- Redigér/Opret Modal ---
if st.button("➕ Ny tjans"):
    st.session_state.edit_chore = "_new"
    st.session_state.edit_mode = True

dialog_title = (
    "🆕 Ny Tjans"
    if st.session_state.edit_chore == "_new"
    else next(
        (f"{c['name']}" for c in chores if c["name"] == st.session_state.edit_chore),
        "Tjans"
    )
)

@st.dialog(dialog_title)
def show_chore_modal():
    is_new = st.session_state.edit_chore == "_new"
    chore = {
        "name": "",
        "frequency_days": 7,
        "points": 1,
        "est_time_min": 10,
        "area": "Andet",
        "tags": [],
        "checklist": [],
        "last_done": None
    } if is_new else next(c for c in chores if c["name"] == st.session_state.edit_chore)

    if not st.session_state.edit_mode:
        st.markdown(f"🪙 {chore['points']}")
        st.markdown(f"⌛ {chore['est_time_min']} min")
        freq = next((k for k, v in FREQ_OPTIONS.items() if v == chore["frequency_days"]), f"{chore['frequency_days']} dage")
        st.markdown(f"📅 {freq}")

        if chore["tags"]:
            st.markdown("""
            <div style='margin-bottom: 0.5rem;'>
            """ + " ".join([f"<span style='background-color:#eee; padding:0.2rem 0.5rem; margin-right:0.25rem; border-radius:1rem; font-size:90%'>{tag}</span>" for tag in chore["tags"]]) + "</div>", unsafe_allow_html=True)

        for item in chore["checklist"]:
            st.markdown(f"- {item}")

        col1, col2 = st.columns(2)
        with col1:
            if not is_new and st.button("✔️ Fuldfør"):
                chore["last_done"] = dt.now().isoformat()
                people[st.session_state.selected_person]["points"] += chore["points"]
                history.append({
                    "person": st.session_state.selected_person,
                    "chore": chore["name"],
                    "points": chore["points"],
                    "timestamp": dt.now().isoformat()
                })
                save_json(CHORES_FILE, chores)
                save_json(PEOPLE_FILE, people)
                save_json(HISTORY_FILE, history)
                st.success("✅ Tjans markeret!")
                st.session_state.edit_chore = None
                st.rerun()
        with col2:
            if st.button("✏️ Rediger"):
                st.session_state.edit_mode = True
                st.rerun()
        return

    # Redigerbar visning
    name = st.text_input("Navn", value=chore["name"])
    freq_label = next((k for k, v in FREQ_OPTIONS.items() if v == chore["frequency_days"]), "Brugerdefineret")
    freq = st.selectbox("Hyppighed", list(FREQ_OPTIONS.keys()) + ["Brugerdefineret"], index=list(FREQ_OPTIONS).index(freq_label) if freq_label in FREQ_OPTIONS else len(FREQ_OPTIONS))

    if freq == "Brugerdefineret":
        freq_days = st.number_input("Indtast antal dage", min_value=1, value=chore["frequency_days"])
    else:
        freq_days = FREQ_OPTIONS[freq]

    area = st.selectbox("Område", AREA_OPTIONS, index=AREA_OPTIONS.index(chore["area"]) if chore["area"] in AREA_OPTIONS else len(AREA_OPTIONS)-1)
    points = st.number_input("Point", value=chore["points"], min_value=0)
    time = st.number_input("Estimeret tid (min)", value=chore["est_time_min"], min_value=0)
    tags = st.text_input("Tags", value=", ".join(chore["tags"]))
    checklist = st.text_area("Tjekliste", value="\n".join(chore["checklist"])).splitlines()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Gem"):
            chore.update({
                "name": name.strip(),
                "frequency_days": freq_days,
                "points": points,
                "est_time_min": time,
                "area": area,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "checklist": [line.strip() for line in checklist if line.strip()]
            })
            if is_new:
                chores.append(chore)
                st.success(f"✅ Tjans '{chore['name']}' oprettet!")
            else:
                st.success("✅ Tjans opdateret!")
            save_json(CHORES_FILE, chores)
            st.session_state.edit_chore = None
            st.session_state.edit_mode = False
            st.rerun()
    with col2:
        if st.button("↩️ Annuller"):
            st.session_state.edit_mode = False
            st.rerun()

    if not is_new:
        if st.button("🗑️ Slet tjans permanent"):
            st.session_state.confirm_delete = True

    if st.session_state.get("confirm_delete"):
        st.warning("⚠️ Er du sikker på, at du vil slette denne tjans permanent?")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("✅ Ja, slet"):
                chores.remove(chore)
                save_json(CHORES_FILE, chores)
                st.success("🗑️ Tjans slettet")
                st.session_state.edit_chore = None
                st.session_state.edit_mode = False
                st.session_state.confirm_delete = False
                st.rerun()
        with col_del2:
            if st.button("❌ Nej, fortryd"):
                st.session_state.confirm_delete = False
                st.rerun()
                chores.remove(chore)
                save_json(CHORES_FILE, chores)
                st.success("🗑️ Tjans slettet")
                st.session_state.edit_chore = None
                st.session_state.edit_mode = False
                st.rerun()

if st.session_state.edit_chore:
    show_chore_modal()

# --- Historik og point-redigering ---
st.subheader("🧾 Historik og Pointjustering")

with st.expander("📜 Rediger historik og point"):
    show_full_history = st.checkbox("Vis al historik grupperet per år, måned og dag")

    if show_full_history:
        from collections import defaultdict

        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for i, event in enumerate(history):
            dt_obj = dt.fromisoformat(event["timestamp"])
            y, m, d = dt_obj.year, dt_obj.month, dt_obj.day
            grouped[y][m][d].append((i, event))

        for year in sorted(grouped.keys(), reverse=True):
            st.markdown(f"## {year}")
            for month in sorted(grouped[year].keys(), reverse=True):
                st.markdown(f"### {dt(year, month, 1).strftime('%B')}")
                for day in sorted(grouped[year][month].keys(), reverse=True):
                    st.markdown(f"**{year}-{month:02}-{day:02}**")
                    for idx, event in grouped[year][month][day]:
                        timestamp = dt.fromisoformat(event["timestamp"]).strftime("%Y-%m-%d %H:%M")

                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        with col1:
                            new_person = st.selectbox("Person", list(people.keys()), index=list(people.keys()).index(event["person"]), key=f"hist_person_{idx}")
                        with col2:
                            new_chore = st.text_input("Tjans", value=event["chore"], key=f"hist_chore_{idx}")
                        with col3:
                            new_points = st.number_input("Point", value=event["points"], min_value=0, step=1, key=f"hist_points_{idx}")
                        with col4:
                            if st.button("🗑️", key=f"hist_delete_{idx}"):
                                people[event["person"]]["points"] -= event["points"]
                                del history[idx]
                                save_json(HISTORY_FILE, history)
                                save_json(PEOPLE_FILE, people)
                                st.rerun()

                        if (new_person != event["person"] or new_chore != event["chore"] or new_points != event["points"]):
                            if st.button("💾 Gem ændringer", key=f"hist_save_{idx}"):
                                people[event["person"]]["points"] -= event["points"]
                                people[new_person]["points"] += new_points
                                event.update({
                                    "person": new_person,
                                    "chore": new_chore,
                                    "points": new_points,
                                })
                                history[idx] = event
                                save_json(HISTORY_FILE, history)
                                save_json(PEOPLE_FILE, people)
                                st.success("Ændringer gemt!")
                                st.rerun()
    else:
        for i, event in enumerate(reversed(history[-50:])):  # Limit to latest 50 for performance
            idx = len(history) - 1 - i
            timestamp = dt.fromisoformat(event["timestamp"]).strftime("%Y-%m-%d %H:%M")
            st.markdown(f"**{timestamp}**")

            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                new_person = st.selectbox("Person", list(people.keys()), index=list(people.keys()).index(event["person"]), key=f"hist_person_{idx}")
            with col2:
                new_chore = st.text_input("Tjans", value=event["chore"], key=f"hist_chore_{idx}")
            with col3:
                new_points = st.number_input("Point", value=event["points"], min_value=0, step=1, key=f"hist_points_{idx}")
            with col4:
                if st.button("🗑️", key=f"hist_delete_{idx}"):
                    people[event["person"]]["points"] -= event["points"]
                    del history[idx]
                    save_json(HISTORY_FILE, history)
                    save_json(PEOPLE_FILE, people)
                    st.rerun()

            if (new_person != event["person"] or new_chore != event["chore"] or new_points != event["points"]):
                if st.button("💾 Gem ændringer", key=f"hist_save_{idx}"):
                    people[event["person"]]["points"] -= event["points"]
                    people[new_person]["points"] += new_points
                    event.update({
                        "person": new_person,
                        "chore": new_chore,
                        "points": new_points,
                    })
                    history[idx] = event
                    save_json(HISTORY_FILE, history)
                    save_json(PEOPLE_FILE, people)
                    st.success("Ændringer gemt!")
                    st.rerun()
