import asyncio
import json
import os
import random
import sys
import time
import uuid
import hashlib
import shutil
import base64
import aiohttp

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    print("❌ pycryptodome not installed. Run: pip install pycryptodome")
    sys.exit(1)

PROGRESS_FILE = "selesai.json"
TOKEN_FILE = "token.json"
BATCH_SIZE = 10
COOLDOWN_SECONDS = 90

USER_REFERRAL_URI = "https://drama.center/?ref=JTXMEM"
USER_REFERRAL_ID = "JTXMEM"

RAW_KEY = os.environ.get("ENCRYPTION_KEY", "")


class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


AUTO_LOGIN_JS_TEMPLATE = r"""const { Wallet } = require("ethers");
const axios = require("axios");
const fs = require("fs");

const colors = {
    cyan: "\x1b[36m", reset: "\x1b[0m", bold: "\x1b[1m", yellow: "\x1b[33m", green: "\x1b[32m"
};
const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

function getRandomIp() {
  return `${Math.floor(Math.random() * 254) + 1}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 254) + 1}`;
}

function loadJson(filepath) {
  try {
    if (fs.existsSync(filepath)) {
      const data = fs.readFileSync(filepath, "utf8");
      return JSON.parse(data);
    }
  } catch (error) {
    console.error(`[-] Error reading ${filepath}:`, error.message);
  }
  return [];
}

function saveJson(filepath, data) {
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2), "utf8");
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function executeSignIn() {
  const accounts = loadJson("bnb.json");
  if (accounts.length === 0) {
    console.log("[-] bnb.json was not found or is empty.");
    process.exit(1);
  }

  const existingTokens = loadJson("token.json");
  const tokenMap = {};
  existingTokens.forEach((item) => { if (item.user_id) tokenMap[item.user_id] = item; });

  const authHeaders = {
    'sec-ch-ua-platform': '"Android"', 'x-supabase-api-version': "2024-01-01",
    'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
    'sec-ch-ua-mobile': "?1", 'x-client-info': "supabase-ssr/0.12.5 createBrowserClient",
    'content-type': "application/json;charset=UTF-8",
    'apikey': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRhZ3hoaXB5bGtvYnlndXZpZWRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcyNjk5NDksImV4cCI6MjEwMjg0NTk0OX0.P6JmfYhruL3LZGEnfXbS85HE4ABerldH9zyHtWEo3vc",
    'origin': "https://drama.center", "x-forwarded-for": getRandomIp(),
    'sec-fetch-site': "cross-site", 'sec-fetch-mode': "cors", 'sec-fetch-dest': "empty",
    'referer': "https://drama.center/", 'accept-language': "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7", 'priority': "u=1, i"
  };

  const domain = "drama.center";
  const uri = "__USER_URI__";
  const version = "1";
  const chainId = 1;
  const TARGET_URL = "https://tagxhipylkobyguviedc.supabase.co/auth/v1/token?grant_type=web3";
  const REF_URL = "https://drama.center/api/referrals";

  for (let i = 0; i < accounts.length; i++) {
    const acc = accounts[i];
    if (!acc.privateKey) continue;

    const wallet = new Wallet(acc.privateKey);
    const address = wallet.address;
    const frame = frames[i % frames.length];
    const percent = Math.floor(((i + 1) / accounts.length) * 100);

    process.stdout.write(`\n${colors.cyan}${frame}${colors.reset} ${colors.bold}Processing EVM Wallets${colors.reset} ${colors.yellow}[${i + 1}/${accounts.length}]${colors.reset} ${colors.green}${percent}%${colors.reset} - ${address}\n`);

    const issuedAt = new Date().toISOString();
    const message = `${domain} wants you to sign in with your Ethereum account:\n${address}\n\nSign in to DramaCenter.\n\nURI: ${uri}\nVersion: ${version}\nChain ID: ${chainId}\nIssued At: ${issuedAt}`;

    try {
      const signature = await wallet.signMessage(message);
      const payload = { chain: "ethereum", message: message, signature: signature };

      const authResponse = await axios.post(TARGET_URL, payload, { headers: { ...authHeaders, "x-forwarded-for": getRandomIp() } });
      const authData = authResponse.data;
      const user_id = authData.user?.id;

      if (!user_id) {
        console.log("[-] Failed to obtain user_id from response.");
      } else {
        console.log(`[+] Login successful! User ID: ${user_id}`);
        const base64Encoded = Buffer.from(JSON.stringify(authData)).toString('base64');
        const formattedToken = `sb-tagxhipylkobyguviedc-auth-token.0=base64-${base64Encoded}`;

        const targetReferral = (i % 10 < 7) ? "__USER_REF_ID__" : "JTXMEM";
        try {
          const refResponse = await axios.post(REF_URL, { referrer_id: targetReferral, referred_id: user_id }, {
            headers: { "Content-Type": "application/json", "Origin": "https://drama.center", "Referer": "https://drama.center/", "x-forwarded-for": getRandomIp() }
          });
          console.log(`[+] Referral Status: ${refResponse.status} OK (Bind to: ${targetReferral})`);
        } catch (refError) {
          console.log(`[-] Referral Error: ${refError.response ? JSON.stringify(refError.response.data) : refError.message}`);
        }

        tokenMap[user_id] = { user_id: user_id, token: formattedToken };
        saveJson("token.json", Object.values(tokenMap));
        console.log(`[+] Data saved (Merge Update) to token.json`);
      }
    } catch (error) {
      console.error(`[-] Error on Address ${address}:`, error.response ? JSON.stringify(error.response.data) : error.message);
    }

    if (i < accounts.length - 1) {
      for (let s = 0; s < 70; s++) {
          process.stdout.write(`\r${colors.cyan}${frames[s % frames.length]}${colors.reset} ${colors.yellow}Sleeping for 7 seconds to avoid rate limits...${colors.reset}`);
          await sleep(100);
      }
      process.stdout.write('\r\x1b[K');
    }
  }
  console.log(`\n[+] Complete! Total ${Object.values(tokenMap).length} data entries in token.json`);
}
executeSignIn();
"""


