
import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import requests
import time
from datetime import datetime
import json

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Zeniq - AI Video Creator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SESSION STATE ====================
if "step" not in st.session_state:
    st.session_state.step = 1
if "mode" not in st.session_state:
    st.session_state.mode = None
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "main_keyword" not in st.session_state:
    st.session_state.main_keyword = ""
if "keywords" not in st.session_state:
    st.session_state.keywords = []
if "script" not in st.session_state:
    st.session_state.script = ""
if "video_ready" not in st.session_state:
    st.session_state.video_ready = False
if "sub_opts" not in st.session_state:
    st.session_state.sub_opts = {}

# ==================== HELPER FUNCTIONS ====================
def show_toast(message, icon="✅"):
    st.toast(f"{icon} {message}")

def generate_voice_edge(text, voice="ur-PK-AsadNeural", pitch="+0Hz", rate="+0%"):
    """Edge TTS se voice generate karta hai (async fix ke saath)."""
    try:
        async def _generate():
            communicate = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp_path = tmp.name
            await communicate.save(tmp_path)
            return tmp_path

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import threading
            result = [None]
            def run():
                result[0] = asyncio.run(_generate())
            t = threading.Thread(target=run)
            t.start()
            t.join()
            return result[0]
        else:
            return asyncio.run(_generate())
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return None

def get_keywords_from_topic(topic):
    """Simulated YouTube/Trends analysis (real API ke liye YouTube Data API chahiye)."""
    base = topic.lower().strip()
    keywords = [
        f"{base} in urdu", f"{base} pakistani", f"{base} islamic bayan",
        f"{base} story", f"{base} 2025", f"{base} explained",
        f"{base} short video", f"{base} viral", f"{base} full video",
        f"{base} new", f"{base} hindi", f"{base} best",
        f"{base} tips", f"{base} motivation", f"{base} for youth",
        f"{base} emotional", f"{base} heart touching", f"{base} kahani",
        f"{base} wazifa", f"{base} live", f"{base} status",
        f"{base} whatsapp status", f"{base} shayari", f"{base} quotes",
        f"{base} podcast", f"{base} comedy", f"{base} drama",
        f"{base} vlog", f"{base} quran", f"{base} islamic"
    ]
    return keywords

def generate_script_for_mode(mode, topic, sub_opts):
    """Mode ke hisab se script generate karta hai (LLM se replace kar sakte hain)."""
    scripts = {
        "single": f"""Assalam o Alaikum dosto...! Aaj hum baat karenge "{topic}" ke baare me...

Dosto, kya aapne kabhi socha hai ke {topic} kya hai...? Hmm...

Dekho, {topic} ki asal baat ye hai ke... insaan ko sabar rakhna chahiye...!

Agar aap {topic} samajh gaye, to zindagi badal jayegi... Hahaha...!

Allah Hafiz dosto...! Like aur subscribe karein...!""",

        "podcast": f"""Host: Assalam o Alaikum! Aaj hamare mehman hain...! Batayein "{topic}" ke baare me kya kehte hain...?

Guest: Shukriya! {topic} bohat important topic hai... Hmm...!

Host: Kya wajaq hi aisa hai...?

Guest: Dekhein, {topic} ki asal baat ye hai ke... insaan ko sochna chahiye...!

Host: Bohat achi baat...! Shukriya mehman...!""",

        "comedy": f"""Bablu: Chacha! {topic} ke baare me kya kehte hain...?

Chacha: Hahaha...! Bablu beta, {topic} ka matlab ye hai ke... Hmm...!

Bablu: Acha...? Phir kya hua...?

Chacha: Ohh...! Phir jo hua wo mat poocho... Hahaha...!

Bablu: Chacha aap to bohat funny hain...! Hahaha...!""",

        "drama": f"""Scene 1 - Ghar Me:

Hero: Ammi! Aaj "{topic}" ki baat ho rahi hai...!

Ammi: Beta, {topic} bohat serious baat hai... Hmm...

Heroine: Lekin Ammi...! Ye kya ho raha hai...?

Villain: Hahaha...! Sab kuch meri plan ke mutabiq hai...!

Scene 2 - Bazaar Me:

Hero: Dekho...! {topic} ka asal raaz ye hai...!

Heroine: Ohh...! Mujhe samajh aa gaya...!""",

        "vlog": f"""Tum: Assalam o Alaikum Dosto! Aaj hum aaye hain {sub_opts.get('place', 'Sea View')} me...! Dekhen kitna pyara nazara hai...!

Dost: Haan yaar, aaj to hawa bhi bohat achi hai...!

Tum: Dosto, {topic} ke baare me aaj samjhayenge...! Idhar dekhen...!

Dost: Waah...! Kitna pyara manzar hai...!

Tum: To dosto, agar pasand aaya to like karein...! Allah Hafiz...!""",

        "quran": f"""[QURAN RECITATION SCRIPT]

📖 {sub_opts.get('surah', 'Surah Yaseen')}

[Qari: Arabic Ayat - Quran.com Se Audio]
   (Arabic text player se aayega - yahan likha nahi jayega)

[Tumhari Clone Voice: Urdu Tarjuma]
   "Yaqeenan Allah sabar karne walon ke saath hai..."

[1 Sec Pause]

[Qari: Next Ayat]

[Tumhari Clone Voice: Urdu Tarjuma]
   "Aur Allah bohat Rehman hai..."

⚠️ Note: Qari ki awaz Quran.com se hogi - AI se nahi banegi
⚠️ Avatar band hoga - Sirf Arabic + Urdu + Background"""
    }
    return scripts.get(mode, "Script generate nahi ho saki.")

