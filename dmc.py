import asyncio
import json
import os
import random
import sys
import time
import uuid
import hashlib
import shutil
import aiohttp
import base64

PROGRESS_FILE = "2selesai.json"
DEVICE_FILE = "2device_ids.json"
TOKEN_FILE = "2token.json"
BNB_FILE = "2bnb.json"
CAPPED_FILE = "2capped.json"
BATCH_SIZE = 10
COOLDOWN_SECONDS = 60

SUPABASE_PUBLISHABLE_KEY = "sb_publishable_yQmoWaeRtZy8i5p75dcNAQ_SnRxhjDv"
SUPABASE_URL = "https://tagxhipylkobyguviedc.supabase.co"

USER_REFERRAL_ID = os.getenv("USER_REFERRAL_ID")
USER_REFERRAL_URI = f"https://drama.center/?ref={USER_REFERRAL_ID}"
LOCAL_CLIENT_KEY = os.getenv("LOCAL_CLIENT_KEY")


class C:
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"; BLUE = "\033[94m"
    MAGENTA = "\033[95m"; CYAN = "\033[96m"; WHITE = "\033[97m"; GRAY = "\033[90m"
    BOLD = "\033[1m"; RESET = "\033[0m"


def clear_screen():
    sys.stdout.write("\033[H\033[2J\033[3J")
    sys.stdout.flush()

def short_addr(a):
    if not a or a == "unknown": return "unknown"
    a = str(a)
    return a[:6] + "..." + a[-4:] if len(a) > 12 else a

def parse_cookie_token(cookie_str):
    try:
        if "base64-" not in cookie_str: return None
        b64 = cookie_str.split("base64-", 1)[1]
        b64 += "=" * (4 - len(b64) % 4)
        return json.loads(base64.b64decode(b64).decode("utf-8"))
    except Exception:
        return None

def build_cookie_string(auth_data):
    b64 = base64.b64encode(json.dumps(auth_data).encode()).decode()
    return f"sb-tagxhipylkobyguviedc-auth-token.0=base64-{b64}"

def extract_wallet_from_cookie(cookie_str):
    try:
        data = parse_cookie_token(cookie_str)
        if not data: return None
        access = data.get("access_token", "")
        if "." not in access: return None
        payload_b64 = access.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
        return payload.get("user_metadata", {}).get("custom_claims", {}).get("address")
    except Exception:
        return None


AUTO_LOGIN_JS_TEMPLATE = r"""const { Wallet } = require("ethers");
const axios = require("axios");
const fs = require("fs");

const colors = {
    reset: "\x1b[0m", cyan: "\x1b[36m", green: "\x1b[32m", red: "\x1b[31m",
    yellow: "\x1b[33m", gray: "\x1b[90m", white: "\x1b[97m", magenta: "\x1b[35m"
};

const LOCAL_API_URL = "https://api.gsectr.my.id/v4";
const LOCAL_CLIENT_KEY = "__LOCAL_CLIENT_KEY__";
const TURNSTILE_SITE_KEY = "0x4AAAAAAE5Imx2BMLN5ABSD";
const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_yQmoWaeRtZy8i5p75dcNAQ_SnRxhjDv";

const DEVICES = [
  { model: "SM-A217F", android: "12", chrome: "136" },
  { model: "SM-A125F", android: "11", chrome: "135" },
  { model: "SM-A325F", android: "13", chrome: "137" },
  { model: "SM-A515F", android: "12", chrome: "134" },
  { model: "Redmi Note 11", android: "13", chrome: "139" },
  { model: "V2109", android: "12", chrome: "136" },
  { model: "RMX3521", android: "13", chrome: "140" },
  { model: "moto g(50)", android: "12", chrome: "136" },
];

function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
function generateProfile() {
  const d = pickRandom(DEVICES);
  const buildMap = { "10": "QP1A.190711.020", "11": "RP1A.200720.011", "12": "SP1A.210812.016", "13": "TP1A.220624.014", "14": "UP1A.231005.007" };
  const build = buildMap[d.android];
  const ua = `Mozilla/5.0 (Linux; Android ${d.android}; ${d.model} Build/${build}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${d.chrome}.0.0.0 Mobile Safari/537.36`;
  return { ua, chromeVer: d.chrome, androidVer: d.android, model: d.model,
    sec_ch_ua: `"Chromium";v="${d.chrome}", "Google Chrome";v="${d.chrome}", "Not A(Brand";v="99"` };
}
function getRandomIp() {
  return `${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 254) + 1}`;
}
function loadJson(filepath) {
  try { if (fs.existsSync(filepath)) return JSON.parse(fs.readFileSync(filepath, "utf8")); } catch (e) {}
  return [];
}
function saveJson(filepath, data) { fs.writeFileSync(filepath, JSON.stringify(data, null, 2), "utf8"); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function buildCookieString(authData) {
  const b64 = Buffer.from(JSON.stringify(authData)).toString('base64');
  return `sb-tagxhipylkobyguviedc-auth-token.0=base64-${b64}`;
}
function shortAddr(a) { return a.slice(0, 6) + "..." + a.slice(-4); }

function decodeWalletFromCookie(cookieStr) {
  try {
    const idx = cookieStr.indexOf('base64-');
    if (idx < 0) return null;
    let b64 = cookieStr.substring(idx + 7);
    while (b64.length % 4) b64 += '=';
    const data = JSON.parse(Buffer.from(b64, 'base64').toString('utf8'));
    const access = data.access_token || '';
    if (!access.includes('.')) return null;
    const parts = access.split('.');
    let p = parts[1];
    while (p.length % 4) p += '=';
    const payload = JSON.parse(Buffer.from(p, 'base64').toString('utf8'));
    return payload?.user_metadata?.custom_claims?.address || null;
  } catch (e) { return null; }
}

async function solveTurnstile(profile, websiteUrl, websiteKey) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const createPayload = {
        method: "CloudflareTask",
        task: {
          type: "turnstile",
          websiteUrl: "https://drama.center",
          websiteKey: TURNSTILE_SITE_KEY
        },
        data: {
          debug: true,
          timeout: 50000
        }
      };

      const createRes = await axios.post(LOCAL_API_URL + "/createTask", createPayload, {
        headers: { 
          "Content-Type": "application/json",
          "ClientKey": LOCAL_CLIENT_KEY,
          "User-Agent": profile.ua 
        },
        timeout: 30000
      });

      const taskId = createRes.data?.taskId;
      if (!taskId) {
        throw new Error("Invalid response: " + JSON.stringify(createRes.data));
      }

      for (let i = 0; i < 60; i++) {
        await sleep(2000);
        const pollRes = await axios.post(LOCAL_API_URL + "/getTaskResult", { taskId }, {
          headers: { 
            "Content-Type": "application/json",
            "ClientKey": LOCAL_CLIENT_KEY,
            "User-Agent": profile.ua 
          },
          timeout: 30000
        });

        const resData = pollRes.data;
        const status = resData.status;

        if (status === "ready") {
          return resData.solution?.token || resData.solution; 
        }
        
        if (status === "error") {
          throw new Error(`API Error: ${resData.err?.msg || resData.err?.usr || "Unknown error"}`);
        }
      }
      throw new Error("Timeout waiting for captcha");
    } catch (err) {
      if (attempt === 3) throw err;
      await sleep(2000);
    }
  }
}

async function bindOne(acc, index, total) {
  const wallet = new Wallet(acc.privateKey);
  const address = wallet.address;
  const profile = generateProfile();

  console.log(`\n${colors.cyan}━━━ [${index + 1}/${total}] ${shortAddr(address)} ━━━${colors.reset}`);
  console.log(`${colors.gray}  Profile: Chrome/${profile.chromeVer}.0.0.0${colors.reset}`);

  const anonHeaders = {
    'sec-ch-ua-platform': '"Android"', 'sec-ch-ua': profile.sec_ch_ua, 'sec-ch-ua-mobile': "?1",
    'User-Agent': profile.ua, 'Accept': "*/*", 'Accept-Encoding': "gzip, deflate, br, zstd",
    'Accept-Language': "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    'Content-Type': "application/json", 'Origin': "https://drama.center", 'Referer': "__USER_URI__",
    'sec-fetch-site': "same-origin", 'sec-fetch-mode': "cors", 'sec-fetch-dest': "empty",
    "x-forwarded-for": getRandomIp()
  };

  console.log(`  ${colors.cyan}[i/4] Minta nonce...${colors.reset}`);
  let nonce = null, usedRef = null;
  const refs = ["__USER_REF_ID__", "RS2C2Z"].filter((v, idx, arr) => arr.indexOf(v) === idx);
  for (const tryRef of refs) {
    try {
      const r = await axios.post("https://drama.center/api/referrals/intent", { referrer: tryRef }, { headers: anonHeaders, timeout: 45000, validateStatus: () => true });
      nonce = r.data?.data?.nonce;
      if (nonce) { usedRef = tryRef; break; }
    } catch (e) {}
    await sleep(1200);
  }
  if (!nonce) { console.log(`    ${colors.red}✗ Nonce GAGAL${colors.reset}`); return { status: "nonce_fail" }; }
  console.log(`    ${colors.green}✓ Nonce OK${colors.reset}`);

  console.log(`  ${colors.yellow}⏳ Meminta token Turnstile...${colors.reset}`);
  let captchaToken;
  try {
    captchaToken = await solveTurnstile(profile);
    console.log(`  ${colors.green}✓ Token didapat${colors.reset}`);
  } catch (e) {
    console.log(`  ${colors.red}✗ Turnstile GAGAL${colors.reset}`); return { status: "captcha_fail" };
  }

  const issuedAt = new Date().toISOString();
  const message = `drama.center wants you to sign in with your Ethereum account:\n${address}\n\nSign in to DramaCenter.\n\nURI: __USER_URI__\nVersion: 1\nChain ID: 1\nIssued At: ${issuedAt}`;
  const signature = await wallet.signMessage(message);
  delete axios.defaults.headers.common['Cookie'];

  const authHeaders = {
    'sec-ch-ua-platform': '"Android"', 'sec-ch-ua': profile.sec_ch_ua, 'sec-ch-ua-mobile': "?1",
    'x-supabase-api-version': "2024-01-01", 'x-client-info': "supabase-ssr/0.12.5 createBrowserClient",
    'content-type': "application/json;charset=UTF-8",
    'apikey': SUPABASE_PUBLISHABLE_KEY, 'authorization': `Bearer ${SUPABASE_PUBLISHABLE_KEY}`,
    'origin': "https://drama.center", 'referer': "__USER_URI__", 'User-Agent': profile.ua
  };

  let authData = null;
  let loginErrMsg = "";
  for (let loginAttempt = 1; loginAttempt <= 3; loginAttempt++) {
    try {
      const r = await axios.post("https://tagxhipylkobyguviedc.supabase.co/auth/v1/token?grant_type=web3", {
        chain: "ethereum", message, signature,
        gotrue_meta_security: { captcha_token: captchaToken }
      }, { headers: authHeaders, timeout: 30000, validateStatus: () => true });
      if (r.data?.user?.id) { authData = r.data; break; }
      loginErrMsg = JSON.stringify(r.data).slice(0, 200);
      if ((r.data?.code || "").includes("captcha") || (r.data?.msg || "").includes("captcha") || (r.data?.message || "").includes("captcha")) {
        captchaToken = await solveTurnstile(profile);
        continue;
      }
      break;
    } catch (e) { loginErrMsg = e.message; if (loginAttempt === 3) break; await sleep(2000); }
  }
  if (!authData) { console.log(`  ${colors.red}✗ Login GAGAL: ${loginErrMsg.slice(0, 100)}${colors.reset}`); return { status: "login_fail", err: loginErrMsg }; }

  const user_id = authData.user.id;
  console.log(`  ${colors.green}✓ Login OK: ${user_id}${colors.reset}`);

  const cookieStr = buildCookieString(authData);
  const deviceId = uuidv4();
  const realWallet = decodeWalletFromCookie(cookieStr) || address;
  console.log(`  ${colors.green}✓ Device (200)${colors.reset}`);

  const baseHeaders = {
    'sec-ch-ua': profile.sec_ch_ua, 'sec-ch-ua-mobile': "?1", 'sec-ch-ua-platform': '"Android"',
    'User-Agent': profile.ua, 'Accept': "*/*", 'Accept-Language': "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    'Content-Type': "application/json", 'Origin': "https://drama.center", 'Referer': "__USER_URI__",
    'sec-fetch-site': "same-origin", 'sec-fetch-mode': "cors", 'sec-fetch-dest': "empty",
    'apikey': SUPABASE_PUBLISHABLE_KEY, "Cookie": cookieStr
  };

  let bindSuccess = false;
  try {
    const r = await axios.post("https://drama.center/api/referrals", { nonce }, { headers: baseHeaders, timeout: 30000, validateStatus: () => true });
    if (r.status === 200 && r.data?.success) bindSuccess = true;
  } catch (e) {}

  try { await axios.post("https://drama.center/api/auth/locale", { locale: "en", timezone: "Asia/Jakarta" }, { headers: baseHeaders, timeout: 20000, validateStatus: () => true }); } catch (e) {}
  try { await axios.get("https://drama.center/api/auth/me", { headers: baseHeaders, timeout: 20000, validateStatus: () => true }); } catch (e) {}
  try { await axios.post("https://drama.center/api/auth/device", { deviceId }, { headers: baseHeaders, timeout: 20000, validateStatus: () => true }); } catch (e) {}

  return {
    status: bindSuccess ? "bind_ok" : "bind_fail_existing",
    data: { user_id, token: cookieStr, device_id: deviceId, wallet_address: realWallet }
  };
}

async function executeSignIn() {
  const bnb = loadJson("2bnb.json");
  if (bnb.length === 0) { console.log("[-] 2bnb.json empty"); process.exit(1); }

  const existingTokens = loadJson(TOKEN_FILE);
  const tokenMap = {};
  const boundAddrs = new Set();

  existingTokens.forEach((it) => {
    if (it.user_id) {
      tokenMap[it.user_id] = it;
      let addr = it.wallet_address;
      if (!addr && it.token) addr = decodeWalletFromCookie(it.token);
      if (addr) boundAddrs.add(addr.toLowerCase());
    }
  });

  const toBind = bnb.filter(a => {
    if (!a.privateKey || !a.address) return false;
    return !boundAddrs.has(a.address.toLowerCase());
  });

  console.log(`\n${colors.cyan}╔══════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.cyan}║  ${colors.bold}${colors.white}🔗 BINDING WALLET BARU${colors.reset}`);
  console.log(`${colors.cyan}╚══════════════════════════════════════════════════════╝${colors.reset}`);
  console.log(`  ${colors.gray}Total 2bnb.json: ${bnb.length}${colors.reset}`);
  console.log(`  ${colors.gray}Udah ke-bind  : ${boundAddrs.size}${colors.reset}`);
  console.log(`  ${colors.green}Perlu di-bind : ${toBind.length}${colors.reset}\n`);

  let bindOk = 0, bindFail = 0, loginFail = 0;

  for (let i = 0; i < toBind.length; i++) {
    const result = await bindOne(toBind[i], i, toBind.length);
    if (result.status === "bind_ok" || result.status === "bind_fail_existing") {
      tokenMap[result.data.user_id] = result.data;
      saveJson(TOKEN_FILE, Object.values(tokenMap));
      if (result.status === "bind_ok") bindOk++;
      else bindFail++;
    } else {
      loginFail++;
    }

    if (i < toBind.length - 1) {
      const cooldown = 8 + Math.floor(Math.random() * 7);
      process.stdout.write(`  ${colors.gray}⏳ Delay ${cooldown}s...${colors.reset}`);
      await sleep(cooldown * 1000);
      process.stdout.write('\r\x1b[K');
    }
  }

  console.log(`\n${colors.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}`);
  console.log(`  ${colors.green}Bind OK${colors.reset}: ${bindOk} | ${colors.yellow}Bind skip${colors.reset}: ${bindFail} | ${colors.red}Login fail${colors.reset}: ${loginFail}`);
  console.log(`  ${colors.gray}Total di 2token.json: ${colors.white}${Object.values(tokenMap).length}${colors.reset}`);
  console.log(`${colors.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${colors.reset}\n`);
}

executeSignIn();
"""


def clean_cookie_files():
    for f in ["cookies.txt", "cookie.txt", ".cookies", "cookies.json"]:
        if os.path.exists(f):
            try: os.remove(f)
            except Exception: pass

def load_tokens():
    if not os.path.exists(TOKEN_FILE): return []
    try:
        with open(TOKEN_FILE, "r") as f:
            raw = json.load(f)
        seen, out = set(), []
        for it in raw:
            uid = it.get("user_id") or it.get("token")
            if uid and uid not in seen:
                seen.add(uid); out.append(it)
        return out
    except Exception: return []

def run_auto_login():
    clean_cookie_files()
    auto_js = (AUTO_LOGIN_JS_TEMPLATE
               .replace("__USER_URI__", USER_REFERRAL_URI)
               .replace("__USER_REF_ID__", USER_REFERRAL_ID)
               .replace("__LOCAL_CLIENT_KEY__", LOCAL_CLIENT_KEY))
    with open("auto_login.js", "w", encoding="utf-8") as f:
        f.write(auto_js)
    os.system("node auto_login.js")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f: return json.load(f)
        except Exception: return {}
    return {}

def save_progress(d):
    with open(PROGRESS_FILE, "w") as f: json.dump(d, f, indent=2)

def load_capped():
    if os.path.exists(CAPPED_FILE):
        try:
            with open(CAPPED_FILE, "r") as f:
                return set(json.load(f))
        except Exception: return set()
    return set()

def save_capped(capped_set):
    with open(CAPPED_FILE, "w") as f:
        json.dump(list(capped_set), f, indent=2)

async def refresh_one_token(session, account):
    old_cookie = account.get("token", "")
    auth_data = parse_cookie_token(old_cookie)
    if not auth_data: return None, "no_cookie"

    refresh_token = auth_data.get("refresh_token", "")
    if not refresh_token: return None, "no_refresh_token"

    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
        "origin": "https://drama.center",
        "referer": "https://drama.center/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/136 Mobile Safari/537.36"
    }

    try:
        async with session.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as r:
            if r.status != 200:
                text = await r.text()
                return None, f"http_{r.status}: {text[:80]}"
            new_data = await r.json()
            if not new_data.get("access_token"):
                return None, "no_access_token"
            return new_data, "ok"
    except Exception as e:
        return None, str(e)

