from threading import Thread
from pyrogram import enums
from telegram.ext import CommandHandler, CallbackQueryHandler
from pyrogram import enums
from time import sleep
from re import split as re_split

from bot import *
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, auto_delete_upload_message, auto_delete_message
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_url, get_user_task
from bot.helper.ext_utils.timegap import timegap_check
from bot.helper.mirror_utils.download_utils.yt_dlp_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.button_build import ButtonMaker
from telegram import ParseMode, InlineKeyboardButton
from .listener import MirrorLeechListener

listener_dict = {}

def _ytdl(bot, message, isZip=False, isLeech=False):
    mssg = message.text
    user_id = message.from_user.id
    msg_id = message.message_id
    multi = 0
    buttons = ButtonMaker()	
    if FSUB:
        try:
            user = bot.get_chat_member(f"{FSUB_CHANNEL_ID}", message.from_user.id)
            LOGGER.info(user.status)
            if user.status not in ("member", "creator", "administrator", "supergroup"):
                if message.from_user.username:
                    uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.username}</a>'
                else:
                    uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
                buttons = ButtonMaker()
                chat_u = CHANNEL_USERNAME.replace("@", "")
                buttons.buildbutton("👉🏻 CHANNEL LINK 👈🏻", f"https://t.me/{chat_u}")
                help_msg = f"Dᴇᴀʀ {uname},\nYᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴍʏ Cʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ Bᴏᴛ \n\nCʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴇʟᴏᴡ Bᴜᴛᴛᴏɴ ᴛᴏ ᴊᴏɪɴ ᴍʏ Cʜᴀɴɴᴇʟ."
                reply_message = sendMarkup(help_msg, bot, message, buttons.build_menu(2))
                Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
                return reply_message
        except Exception:
            pass
    if BOT_PM and message.chat.type != 'private':
        try:
            msg1 = f'Added your Requested link to Download\n'
            send = bot.sendMessage(message.from_user.id, text=msg1)
            send.delete()
        except Exception as e:
            LOGGER.warning(e)
            bot_d = bot.get_me()
            b_uname = bot_d.username
            uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
            botstart = f"http://t.me/{b_uname}"
            buttons.buildbutton("Click Here to Start Me", f"{botstart}")
            startwarn = f"Dear {uname},\n\n<b>I found that you haven't started me in PM (Private Chat) yet.</b>\n\n" \
                        f"From now on i will give link and leeched files in PM and log channel only"
            reply_message = sendMarkup(startwarn, bot, message, buttons.build_menu(2))
            Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
            return reply_message

    total_task = len(download_dict)
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in SUDO_USERS and user_id not in PAID_USERS:
        if PAID_SERVICE is True:
            if TOTAL_TASKS_LIMIT == total_task:
                return sendMessage(f"<b>Bᴏᴛ Tᴏᴛᴀʟ Tᴀsᴋ Lɪᴍɪᴛ : {TOTAL_TASKS_LIMIT}\nTᴀsᴋs Pʀᴏᴄᴇssɪɴɢ : {total_task}\n#total limit exceed </b>\n#Buy Paid Service", bot ,message)
            if USER_TASKS_LIMIT == get_user_task(user_id):
                return sendMessage(f"<b>Bᴏᴛ Usᴇʀ Tᴀsᴋ Lɪᴍɪᴛ : {USER_TASKS_LIMIT} \nYᴏᴜʀ Tᴀsᴋs : {get_user_task(user_id)}\n#user limit exceed</b>\n#Buy Paid Service", bot ,message)
        else:
            if TOTAL_TASKS_LIMIT == total_task:
                return sendMessage(f"<b>Bᴏᴛ Tᴏᴛᴀʟ Tᴀsᴋ Lɪᴍɪᴛ : {TOTAL_TASKS_LIMIT}\nTᴀsᴋs Pʀᴏᴄᴇssɪɴɢ : {total_task}\n#total limit exceed </b>", bot ,message)
            if USER_TASKS_LIMIT == get_user_task(user_id):
                return sendMessage(f"<b>Bᴏᴛ Usᴇʀ Tᴀsᴋ Lɪᴍɪᴛ : {USER_TASKS_LIMIT} \nYᴏᴜʀ Tᴀsᴋs : {get_user_task(user_id)}\n#user limit exceed</b>", bot ,message)

    if user_id != OWNER_ID and user_id not in SUDO_USERS and user_id not in PAID_USERS:
        time_gap = timegap_check(message)
        if time_gap:
            return
        TIME_GAP_STORE[message.from_user.id] = time()

    link = mssg.split()
    if len(link) > 1:
        link = link[1].strip()
        if link.strip().isdigit():
            multi = int(link)
            link = ''
        elif link.strip().startswith(("|", "pswd:", "opt:")):
            link = ''
    else:
        link = ''

    name = mssg.split('|', maxsplit=1)
    if len(name) > 1:
        if 'opt: ' in name[0] or 'pswd: ' in name[0]:
            name = ''
        else:
            name = name[1]
        if name != '':
            name = re_split('pswd:|opt:', name)[0]
            name = name.strip()
    else:
        name = ''

    pswd = mssg.split(' pswd: ')
    if len(pswd) > 1:
        pswd = pswd[1]
        pswd = pswd.split(' opt: ')[0]
    else:
        pswd = None

    opt = mssg.split(' opt: ')
    if len(opt) > 1:
        opt = opt[1]
    else:
        opt = None

    if message.from_user.username:
        tag = f"@{message.from_user.username}"
    else:
        tag = message.from_user.mention_html(message.from_user.first_name)

    reply_to = message.reply_to_message
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text.split(maxsplit=1)[0].strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)

    if not is_url(link):
        help_msg = "<b>Send link along with command line:</b>"
        help_msg += "\n<code>/cmd</code> link |newname pswd: xx(zip) opt: x:y|x1:y1"
        help_msg += "\n\n<b>By replying to link:</b>"
        help_msg += "\n<code>/cmd</code> |newname pswd: xx(zip) opt: x:y|x1:y1"
        help_msg += "\n\n<b>Options Example:</b> opt: playliststart:^10|matchtitle:S13|writesubtitles:true"
        help_msg += "\n\n<b>Multi links only by replying to first link:</b>"
        help_msg += "\n<code>/cmd</code> 10(number of links). Number should be always before |newname, pswd: and opt:"
        help_msg += "\n\n<b>NOTE:</b> Add `^` before integer, some values must be integer and some string."
        help_msg += " Like playlist_items:10 works with string, so no need to add `^` before the number"
        help_msg += " but playlistend works only with integer so you must add `^` before the number like example above."
        help_msg += "\n\nCheck all arguments from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L178'>FILE</a>."
        reply_message = sendMessage(help_msg, bot, message)
        Thread(target=auto_delete_message, args=(bot, message, reply_message)).start()
        return reply_message

    listener = MirrorLeechListener(bot, message, isZip, isLeech=isLeech, pswd=pswd, tag=tag)
    buttons = ButtonMaker()
    best_video = "bv*+ba/b"
    best_audio = "ba/b"
    ydl = YoutubeDLHelper(listener)
    try:
        result = ydl.extractMetaData(link, name, opt, True)
    except Exception as e:
        msg = str(e).replace('<', ' ').replace('>', ' ')
        return sendMessage(tag + " " + msg, bot, message)
    formats_dict = {}
    if 'entries' in result:
        for i in ['144', '240', '360', '480', '720', '1080', '1440', '2160']:
            video_format = f"bv*[height<={i}][ext=mp4]+ba[ext=m4a]/b[height<={i}]"
            b_data = f"{i}|mp4"
            formats_dict[b_data] = video_format
            buttons.sbutton(f"{i}-mp4", f"qu {msg_id} {b_data} t")
            video_format = f"bv*[height<={i}][ext=webm]+ba/b[height<={i}]"
            b_data = f"{i}|webm"
            formats_dict[b_data] = video_format
            buttons.sbutton(f"{i}-webm", f"qu {msg_id} {b_data} t")
        buttons.sbutton("MP3", f"qu {msg_id} mp3 t")
        buttons.sbutton("Best Videos", f"qu {msg_id} {best_video} t")
        buttons.sbutton("Best Audios", f"qu {msg_id} {best_audio} t")
        buttons.sbutton("Cancel", f"qu {msg_id} cancel")
        YTBUTTONS = buttons.build_menu(3)
        listener_dict[msg_id] = [listener, user_id, link, name, YTBUTTONS, opt, formats_dict]
        bmsg = sendMarkup('Choose Playlist Videos Quality:', bot, message, YTBUTTONS)
    else:
        formats = result.get('formats')
        formats_dict = {}
        if formats is not None:
            for frmt in formats:
                if frmt.get('tbr'):

                    format_id = frmt['format_id']

                    if frmt.get('filesize'):
                        size = frmt['filesize']
                    elif frmt.get('filesize_approx'):
                        size = frmt['filesize_approx']
                    else:
                        size = 0

                    if frmt.get('height'):
                        height = frmt['height']
                        ext = frmt['ext']
                        fps = frmt['fps'] if frmt.get('fps') else ''
                        b_name = f"{height}p{fps}-{ext}"
                        if ext == 'mp4':
                            v_format = f"bv*[format_id={format_id}]+ba[ext=m4a]/b[height={height}]"
                        else:
                            v_format = f"bv*[format_id={format_id}]+ba/b[height={height}]"
                    elif frmt.get('video_ext') == 'none' and frmt.get('acodec') != 'none':
                        b_name = f"{frmt['acodec']}-{frmt['ext']}"
                        v_format = f"ba[format_id={format_id}]"
                    else:
                        continue

                    if b_name in formats_dict:
                        formats_dict[b_name][str(frmt['tbr'])] = [size, v_format]
                    else:
                        subformat = {}
                        subformat[str(frmt['tbr'])] = [size, v_format]
                        formats_dict[b_name] = subformat

            for b_name, d_dict in formats_dict.items():
                if len(d_dict) == 1:
                    tbr, v_list = list(d_dict.items())[0]
                    buttonName = f"{b_name} ({get_readable_file_size(v_list[0])})"
                    buttons.sbutton(buttonName, f"qu {msg_id} {b_name}|{tbr}")
                else:
                    buttons.sbutton(b_name, f"qu {msg_id} dict {b_name}")
        buttons.sbutton("MP3", f"qu {msg_id} mp3")
        buttons.sbutton("Best Video", f"qu {msg_id} {best_video}")
        buttons.sbutton("Best Audio", f"qu {msg_id} {best_audio}")
        buttons.sbutton("Cancel", f"qu {msg_id} cancel")
        YTBUTTONS = buttons.build_menu(2)
        listener_dict[msg_id] = [listener, user_id, link, name, YTBUTTONS, opt, formats_dict]
        bmsg = sendMarkup('Choose Video Quality:', bot, message, YTBUTTONS)

    Thread(target=_auto_cancel, args=(bmsg, msg_id)).start()
    if multi > 1:
        sleep(4)
        nextmsg = type('nextmsg', (object, ), {'chat_id': message.chat_id, 'message_id': message.reply_to_message.message_id + 1})
        ymsg = message.text.split(maxsplit=2)
        ymsg[1] = f"{multi - 1}"
        nextmsg = sendMessage(" ".join(ymsg), bot, nextmsg)
        nextmsg.from_user.id = message.from_user.id
        sleep(4)
        Thread(target=_ytdl, args=(bot, nextmsg, isZip, isLeech)).start()

