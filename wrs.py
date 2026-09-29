import asyncio
import os, sys
import json
import re
import string
import urllib.parse
import requests
import time
import random
import uuid
import base64
import secrets
import hashlib

from urllib.parse import urlparse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import RequestWebViewRequest
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

print("🚀 [DEBUG] Script dimulai!", flush=True)

# ==================== DEVICE CONFIG GENERATOR ====================
def config_device():
    devices = [
        {"model": "SM-G998B", "android": "13", "chrome_base": "114"},
        {"model": "SM-S918B", "android": "14", "chrome_base": "121"},
        {"model": "2201116SG", "android": "13", "chrome_base": "115"},
        {"model": "23124RA7EO", "android": "14", "chrome_base": "122"},
        {"model": "Pixel 7", "android": "14", "chrome_base": "123"},
        {"model": "CPH2447", "android": "13", "chrome_base": "116"},
        {"model": "V2250", "android": "13", "chrome_base": "117"},
    ]
    dev = random.choice(devices)
    chrome_ver = f"{dev['chrome_base']}.{random.randint(0, 5)}.{random.randint(1000, 9999)}.{random.randint(10, 99)}"
    tg_ver = f"{random.randint(9, 10)}.{random.randint(0, 5)}.{random.randint(0, 5)}"
    
    return {
        "user_agent": f"Mozilla/5.0 (Linux; Android {dev['android']}; {dev['model']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36 Telegram-Android/{tg_ver}",
        "device_model": dev["model"],
        "system_version": f"Android {dev['android']}",
        "app_version": tg_ver,
        "lang_code": "en"
    }

# ==================== KONFIGURASI TARGET ====================
RAW_TARGETS = [
    {"name": "MNAC", "bot": "Miniappcrypto_bot", "url": "https://linksfly.link", "skip": {"GT", "FEY"}, "filter": ["ltc"], "ref": ""},
    {"name": "MNAF", "bot": "MiniappFaucetsbot", "url": "https://mrappswala.com", "skip": {"GT", "FEY"}, "filter": ["ltc"], "ref": ""},
    {"name": "VIPC", "bot": "VipcoinFaucet_bot", "url": "https://vipcoinfaucet.com", "skip": {"GT", "FEY"}, "filter": ["ltc"], "ref": ""},
    {"name": "EWRS", "bot": "EarncryptowrsBot", "url": "https://earncryptowrs.in", "skip": {"GT", "FEY"}, "filter": ["ltc"], "ref": "ref_1106"},
    {"name": "GLEE", "bot": "gamerleebot", "url": "https://gamerlee.com", "skip": {"GT"}, "filter": ["ltc"], "ref": ""}
]

TARGETS = []
for t in RAW_TARGETS:
    cfg = config_device()
    TARGETS.append({"name": t["name"], "bot_username": t["bot"], "url": t["url"], "skip_coins": t["skip"], "coins_filter": t["filter"], "ref_code": t.get("ref", ""), **cfg})

API_ID = 34017330
API_HASH = 'f37aab7f8d68ce67f1d581a03f3129b9'

# ==================== COOLDOWN & BATCH CONFIG ====================
WORK_MIN_MINUTES, WORK_MAX_MINUTES = 45, 50
REST_MIN_MINUTES, REST_MAX_MINUTES = 260, 360
COUNTDOWN_INTERVAL = 30 * 60
CLAIM_DELAY, SAFETY_MIN, SAFETY_MAX = 15, 3, 5
PER_VISIT_LIMIT, PER_VISIT_MIN_MIN, PER_VISIT_MAX_MIN = 10, 3, 4
GLOBAL_LIMIT, GLOBAL_MIN_MIN, GLOBAL_MAX_MIN = 10, 3, 4
FAUCET_BATCH_MIN, FAUCET_BATCH_MAX = 100, 200

target_state = {}

def init_target_state(account_key, target_name, username="Unknown"):
    key = f"{account_key}_{target_name}"
    if key not in target_state:
        target_state[key] = {
            "account_key": account_key, "target_name": target_name, "account_username": username,
            "session": None, "init_data": None, "uid": None, "need_relogin": False, "is_dead": False, 
            "filter_reset_done": False, "cycle_start": time.monotonic(), 
            "work_seconds": random.randint(WORK_MIN_MINUTES, WORK_MAX_MINUTES) * 60,
            "visit_success": 0, "global_counter": 0, "batch_faucet_count": 0, 
            "current_batch_size": random.randint(FAUCET_BATCH_MIN, FAUCET_BATCH_MAX),
            "coin_exhausted": set(), "coin_skip_until": {}
        }
    return target_state[key]

