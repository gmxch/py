import requests
import json
import time
import os
import sys
import random
import asyncio
import urllib.parse
import uuid
import hashlib
import base64
from datetime import datetime
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

API_ID = 34017330
API_HASH = 'f37aab7f8d68ce67f1d581a03f3129b9'

RAW_KEY = os.environ.get('ENCRYPTION_KEY')
if not RAW_KEY:
    print("ENCRYPTION_KEY tidak ditemukan di environment variable. Exiting...")
    sys.exit(1)

ACCOUNTS_FILE = "accounts.json"
STATE_FILE = "tasks_state.json"
VALID_COUNTRIES = ["id", "us", "sg", "my", "ph", "vn", "th"]

R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
B = '\033[94m'
C = '\033[96m'
W = '\033[97m'
RESET = '\033[0m'

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_retry_session(retries=5, backoff_factor=2):
    session = requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                  status_forcelist=[500, 502, 503, 504, 408], allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.verify = False
    return session

http_session = create_retry_session()

def post_request(url, params=None, data=None, headers=None):
    return http_session.post(url, params=params, data=data, headers=headers, timeout=60)

def get_aes_key(raw_key):
    return hashlib.sha256(raw_key.encode()).digest()

def decrypt_data(encrypted_data, key):
    iv_b64, ct_b64 = encrypted_data.split(':')
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ct_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ct), AES.block_size)
    return decrypted.decode('utf-8')

def generate_proxy():
    session_id = random.randint(1000000, 9999999)
    country = random.choice(VALID_COUNTRIES)
    return {
        'proxy_type': 'http',
        'addr': 'gate.ipdeep.com',
        'port': 8082,
        'username': f"d5366267000-res-country-{country}-session-{session_id}-sessiontime-5",
        'password': "0WvMtqci"
    }

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_cooldown_remaining(account_key, action_id, cooldown_seconds):
    state = load_state()
    last_claim = state.get(account_key, {}).get(action_id, {}).get('last_claim', 0)
    remaining = cooldown_seconds - (int(time.time()) - last_claim)
    return remaining if remaining > 0 else 0

def update_action_state(account_key, action_id, last_reward=0):
    state = load_state()
    if account_key not in state: state[account_key] = {}
    state[account_key][action_id] = {'last_claim': int(time.time()), 'last_reward': last_reward}
    save_state(state)

def get_atf_cache(account_key, max_age_hours=24):
    state = load_state()
    cache = state.get(account_key, {}).get('atf_cache', {})
    if cache and (int(time.time()) - cache.get('timestamp', 0) < (max_age_hours * 3600)):
        return cache
    return None

def save_atf_cache(account_key, data):
    state = load_state()
    if account_key not in state: state[account_key] = {}
    data['timestamp'] = int(time.time())
    state[account_key]['atf_cache'] = data
    save_state(state)

def clear_atf_cache(account_key):
    state = load_state()
    if account_key in state and 'atf_cache' in state[account_key]:
        del state[account_key]['atf_cache']
        save_state(state)

def get_timestamp(): return str(int(time.time() * 1000))
def get_current_time(): return datetime.now().strftime("%H:%M:%S")
def clear_terminal(): os.system('cls' if os.name == 'nt' else 'clear')

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36 Telegram-Android/10.6.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.5.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.4.1",
    "Mozilla/5.0 (Linux; Android 13; SM-A546E Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro Build/TKQ1.221114.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UQ1A.240205.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.143 Mobile Safari/537.36 Telegram-Android/10.7.0"
]

