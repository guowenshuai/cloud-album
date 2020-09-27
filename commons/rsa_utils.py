import pickle,base64
import rsa
from rsa.key import PrivateKey,PublicKey



class RsaCipher:

    def new(self,size=256):
        pubkey,privkey = rsa.newkeys(size)
        return pubkey,privkey

    @staticmethod
    def encrypt(message,pubkey):
        crypto = rsa.encrypt(message,pubkey)
        return crypto

    @staticmethod
    def decrypt(crypto,privkey):
        raw = rsa.decrypt(crypto,privkey)
        return raw

    @staticmethod
    def dumps(obj):
        '''将公私钥对象转换为base64编码字节串'''
        byte_obj = base64.b64encode(pickle.dumps(obj))
        return byte_obj

    @staticmethod
    def loads(byte_obj):
        '''将base64编码字节串转换为公私钥对象'''
        obj = pickle.loads(base64.b64decode(byte_obj))
        return obj

    @staticmethod
    def priv_gen_pub(priv):
        """
        通过私钥生成公钥
        :param priv:
        :param pub:
        :return:
        """
        if isinstance(priv,PrivateKey):
            return PublicKey(priv.n,priv.e)
        raise TypeError()


if __name__ == '__main__':
    rsacipher = RsaCipher()
    pub,pri = rsacipher.new()
    print(rsacipher.dumps(pri))