def _qual_subbuttons(task_id, b_name, msg):
    buttons = ButtonMaker()
    task_info = listener_dict[task_id]
    formats_dict = task_info[6]
    for tbr, d_data in formats_dict[b_name].items():
        buttonName = f"{tbr}K ({get_readable_file_size(d_data[0])})"
        buttons.sbutton(buttonName, f"qu {task_id} {b_name}|{tbr}")
    buttons.sbutton("Back", f"qu {task_id} back")
    buttons.sbutton("Cancel", f"qu {task_id} cancel")
    SUBBUTTONS = buttons.build_menu(2)
    editMessage(f"Choose Bit rate for <b>{b_name}</b>:", msg, SUBBUTTONS)

def _mp3_subbuttons(task_id, msg, playlist=False):
    buttons = ButtonMaker()
    audio_qualities = [64, 128, 320]
    for q in audio_qualities:
        if playlist:
            i = 's'
            audio_format = f"ba/b-{q} t"
        else:
            i = ''
            audio_format = f"ba/b-{q}"
        buttons.sbutton(f"{q}K-mp3", f"qu {task_id} {audio_format}")
    buttons.sbutton("Back", f"qu {task_id} back")
    buttons.sbutton("Cancel", f"qu {task_id} cancel")
    SUBBUTTONS = buttons.build_menu(2)
    editMessage(f"Choose Audio{i} Bitrate:", msg, SUBBUTTONS)

