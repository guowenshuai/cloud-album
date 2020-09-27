from Crypto.Cipher import AES
import Crypto.Random
import base64
from Crypto.Util.Padding import pad,unpad
from hashlib import md5

BLOCK_SIZE =32

def auto_fill(x):
    if len(x) <= 32:
        while len(x) not in [16, 24, 32]:
            x += " "
        return x.encode()
    else:
        raise Exception('密钥长度不能大于32位！')
#
# def pad(s):
#     """
#     补充字符，最少一个
#     """
#     length = len(s)
#     add = BS - length % BS
#     byte = chr(add).encode()
#     return s + byte * add
#
#
# def unpad(s):
#     """
#     去除字符
#     :param s:
#     :return:
#     """
#     length = len(s)
#     byte = s[length - 1:]
#     add = ord(byte)
#     return s[:-add]


class AESCipher:

    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(auto_fill(key), Crypto.Cipher.AES.MODE_ECB)

    def encrypt(self, raw:bytes):
        '''加密'''
        enc = base64.b64encode(self.cipher.encrypt(pad(raw,BLOCK_SIZE)))
        return enc

    def decrypt(self, enc:bytes):
        '''解密'''
        return unpad(self.cipher.decrypt(base64.b64decode(enc)),BLOCK_SIZE)

if __name__ == '__main__':
    # 注意key是16字节长
    key = "f2c85e0140a47415"
    raw = '0xb0235863192b323724d8e9ab490c94704e99e9b369f6c1f491157a8c7b985afa752d28994db66cd9904beeccd65269a46e35e4191a39ff4057ed2fbce38f3834771802b14675199efae2cd3d0f5219dbff7c07e5911263b28b8781964b6f6280d832a075a8c282ceccefad805eb63c0f87f1a23c9d23f843dc578740443979da8fb1cf4fe28b89f97d6d2acd8bb7b052ae2523aff4c4117218c1fa7ba97180313fb18deb5130ad2214952c9f830b1a8bb84a2d29c0f6780d8b0093b1bc9e3da6983c4411e45d7c7f9c4b4d55f389bb750bcf1578a2f33f04d4c20d96d0760625d80b41ae41f283170f91ef9cf0ec94d61fb8e7708bde7df46b8ae839944f9f19'
    aes = AESCipher(key)
    enc = aes.encrypt(raw.encode())
    print(enc)
    raw = aes.decrypt(enc)
    print(raw)