async def async_get(session, url, **kwargs): return await asyncio.to_thread(session.get, url, **kwargs)
async def async_post(session, url, **kwargs): return await asyncio.to_thread(session.post, url, **kwargs)

def parse_telegram_user(init_data: str) -> dict:
    try:
        user_param = urllib.parse.parse_qs(init_data).get('user', [None])[0]
        return json.loads(user_param) if user_param else {}
    except Exception: return {}

def is_setup_page(html: str) -> bool:
    return bool(html and '/app/setup/account' in html and 'name="wallet"' in html and 'name="username"' in html)

def get_aes_key(raw_key):
    return hashlib.sha256(raw_key.encode()).digest()

def decrypt_data(encrypted_str, key):
    iv_b64, ct_b64 = encrypted_str.split(':')
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ct_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode('utf-8')

# ==================== MULTI-ACCOUNT JSON MANAGER (DEBUG MODE) ====================
async def get_all_authorized_clients_from_json():
    print("🔍 [DEBUG 1] Checking ENCRYPTION_KEY...", flush=True)
    raw_key = os.environ.get("ENCRYPTION_KEY")
    if not raw_key:
        print("[!] ❌ ENCRYPTION_KEY environment variable not set!", flush=True)
        return []
    print("✅ [DEBUG 2] ENCRYPTION_KEY found.", flush=True)
        
    print("🔍 [DEBUG 3] Checking full.json existence...", flush=True)
    if not os.path.exists("full.json"):
        print("[!] ❌ full.json not found!", flush=True)
        return []
    print("✅ [DEBUG 4] full.json exists.", flush=True)
    
    try:
        print("🔍 [DEBUG 5] Attempting to read and parse full.json...", flush=True)
        with open("full.json", "r") as f:
            accounts = json.load(f)
        print(f"✅ [DEBUG 6] Successfully parsed full.json. Found {len(accounts)} accounts.", flush=True)
    except json.JSONDecodeError as e:
        print(f"[!] ❌ full.json is NOT valid JSON! Error: {e}", flush=True)
        return []
    except Exception as e:
        print(f"[!] ❌ Failed to read full.json: {e}", flush=True)
        return []
        
    if not accounts:
        print("[!] ❌ No accounts found in full.json!", flush=True)
        return []
        
    print(f"[*] Ditemukan {len(accounts)} akun di full.json. Memverifikasi...\n", flush=True)
    active_clients = []
    
    try:
        aes_key = get_aes_key(raw_key)
        print("✅ [DEBUG 7] AES Key generated.", flush=True)
    except Exception as e:
        print(f"[!] ❌ Failed to generate AES key: {e}", flush=True)
        return []
    
    for account_key, data in accounts.items():
        try:
            print(f"[*] Memproses akun: {account_key}...", flush=True)
            
            if "sess" not in data:
                print(f"  [❌] Key 'sess' not found for {account_key}. Skipping.", flush=True)
                continue
                
            print(f"  [⏳] Decrypting session for {account_key}...", flush=True)
            decrypted_session = decrypt_data(data["sess"], aes_key)
            print(f"  [✅] Decryption successful for {account_key}.", flush=True)
            
            print(f"  [⏳] Initializing TelegramClient for {account_key}...", flush=True)
            client = TelegramClient(StringSession(decrypted_session), API_ID, API_HASH)
            
            # 🔑 KUNCI ANTI-STUCK: Jeda acak sebelum connect agar tidak di-blokir Telegram
            delay = random.uniform(3.0, 6.0)
            print(f"  [⏳] Waiting {delay:.1f}s before connecting to Telegram...", flush=True)
            await asyncio.sleep(delay)
            
            print(f"  [⏳] Connecting to Telegram for {account_key}...", flush=True)
            await client.connect()
            print(f"  [✅] Connected to Telegram for {account_key}.", flush=True)
            
            if await client.is_user_authorized():
                me = await client.get_me()
                username = me.username or me.first_name or str(me.id)
                print(f"  [✅] @{username} ({account_key}) berhasil connect.", flush=True)
                active_clients.append((client, account_key, username))
            else:
                print(f"  [❌] {account_key} tidak terotorisasi. Lewati.", flush=True)
                await client.disconnect()
                
        except Exception as e:
            print(f"  [❌] Gagal memuat/decrypt {account_key}: {e}", flush=True)
            try:
                await client.disconnect()
            except:
                pass
            
    print(f"✅ [DEBUG 8] Finished processing all accounts. Returning {len(active_clients)} active clients.", flush=True)
    return active_clients