def select_format(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    msg = query.message
    data = data.split(" ")
    task_id = int(data[1])
    try:
        task_info = listener_dict[task_id]
    except:
        return editMessage("This is an old task", msg)
    uid = task_info[1]
    if user_id != uid and not CustomFilters._owner_query(user_id):
        return query.answer(text="This task is not for you!", show_alert=True)
    elif data[2] == "dict":
        query.answer()
        b_name = data[3]
        _qual_subbuttons(task_id, b_name, msg)
        return
    elif data[2] == "back":
        query.answer()
        return editMessage('Choose Video Quality:', msg, task_info[4])
    elif data[2] == "mp3":
        query.answer()
        if len(data) == 4:
            playlist = True
        else:
            playlist = False
        _mp3_subbuttons(task_id, msg, playlist)
        return
    elif data[2] == "cancel":
        query.answer()
        editMessage('Task has been cancelled.', msg)
    else:
        query.answer()
        listener = task_info[0]
        link = task_info[2]
        name = task_info[3]
        opt = task_info[5]
        qual = data[2]
        if len(data) == 4:
            playlist = True
            if '|' in qual:
                qual = task_info[6][qual]
        else:
            playlist = False
            if '|' in qual:
                b_name, tbr = qual.split('|')
                qual = task_info[6][b_name][tbr][1]
        ydl = YoutubeDLHelper(listener)
        Thread(target=ydl.add_download, args=(link, f'{DOWNLOAD_DIR}{task_id}', name, qual, playlist, opt)).start()
        query.message.delete()
    del listener_dict[task_id]

def _auto_cancel(msg, msg_id):
    sleep(120)
    try:
        del listener_dict[msg_id]
        editMessage('Timed out! Task has been cancelled.', msg)
    except:
        pass

def ytdl(update, context):
    _ytdl(context.bot, update.message)

def ytdlZip(update, context):
    _ytdl(context.bot, update.message, True)

def ytdlleech(update, context):
    _ytdl(context.bot, update.message, isLeech=True)

def ytdlZipleech(update, context):
    _ytdl(context.bot, update.message, True, True)

if WATCH_ENABLED:
    ytdl_handler = CommandHandler(BotCommands.WatchCommand, ytdl,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ytdl_zip_handler = CommandHandler(BotCommands.ZipWatchCommand, ytdlZip,
                                        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ytdl_leech_handler = CommandHandler(BotCommands.LeechWatchCommand, ytdlleech,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ytdl_zip_leech_handler = CommandHandler(BotCommands.LeechZipWatchCommand, ytdlZipleech,
                                        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)

else:
    ytdl_handler = CommandHandler(BotCommands.WatchCommand, ytdl,
                                    filters=CustomFilters.owner_filter | CustomFilters.authorized_user, run_async=True)
    ytdl_zip_handler = CommandHandler(BotCommands.ZipWatchCommand, ytdlZip,
                                        filters=CustomFilters.owner_filter | CustomFilters.authorized_user, run_async=True)
    ytdl_leech_handler = CommandHandler(BotCommands.LeechWatchCommand, ytdlleech,
                                    filters=CustomFilters.owner_filter | CustomFilters.authorized_user, run_async=True)
    ytdl_zip_leech_handler = CommandHandler(BotCommands.LeechZipWatchCommand, ytdlZipleech,
                                        filters=CustomFilters.owner_filter | CustomFilters.authorized_user, run_async=True)

quality_handler = CallbackQueryHandler(select_format, pattern="qu", run_async=True)

dispatcher.add_handler(ytdl_handler)
dispatcher.add_handler(ytdl_zip_handler)
dispatcher.add_handler(ytdl_leech_handler)
dispatcher.add_handler(ytdl_zip_leech_handler)
dispatcher.add_handler(quality_handler)