def fetch_quran_audio(surah_number=36, reciter_id=7):
    """Quran.com API se audio URL fetch karta hai."""
    try:
        url = f"https://api.quran.com/api/v4/chapter_recitations/{reciter_id}/{surah_number}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("audio_file", {}).get("audio_url")
    except Exception as e:
        st.warning(f"Quran API error: {e}")
    return None

def call_flux_api(prompt, fal_key):
    """FLUX API se image URL fetch karta hai."""
    try:
        headers = {"Authorization": f"Key {fal_key}"}
        resp = requests.post(
            "https://fal.run/fal-ai/flux/dev",
            headers=headers,
            json={"prompt": prompt, "image_size": "landscape_4_3"},
            timeout=60
        )
        if resp.status_code == 200:
            return resp.json().get("images", [{}])[0].get("url")
        else:
            st.error(f"FLUX error: {resp.text}")
    except Exception as e:
        st.error(f"FLUX exception: {e}")
    return None

def call_did_avatar(image_url, text, did_key):
    """D-ID API se avatar video URL fetch karta hai (polling ke saath)."""
    try:
        headers = {
            "Authorization": f"Basic {did_key}",
            "Content-Type": "application/json"
        }
        resp = requests.post(
            "https://api.d-id.com/talks",
            headers=headers,
            json={"source_url": image_url, "script": {"type": "text", "input": text}},
            timeout=30
        )
        if resp.status_code not in (200, 201):
            st.error(f"D-ID error: {resp.text}")
            return None
        talk_id = resp.json().get("id")
        if not talk_id:
            return None

        for _ in range(20):
            time.sleep(3)
            r = requests.get(f"https://api.d-id.com/talks/{talk_id}", headers=headers, timeout=10)
            d = r.json()
            if d.get("status") == "done":
                return d.get("result_url")
        st.warning("Avatar time out ho gaya.")
    except Exception as e:
        st.error(f"D-ID exception: {e}")
    return None

# ==================== UI: HEADER ====================
st.title("🎬 ZENIQ")
st.caption("Mukammal AI Video Creator — 6 Modes · 13 Steps · Free")
st.info("⚡ Daily Limit: 20 Videos · Bilkul Free · Streamlit Version")