# ================= DECRYPTION LOGIC =================
def get_aes_key(raw_key):
    return hashlib.sha256(raw_key.encode()).digest()

def decrypt_data(encrypted_str, key):
    iv_b64, ct_b64 = encrypted_str.split(':')
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ct_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode('utf-8')

def decrypt_wallets():
    if os.path.exists("bnb.json.enc"):
        print(f"{C.CYAN}🔓 Decrypting bnb.json.enc...{C.RESET}")
        with open("bnb.json.enc", "r") as f:
            encrypted_str = f.read().strip()
        
        aes_key = get_aes_key(RAW_KEY)
        try:
            decrypted_json = decrypt_data(encrypted_str, aes_key)
            with open("bnb.json", "w") as f:
                f.write(decrypted_json)
            print(f"{C.GREEN}✅ Wallets decrypted successfully.{C.RESET}\n")
        except Exception as e:
            print(f"{C.RED}❌ Decryption failed: {e}{C.RESET}")
            sys.exit(1)
    elif not os.path.exists("bnb.json"):
        print(f"{C.RED}❌ Neither bnb.json.enc nor bnb.json found!{C.RESET}")
        sys.exit(1)
# ====================================================


def clear_screen():
    sys.stdout.write("\033[H\033[2J\033[3J")
    sys.stdout.flush()

def get_term_width():
    cols, _ = shutil.get_terminal_size((50, 20))
    return min(cols, 60)

