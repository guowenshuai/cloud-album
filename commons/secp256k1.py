import binascii
import random

_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_b = 0x0000000000000000000000000000000000000000000000000000000000000007
_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
"""
椭圆曲线方程为：y^2=x^3+ax+b，这里的a,b对应上面的_a,_b

私钥和公钥：
K=k*G
G为选取的曲线上固定一个点，坐标就是(_Gx,_Gy)
k就是私钥，私钥就是一个数字，公钥就是k乘G后得到的点的坐标
   随机生成k=random.randint(1,_r)
   
为了避免公钥取小数，两边对_p取模（mod是求模运算），这是比特币的椭圆曲线方程：
y^2modp=(x^3+ax+b)modp
_r是一个和_P相关的参数，私钥不能大于_r

椭圆曲线上点运算：
定义两个点P+Q等于P,Q连线与椭圆曲线相交点关于x轴对称点R，R坐标可由P,Q两点坐标求出：
Xr = (l^2-Xp-Xq)mod _p
Yr = (l(Xp-Xr)-Yp)mod _p
其中 l = (Yq-Yp)*(Xq-Xp)^-1 mod _p
若P=Q，则2P等于过P点做椭圆曲线切线交椭圆的点关于x轴对称的点R，其中：
Xr = (l^2-2Xp)mod _p
Yr = (l(Xp-Xr)-Yp)mod _p
其中 l = (3Xp^2+a)*(2Yp)^-1 mod _p

根据上面的公式我们就能通过私钥算出公钥了，但是还有一个问题（分数如何求模）
（a/b)mod p ====>(a*b^-1)mod p 难就难在如何求b^-1mod p，我们把这种求模
称为求逆元

"""
#  扩展欧几里得算法求逆元（递归法）
def exgcd(a,b):
    if b==0:
        return 1,0
    else:
        k=a//b
        remainder = a%b
        x1,y1 = exgcd(b,remainder)
        x,y = y1,x1-k*y1
    return x,y

#  扩展欧几里得算法求逆元（顺序计算）
def inv_mod(b, p):
    if b < 0 or p <= b:
        b = b % p
    c, d = b, p
    uc, vc, ud, vd = 1, 0, 0, 1
    while c != 0:
        q, c, d = divmod(d, c) + (c,)
        uc, vc, ud, vd = ud - q * uc, vd - q * vc, uc, vc
    assert d == 1
    if ud > 0:
        return ud
    else:
        return ud + p


def double(x,y,p=_p,a=_a,b=_b):
    l = ((3 * x * x + a) * inv_mod(2 * y,p)) % p
    x3 = (l * l -2 * x) % p
    y3 = (l *(x - x3) - y) % p
    return x3,y3

def add(x1,y1,x2,y2,p=_p,a=_a,b=_b):
    if x1 == x2 and y1 == y2:
        return double(x1,y1,p,a,b)
    l = ((y2 - y1) * inv_mod(x2 - x1,p)) % p
    x3 = (l * l - x1 - x2) % p
    y3 = (l * (x1 - x3) - y1) % p
    return x3,y3

# 定义一个曲线
class CurveFp(object):

    def __init__(self, p=_p, a=_a, b=_b):
        """ y^2 = x^3 + a*x + b (mod p)."""
        self.p = p
        self.a = a
        self.b = b

    # 判断给出的点在不在曲线内
    def contains_point(self, x, y):
        return (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0

    # 返回有限域内所有符合的点
    def show_all_points(self):
        return [(x, y) for x in range(self.p) for y in range(self.p) if
                (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0]

    def __repr__(self):
        return "Curve(p={0:d}, a={1:d}, b={2:d})".format(self.p, self.a, self.b)

# 定义一个椭圆曲线加密类
class Ecc(object):
    def __init__(self,curv=CurveFp(),G=(_Gx,_Gy),P=_p,R=_r):
        self.curv = curv
        self.G= G
        self.P = P
        self.R = R

    #返回公私钥
    def new(self):
        private = self.private()
        public = self.public(private)
        return private,public


    def numer_to_bytes(self,num,l):
        fmt_str = "%0" + str(2 * l) + "x"
        string = binascii.unhexlify((fmt_str % num).encode())
        return string

    # 随机生成私钥16进制的
    def private(self):
        n = random.randint(1,self.R)
        pri = hex(n)
        return pri

    # 通过私钥生成公钥，这里我取得是g点的x轴作为公钥，后续待定
    def public(self,private):
        if private == 0 or int(private,16)>=self.R:
            raise Exception('私钥不符合要求')
        private = str(bin(int(private,16)))[2:]
        for i in range(1,len(private)):
            g = double(self.G[0],self.G[1])
            if private[i] =='1':
                g=add(g[0],g[1],self.G[0],self.G[1])

        return hex(g[0])

    #todo
    def sign(self):
        pass

    def verify(self):
        pass


if __name__ == '__main__':
   ecc = Ecc()
   pri,pub= ecc.new()
   print(pri,pub)