# ==================== SIDEBAR: PROGRESS + KEYS ====================
with st.sidebar:
    st.header("📍 Progress")
    steps = ["Mode", "Trends", "Top 10", "Script", "Voice", "Photo", "Avatar", "Logo", "Edit", "Render", "Meta", "Score", "Upload"]
    for i, s in enumerate(steps, 1):
        if i == st.session_state.step:
            st.markdown(f"**→ {i}. {s}**")
        elif i < st.session_state.step:
            st.markdown(f"~~{i}. {s}~~ ✅")
        else:
            st.markdown(f"{i}. {s}")

    st.divider()
    st.header("🔑 API Keys")
    fal_key = st.text_input("FAL Key (FLUX)", type="password", key="fal_key_input")
    did_key = st.text_input("D-ID Key (Avatar)", type="password", key="did_key_input")
    st.caption("Keys sirf session mein rehti hain.")

    st.divider()
    if st.button("🔄 Reset App"):
        st.session_state.clear()
        st.rerun()

# ==================== STEP 1: MODE ====================
st.header("STEP 1: Video Ka Type Chuno")

modes = {
    "single": "🎙️ Single Video (1 Aadmi)",
    "podcast": "🎧 Podcast (2 Voices)",
    "comedy": "😂 Comedy (Bablu + Chacha)",
    "drama": "🎭 Drama (3-4 Character)",
    "vlog": "📹 Vlog (Visit + Explain)",
    "quran": "📖 Quran Recitation (Quran.com)"
}

cols = st.columns(3)
for idx, (key, label) in enumerate(modes.items()):
    with cols[idx % 3]:
        if st.button(label, key=f"mode_{key}", use_container_width=True):
            st.session_state.mode = key
            show_toast(f"Mode selected: {key}")

if st.session_state.mode:
    st.success(f"✅ Selected Mode: **{st.session_state.mode.upper()}**")

    sub_opts = {}
    if st.session_state.mode == "drama":
        sub_opts["characters"] = st.selectbox("Kitne Character?", ["2", "3", "4"])
        sub_opts["genre"] = st.selectbox("Drama Kaisa?", ["Emotional", "Sad", "Funny", "Suspense", "Pyar Wala", "Saas Bahu Wala"])
        sub_opts["parts"] = st.selectbox("Kitne Part?", ["1 Part", "3 Part - Part 1,2,3"])
    elif st.session_state.mode == "vlog":
        sub_opts["place"] = st.selectbox("Kahan Gaye Ho?", ["Sea View", "Saddar", "Gaon", "Faisal Masjid"])
        sub_opts["explain"] = st.selectbox("Kya Explain Kar Rahe Ho?", ["Is Jagah Ki Kahani", "Is Cheez Ka Raaz"])
    elif st.session_state.mode == "quran":
        sub_opts["surah"] = st.selectbox("Konsi Surah?", ["Surah Yaseen", "Surah Rehman", "Surah Mulk", "Ayatul Kursi"])
        sub_opts["qari"] = st.selectbox("Konsa Qari?", ["Mishary", "Abdul Basit", "Sudais"])
    st.session_state.sub_opts = sub_opts

    st.session_state.topic = st.text_input(
        "📝 Topic Likho",
        value=st.session_state.topic,
        placeholder="Jaise: 'Sabar ki taqat' ya 'Sea View ki kahani'"
    )

# ==================== STEP 2: TRENDS ====================
if st.session_state.mode and st.session_state.topic:
    st.divider()
    st.header("STEP 2: YouTube + Trends + Keywords")
    if st.button("🔍 Analyze Trends & Find Main Keyword"):
        with st.spinner("Analyzing..."):
            keywords = get_keywords_from_topic(st.session_state.topic)
            st.session_state.keywords = keywords
            st.session_state.main_keyword = keywords[0]
            st.session_state.step = max(st.session_state.step, 2)
            show_toast("Main keyword found!")
    if st.session_state.main_keyword:
        st.success(f"🎯 Main Keyword: **{st.session_state.main_keyword}**")
        st.write("Viral Chance: **87%** (Simulated)")
        with st.expander("📊 Dekhein 30 Best Keywords"):
            for i, kw in enumerate(st.session_state.keywords, 1):
                st.write(f"{i}. {kw}")

