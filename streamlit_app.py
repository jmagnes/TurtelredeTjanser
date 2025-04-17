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
st.title("🦪 TurtelredeTjanser")

if "selected_person" not in st.session_state:
    st.session_state.selected_person = None

if "edit_chore" not in st.session_state:
    st.session_state.edit_chore = None

# --- Person galleri ---
st.subheader("👥 Hvem er du?")
cols = st.columns(len(people))
for i, (person, pdata) in enumerate(people.items()):
    with cols[i]:
        is_selected = st.session_state.selected_person == person
        btn_label = f"{person} ({pdata['points']}🪙)"
        btn_style = "primary" if is_selected else "secondary"
        if st.session_state.selected_person != person:
            st.rerun()
        if st.button(btn_label, key=f"person_{i}", type=btn_style):
            st.session_state.selected_person = person
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
AREA_OPTIONS = ["Soveværelse", "Stue", "Køkken", "Hjem", "Bad", "Andet"]
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

        label = f"{color} {chore['name']}"
        btn_style = "primary" if st.session_state.edit_chore == chore["name"] else "secondary"
        if st.button(label, key=f"open_{area}_{i}", type=btn_style):
            st.session_state.edit_chore = chore["name"]

# --- Redigér/Opret Modal ---
if st.button("➕ Ny tjans"):
    st.session_state.edit_chore = "_new"

if st.session_state.edit_chore:
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

    st.markdown("---")
    st.subheader("✏️ Redigér Tjans" if not is_new else "🆕 Ny Tjans")

    name = st.text_input("Navn", value=chore["name"])
    freq_label = next((k for k, v in FREQ_OPTIONS.items() if v == chore["frequency_days"]), "Brugerdefineret")
    freq = st.selectbox("Hyppighed", list(FREQ_OPTIONS.keys()) + ["Brugerdefineret"], index=list(FREQ_OPTIONS).index(freq_label) if freq_label in FREQ_OPTIONS else len(FREQ_OPTIONS))

    if freq == "Brugerdefineret":
        freq_days = st.number_input("Indtast antal dage", min_value=1, value=chore["frequency_days"])
    else:
        freq_days = FREQ_OPTIONS[freq]

    points = st.number_input("Point", value=chore["points"], min_value=0)
    time = st.number_input("Estimeret tid (min)", value=chore["est_time_min"], min_value=0)
    tags = st.text_input("Tags", value=", ".join(chore["tags"]))
    checklist = st.text_area("Tjekliste", value="\n".join(chore["checklist"])).splitlines()

    if st.button("💾 Gem", type="primary"):
        chore.update({
            "name": name.strip(),
            "frequency_days": freq_days,
            "points": points,
            "est_time_min": time,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "checklist": [line.strip() for line in checklist if line.strip()]
        })
        if is_new:
            chore["area"] = "Andet"  # default value for new
            chores.append(chore)
            st.success(f"✅ Tjans '{chore['name']}' oprettet!")
        else:
            st.success("✅ Tjans opdateret!")
        save_json(CHORES_FILE, chores)
        st.session_state.edit_chore = None

    if not is_new and st.button("✔️ Fuldfør", type="primary"):
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

    if not is_new and st.button("🗑️ Slet tjans permanent"):
        chores.remove(chore)
        save_json(CHORES_FILE, chores)
        st.success("🗑️ Tjans slettet")
        st.session_state.edit_chore = None

    if st.button("❌ Luk"):
        st.session_state.edit_chore = None