USER_AGENTS = [
    # Samsung Galaxy S Series
    "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36 Telegram-Android/10.6.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.5.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.4.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.150 Mobile Safari/537.36 Telegram-Android/10.3.0",
    
    # Samsung Galaxy A Series
    "Mozilla/5.0 (Linux; Android 13; SM-A546E Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 13; SM-A536E Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.1.0",
    "Mozilla/5.0 (Linux; Android 12; SM-A325F Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.172 Mobile Safari/537.36 Telegram-Android/9.9.0",
    
    # Samsung Galaxy Note Series
    "Mozilla/5.0 (Linux; Android 12; SM-G991B Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36 Telegram-Android/9.6.0",
    "Mozilla/5.0 (Linux; Android 12; SM-G996B Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.162 Mobile Safari/537.36 Telegram-Android/9.5.0",
    "Mozilla/5.0 (Linux; Android 11; SM-N975F Build/RP1A.200720.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.135 Mobile Safari/537.36 Telegram-Android/9.4.0",
    
    # Xiaomi / Redmi
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 9 Pro Build/RKQ1.200826.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.116 Mobile Safari/537.36 Telegram-Android/9.3.3",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro Build/TKQ1.221114.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 11 Pro Build/TKQ1.221114.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.1.0",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 10 Pro Build/SKQ1.210216.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.168 Mobile Safari/537.36 Telegram-Android/9.7.0",
    "Mozilla/5.0 (Linux; Android 13; POCO F5 Build/TKQ1.221114.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.3.0",
    "Mozilla/5.0 (Linux; Android 12; Mi 11 Build/SKQ1.210216.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36 Telegram-Android/9.6.0",
    
    # OnePlus
    "Mozilla/5.0 (Linux; Android 14; CPH2581 Build/UKQ1.230924.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36 Telegram-Android/10.6.1",
    "Mozilla/5.0 (Linux; Android 13; CPH2449 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 13; LE2121 Build/TKQ1.220922.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.150 Mobile Safari/537.36 Telegram-Android/10.1.0",
    "Mozilla/5.0 (Linux; Android 12; IN2023 Build/SKQ1.210216.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.168 Mobile Safari/537.36 Telegram-Android/9.8.0",
    
    # Google Pixel
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UQ1A.240205.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.143 Mobile Safari/537.36 Telegram-Android/10.7.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/UQ1A.240205.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.143 Mobile Safari/537.36 Telegram-Android/10.7.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.4.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.3.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a Build/TQ3A.230901.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.150 Mobile Safari/537.36 Telegram-Android/10.2.0",
    
    # Vivo / Oppo / Realme
    "Mozilla/5.0 (Linux; Android 13; V2254 Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.1.0",
    "Mozilla/5.0 (Linux; Android 13; CPH2465 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36 Telegram-Android/10.3.0",
    "Mozilla/5.0 (Linux; Android 13; RMX3700 Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36 Telegram-Android/10.2.0",
    "Mozilla/5.0 (Linux; Android 12; V2185 Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.168 Mobile Safari/537.36 Telegram-Android/9.7.0",
    
    # Huawei / Honor
    "Mozilla/5.0 (Linux; Android 12; NOH-NX9 Build/HUAWEINOH-N29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36 Telegram-Android/9.6.0",
    "Mozilla/5.0 (Linux; Android 12; LNA-NX9 Build/HONORLNA-N29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.162 Mobile Safari/537.36 Telegram-Android/9.5.0"
]

def is_unauthorized_error(response_data):
    if response_data.get("status") == "error":
        message = response_data.get("message", "").lower()
        if "unauthorized" in message or "invalid" in message or "session" in message:
            return True
    return False

async def fetch_and_login_atf(client, account_key, url):
    try:
        bot_ent = await client.get_entity('@ATF_AIRDROP_bot')
        await client.send_message(bot_ent, '/start')
        await asyncio.sleep(2)
        
        web_view = await client(functions.messages.RequestWebViewRequest(
            peer=bot_ent, bot=bot_ent, platform='android', from_bot_menu=True,
            url='https://atfminers.asloni.online'
        ))
        
        raw_data = web_view.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]
        init_data = urllib.parse.unquote(raw_data)
        
        user_json = json.loads(urllib.parse.unquote(init_data.split('user=')[1].split('&')[0]))
        tg_id, username = int(user_json['id']), user_json.get('username', '')
        
        device_id = f"dev-{str(uuid.uuid4())}"
        base_headers = {
            'User-Agent': random.choice(USER_AGENTS), 'Content-Type': "application/json",
            'x-requested-with': "XMLHttpRequest", 'origin': "https://atfminers.asloni.online",
            'referer': "https://atfminers.asloni.online/miner/index.html?v=100", 'Host': 'atfminers.asloni.online'
        }
        
        resp_login = post_request(url, params={'action': "login", 't': get_timestamp()}, 
                                  data=json.dumps({"initData": init_data, "request_id": str(uuid.uuid4()), 
                                                   "device_id": device_id, "tg_id": tg_id, "username": username}), 
                                  headers=base_headers)
        data_login = resp_login.json()
        
        if data_login.get("status") == "success":
            tma_token = data_login.get("tma_session_token")
            if tma_token:
                base_headers['x-atf-tma-session'] = tma_token
                base_headers['cookie'] = f"atf_tma_session={tma_token}"
            
            user_data = data_login.get("user", {})
            wallet = user_data.get("wallet_address", "")
            public_key = user_data.get("wallet_public_key", "")
            
            save_atf_cache(account_key, {
                'init_data': init_data, 'tg_id': tg_id, 'username': username,
                'tma_token': tma_token, 'wallet': wallet, 'public_key': public_key
            })
            print(f"{G}[+] ATF Login Success & Cached!{RESET}")
            return init_data, base_headers, tg_id, username, wallet, public_key
        else:
            print(f"{R}[!] ATF Login failed: {data_login.get('message')}{RESET}")
            return None, None, None, None, None, None
    except Exception as e:
        print(f"{R}[!] Error fetching ATF data: {e}{RESET}")
        return None, None, None, None, None, None