async def get_init_data(client, target, account_key, username):
    bot = await client.get_input_entity(target["bot_username"])
    try:
        webview = await client(RequestWebViewRequest(peer=bot, bot=bot, platform='android', url=target["url"], start_param=target["ref_code"]))
        init_data_raw = webview.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
        init_data = urllib.parse.unquote(init_data_raw)
        user_data = json.loads(urllib.parse.parse_qs(init_data).get('user', [None])[0] or '{}')
        return init_data, str(user_data.get('id', '0'))
    except Exception as e: 
        return None, None

async def perform_login(init_data, uid, target, username):
    session = requests.Session()
    if proxy := os.environ.get('PROXY'): 
        session.proxies = {'http': proxy, 'https': proxy}
    session.headers.update({
        'User-Agent': target["user_agent"], 'X-Requested-With': 'org.telegram.messenger.web',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': f'{target["lang_code"]}-{target["lang_code"].upper()},{target["lang_code"]};q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'Connection': 'keep-alive'
    })
    try:
        resp = await async_get(session, target["url"], timeout=15)
        csrf_token = session.cookies.get('csrf_cookie_name')
        nonce_match = re.search(r'name="reg_nonce"\s+value="([^"]+)"', resp.text)
        if not csrf_token or not nonce_match: return False, None, None, None
        login_uid = hashlib.md5(str(uid).encode()).hexdigest() if target["name"] in ["MNAC", "MNAF", "VIPC", "EWRS"] else uid
        payload = {'csrf_test_name': csrf_token, 'tg_init_data': init_data, 'reg_nonce': nonce_match.group(1), 'uid': login_uid, 'website_url': ''}
        session.headers.update({'Content-Type': 'application/x-www-form-urlencoded', 'Referer': target["url"] + '/app/dashboard/'})
        resp = await async_post(session, target["url"] + '/app/auth/telegram_login', data=payload, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and ('dashboard' in resp.url.lower() or is_setup_page(resp.text) or 'dashboard' in resp.text.lower()):
            return True, login_uid, resp.text, session
        return False, None, None, None
    except Exception: 
        return False, None, None, None

# ==================== CAPTCHA SOLVER ====================
async def solve_icaptcha(host, data, session, user_agent):
    endpoint = data.get('endpoint')
    token = data.get('token')
    if not endpoint or not token: return None
    if not endpoint.startswith('http'): endpoint = host.rstrip('/') + '/' + endpoint.lstrip('/')

    widget_id, ts = str(uuid.uuid4()), int(time.time() * 1000)
    base_headers = {"X-Requested-With": "XMLHttpRequest", "x-iconcaptcha-token": token, "Referer": host + "/", "Origin": host, "User-Agent": user_agent, "Accept": "*/*"}
    load_dict = {"widgetId": widget_id, "action": "LOAD", "theme": "light", "token": token, "timestamp": ts, "initTimestamp": ts - 2000}
    encoded_payload = base64.b64encode(json.dumps(load_dict).encode('utf-8')).decode('utf-8')

    challenge_id = None
    for _ in range(3):
        try:
            res = await async_post(session, endpoint, data={"payload": encoded_payload}, headers={**base_headers, "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
            if res.text:
                res_json = json.loads(base64.b64decode(res.text.strip()).decode('utf-8'))
                if challenge_id := res_json.get('identifier'): break
        except Exception: pass
        await asyncio.sleep(random.uniform(2, 4))
    if not challenge_id: return None

    for i in range(5):
        ts = int(time.time() * 1000)
        selection_dict = {"x": (i * 64) + random.randint(20, 40), "y": random.randint(22, 30), "width": 320, "token": token, "action": "SELECTION", "widgetId": widget_id, "timestamp": ts, "challengeId": challenge_id, "initTimestamp": ts - 2000}
        encoded_selection = base64.b64encode(json.dumps(selection_dict).encode('utf-8')).decode('utf-8')
        boundary = '----WebKitFormBoundary' + secrets.token_hex(8)
        body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload\"\r\n\r\n{encoded_selection}\r\n--{boundary}--\r\n"
        try:
            res = await async_post(session, endpoint, data=body.encode('utf-8'), headers={**base_headers, "Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=10)
            if res.text and json.loads(base64.b64decode(res.text.strip()).decode('utf-8')).get('completed'):
                return {'_iconcaptcha-token': token, 'ic-rq': 1, 'ic-wid': widget_id, 'ic-cid': challenge_id, 'ic-hp': ''}
        except Exception: pass
        await asyncio.sleep(random.uniform(2, 4))
    return None

def extract_faucet_urls(html, target):
    pattern = rf'href="({re.escape(target["url"])}[^"]*faucet[^"]*)"'
    raw_urls = re.findall(pattern, html)
    clean_urls = list({url.replace(' ', '').strip() for url in raw_urls if url})
    filtered = []
    for url in clean_urls:
        low = url.lower()
        if any(skip in low for skip in target["skip_coins"]): continue
        if target["coins_filter"] and not any(f"/faucet/currency/{c.lower()}" in low for c in target["coins_filter"]): continue
        if '/faucet/currency/' not in low: continue
        filtered.append(url)
    random.shuffle(filtered)
    return filtered

def extract_timer(html):
    m = re.search(r'<b[^>]*id=["\']minute["\'][^>]*>(\d+)</b>\s*:\s*<b[^>]*id=["\']second["\'][^>]*>(\d+)</b>', html, re.IGNORECASE)
    if m: return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r'<h3[^>]*>\s*(\d+)\s*:\s*(\d+)\s*</h3>', html, re.IGNORECASE)
    if m: return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r'var\s+wait\s*=\s*(\d+)', html)
    if m: return int(m.group(1))
    return None

def _faucet_form(html, init_data, bot_url):
    action_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.IGNORECASE)
    action_url = action_match.group(1) if action_match else None
    if action_url and not action_url.startswith('http'): action_url = bot_url.rstrip('/') + '/' + action_url.lstrip('/')
    payload = {'tg_init_data': init_data}
    for field in ['csrf_test_name', 'claim_token', '_iconcaptcha-token']:
        match = re.search(rf'name=["\']{field}["\'][^>]*value=["\']([^"\']*)["\']', html, re.IGNORECASE) or re.search(rf'value=["\']([^"\']*)["\'][^>]*name=["\']{field}["\']', html, re.IGNORECASE)
        if match: payload[field] = match.group(1)
    return action_url, payload

async def _faucet(session, url, init_data, target, account_key):
    state = target_state[f"{account_key}_{target['name']}"]
    username = state["account_username"]
    coin_name = urlparse(url).path.rstrip('/').split('/')[-1].upper()

    state["batch_faucet_count"] += 1
    if state["batch_faucet_count"] >= state["current_batch_size"]:
        sleep_sec = random.randint(10 * 60, 20 * 60)
        print(f"\n[!] [{account_key}] {target['name']} Batch selesai. Istirahat {sleep_sec/60:.1f} m & relogin...", flush=True)
        await asyncio.sleep(sleep_sec)
        state["batch_faucet_count"] = 0
        state["current_batch_size"] = random.randint(FAUCET_BATCH_MIN, FAUCET_BATCH_MAX)
        state["need_relogin"] = True
        return "relogin", None

    got_success, visit_success, global_counter, trigger, fail_counter = False, state["visit_success"], state["global_counter"], None, 0

    while True:
        await asyncio.sleep(CLAIM_DELAY)
        try:
            resp = await async_get(session, url, timeout=15)
            if resp.status_code != 200: break

            fau = resp.text
            action_url, payload = _faucet_form(fau, init_data, target["url"])

            if not action_url:
                if '/auth/login' in fau or '/app/auth/validation' in fau: return "relogin", None
                timer = extract_timer(fau)
                if timer and timer > 0:
                    await asyncio.sleep(timer + random.randint(SAFETY_MIN, SAFETY_MAX)); continue
                fail_counter += 1
                if fail_counter >= 3: break
                await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue

            if not payload.get('claim_token') or not payload.get('csrf_test_name'):
                await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue

            if 'iconcaptcha-widget' in fau:
                captcha_result = await solve_icaptcha(target["url"], {'endpoint': target["url"] + '/icaptcha/req', 'token': payload.get('_iconcaptcha-token', '')}, session, target["user_agent"])
                if not captcha_result:
                    await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue
                payload.update(captcha_result)

            session.headers.update({'Referer': url, 'Content-Type': 'application/x-www-form-urlencoded', 'X-Telegram-Init-Data': init_data})
            post_resp = await async_post(session, action_url, data=payload, timeout=15)
            if post_resp.status_code != 200:
                fail_counter += 1
                if fail_counter >= 3: break
                await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue

            cla = post_resp.text
            icon_match, text_match = re.search(r"icon:\s*'([^']+)'", cla), re.search(r"text:\s*'([^']+)'", cla)
            icon, text = (icon_match.group(1) if icon_match else None), (text_match.group(1) if text_match else None)

            if not (icon and text):
                timer = extract_timer(cla)
                if timer and timer > 0:
                    await asyncio.sleep(timer + random.randint(SAFETY_MIN, SAFETY_MAX)); continue
                fail_counter += 1
                if fail_counter >= 3: break
                await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue

            if re.search(r'blacklist|flagged|banned|suspend', text, re.IGNORECASE):
                print(f"  [🚫 BANNED] [{account_key}] {target['name']} (@{username})", flush=True)
                return "banned", None
            
            if re.search(r'Invalid Claim|sufficient|insufficient|does not have|could not be processed|maximum|reached the limit', text, re.IGNORECASE):
                return "exhausted", None

            if icon.lower() == 'success' or re.search(r'success|has been send|has been sent|point', text, re.IGNORECASE):
                got_success, fail_counter, visit_success, global_counter = True, 0, visit_success + 1, global_counter + 1
                print(f"  [✅ SUKSES] [{account_key}] {target['name']} | {coin_name} | V:{visit_success}/{PER_VISIT_LIMIT} G:{global_counter}/{GLOBAL_LIMIT}", flush=True)
                
                if visit_success >= PER_VISIT_LIMIT: trigger = "per_visit"; break
                if global_counter >= GLOBAL_LIMIT: trigger = "global"; break
                await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX)); continue

            fail_counter += 1
            if fail_counter >= 3: break
            await asyncio.sleep(random.randint(SAFETY_MIN, SAFETY_MAX))
        except Exception as e:
            break

    state["visit_success"], state["global_counter"] = visit_success, global_counter
    return "success" if got_success else "fail", trigger