# ==================== STEP 3: TOP 10 ====================
if st.session_state.main_keyword:
    st.divider()
    st.header("STEP 3: Top 10 Video Analyze")
    if st.button("📊 Top 10 Videos Dekho"):
        with st.spinner("Fetching top videos..."):
            for i in range(1, 11):
                st.write(f"**#{i}** {st.session_state.main_keyword} - Video {i}")
                st.caption(f"Title: {st.session_state.main_keyword} - Best {i} | Thumbnail: Bold + Face | First 5s: Hook")
            st.session_state.step = max(st.session_state.step, 3)

# ==================== STEP 4: SCRIPT ====================
if st.session_state.main_keyword:
    st.divider()
    st.header("STEP 4: Script Generate")
    if st.button("✍️ Script Banao"):
        with st.spinner("Generating script..."):
            script = generate_script_for_mode(st.session_state.mode, st.session_state.topic, st.session_state.sub_opts)
            st.session_state.script = script
            st.session_state.step = max(st.session_state.step, 4)
            show_toast("Script ready!")
    if st.session_state.script:
        st.text_area("📜 Generated Script", st.session_state.script, height=300)

# ==================== STEP 5: VOICE ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 5: Voice Over - Humanize")
    voice_engine = st.radio("Voice Engine", ["Edge TTS", "Google Cloud TTS", "gTTS"], horizontal=True)
    if st.button("🔊 Test Voice"):
        if voice_engine == "Edge TTS":
            with st.spinner("Generating voice..."):
                test_text = st.session_state.script[:150]
                audio_path = generate_voice_edge(test_text, voice="ur-PK-AsadNeural")
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)
                    st.session_state.step = max(st.session_state.step, 5)
                    os.remove(audio_path)
                else:
                    st.warning("Voice generate nahi ho saki.")
        else:
            st.info(f"{voice_engine} ke liye API key chahiye. Filhal Edge TTS use karein.")

# ==================== STEP 5b: QURAN AUDIO ====================
if st.session_state.mode == "quran":
    st.divider()
    st.header("📖 Quran Audio (Quran.com)")
    surah_map = {"Surah Yaseen": 36, "Surah Rehman": 55, "Surah Mulk": 67, "Ayatul Kursi": 2}
    surah_num = surah_map.get(st.session_state.sub_opts.get("surah", "Surah Yaseen"), 36)
    if st.button("🎧 Quran Audio Fetch Karo"):
        with st.spinner("Quran.com se audio la raha hai..."):
            audio_url = fetch_quran_audio(surah_num, 7)
            if audio_url:
                st.audio(audio_url)
                st.success("✅ Quran audio ready!")
            else:
                st.error("Audio fetch nahi hua.")

# ==================== STEP 6: PHOTO ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 6: Photo + Videos")
    photo_source = st.selectbox("Source", ["AI (FLUX)", "Pexels (Free)", "Apni Photo Upload"])
    if photo_source == "AI (FLUX)":
        flux_prompt = st.text_input("FLUX Prompt", value=f"{st.session_state.topic} beautiful cinematic")
        if st.button("🖼️ FLUX Image Banao"):
            if not fal_key:
                st.warning("Sidebar mein FAL Key daalein.")
            else:
                with st.spinner("FLUX image bana raha hai..."):
                    url = call_flux_api(flux_prompt, fal_key)
                    if url:
                        st.image(url, caption="FLUX Image")
                        st.session_state["flux_image_url"] = url
                        st.session_state.step = max(st.session_state.step, 6)
    elif photo_source == "Apni Photo Upload":
        uploaded = st.file_uploader("Photo upload karein", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, caption="Uploaded")