def print_main_banner():
    clear_screen()
    w = get_term_width() - 2
    border = "─" * w
    print(f"{C.MAGENTA}╭{border}╮{C.RESET}")
    print(f"{C.MAGENTA}│{C.BOLD}{C.CYAN}{'🎬 DRAMA WATCH AUTOMATION v2.0':^{w}}{C.MAGENTA}│{C.RESET}")
    print(f"{C.MAGENTA}│{C.WHITE}{'⚡ Multi-Worker Independent Batch':^{w}}{C.MAGENTA}│{C.RESET}")
    print(f"{C.MAGENTA}│{C.BLUE}{'🔥 SYNDICATEBOT NET - GITHUB ACTIONS':^{w}}{C.MAGENTA}│{C.RESET}")
    print(f"{C.MAGENTA}╰{border}╯{C.RESET}\n")


def generate_random_ip():
    return f"{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def load_tokens():
    if not os.path.exists(TOKEN_FILE): return []
    try:
        with open(TOKEN_FILE, "r") as f: raw_data = json.load(f)
        unique_accounts, seen_ids = [], set()
        for item in raw_data:
            uid = item.get("user_id") or item.get("token")
            if uid and uid not in seen_ids:
                seen_ids.add(uid)
                unique_accounts.append(item)
        return unique_accounts
    except Exception:
        return []

def run_auto_login():
    print(f"\n{C.RED}{C.BOLD}♻️  CLEARING OLD {TOKEN_FILE} & STARTING AUTO-LOGIN FROM bnb.json...{C.RESET}")
    if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)

    auto_js = AUTO_LOGIN_JS_TEMPLATE.replace("__USER_URI__", USER_REFERRAL_URI).replace("__USER_REF_ID__", USER_REFERRAL_ID)
    with open("auto_login.js", "w", encoding="utf-8") as f:
        f.write(auto_js)

    print(f"{C.CYAN}ℹ️  Required Node.js libraries: {C.WHITE}npm install ethers axios{C.RESET}")
    os.system("node auto_login.js")
    print(f"{C.GREEN}{C.BOLD}✅ Token generation complete! Reloading token.json...{C.RESET}\n")
    time.sleep(2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f: return json.load(f)
        except Exception: return {}
    return {}

def save_progress(progress_data):
    with open(PROGRESS_FILE, "w") as f: json.dump(progress_data, f, indent=2)

def get_headers(cookie_token):
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-A217F Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.87 Mobile Safari/537.36",
        "sec-ch-ua-platform": '"Android"', "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
        "sec-ch-ua-mobile": "?1", "sec-fetch-site": "same-origin", "sec-fetch-mode": "cors", "sec-fetch-dest": "empty",
        "accept-language": "en-US,en;q=0.9", "X-Forwarded-For": generate_random_ip(), "Cookie": cookie_token,
    }