# ==================== COOLDOWN & MAIN LOOP ====================
async def cooldown_sleep(total_seconds: int, label: str):
    print(f"\n[⏳ COOLDOWN] {label} selama {total_seconds // 60} menit", flush=True)
    start, last_print = time.monotonic(), time.monotonic()
    while True:
        now, remaining = time.monotonic(), total_seconds - (time.monotonic() - start)
        if remaining <= 0: break
        if now - last_print >= COUNTDOWN_INTERVAL:
            print(f"  [⏳] Sisa waktu: {int(remaining // 60)} menit...", flush=True); last_print = now
        await asyncio.sleep(min(60, remaining))
    print(f"  [✅] Cooldown selesai, lanjut kerja.\n", flush=True)

async def short_rest_sleep(minutes: int, label: str):
    print(f"\n[☕ REST] {label} selama {minutes} menit", flush=True)
    await asyncio.sleep(minutes * 60)
    print(f"  [✅] Istirahat selesai.\n", flush=True)

async def wait_for_cooldown(state, target_name):
    elapsed = time.monotonic() - state["cycle_start"]
    if elapsed < state["work_seconds"]: return state["cycle_start"]
    await cooldown_sleep(random.randint(REST_MIN_MINUTES, REST_MAX_MINUTES) * 60, f"Istirahat {target_name} ({state['account_username']})")
    return time.monotonic()