async def refresh_all_tokens():
    accounts = load_tokens()
    if not accounts: return

    print(f"\n{C.CYAN}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.CYAN}║{C.BOLD}{C.WHITE}   AUTO REFRESH TOKEN{' ' * 32}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╚══════════════════════════════════════════════════════╝{C.RESET}")
    print(f"  {C.GRAY}Total: {len(accounts)} token{C.RESET}\n")

    success = 0; fail = 0; updated = []

    async with aiohttp.ClientSession() as session:
        for i, acc in enumerate(accounts, 1):
            wallet = acc.get("wallet_address") or "?"
            label = short_addr(wallet)
            print(f"  {C.CYAN}[{i}/{len(accounts)}]{C.RESET} {label:<20} ", end="", flush=True)

            new_data, status = await refresh_one_token(session, acc)
            if new_data:
                new_cookie = build_cookie_string(new_data)
                new_wallet = extract_wallet_from_cookie(new_cookie) or wallet
                updated.append({
                    "user_id": new_data.get("user", {}).get("id") or acc.get("user_id"),
                    "token": new_cookie,
                    "device_id": acc.get("device_id"),
                    "wallet_address": new_wallet
                })
                success += 1
                print(f"{C.GREEN}✓ refreshed{C.RESET}")
            else:
                fail += 1
                print(f"{C.RED}✗ {status[:50]}{C.RESET}")
                updated.append(acc)
            await asyncio.sleep(0.5)

    with open(TOKEN_FILE, "w") as f:
        json.dump(updated, f, indent=2)

    print(f"\n  {C.GREEN}OK{C.RESET}: {success} | {C.RED}FAIL{C.RESET}: {fail}\n")
    time.sleep(1.5)