async def process_task_auto(account_key, session_headers, init_data, tg_id, base_url, task):
    task_id = task['task_id']
    task_name = task['name']
    wait_time = task.get('wait_time', 12)
    
    remaining = get_cooldown_remaining(account_key, task_id, task['cooldown'])
    if remaining > 0:
        return init_data, session_headers, False
    
    print(f"{Y}[*] Processing: {task_name}{RESET}")
    current_headers, current_init_data = session_headers.copy(), init_data
    device_id = f"dev-{str(uuid.uuid4())}"
    
    try:
        payload = {"initData": current_init_data, "request_id": str(uuid.uuid4()), "device_id": device_id, 
                   "tg_id": str(tg_id), "task_id": task_id, "client_started_at": int(time.time())}
        
        resp_start = post_request(base_url, params={'action': 'start_task', 't': get_timestamp()}, data=json.dumps(payload), headers=current_headers)
        data_start = resp_start.json()
        
        if is_unauthorized_error(data_start):
            clear_atf_cache(account_key)
            return None, None, True
        
        if data_start.get("status") == "error" and "cooldown" in data_start.get("message", "").lower():
            update_action_state(account_key, task_id, 0)
            return current_init_data, current_headers, False
        
        if data_start.get("status") == "success" and data_start.get("started") == True:
            if task_id in ["youtube_like_comment", "twitter_retweet"]: wait_time = random.randint(10, 15)
            if wait_time > 0:
                print(f"{Y}[*] Waiting {wait_time}s before claiming...{RESET}")
                await asyncio.sleep(wait_time)
            
            resp_claim = post_request(base_url, params={'action': 'claim_task', 't': get_timestamp()}, data=json.dumps(payload), headers=current_headers)
            data_claim = resp_claim.json()
            
            if is_unauthorized_error(data_claim):
                clear_atf_cache(account_key)
                return None, None, True
            
            if data_claim.get("status") == "success":
                reward, new_balance = data_claim.get("reward", 0), data_claim.get("new_balance", 0)
                print(f"{G}[+] Claimed! +{W}{reward}{G} ATF | Balance: {W}{new_balance}{RESET}")
                update_action_state(account_key, task_id, reward)
            elif "cooldown" in str(data_claim.get("message", "")).lower():
                update_action_state(account_key, task_id, 0)
    except Exception as e:
        print(f"{R}[!] Error processing {task_name}: {e}{RESET}")
    
    return current_init_data, current_headers, False

