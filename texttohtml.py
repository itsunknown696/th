from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import html
import os
from datetime import datetime

# Conversation states
FILENAME, TITLE, GLITCH, CLASS, HEADER, METHOD_CHOICE, BUTTON_PAIRS, LINE_RANGE = range(8)

# Configuration
BOT_TOKEN = "7782085620:AAENkSow5fgy0UdPr_75exMmK_ZHU2J9rUQ"
LOG_CHANNEL_ID = -1002278484608
user_data = {}

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "📄 Welcome to HTML Generator Bot!\n\n"
        "Use /html to create beautiful HTML pages\n"
        "Other commands:\n"
        "/pw - PW Link Changer\n"
        "/start - Allen Link Extractor"
    )

def start_process(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("📄 Please send me the filename you want for your HTML file (without .html extension)\n\nExample: my_lectures")
    return FILENAME

def get_filename(update: Update, context: CallbackContext) -> int:
    filename = update.message.text.strip()
    if not filename:
        update.message.reply_text("❌ Invalid filename. Please try again.")
        return FILENAME
    
    user_data[update.effective_user.id] = {
        'filename': filename,
        'username': update.effective_user.username or 'No username',
        'first_name': update.effective_user.first_name or '',
        'last_name': update.effective_user.last_name or ''
    }
    update.message.reply_text("Send Me The Text That You Want To Be Page Title")
    return TITLE

def get_title(update: Update, context: CallbackContext) -> int:
    user_data[update.effective_user.id]['title'] = update.message.text
    update.message.reply_text("Now Send Me Your Name")
    return GLITCH

def get_glitch_text(update: Update, context: CallbackContext) -> int:
    user_data[update.effective_user.id]['glitch'] = update.message.text
    update.message.reply_text("Now Send Coaching Platform Name")
    return CLASS

def get_class(update: Update, context: CallbackContext) -> int:
    user_data[update.effective_user.id]['class'] = update.message.text
    update.message.reply_text("Now Send Me Sir Name And Chapter Name")
    return HEADER

def get_header(update: Update, context: CallbackContext) -> int:
    user_data[update.effective_user.id]['header'] = update.message.text
    update.message.reply_text(
        "📌 How do you want to send button links?\n\n"
        "1️⃣ Manual Input – Send text:link pairs (one per line)\n"
        "2️⃣ Upload TXT File – Send a .txt file with text:link pairs\n\n"
        "Reply with 1 or 2"
    )
    return METHOD_CHOICE

def handle_method_choice(update: Update, context: CallbackContext) -> int:
    choice = update.message.text.strip()

    if choice == "1":
        update.message.reply_text(
            "📝 Send your button texts & links in this format (one per line):\n\n"
            "Example:\n"
            "Lecture 1:https://example.com/1\n"
            "Lecture 1:https://example.com/2"
        )
        return BUTTON_PAIRS

    elif choice == "2":
        update.message.reply_text("📤 Please upload a .txt file containing text:link pairs (one per line).\n\n"
                                "Then send the line range you want to process in format:\n"
                                "from-to\n\n"
                                "Example: 1-10 (will process lines 1 to 10)")
        return LINE_RANGE

    else:
        update.message.reply_text("❌ Invalid choice. Please reply with 1 or 2.")
        return METHOD_CHOICE

def get_line_range(update: Update, context: CallbackContext) -> int:
    if not update.message.document:
        update.message.reply_text("❌ Please upload a .txt file first.")
        return LINE_RANGE
    
    user_data[update.effective_user.id]['document'] = update.message.document
    update.message.reply_text("📝 Now send the line range you want to process (e.g. 1-10):")
    return BUTTON_PAIRS

def get_button_pairs(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    data = user_data[user_id]

    if 'document' in data:
        if '-' not in update.message.text:
            update.message.reply_text("❌ Invalid format. Please use format: from-to (e.g. 1-10)")
            return BUTTON_PAIRS
        
        try:
            from_line, to_line = map(int, update.message.text.split('-'))
            if from_line < 1 or to_line < from_line:
                raise ValueError
        except:
            update.message.reply_text("❌ Invalid line range. Please try again.")
            return BUTTON_PAIRS

        file = data['document'].get_file()
        downloaded_file = file.download()

        with open(downloaded_file, 'r', encoding='utf-8') as f:
            all_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        os.remove(downloaded_file)
        from_idx = max(0, from_line - 1)
        to_idx = min(len(all_lines), to_line)
        lines = all_lines[from_idx:to_idx]
        del data['document']

    elif update.message.text:
        lines = [line.strip() for line in update.message.text.split('\n') if line.strip()]
    
    else:
        update.message.reply_text("❌ No pairs found. Please try again.")
        return BUTTON_PAIRS

    button_texts = []
    button_links = []

    for line in lines:
        if ':' not in line:
            update.message.reply_text(f"❌ Invalid format in line: '{line}'. Use `text:link` format.")
            return BUTTON_PAIRS

        text, link = line.split(':', 1)
        text = text.strip()
        link = link.strip()
        
        if 'media-cdn.classplusapp.com' in link:
            link = f"https://master-api-v3.vercel.app/nomis-player?url={link}"

        button_texts.append(text)
        button_links.append(link)

    if not button_texts:
        update.message.reply_text("❌ No valid button pairs found. Try again.")
        return BUTTON_PAIRS

    data['button_texts'] = button_texts
    data['button_links'] = button_links
    generate_html(update, user_id)
    return ConversationHandler.END

def generate_html(update: Update, user_id: int) -> None:
    data = user_data[user_id]
    
    buttons_html = ""
    for text, link in zip(data['button_texts'], data['button_links']):
        buttons_html += f"""
           <li><a href="{html.escape(link)}" target="_blank"><button class="lecture-button">{html.escape(text)}</button></a></li>"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(data['title'])}</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Cyberpunk Neon Theme */
        :root {{
          --neon-purple: #bc13fe;
          --neon-pink: #ff00ff;
          --neon-blue: #00ffff;
          --neon-green: #00ff41;
          --dark-purple: #8e44ad;
          --deep-black: #000000;
          --dark-gray: #121212;
          --light-gray: #bdc3c7;
          --matrix-green: #0f0;
        }}

        body {{
          margin: 0;
          padding: 0;
          font-family: 'Orbitron', 'Rajdhani', sans-serif;
          background-color: var(--deep-black);
          color: var(--light-gray);
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          flex-direction: column;
          overflow-x: hidden;
          position: relative;
        }}

        /* Japanese Kanji Rain Background */
        .kanji-rain {{
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: -1;
          overflow: hidden;
        }}

        .kanji {{
          position: absolute;
          color: rgba(0, 255, 65, 0.3);
          font-size: 20px;
          writing-mode: vertical-rl;
          text-orientation: upright;
          animation: fall linear infinite;
          text-shadow: 0 0 5px var(--matrix-green);
          user-select: none;
          z-index: -1;
        }}

        @keyframes fall {{
          to {{
            transform: translateY(100vh);
          }}
        }}

        /* Cyberpunk grid overlay */
        body::before {{
          content: "";
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: 
            linear-gradient(rgba(142, 68, 173, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(142, 68, 173, 0.05) 1px, transparent 1px);
          background-size: 30px 30px;
          z-index: -1;
          pointer-events: none;
        }}

        .container {{
          text-align: center;
          background: rgba(0, 0, 0, 0.85);
          padding: 40px 30px;
          border-radius: 0;
          box-shadow: 
            0 0 25px var(--neon-purple),
            0 0 50px rgba(188, 19, 254, 0.3);
          max-width: 500px;
          width: 90%;
          margin-bottom: 20px;
          backdrop-filter: blur(5px);
          border: 1px solid var(--neon-purple);
          position: relative;
          overflow: hidden;
          transition: transform 0.3s ease;
          border-image: linear-gradient(45deg, var(--neon-purple), var(--neon-blue), var(--neon-pink)) 1;
          z-index: 1;
        }}

        .container:hover {{
          transform: translateY(-5px);
          box-shadow: 
            0 0 35px var(--neon-purple),
            0 0 70px rgba(188, 19, 254, 0.4);
        }}

        /* Cyberpunk corner accents */
        .container::before, .container::after {{
          content: "";
          position: absolute;
          width: 30px;
          height: 30px;
          border: 2px solid var(--neon-purple);
          transition: all 0.3s ease;
        }}

        .container::before {{
          top: 0;
          left: 0;
          border-right: none;
          border-bottom: none;
        }}

        .container::after {{
          bottom: 0;
          right: 0;
          border-left: none;
          border-top: none;
        }}

        .container:hover::before, .container:hover::after {{
          width: 50px;
          height: 50px;
          border-color: var(--neon-blue);
        }}

        h1 {{
          font-size: 3.2rem;
          margin-bottom: 5px;
          color: var(--neon-purple);
          text-shadow: 
            0 0 10px var(--neon-purple),
            0 0 20px var(--neon-purple);
          letter-spacing: 3px;
          font-weight: 700;
          position: relative;
          animation: textFlicker 3s infinite alternate;
          text-transform: uppercase;
        }}

        @keyframes textFlicker {{
          0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {{
            text-shadow: 
              0 0 10px var(--neon-purple),
              0 0 20px var(--neon-purple),
              0 0 30px var(--neon-purple);
          }}
          20%, 24%, 55% {{
            text-shadow: none;
            color: var(--neon-blue);
          }}
        }}

        h2 {{
          font-size: 1.8rem;
          margin-bottom: 25px;
          color: var(--light-gray);
          letter-spacing: 2px;
          position: relative;
          text-transform: uppercase;
        }}

        h2::after {{
          content: "";
          display: block;
          width: 100px;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--neon-purple), transparent);
          margin: 15px auto;
        }}

        h3 {{
          font-size: 1.5rem;
          margin-top: 0;
          color: var(--light-gray);
          letter-spacing: 2px;
          text-transform: uppercase;
          position: relative;
        }}

        h3::before {{
          content: ">> ";
          color: var(--neon-green);
        }}

        h3::after {{
          content: " <<";
          color: var(--neon-green);
        }}

        .lecture-list {{
          list-style: none;
          padding: 0;
          margin: 0;
        }}

        .lecture-list li {{
          margin: 15px 0;
          position: relative;
        }}

        .lecture-list a {{
          text-decoration: none;
        }}

        .lecture-button {{
          display: inline-block;
          padding: 12px 40px;
          background: linear-gradient(135deg, var(--dark-gray), var(--dark-purple));
          color: white;
          font-size: 1.2rem;
          font-weight: 600;
          border: none;
          border-radius: 0;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 
            0 0 10px rgba(188, 19, 254, 0.3),
            inset 0 0 5px rgba(255, 255, 255, 0.1);
          position: relative;
          overflow: hidden;
          letter-spacing: 1px;
          clip-path: polygon(
            0 0,
            100% 0,
            100% calc(100% - 10px),
            calc(100% - 10px) 100%,
            0 100%
          );
          text-transform: uppercase;
          z-index: 1;
        }}

        .lecture-button::before {{
          content: "";
          position: absolute;
          top: -2px;
          left: -2px;
          right: -2px;
          bottom: -2px;
          background: linear-gradient(45deg, 
            var(--neon-purple), 
            var(--neon-blue), 
            var(--neon-pink));
          z-index: -1;
          background-size: 200% 200%;
          animation: gradientBorder 3s ease infinite;
          opacity: 0;
          transition: opacity 0.3s ease;
          clip-path: polygon(
            0 0,
            100% 0,
            100% calc(100% - 10px),
            calc(100% - 10px) 100%,
            0 100%
          );
        }}

        .lecture-button:hover::before {{
          opacity: 1;
        }}

        .lecture-button:hover {{
          transform: translateY(-3px);
          box-shadow: 
            0 0 20px rgba(188, 19, 254, 0.5),
            inset 0 0 10px rgba(255, 255, 255, 0.2);
          background: linear-gradient(135deg, var(--dark-purple), var(--dark-gray));
          color: var(--neon-green);
        }}

        .lecture-button::after {{
          content: "";
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
          transition: 0.5s;
        }}

        .lecture-button:hover::after {{
          left: 100%;
        }}

        @keyframes gradientBorder {{
          0% {{ background-position: 0% 50%; }}
          50% {{ background-position: 100% 50%; }}
          100% {{ background-position: 0% 50%; }}
        }}

        .footer {{
          text-align: center;
          font-size: 0.9rem;
          color: var(--light-gray);
          margin-top: 20px;
          letter-spacing: 1px;
          text-transform: uppercase;
        }}

        .footer span {{
          color: var(--neon-purple);
          font-weight: 600;
        }}

        .social-link {{
          color: var(--neon-purple);
          text-decoration: none;
          margin: 0 5px;
          transition: all 0.3s ease;
          position: relative;
          font-weight: 600;
        }}

        .social-link:hover {{
          color: var(--neon-blue);
          text-shadow: 0 0 10px var(--neon-blue);
        }}

        .social-link::after {{
          content: "";
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 0;
          height: 1px;
          background: var(--neon-blue);
          transition: width 0.3s ease;
        }}

        .social-link:hover::after {{
          width: 100%;
        }}

        .social-link img {{
          vertical-align: middle;
          margin-right: 5px;
          filter: drop-shadow(0 0 5px var(--neon-purple));
          transition: filter 0.3s ease;
        }}

        .social-link:hover img {{
          filter: drop-shadow(0 0 5px var(--neon-blue));
        }}

        .back-to-top {{
          position: fixed;
          bottom: 20px;
          right: 20px;
          background: var(--dark-gray);
          color: var(--neon-purple);
          border: 1px solid var(--neon-purple);
          border-radius: 50%;
          width: 50px;
          height: 50px;
          cursor: pointer;
          box-shadow: 
            0 0 10px var(--neon-purple),
            inset 0 0 5px var(--neon-purple);
          display: none;
          transition: all 0.3s ease;
          font-size: 1.5rem;
          z-index: 100;
        }}

        .back-to-top:hover {{
          background: var(--neon-purple);
          color: var(--deep-black);
          box-shadow: 
            0 0 20px var(--neon-purple),
            inset 0 0 10px var(--deep-black);
          transform: scale(1.1);
          border-color: var(--neon-blue);
        }}

        /* Cyberpunk glitch effect */
        .glitch {{
          position: relative;
        }}

        .glitch::before, .glitch::after {{
          content: attr(data-text);
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          opacity: 0.8;
        }}

        .glitch::before {{
          color: var(--neon-blue);
          animation: glitch-effect 3s infinite;
          z-index: -1;
        }}

        .glitch::after {{
          color: var(--neon-pink);
          animation: glitch-effect 2s infinite reverse;
          z-index: -2;
        }}

        @keyframes glitch-effect {{
          0% {{ transform: translate(0); }}
          20% {{ transform: translate(-3px, 3px); }}
          40% {{ transform: translate(-3px, -3px); }}
          60% {{ transform: translate(3px, 3px); }}
          80% {{ transform: translate(3px, -3px); }}
          100% {{ transform: translate(0); }}
        }}

        /* Responsive adjustments */
        @media (max-width: 768px) {{
          h1 {{
            font-size: 2.5rem;
          }}
          
          h2 {{
            font-size: 1.5rem;
          }}
          
          .lecture-button {{
            padding: 10px 30px;
            font-size: 1rem;
          }}
          
          .footer {{
            font-size: 0.8rem;
          }}
        }}
    </style>
</head>
<body>
    <div class="kanji-rain" id="kanjiRain"></div>
    
    <div class="container">
        <h1 class="glitch" data-text="{html.escape(data['glitch'])}">{html.escape(data['glitch'])}</h1><br>
        <h2>{html.escape(data['class'])}</h2><br>
        <h3>{html.escape(data['header'])}</h3><br>
        <ul class="lecture-list">
           {buttons_html}
           <li><a href="https://youtu.be/Tba8arFqBFw?si=q01kKfamn4rKW_er" target="_blank"><button class="lecture-button">How To Process Links</button></a></li>
        </ul>
    </div>

    <div class="footer">
        <p>Leaked by <span>Nomis</span> | From <span>IIT School Institute ({html.escape(data['class'])})</span> | <br><br><br>
            <a href="https://t.me/ItsNomis" target="_blank" class="social-link">
                <img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png" alt="Telegram" width="16"> Telegram
            </a> | 
            <a href="http://www.aboutnomis.carrd.co" target="_blank" class="social-link">
                <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="Website" width="16"> Website
            </a>
        </p>
    </div>

    <button class="back-to-top" onclick="scrollToTop()">⬆️</button>

    <script>
        // Back to Top Button functionality
        const backToTopBtn = document.querySelector('.back-to-top');

        window.addEventListener('scroll', () => {{
          backToTopBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
        }});

        function scrollToTop() {{
          window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // Japanese Kanji Rain Animation
        const kanjiCharacters = ['侍', '忍', '龍', '鬼', '刀', '影', '闇', '光', '電', '夢', '愛', '戦', '死', '生', '風', '火', '水', '土', '空', '心'];
        const kanjiContainer = document.getElementById('kanjiRain');
        const kanjiCount = 50;

        function createKanji() {{
          const kanji = document.createElement('div');
          kanji.className = 'kanji';
          kanji.textContent = kanjiCharacters[Math.floor(Math.random() * kanjiCharacters.length)];
          kanji.style.left = Math.random() * 100 + 'vw';
          kanji.style.animationDuration = (Math.random() * 5 + 3) + 's';
          kanji.style.opacity = Math.random() * 0.5 + 0.1;
          kanji.style.fontSize = (Math.random() * 10 + 16) + 'px';
          kanji.style.zIndex = -1;
          kanjiContainer.appendChild(kanji);
          
          setTimeout(() => {{
            kanji.remove();
          }}, 8000);
        }}

        // Initialize kanji rain  
        function initKanjiRain() {{
          for (let i = 0; i < kanjiCount; i++) {{
            setTimeout(createKanji, i * 200);
          }}
          setInterval(createKanji, 300);
        }}

        // Initialize everything when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {{
          initKanjiRain();
          
          // Add any other initialization code here
          backToTopBtn.style.display = 'none'; // Hide back-to-top button initially
        }});
    </script>
</body>
</html>"""
    
    filename = f"{data['filename']}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    caption = (f"📄 New HTML File Generated\n\n"
             f"👤 User: {data['first_name']} {data['last_name']}\n"
             f"🆔 ID: {user_id}\n"
             f"🔗 Username: @{data['username']}\n"
             f"📛 Title: {data['title']}\n"
             f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
             f"🔢 Buttons: {len(data['button_texts'])}")
    
    with open(filename, 'rb') as f:
        update.message.reply_document(
            document=f,
            filename=filename,
            caption=caption
        )
    
    try:
        log_bot = Bot(token=BOT_TOKEN)
        log_message = (
            f"📄 New HTML File Generated\n\n"
            f"👤 User: {data['first_name']} {data['last_name']}\n"
            f"🆔 ID: {user_id}\n"
            f"🔗 Username: @{data['username']}\n"
            f"📛 Title: {data['title']}\n"
            f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔢 Buttons: {len(data['button_texts'])}"
        )
        
        with open(filename, 'rb') as f:
            log_bot.send_document(
                chat_id=LOG_CHANNEL_ID,
                document=f,
                filename=f"user_{user_id}_{filename}",
                caption=log_message
            )
    except Exception as e:
        print(f"Failed to send log: {e}")
    
    os.remove(filename)
    del user_data[user_id]

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.')
    if update.effective_user.id in user_data:
        del user_data[update.effective_user.id]
    return ConversationHandler.END

def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Add regular commands
    dispatcher.add_handler(CommandHandler("start", start))

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('html', start_process)],
        states={
            FILENAME: [MessageHandler(Filters.text & ~Filters.command, get_filename)],
            TITLE: [MessageHandler(Filters.text & ~Filters.command, get_title)],
            GLITCH: [MessageHandler(Filters.text & ~Filters.command, get_glitch_text)],
            CLASS: [MessageHandler(Filters.text & ~Filters.command, get_class)],
            HEADER: [MessageHandler(Filters.text & ~Filters.command, get_header)],
            METHOD_CHOICE: [MessageHandler(Filters.text & ~Filters.command, handle_method_choice)],
            LINE_RANGE: [MessageHandler(Filters.document, get_line_range)],
            BUTTON_PAIRS: [
                MessageHandler(Filters.text & ~Filters.command, get_button_pairs),
                MessageHandler(Filters.document, get_button_pairs)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()