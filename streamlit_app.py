# turtelrede_app.py
import streamlit as st
import json
import os
from datetime import datetime as dt, timedelta

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

# --- Sidebar ---
st.sidebar.title("🦪 TurtelredeTjanser")
view = st.sidebar.radio("Visning", ["✅ Tjanser", "📋 Redigér Tjanser", "📊 Pointoversigt"])

# --- Main: Markér tjanser ---
if view == "✅ Tjanser":
    st.title("✅ Udfør Tjanser")
    person = st.selectbox("Hvem er du?", list(people.keys()))

    def get_status_color(days_since, freq):
        if days_since <= freq * 0.8:
            return "🟢"
        elif days_since <= freq:
            return "🟡"
        else:
            return "🔴"

    chores_sorted = sorted(
        chores,
        key=lambda c: (
            (dt.now() - dt.fromisoformat(c.get("last_done", "2000-01-01T00:00:00"))).days / c["frequency_days"]
        ),
        reverse=True
    )

    for i, chore in enumerate(chores_sorted):
        last_done_str = chore.get("last_done")
        if not last_done_str:
            days_since = 9999
            status = "❓"
        else:
            days_since = (dt.now() - dt.fromisoformat(last_done_str)).days
            status = get_status_color(days_since, chore["frequency_days"])

        with st.expander(f"{status} {chore['name']} ({'aldrig' if days_since == 9999 else f'{days_since} dage'} siden)"):
            st.write(f"⏱️ Estimeret tid: {chore['est_time_min']} minutter")
            st.write(f"🏷️ Tags: {', '.join(chore['tags'])}")
            st.write(f"📍 Område: {chore['area']}")
            st.write("📝 Tjekliste:")
            for item in chore["checklist"]:
                st.markdown(f"- [ ] {item}")

            if st.button(f"✅ Marker som gjort af {person}", key=f"done_{i}"):
                chore["last_done"] = dt.now().isoformat()
                people[person]["points"] += chore["points"]
                history.append({
                    "person": person,
                    "chore": chore["name"],
                    "points": chore["points"],
                    "timestamp": dt.now().isoformat()
                })
                save_json(CHORES_FILE, chores)
                save_json(PEOPLE_FILE, people)
                save_json(HISTORY_FILE, history)
                st.success("✅ Tjans markeret!")

# --- Main: Redigér tjanser ---
elif view == "📋 Redigér Tjanser":
    st.title("📋 Opret eller Redigér Tjanser")
    chore_names = [c["name"] for c in chores]
    selected = st.selectbox("Vælg en eksisterende tjans eller skriv ny", ["Ny tjans..."] + chore_names)

    if selected == "Ny tjans...":
        chore = {
            "name": "",
            "frequency_days": 7,
            "last_done": dt.now().isoformat(),
            "points": 1,
            "est_time_min": 5,
            "tags": [],
            "area": "",
            "checklist": []
        }
        editing_new = True
    else:
        chore = next(c for c in chores if c["name"] == selected)
        editing_new = False

    new_name = st.text_input("Navn på tjans", value=chore["name"])
    frequency = st.number_input("Hyppighed (dage)", min_value=1, value=chore["frequency_days"])
    points = st.number_input("Point", min_value=0, value=chore["points"])
    time_min = st.number_input("Estimeret tid (min)", min_value=0, value=chore["est_time_min"])
    area = st.text_input("Område", value=chore["area"])
    tags = st.text_input("Tags (kommasepareret)", value=", ".join(chore["tags"])).split(",")
    checklist = [line for line in st.text_area(
        "Tjekliste (én per linje)",
        value="\n".join([] if editing_new else chore["checklist"])
    ).splitlines() if line.strip()]

    updated_chore = {
        "name": new_name.strip(),
        "frequency_days": frequency,
        "points": points,
        "est_time_min": time_min,
        "area": area.strip(),
        "tags": [t.strip() for t in tags if t.strip()],
        "checklist": checklist,
        "last_done": chore.get("last_done", dt.now().isoformat())
    }

    if st.button("✅ Gem tjans"):
        if editing_new:
            chores.append(updated_chore)
            st.success("✅ Ny tjans gemt!")
        else:
            for i, c in enumerate(chores):
                if c["name"] == selected:
                    chores[i] = updated_chore
                    break
            st.success("✅ Tjans opdateret!")
        save_json(CHORES_FILE, chores)

    if not editing_new and st.button("🗑️ Slet tjans"):
        chores = [c for c in chores if c["name"] != selected]
        save_json(CHORES_FILE, chores)
        st.success("🗑️ Tjans slettet")

# --- Main: Pointoversigt ---
elif view == "📊 Pointoversigt":
    st.title("📊 Pointstatus")
    for person, data in people.items():
        st.write(f"**{person}**: {data['points']} point")

    st.subheader("🕓 Historik")
    recent = sorted(history, key=lambda x: x["timestamp"], reverse=True)[:20]
    for entry in recent:
        ts = dt.fromisoformat(entry["timestamp"]).strftime("%d.%m %H:%M")
        st.write(f"{ts}: {entry['person']} lavede '{entry['chore']}' (+{entry['points']} point)")