def get_headers(cookie_token):
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-A217F Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not A(Brand";v="99"',
        "sec-ch-ua-mobile": "?1", "sec-ch-ua-platform": '"Android"',
        "x-requested-with": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://drama.center", "Referer": "https://drama.center/",
        "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty",
        "Cookie": cookie_token,
    }

async def process_account_tick(batch_id, session, account_data, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event, capped_set, capped_lock, dead_tokens, dead_wallets):
    token = account_data.get("token")
    if token in dupe_tokens: return

    async with capped_lock:
        if token in capped_set:
            return

    await global_pause.wait()
    headers = get_headers(token)
    try:
        async with session.get("https://drama.center/api/auth/me", headers=headers, timeout=10) as auth_res:
            auth_json = await auth_res.json()
            if not auth_json.get("success"): return
            user_info = auth_json.get("user", {})
            account_id = user_info.get("id")
            wallet = user_info.get("wallet_address")
            acc_label = wallet or account_id
            async with progress_lock:
                if account_id in active_ids and active_ids[account_id] != token:
                    dupe_tokens.add(token)
                    if len(dupe_tokens) >= (total_accounts * 0.5): regen_event.set()
                    return
                active_ids[account_id] = token
            device_id = account_data.get("device_id") or str(uuid.uuid4())
    except Exception: return

    async with progress_lock:
        if account_id not in all_progress: all_progress[account_id] = {}
        account_progress = all_progress[account_id]

    await global_pause.wait()
    try:
        async with session.get("https://drama.center/api/dramas?sort=popular&limit=1000&language=en", headers=headers, timeout=10) as res:
            res_json = await res.json()
            dramas_data = res_json.get("data", [])
    except Exception: return

    for drama in dramas_data:
        await global_pause.wait()
        drama_id = drama["id"]
        if account_progress.get(drama_id, {}).get("completed"): continue
        try:
            async with session.get(f"https://drama.center/api/dramas/{drama_id}", headers=headers, timeout=10) as ep_res:
                ep_json = await ep_res.json()
                episodes = ep_json.get("data", {}).get("episodes", [])
        except Exception: continue
        if not episodes: continue
        total_episodes = len(episodes)
        last_saved_ep = account_progress.get(drama_id, {}).get("last_episode", 0)
        if last_saved_ep >= total_episodes:
            async with progress_lock:
                account_progress[drama_id]["completed"] = True
                save_progress(all_progress)
            continue
        ep_idx = last_saved_ep
        ep_id = episodes[ep_idx]["id"]
        ep_number = ep_idx + 1
        try:
            await global_pause.wait()
            async with session.post(f"https://drama.center/api/dramas/{drama_id}/episodes/watch-tick", headers=headers, json={"episodeId": ep_id, "deviceId": device_id}, timeout=10) as tick_res:
                tick_json = await tick_res.json()
                tick_data = tick_json.get("data", {})
                credited = tick_data.get("credited", 0)
                reject_reason = tick_data.get("rejectReason")
                
                if credited > 0:
                    async with session.post("https://drama.center/api/watch-reward/collect", headers=headers, json={}, timeout=10) as collect_res:
                        collect_data = (await collect_res.json()).get("data", {})
                        print(f"{C.CYAN}[Batch {batch_id}] [{acc_label[:14]}] {C.GREEN}✅ Ep {ep_number}/{total_episodes} | +{credited} | Total: {collect_data.get('totalToday', 0)}{C.RESET}")
                    async with progress_lock:
                        account_progress[drama_id] = {"title": drama.get("title", "?"), "last_episode": ep_number, "total_episodes": total_episodes, "completed": ep_number == total_episodes}
                        all_progress[account_id] = account_progress
                        save_progress(all_progress)
                
                elif reject_reason == "episode_maxed":
                    async with progress_lock:
                        account_progress[drama_id] = {"title": drama.get("title", "?"), "last_episode": ep_number, "total_episodes": total_episodes, "completed": ep_number == total_episodes}
                        all_progress[account_id] = account_progress
                        save_progress(all_progress)
                
                elif reject_reason in ["user_daily_cap", "account_inactive"]:
                    print(f"{C.RED}⛔ [Batch {batch_id}] [{acc_label[:14]}] {reject_reason}. Ditandai untuk dihapus.{C.RESET}")
                    async with progress_lock:
                        dead_tokens.add(token)
                        if wallet: dead_wallets.add(wallet)
                    return "inactive"
                
                elif reject_reason == "ip_daily_cap":
                    async with capped_lock:
                        capped_set.add(token)
                        save_capped(capped_set)
                        capped_count = len(capped_set)
                    print(f"{C.YELLOW}⛔ [Batch {batch_id}] [{acc_label[:14]}] IP daily cap — akun ditandai capped ({capped_count}/{total_accounts}){C.RESET}")

                    if capped_count >= total_accounts:
                        if global_pause.is_set():
                            async with pause_lock:
                                if global_pause.is_set():
                                    global_pause.clear()
                                    print(f"\n{C.RED}{C.BOLD}🚨 SEMUA AKUN KENA IP DAILY CAP!{C.RESET}")
                                    print(f"{C.RED}Menghentikan script...{C.RESET}")
                                    sys.exit(1)
                return
                
        except Exception: return

