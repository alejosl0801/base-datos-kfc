// Uso: node cifrar.js <archivo_json> <archivo_clave>  ->  imprime base64(salt16 | iv12 | ciphertext | tag16)
const fs = require('fs');
const crypto = require('crypto');
const [,, jsonPath, clavePath] = process.argv;
const clave = fs.readFileSync(clavePath, 'utf8').trim();
const data = fs.readFileSync(jsonPath);
const salt = crypto.randomBytes(16);
const iv = crypto.randomBytes(12);
const key = crypto.pbkdf2Sync(clave, salt, 600000, 32, 'sha256');
const c = crypto.createCipheriv('aes-256-gcm', key, iv);
const ct = Buffer.concat([c.update(data), c.final()]);
const tag = c.getAuthTag();
process.stdout.write(Buffer.concat([salt, iv, ct, tag]).toString('base64'));
