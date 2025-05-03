import CryptoJS from "crypto-js";

const secretKeyString = import.meta.env.VITE_AES_KEY;

if (!secretKeyString) throw new Error("VITE_AES_KEY is not defined in .env");

const secretKey = CryptoJS.enc.Utf8.parse(secretKeyString);

export const encrypt = (text) => {
    const iv = CryptoJS.lib.WordArray.random(16);
    const encrypted = CryptoJS.AES.encrypt(text, secretKey, {
        iv: iv,
        padding: CryptoJS.pad.Pkcs7,
        mode: CryptoJS.mode.CBC
    });

    return {
        iv: iv.toString(CryptoJS.enc.Base64),
        ciphertext: encrypted.ciphertext.toString(CryptoJS.enc.Base64)
    };
};

export const decrypt = (ciphertext, iv) => {
    const ivWordArray = CryptoJS.enc.Base64.parse(iv);
    const cipherParams = CryptoJS.lib.CipherParams.create({
        ciphertext: CryptoJS.enc.Base64.parse(ciphertext)
    });

    const decrypted = CryptoJS.AES.decrypt(cipherParams, secretKey, {
        iv: ivWordArray,
        padding: CryptoJS.pad.Pkcs7,
        mode: CryptoJS.mode.CBC
    });

    return decrypted.toString(CryptoJS.enc.Utf8);
};