async def process_target(client, target, account_key):
    state = target_state[f"{account_key}_{target['name']}"]
    username = state["account_username"]
    
    while True:
        if state.get("is_dead"):
            print(f"  [⛔ STOP] [{account_key}] {target['name']} dihentikan permanen.", flush=True)
            return 

        state["cycle_start"] = await wait_for_cooldown(state, target["name"])
        state["work_seconds"] = random.randint(WORK_MIN_MINUTES, WORK_MAX_MINUTES) * 60

        if state["need_relogin"]:
            state["need_relogin"] = False
            state["coin_exhausted"].clear()
            state["coin_skip_until"].clear()
            state["visit_success"], state["global_counter"] = 0, 0

        if not state["init_data"] or not state["uid"] or state["need_relogin"]:
            init_data, uid = await get_init_data(client, target, account_key, username)
            if not init_data: await asyncio.sleep(10); continue
            success, real_uid, dashboard_html, session = await perform_login(init_data, uid, target, username)
            if not success: await asyncio.sleep(10); continue
            state["init_data"], state["uid"], state["session"] = init_data, real_uid, session
            
            if is_setup_page(dashboard_html):
                print(f"  [⚠️ SETUP] [{account_key}] {target['name']} butuh setup manual. Dilewati.", flush=True)
                state["is_dead"] = True
                continue
            continue

        try:
            resp = await async_get(state["session"], target["url"] + '/app/dashboard/', timeout=15)
            active_faucets = extract_faucet_urls(resp.text, target)
        except Exception: 
            await asyncio.sleep(10); continue

        if target["coins_filter"] and not state.get("filter_reset_done", False):
            all_filtered_done = True
            for c in target["coins_filter"]:
                c_upper = c.upper()
                is_exhausted = c_upper in state["coin_exhausted"]
                is_skipped = state["coin_skip_until"].get(c_upper, 0) > time.time()
                if not (is_exhausted or is_skipped):
                    all_filtered_done = False
                    break
            
            if all_filtered_done:
                print(f"\n  [🔄 RESET] [{account_key}] {target['name']} filter {target['coins_filter']} habis. Reset ke semua koin & relogin...", flush=True)
                target["coins_filter"] = []          
                state["filter_reset_done"] = True    
                state["need_relogin"] = True         
                continue                             

        now = time.time()
        claimable = [(url, urlparse(url).path.split('/')[-1].upper()) for url in active_faucets 
                     if urlparse(url).path.split('/')[-1].upper() not in state["coin_exhausted"] 
                     and state["coin_skip_until"].get(urlparse(url).path.split('/')[-1].upper(), 0) <= now]

        if not claimable:
            await asyncio.sleep(30)
            continue

        total_success = 0
        for url, coin in claimable:
            if state["need_relogin"] or state.get("is_dead"): break
            
            status, trigger = await _faucet(state["session"], url, state["init_data"], target, account_key)
            
            if status == "success": total_success += 1
            elif status == "relogin": state["need_relogin"] = True; break
            elif status == "exhausted": state["coin_exhausted"].add(coin)
            elif status == "banned":
                state["is_dead"] = True
                break
            
            if trigger == "per_visit":
                await short_rest_sleep(random.randint(PER_VISIT_MIN_MIN, PER_VISIT_MAX_MIN), f"per-kunjungan {target['name']}")
                state["visit_success"] = 0
            elif trigger == "global":
                await short_rest_sleep(random.randint(GLOBAL_MIN_MIN, GLOBAL_MAX_MIN), f"global {target['name']}")
                state["global_counter"] = 0

        await asyncio.sleep(3)