async def process_account_tick(batch_id, session, account_data, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event):
    token = account_data.get("token")
    if token in dupe_tokens: return

    await global_pause.wait()
    headers = get_headers(token)
    auth_url = "https://drama.center/api/auth/me"

    try:
        async with session.get(auth_url, headers=headers, timeout=10) as auth_res:
            auth_json = await auth_res.json()
            if not auth_json.get("success"): return

            user_info = auth_json.get("user", {})
            account_id = user_info.get("id")
            email = user_info.get("email")
            wallet = user_info.get("wallet_address")
            acc_label = wallet or email or account_id

            async with progress_lock:
                if account_id in active_ids and active_ids[account_id] != token:
                    dupe_tokens.add(token)
                    print(f"{C.YELLOW}⚠️  [Batch {batch_id}] 👤 [{acc_label[:14]}] Duplicate detected in token.json! (Skipped){C.RESET}")
                    if len(dupe_tokens) >= (total_accounts * 0.5): regen_event.set()
                    return
                else:
                    active_ids[account_id] = token

            device_id = str(uuid.UUID(hashlib.md5(account_id.encode()).hexdigest()))
    except Exception:
        return

    async with progress_lock:
        if account_id not in all_progress: all_progress[account_id] = {}
        account_progress = all_progress[account_id]

    await global_pause.wait()

    try:
        dramas_api_url = "https://drama.center/api/dramas?sort=popular&limit=1000&language=en"
        async with session.get(dramas_api_url, headers=headers, timeout=10) as res:
            res_json = await res.json()
            dramas_data = res_json.get("data", [])
    except Exception:
        return

    for drama in dramas_data:
        await global_pause.wait()
        drama_id = drama["id"]
        drama_title = drama.get("title", "Unknown Title")

        if account_progress.get(drama_id, {}).get("completed"): continue

        episodes_url = f"https://drama.center/api/dramas/{drama_id}"
        try:
            async with session.get(episodes_url, headers=headers, timeout=10) as ep_res:
                ep_json = await ep_res.json()
                episodes = ep_json.get("data", {}).get("episodes", [])
        except Exception:
            continue

        if not episodes: continue

        total_episodes = len(episodes)
        last_saved_ep = account_progress.get(drama_id, {}).get("last_episode", 0)

        if last_saved_ep >= total_episodes:
            async with progress_lock:
                account_progress[drama_id]["completed"] = True
                save_progress(all_progress)
            continue

        ep_idx = last_saved_ep
        ep = episodes[ep_idx]
        ep_id = ep["id"]
        ep_number = ep_idx + 1
        tick_url = f"https://drama.center/api/dramas/{drama_id}/episodes/watch-tick"
        payload = {"episodeId": ep_id, "deviceId": device_id}

        try:
            await global_pause.wait()
            async with session.post(tick_url, headers=headers, json=payload, timeout=10) as tick_res:
                tick_json = await tick_res.json()
                tick_data = tick_json.get("data", {})
                credited = tick_data.get("credited", 0)
                reject_reason = tick_data.get("rejectReason")

                if credited > 0:
                    collect_url = "https://drama.center/api/watch-reward/collect"
                    async with session.post(collect_url, headers=headers, json={}, timeout=10) as collect_res:
                        collect_json = await collect_res.json()
                        collect_data = collect_json.get("data", {})
                        print(f"{C.CYAN}[Batch {batch_id}] 👤 [{acc_label[:14]}] {C.GREEN}✅ Episode {ep_number}/{total_episodes} | Credited: {credited} | Total: {collect_data.get('totalToday', 0)}{C.RESET}")

                    async with progress_lock:
                        account_progress[drama_id] = { "title": drama_title, "last_episode": ep_number, "total_episodes": total_episodes, "completed": (ep_number == total_episodes) }
                        all_progress[account_id] = account_progress
                        save_progress(all_progress)

                elif reject_reason == "episode_maxed":
                    print(f"{C.CYAN}[Batch {batch_id}] 👤 [{acc_label[:14]}] {C.BLUE}⏩ Episode {ep_number}/{total_episodes} | Episode limit reached (Skipping){C.RESET}")
                    async with progress_lock:
                        account_progress[drama_id] = { "title": drama_title, "last_episode": ep_number, "total_episodes": total_episodes, "completed": (ep_number == total_episodes) }
                        all_progress[account_id] = account_progress
                        save_progress(all_progress)

                elif reject_reason == "ip_daily_cap":
                    print(f"{C.CYAN}[Batch {batch_id}] 👤 [{acc_label[:14]}] {C.RED}⛔ Episode {ep_number}/{total_episodes} | Status: ip_daily_cap{C.RESET}")
                    print(f"{C.YELLOW}⚠️ CI Environment: IP cap reached. Skipping remaining episodes for this account.{C.RESET}")
                    break 

                else:
                    print(f"{C.CYAN}[Batch {batch_id}] 👤 [{acc_label[:14]}] {C.YELLOW}⚠️  Episode {ep_number}/{total_episodes} | Status: {reject_reason or 'No Reward'}{C.RESET}")
                return
        except Exception:
            return


