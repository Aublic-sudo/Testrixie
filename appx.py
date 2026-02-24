import requests
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

USER_APPX = {}

API_MAP = {
    "purchased":[
        "/get/mycoursev2?userid={uid}",
        "/get/get_all_purchases?userid={uid}&item_type=10"
    ],

    "folder_subject":[
        "/get/allsubjectfrmlivecourseclass?courseid={id}&start=-1"
    ],

    "previous":[
        "/get/get_previous_live_videos?course_id={id}&start=-1&folder_wise_course=1&userid={uid}"
    ]
}

def get_headers(token,uid):
    return {
        "Authorization":token,
        "Client-Service":"Appx",
        "Auth-Key":"appxapi",
        "User-ID":uid,
        "source":"website"
    }

# ================= SETUP =================

def setup_appx(bot):

    # ================= COURSES =================
    @bot.on_message(filters.command("appxcourses"))
    async def appx_courses(client,m):

        user_id=m.from_user.id

        if user_id not in USER_APPX:
            return await m.reply_text("❌ Login first using /appxlogin")

        data=USER_APPX[user_id]

        api=data["api"]
        token=data["token"]
        uid=data["uid"]

        for ep in API_MAP["purchased"]:

            try:
                r=requests.get(
                    api+ep.replace("{uid}",uid),
                    headers=get_headers(token,uid)
                ).json()

                if r.get("data"):

                    for c in r["data"]:
                        cid=c.get("id") or c.get("item_id")
                        name=c.get("course_name") or c.get("title")

                        USER_APPX[user_id]["course"]=str(cid)

                        btn=InlineKeyboardMarkup([[
                            InlineKeyboardButton(
                                "📁 Folderwise",
                                callback_data=f"appxfolder_{cid}"
                            ),
                            InlineKeyboardButton(
                                "📼 Previous",
                                callback_data=f"appxprev_{cid}"
                            )
                        ]])

                        await m.reply_text(
                            f"🎯 {cid} - {name}",
                            reply_markup=btn
                        )

            except:
                pass

    # ================= PREVIOUS =================
    @bot.on_callback_query(filters.regex("appxprev_"))
    async def prev_handler(client,cb):

        user_id=cb.from_user.id
        data=USER_APPX[user_id]

        api=data["api"]
        token=data["token"]
        uid=data["uid"]

        course_id=cb.data.split("_")[1]

        await cb.message.edit("📼 Loading Previous Videos...")

        url=api+API_MAP["previous"][0]\
            .replace("{id}",course_id)\
            .replace("{uid}",uid)

        r=requests.get(url,headers=get_headers(token,uid)).json()

        txt="🎬 Previous Lectures\n\n"

        for v in r.get("data",[])[:30]:
            txt+=f"🆔 {v['id']} - {v['Title']}\n"

        await cb.message.edit(txt)

    # ================= FOLDERWISE =================
    @bot.on_callback_query(filters.regex("appxfolder_"))
    async def folder_handler(client,cb):

        user_id=cb.from_user.id
        data=USER_APPX[user_id]

        api=data["api"]
        token=data["token"]
        uid=data["uid"]

        course_id=cb.data.split("_")[1]

        await cb.message.edit("📁 Loading Subjects...")

        url=api+API_MAP["folder_subject"][0].replace("{id}",course_id)

        r=requests.get(url,headers=get_headers(token,uid)).json()

        btns=[]

        for s in r.get("data",[]):
            btns.append([
                InlineKeyboardButton(
                    s["subject_name"][:35],
                    callback_data=f"appxtopic_{course_id}_{s['subjectid']}"
                )
            ])

        await cb.message.edit(
            "📁 Select Subject",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    # ================= TOPIC =================
    @bot.on_callback_query(filters.regex("appxtopic_"))
    async def topic_handler(client, cb):

        user_id = cb.from_user.id
        data = USER_APPX[user_id]

        api = data["api"]
        token = data["token"]
        uid = data["uid"]

        _, course_id, sid = cb.data.split("_")

        await cb.message.edit("📖 Loading Topics...")

        url = f"{api}/get/alltopicfrmlivecourseclass?courseid={course_id}&subjectid={sid}&start=-1"

        r = requests.get(url, headers=get_headers(token,uid)).json()

        btns=[]
        for t in r.get("data",[]):

            btns.append([
                InlineKeyboardButton(
                    t["topic_name"][:35],
                    callback_data=f"appxconcept_{course_id}_{sid}_{t['topicid']}"
                )
            ])

        await cb.message.edit(
            "📖 Select Topic",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    # ================= CONCEPT =================
    @bot.on_callback_query(filters.regex("appxconcept_"))
    async def concept_handler(client, cb):

        user_id = cb.from_user.id
        data = USER_APPX[user_id]

        api = data["api"]
        token = data["token"]
        uid = data["uid"]

        _, course_id, sid, tid = cb.data.split("_")

        await cb.message.edit("🧠 Loading Concepts...")

        url = f"{api}/get/allconceptfrmlivecourseclass?topicid={tid}&courseid={course_id}&subjectid={sid}&start=-1"

        r = requests.get(url, headers=get_headers(token,uid)).json()

        btns=[]
        for c in r.get("data",[]):

            btns.append([
                InlineKeyboardButton(
                    c["concept_name"][:35],
                    callback_data=f"appxvideo_{course_id}_{sid}_{tid}"
                )
            ])

        await cb.message.edit(
            "🧠 Select Concept",
            reply_markup=InlineKeyboardMarkup(btns)
        )

    # ================= VIDEO LIST =================
    @bot.on_callback_query(filters.regex("appxvideo_"))
    async def video_list_handler(client, cb):

        user_id = cb.from_user.id
        data = USER_APPX[user_id]

        api = data["api"]
        token = data["token"]
        uid = data["uid"]

        _, course_id, sid, tid = cb.data.split("_")

        await cb.message.edit("🎬 Loading Videos...")

        url = f"{api}/get/livecourseclassbycoursesubtopconceptapiv3?topicid={tid}&start=-1&conceptid=&courseid={course_id}&subjectid={sid}"

        r = requests.get(url, headers=get_headers(token,uid)).json()

        txt="🎬 Videos:\n\n"

        for v in r.get("data",[])[:40]:
            txt+=f"🆔 {v['id']} - {v['Title']}\n"

        txt+="\nSend video id to download."

        await cb.message.edit(txt)

    # ================= DOWNLOAD =================
    @bot.on_message(filters.text & filters.private)
    async def appx_video_download(client, m):

        user_id = m.from_user.id

        if user_id not in USER_APPX:
            return

        if not m.text.isdigit():
            return

        vid = m.text.strip()

        data = USER_APPX[user_id]

        api = data["api"]
        token = data["token"]
        uid = data["uid"]
        course = data["course"]

        await m.reply_text("🔎 Fetching Video Details...")

        endpoints=[
            f"/get/fetchVideoDetailsById?course_id={course}&folder_wise_course=1&ytflag=0&video_id={vid}",
            f"/get/fetchVideoDetailsById?course_id={course}&folder_wise_course=0&ytflag=0&video_id={vid}",
            f"/get/fetchVideoDetailsById?course_id={course}&video_id={vid}&ytflag=0&folder_wise_course=0"
        ]

        video_url=None
        title="APPX_VIDEO"

        for ep in endpoints:
            try:
                r=requests.get(api+ep,headers=get_headers(token,uid)).json()
                if r.get("data"):
                    title=r["data"].get("Title","APPX_VIDEO")
                    video_url=r["data"].get("download_link")
                    if video_url:
                        break
            except:
                pass

        if not video_url:
            return await m.reply_text("❌ Link not found")

        filename=f"{title}.mp4".replace("/"," ")

        await m.reply_text("⬇️ Recording Started...")

        proc=await asyncio.create_subprocess_exec(
            "ffmpeg","-y","-i",video_url,
            "-c:v","libx264",
            "-preset","ultrafast",
            "-c:a","aac",
            filename
        )

        await proc.wait()

        caption=(
            f"🎥 <b>Video Title :</b> {title}\n\n"
            f"<blockquote>📚 Batch Name : APPX</blockquote>\n\n"
            f"<b>Extracted by ➤ @RixieHQ</b>"
        )

        await client.send_video(
            m.chat.id,
            filename,
            caption=caption,
            supports_streaming=True
        )

        import os
        os.remove(filename)