async def main():
    print("🚀 [DEBUG] Masuk ke fungsi main()", flush=True)
    print("[*] Memuat akun dari full.json...\n", flush=True)
    
    active_clients = await get_all_authorized_clients_from_json()
    if not active_clients:
        print("[!] Tidak ada session valid yang bisa digunakan. Keluar.", flush=True)
        return

    print("\n[*] Initializing all targets for all accounts sequentially...", flush=True)
    all_tasks = []
    
    for client, account_key, username in active_clients:
        for target in TARGETS:
            state = init_target_state(account_key, target["name"], username)
            init_data, uid = await get_init_data(client, target, account_key, username)
            if not init_data: continue
            success, real_uid, dashboard_html, session = await perform_login(init_data, uid, target, username)
            if not success: continue
            state["init_data"], state["uid"], state["session"] = init_data, real_uid, session
            if is_setup_page(dashboard_html):
                state["is_dead"] = True
                continue
            all_tasks.append(process_target(client, target, account_key))

    if not all_tasks: 
        print("\n[!] Tidak ada target yang berhasil diinisialisasi. Keluar.", flush=True)
        return

    print(f"\n▶️ Memulai eksekusi PARALEL untuk {len(all_tasks)} task...\n", flush=True)
    await asyncio.gather(*all_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⛔ Script dihentikan secara manual.", flush=True)