async def batch_worker(batch_id, batch_accounts, session, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event, capped_set, capped_lock, dead_tokens, dead_wallets):
    await global_pause.wait()
    valid = len([a for a in batch_accounts if a.get("token") not in dupe_tokens and a.get("token") not in capped_set])
    if valid > 0:
        print(f"{C.MAGENTA}{C.BOLD} [Batch {batch_id}] {valid} acc  [{time.strftime('%H:%M:%S')}]{C.RESET}")
    
    tasks = [process_account_tick(batch_id, session, a, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event, capped_set, capped_lock, dead_tokens, dead_wallets) for a in batch_accounts]
    await asyncio.gather(*tasks)

async def main():
    clear_screen()
    print(f"\n{C.CYAN}=== AUTO ==={C.RESET}\n")

    if os.path.exists(BNB_FILE) and os.path.exists(TOKEN_FILE):
        try:
            with open(BNB_FILE) as f: bnb = json.load(f)
            with open(TOKEN_FILE) as f: toks = json.load(f)
            bound_addrs = set()
            for t in toks:
                addr = t.get("wallet_address")
                if addr: bound_addrs.add(addr.lower())
            to_bind = [a for a in bnb if a.get("address") and a["address"].lower() not in bound_addrs]
            if to_bind:
                print(f"{C.YELLOW}⚠ Ada {len(to_bind)} wallet baru belum ke-bind. Binding...{C.RESET}\n")
                run_auto_login()
                time.sleep(2)
        except Exception:
            pass
    elif not os.path.exists(TOKEN_FILE) and os.path.exists(BNB_FILE):
        run_auto_login()

    accounts = load_tokens()
    if len(accounts) == 0:
        print(f"{C.RED}❌ 2token.json kosong!{C.RESET}")
        sys.exit(1)

    await refresh_all_tokens()

    accounts = load_tokens()
    total_acc = len(accounts)
    print(f"{C.GREEN}✅ {total_acc} account ready{C.RESET}")
    print(f"{C.GRAY}BATCH_SIZE={BATCH_SIZE} | Cooldown global {COOLDOWN_SECONDS}s{C.RESET}\n")
    time.sleep(2)

    capped_set = load_capped()
    if capped_set:
        print(f"{C.YELLOW}⚠ {len(capped_set)} akun udah capped hari ini (dari run sebelumnya){C.RESET}\n")

    capped_lock = asyncio.Lock()

    iter_num = 0
    async with aiohttp.ClientSession() as session:
        while True:
            iter_num += 1

            async with capped_lock:
                if len(capped_set) >= total_acc:
                    print(f"\n{C.RED}{C.BOLD}🚨 SEMUA AKUN CAPPED!{C.RESET}")
                    print(f"{C.RED}🚨 GitHub Actions tidak mendukung input manual. Menghentikan script...{C.RESET}")
                    sys.exit(1)

            print(f"\n{C.MAGENTA}╔══════════════════════════════════════════════════════╗{C.RESET}")
            print(f"{C.MAGENTA}║{C.BOLD}{C.WHITE}  🍯 ITER #{iter_num} - {total_acc} akun - {time.strftime('%H:%M:%S')}{' ' * 12}{C.MAGENTA}║{C.RESET}")
            print(f"{C.MAGENTA}╚══════════════════════════════════════════════════════╝{C.RESET}\n")

            batches = [accounts[i:i + BATCH_SIZE] for i in range(0, len(accounts), BATCH_SIZE)]
            all_progress = load_progress()
            progress_lock = asyncio.Lock()
            pause_lock = asyncio.Lock()
            global_pause = asyncio.Event()
            global_pause.set()
            active_ids = {}
            dupe_tokens = set()
            dead_tokens = set()
            dead_wallets = set()
            regen_event = asyncio.Event()

            workers = [asyncio.create_task(batch_worker(idx, accs, session, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, len(accounts), regen_event, capped_set, capped_lock, dead_tokens, dead_wallets)) for idx, accs in enumerate(batches, 1)]
            regen_task = asyncio.create_task(regen_event.wait())
            
            done, pending = await asyncio.wait(workers + [regen_task], return_when=asyncio.FIRST_COMPLETED)
            
            # 1. CLEANUP OTOMATIS
            if dead_tokens:
                print(f"\n{C.YELLOW}🧹 Membersihkan {len(dead_tokens)} akun inactive/capped dari file...{C.RESET}")
                
                accounts = [a for a in accounts if a.get("token") not in dead_tokens]
                with open(TOKEN_FILE, "w") as f:
                    json.dump(accounts, f, indent=2)
                
                if os.path.exists(BNB_FILE):
                    with open(BNB_FILE, "r") as f:
                        bnb_data = json.load(f)
                    bnb_data = [b for b in bnb_data if b.get("address") not in dead_wallets]
                    with open(BNB_FILE, "w") as f:
                        json.dump(bnb_data, f, indent=2)
                
                dead_tokens.clear()
                dead_wallets.clear()
                total_acc = len(accounts)
                print(f"{C.GREEN}✓ Bersih. Sisa akun aktif: {total_acc}{C.RESET}\n")

            if len(accounts) == 0:
                print(f"\n{C.RED}🚨 SEMUA AKUN INACTIVE/CAPPED.{C.RESET}")
                print(f"{C.YELLOW}⚠ Tidak ada akun tersisa. Script berhenti.{C.RESET}")
                break

            for t in pending:
                t.cancel()

            print(f"\n{C.GREEN}✓ Iter #{iter_num} selesai. Cooldown global {COOLDOWN_SECONDS}s...{C.RESET}\n")
            for s in range(COOLDOWN_SECONDS, 0, -1):
                print(f"\r{C.YELLOW}💤 Cooldown global: {s}s tersisa...{C.RESET}     ", end="", flush=True)
                await asyncio.sleep(1)
            print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}⚠ Stopped.{C.RESET}")
        sys.exit(0)