# ==================== STEP 7: AVATAR ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 7: Avatar")
    avatar_type = st.selectbox("Avatar Type", ["Islamic Male", "Hijab Female", "Young Boy", "Old Man", "Hero", "Heroine", "Ammi", "Villain", "Vlogger", "Avatar Band"])
    if avatar_type != "Avatar Band":
        avatar_img_url = st.text_input("Avatar Image URL (public)", value=st.session_state.get("flux_image_url", ""))
        avatar_text = st.text_input("Avatar Text", value=st.session_state.script[:200])
        if st.button("🧑 Avatar Video Banao"):
            if not did_key:
                st.warning("Sidebar mein D-ID Key daalein.")
            elif not avatar_img_url:
                st.warning("Image URL daalein.")
            else:
                with st.spinner("Avatar video ban raha hai (10-30 sec)..."):
                    url = call_did_avatar(avatar_img_url, avatar_text, did_key)
                    if url:
                        st.video(url)
                        st.session_state["avatar_url"] = url
                        st.session_state.step = max(st.session_state.step, 7)

# ==================== STEP 8: LOGO ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 8: Logo")
    st.file_uploader("Apna Logo Upload Karo", type=["png", "jpg", "jpeg"])

# ==================== STEP 9: EDITING ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 9: Editing")
    st.selectbox("Music", ["Apna Music", "Zeniq Free Music", "Bina Music"])

# ==================== STEP 10: RENDER ====================
if st.session_state.script:
    st.divider()
    st.header("STEP 10: Final Rendering")
    if st.button("🎬 Render Video"):
        progress = st.progress(0)
        status = st.empty()
        steps_render = [
            "Voice over generate ho rahi hai...",
            "Photos/videos arrange ho rahe hain...",
            "Avatars sync ho rahe hain...",
            "Editing & effects apply ho rahe hain...",
            "Final render ho raha hai...",
            "Auto shorts cut ho rahe hain..."
        ]
        for i, s in enumerate(steps_render):
            progress.progress((i + 1) * 100 // len(steps_render))
            status.text(s)
            time.sleep(0.5)
        st.success("✅ Video ready! (Simulation - real video ke liye moviepy local par use karein)")
        st.session_state.video_ready = True
        st.session_state.step = max(st.session_state.step, 10)

# ==================== STEP 11: METADATA ====================
if st.session_state.video_ready:
    st.divider()
    st.header("STEP 11: Title + Thumbnail + Description + Tags")
    if st.button("📝 Generate Metadata"):
        kw = st.session_state.main_keyword
        st.subheader("📌 3 Titles")
        st.write(f"1. {kw} - Complete Guide 2025")
        st.write(f"2. {kw} - Jo Sabko Pata Hona Chahiye")
        st.write(f"3. {kw} - Best Explanation in Urdu")
        st.subheader("📝 Description")
        st.text_area("Description", f"{kw} ke baare me poori maloomat. {kw} samajhne ke liye ye video zaroor dekhein.\n\nBaaki: {', '.join(st.session_state.keywords[1:])}", height=150)
        st.subheader("🏷️ Tags")
        st.code(", ".join(st.session_state.keywords))
        st.caption("Recitation & Text via Quran.com / Quran Foundation - Translation Voice: Zeniq")
        st.session_state.step = max(st.session_state.step, 11)

# ==================== STEP 12-13 ====================
if st.session_state.video_ready:
    st.divider()
    st.header("STEP 12: Zeniq Score")
    st.metric("Score", "95/100", delta="Excellent")
    st.header("STEP 13: Scheduler + Upload")
    st.selectbox("Upload Option", ["Abhi Upload", "Scheduler (9 AM Long, 6 PM Short)", "Bulk Mode (10 Videos)"])
    st.multiselect("Platforms", ["YouTube", "TikTok", "Shorts", "Download"])
    if st.button("🚀 Complete & Launch"):
        st.balloons()
        st.success("Zeniq flow complete!")

# ==================== FOOTER ====================
st.divider()
st.caption("Zeniq v1.0 · Streamlit Version · Made for Pakistani Creators")
