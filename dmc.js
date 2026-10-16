const fs = require('fs');
const { Wallet } = require('ethers');

const count = parseInt(process.argv[2], 10) || 5;

if (!Number.isInteger(count) || count <= 0) {
    console.log("Invalid wallet amount. Usage: node bnb.js <count>");
    process.exit(1);
}

const wallets = [];
console.log(`\nGenerating ${count} EVM Wallet(s)...`);

for (let i = 0; i < count; i++) {
    const wallet = Wallet.createRandom();
    wallets.push({
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic.phrase
    });
    process.stdout.write(`\rGenerating: [${i + 1}/${count}]`);
}

console.log('\n');

fs.writeFileSync('2bnb.json', JSON.stringify(wallets, null, 2));

console.log(`Successfully generated ${count} EVM wallet(s).`);
console.log(`Saved to: 2bnb.json\n`);