async def process_account_cycle(account_key, decrypted_session, proxy_config, username_hash):
    print(f"\n{C}{'='*60}")
    print(f"{G}⛏️  PROCESSING: {account_key} (@{username_hash}) ⛏️")
    print(f"{C}{'='*60}{RESET}")
    
    client = TelegramClient(StringSession(decrypted_session), API_ID, API_HASH, proxy=proxy_config)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"{R}[!] Session Telegram invalid/expired. Skipping.{RESET}")
            return
        
        me = await client.get_me()
        print(f"{G}[+] Logged in: {me.username or me.first_name} (Proxy: {proxy_config['addr']}){RESET}")
        
        url = "https://atfminers.asloni.online/miner/index.php"
        cached_data = get_atf_cache(account_key)
        
        if cached_data:
            print(f"{G}[+] Using cached ATF session{RESET}")
            current_init_data = cached_data['init_data']
            tg_id = cached_data['tg_id']
            username = cached_data['username']
            wallet = cached_data['wallet']
            public_key = cached_data['public_key']
            current_headers = {
                'User-Agent': random.choice(USER_AGENTS), 'Content-Type': "application/json",
                'x-requested-with': "XMLHttpRequest", 'origin': "https://atfminers.asloni.online",
                'referer': "https://atfminers.asloni.online/miner/index.html?v=100", 'Host': 'atfminers.asloni.online',
                'x-atf-tma-session': cached_data['tma_token'],
                'cookie': f"atf_tma_session={cached_data['tma_token']}"
            }
        else:
            print(f"{Y}[*] Fetching fresh initData via WebView...{RESET}")
            res = await fetch_and_login_atf(client, account_key, url)
            if res[0] is None:
                return
            current_init_data, current_headers, tg_id, username, wallet, public_key = res

        tasks_ready = [task for task in TASKS if get_cooldown_remaining(account_key, task['task_id'], task['cooldown']) == 0]
        for task in tasks_ready:
            new_init, new_headers, needs_refresh = await process_task_auto(account_key, current_headers, current_init_data, tg_id, url, task)
            if needs_refresh:
                res = await fetch_and_login_atf(client, account_key, url)
                if res[0]:
                    current_init_data, current_headers, tg_id, username, wallet, public_key = res
            await asyncio.sleep(2)
        
        try:
            resp_sync = post_request(url, params={'action': "sync_wallet", 't': get_timestamp()}, 
                                     data=json.dumps({"initData": current_init_data, "request_id": str(uuid.uuid4()), 
                                                      "device_id": f"dev-{uuid.uuid4()}", "tg_id": tg_id, "wallet": wallet, "public_key": public_key}), 
                                     headers=current_headers)
            data_sync = resp_sync.json()
            if is_unauthorized_error(data_sync):
                clear_atf_cache(account_key)
            elif data_sync.get("status") == "success":
                print(f"{G}[+] Sync Success | Mined Balance: {W}{data_sync.get('user', {}).get('mined_balance', 'N/A')}{RESET}")
        except Exception as e:
            print(f"{R}[!] Sync Wallet Error: {e}{RESET}")
        
        boost_cd = get_cooldown_remaining(account_key, "boost", 3600)
        if boost_cd == 0:
            print(f"\n{Y}[*] Executing Boost (1x)...{RESET}")
            try:
                resp_boost = post_request(url, params={'action': "activate_boost", 't': get_timestamp()}, 
                                          data=json.dumps({"initData": current_init_data, "request_id": str(uuid.uuid4()), 
                                                           "device_id": f"dev-{uuid.uuid4()}", "tg_id": tg_id, "display_preview": 100.188}), 
                                          headers=current_headers)
                data_boost = resp_boost.json()
                if data_boost.get("status") == "success":
                    print(f"{G}[+] Boost Success | Pending: {W}{data_boost.get('pending_reward', '0')}{RESET}")
                    update_action_state(account_key, "boost", 0)
                elif is_unauthorized_error(data_boost):
                    clear_atf_cache(account_key)
            except Exception as e:
                print(f"{R}[!] Boost Error: {e}{RESET}")
        else:
            h, m, s = boost_cd // 3600, (boost_cd % 3600) // 60, boost_cd % 60
            print(f"{Y}[*] Boost cooldown: {h:02d}:{m:02d}:{s:02d}{RESET}")

        claim_cd = get_cooldown_remaining(account_key, "claim", 3600)
        if claim_cd == 0:
            print(f"\n{Y}[*] Executing Claim (1x)...{RESET}")
            try:
                resp_claim = post_request(url, params={'action': "claim", 't': get_timestamp()}, 
                                          data=json.dumps({"initData": current_init_data, "request_id": str(uuid.uuid4()), 
                                                           "device_id": f"dev-{uuid.uuid4()}", "tg_id": tg_id, "claim_preview": 1.1227}), 
                                          headers=current_headers)
                data_claim = resp_claim.json()
                if data_claim.get("status") == "success":
                    print(f"{G}[+] Claim Success | Amount: {W}{data_claim.get('claimed_amount', '0')}{RESET}")
                    update_action_state(account_key, "claim", 0)
                elif is_unauthorized_error(data_claim):
                    clear_atf_cache(account_key)
            except Exception as e:
                print(f"{R}[!] Claim Error: {e}{RESET}")
        else:
            h, m, s = claim_cd // 3600, (claim_cd % 3600) // 60, claim_cd % 60
            print(f"{Y}[*] Claim cooldown: {h:02d}:{m:02d}:{s:02d}{RESET}")

    except Exception as e:
        print(f"{R}[!] Critical Error in {account_key}: {e}{RESET}")
    finally:
        await client.disconnect()



async def main():
    clear_terminal()
    print(f"{C}============================================={RESET}")
    print(f"{G}                   ATF  {RESET}")
    print(f"{C}============================================={RESET}")
    
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"{R}[!] {ACCOUNTS_FILE} not found.{RESET}")
        return
    
    with open(ACCOUNTS_FILE, 'r') as f:
        accounts = json.load(f)
    
    aes_key = get_aes_key(RAW_KEY)
    print(f"{Y}[*] Found {len(accounts)} accounts to process.{RESET}")
    
    cycle_count = 1
    while True:
        print(f"\n{C}>>> STARTING GLOBAL CYCLE #{cycle_count} <<<{RESET}")
        
        for acc_key, acc_data in accounts.items():
            try:
                decrypted_session = decrypt_data(acc_data['sess'], aes_key)
                proxy_config = generate_proxy()
                await process_account_cycle(acc_key, decrypted_session, proxy_config, acc_data.get('user', 'unknown'))
                await asyncio.sleep(3) # Jeda antar akun
            except Exception as e:
                print(f"{R}[!] Failed to process {acc_key}: {e}{RESET}")
                continue
        
        cycle_count += 1
        print(f"\n{G}[*] Semua akun telah diproses. Menunggu 60 detik sebelum siklus berikutnya...{RESET}")
        await asyncio.sleep(60) # Jeda global 60 detik
        clear_terminal()

if __name__ == '__main__':
    asyncio.run(main())
