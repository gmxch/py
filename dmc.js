const fs = require('fs');
const { HDNodeWallet, Mnemonic } = require('ethers');

const count = parseInt(process.argv[2], 10) || 5;
const FILE = '2bnb.json';

if (!Number.isInteger(count) || count <= 0) {
    console.log("Invalid wallet amount. Usage: node dmc.js <count>");
    process.exit(1);
}

const SEED_MNEMONIC_B64 = process.env.SEED_MNEMONIC_B64;
if (!SEED_MNEMONIC_B64) {
    console.log("SEED_MNEMONIC_B64 env tidak diset!");
    process.exit(1);
}

let SEED_MNEMONIC;
try {
    SEED_MNEMONIC = Buffer.from(SEED_MNEMONIC_B64, 'base64').toString('utf-8').trim();
} catch (e) {
    console.log(`Gagal decode base64: ${e.message}`);
    process.exit(1);
}

if (!SEED_MNEMONIC) {
    console.log("Mnemonic kosong setelah decode!");
    process.exit(1);
}

const START_INDEX = Math.floor(Date.now() / 1000);

console.log(`\nDeriving ${count} wallet dari seed (start index = timestamp ${START_INDEX})...\n`);

const mnemonicObj = Mnemonic.fromPhrase(SEED_MNEMONIC);
const wallets = [];

for (let i = 0; i < count; i++) {
    const idx = START_INDEX + i;
    const wallet = HDNodeWallet.fromMnemonic(mnemonicObj, `m/44'/60'/0'/0/${idx}`);

    wallets.push({
        index: idx,
        address: wallet.address,
        privateKey: wallet.privateKey
    });
    process.stdout.write(`\r[${i + 1}/${count}] index=${idx} ${wallet.address.slice(0, 10)}...`);
}

console.log('\n');
fs.writeFileSync(FILE, JSON.stringify(wallets, null, 2));
console.log(`Saved ${wallets.length} wallet ke ${FILE}\n`);
