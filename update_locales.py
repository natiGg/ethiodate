import re

with open('src/bot/locales.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Amharic ask_photos specifically
amharic_ask = r'"ask_photos": "እባክዎ ቢያንስ 2-3 ግልፅ የሆኑ ፎቶዎችዎን \(አንድ በአንድ\) ይላኩልን።\nፎቶዎችን ልከው ሲጨርሱ /done ብለው ይፃፉ።",'

replacement = '"ask_photos": "እባክዎ ቢያንስ 2 ግልፅ የሆኑ ፎቶዎችዎን (አንድ በአንድ) ይላኩልን።",\n        "photo_received_need_more": "ፎቶዎ ደርሶናል! 📸 እባክዎ ቢያንስ 1 ተጨማሪ ፎቶ ይላኩ።",\n        "photo_received_done": "ፎቶዎ ደርሶናል! 📸 ተጨማሪ ፎቶዎችን መላክ ይችላሉ፣ ወይም ምዝገባዎን ማጠናቀቅ ይችላሉ።",\n        "btn_finish_register": "✅ ምዝገባውን አጠናቅ",'

new_content = content.replace(amharic_ask, replacement)

with open('src/bot/locales.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