async def batch_worker(batch_id, batch_accounts, session, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event):
    while True:
        await global_pause.wait()
        start_time = time.time()
        timestamp = time.strftime("%H:%M:%S")

        valid_accounts_count = len([acc for acc in batch_accounts if acc.get("token") not in dupe_tokens])

        if valid_accounts_count > 0:
            print(f"{C.MAGENTA}{C.BOLD}🚀 [Batch {batch_id}] Running {valid_accounts_count} valid account(s) simultaneously 🕒 [{timestamp}]{C.RESET}")

        tasks = [process_account_tick(batch_id, session, acc, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event) for acc in batch_accounts]
        await asyncio.gather(*tasks)

        if regen_event.is_set(): break

        elapsed = time.time() - start_time
        sleep_needed = max(0, COOLDOWN_SECONDS - elapsed)

        if valid_accounts_count > 0:
            print(f"{C.GREEN}✔️  [Batch {batch_id}] Completed ({round(elapsed, 2)}s). Cooldown: {round(sleep_needed, 1)}s...{C.RESET}")

        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for second in range(int(sleep_needed)):
            if regen_event.is_set(): break
            await global_pause.wait()
            frame = spinner[second % len(spinner)]
            print(f"\r{C.BLUE}{frame}{C.RESET} {C.CYAN}[Batch {batch_id}] Cooldown remaining: {C.YELLOW}{int(sleep_needed) - second}s{C.RESET}", end="", flush=True)
            await asyncio.sleep(1)
        print()


async def main():
    decrypt_wallets()
    
    print(f"{C.GREEN}{C.BOLD}✅ Using hardcoded referral: {USER_REFERRAL_ID}{C.RESET}\n")

    while True:
        print_main_banner()
        accounts = load_tokens()
        total_accounts = len(accounts)

        if total_accounts == 0:
            print(f"{C.YELLOW}{C.BOLD}⚠️  token.json is missing or empty!{C.RESET}")
            run_auto_login()
            accounts = load_tokens()
            total_accounts = len(accounts)
            if total_accounts == 0:
                print(f"{C.RED}{C.BOLD}❌ Token generation failed. Please make sure bnb.json is valid!{C.RESET}")
                sys.exit(1)

        print(f"{C.GREEN}{C.BOLD}✅ Loaded {total_accounts} initial account(s) from '{TOKEN_FILE}'{C.RESET}")
        print(f"{C.CYAN}🔗 Active Referral ID: {C.WHITE}{USER_REFERRAL_ID}{C.RESET}\n")

        batches = [accounts[i : i + BATCH_SIZE] for i in range(0, total_accounts, BATCH_SIZE)]
        all_progress = load_progress()

        progress_lock = asyncio.Lock()
        pause_lock = asyncio.Lock()
        global_pause = asyncio.Event()
        global_pause.set()

        active_ids = {}
        dupe_tokens = set()
        regen_event = asyncio.Event()

        async with aiohttp.ClientSession() as session:
            workers = []
            for batch_idx, batch_accs in enumerate(batches, start=1):
                task = asyncio.create_task(batch_worker(batch_idx, batch_accs, session, all_progress, progress_lock, global_pause, pause_lock, active_ids, dupe_tokens, total_accounts, regen_event))
                workers.append(task)
                await asyncio.sleep(1)

            regen_task = asyncio.create_task(regen_event.wait())
            done, pending = await asyncio.wait(workers + [regen_task], return_when=asyncio.FIRST_COMPLETED)

            if regen_event.is_set():
                print(f"\n{C.RED}{C.BOLD}🚨 TOO MANY DUPLICATE ACCOUNTS DETECTED (>50%){C.RESET}")
                print(f"{C.YELLOW}{C.BOLD}♻️  Force-stopping all batches and restarting the login process...{C.RESET}")
                for task in pending: task.cancel()
                run_auto_login()
                continue
            else:
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}{C.BOLD}⚠️  Program stopped by user. Progress has been saved.{C.RESET}")
        sys.exit(0)