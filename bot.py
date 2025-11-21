import os
import zipfile
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

TEMP = Path("temp")
TEMP.mkdir(exist_ok=True)

# ====== دالة تضبيط الصورة ======
def resize_to_512(img: Image.Image):
    img = img.convert("RGBA")
    img.thumbnail((512, 512))
    return img

# ====== تحويل كل الستكرز ======
async def convert_pack(chat_id, sticker_set):

    folder = TEMP / f"{chat_id}_{sticker_set.name}"
    folder.mkdir(exist_ok=True)

    stickers_list = []
    count = 1

    for st in sticker_set.stickers:
        if st.is_animated:
            continue

        file = await bot.get_file(st.file_id)
        data = await bot.download_file(file.file_path)

        img = Image.open(data)
        img = resize_to_512(img)

        file_name = f"sticker_{count}.webp"
        img.save(folder / file_name, "WEBP", lossless=True)

        stickers_list.append({
            "image": file_name,
            "emoji": st.emoji or ""
        })

        count += 1

    # metadata.json
    meta = {
        "name": sticker_set.name,
        "title": sticker_set.title,
        "publisher": "Telegram2WhatsApp Bot",
        "stickers": stickers_list
    }

    with open(folder / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # tray.webp (أول ستكر)
    first = Image.open(folder / "sticker_1.webp")
    first = first.resize((96, 96))
    first.save(folder / "tray.webp", "WEBP")

    # ZIP
    zip_path = folder / f"{sticker_set.name}.zip"

    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(folder / "metadata.json", "metadata.json")
        z.write(folder / "tray.webp", "tray.webp")
        for s in stickers_list:
            z.write(folder / s["image"], s["image"])

    return zip_path


# ====== أوامر ======

@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    await msg.answer("ابعتلي اسم الستكر باك أو ابعت ستكر من الباك وأنا هحولهولك واتساب ✔️")

@dp.message_handler(commands=["convert"])
async def convert_cmd(msg: types.Message):
    name = msg.get_args().strip()
    if not name:
        return await msg.answer("اكتب اسم الباك: /convert <name>")

    await msg.answer("ثانية واحدة بنجيب الباك… ⏳")

    try:
        sticker_set = await bot.get_sticker_set(name)
    except:
        return await msg.answer("❌ مش لاقي الباك ده")

    zip_file = await convert_pack(msg.from_user.id, sticker_set)

    await msg.answer_document(open(zip_file, "rb"), caption="✔️ اتفضل الباك جاهز ZIP")

@dp.message_handler(content_types=types.ContentType.STICKER)
async def sticker_detect(msg: types.Message):
    if msg.sticker.set_name:
        await msg.answer("تمام، بنجيب الباك كله… ⏳")

        sticker_set = await bot.get_sticker_set(msg.sticker.set_name)
        zip_file = await convert_pack(msg.from_user.id, sticker_set)

        await msg.answer_document(open(zip_file, "rb"), caption="✔️ اتفضل الباك جاهز ZIP")
    else:
        await msg.answer("الستكر ده مش تبع باك 🤷‍♂️")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)