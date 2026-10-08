#include <stdio.h>
#include <stdlib.h>
#include <string.h>

//phan 1
int subtract(int x, int y)
{
return (x+(~y+1));
}

int cal100x(int x){
return (x<<6)+(x<<5)+(x<<2);
}

int getNibble(int x, int n){
int shift=n << 2;
return (x >> shift) & 0xF;
}

int clearByte(int x, int n){
return x & ~(0xFF<<(n<<3));
}

int mulpw2(int x, int n){
int pos_n=~n+1;
return x >> pos_n;
}

int remPw2(int x, int n){
int sign = x>>31;
int bias = (1<<n)+~0;
int q = (x + (bias & sign)) >>n;
return x + ~(q<<n) +1;
}

//phan 2
int isNegation(int x, int y){
int neg_x=~x+1;
return !(neg_x ^ y);
}

int isMul8Not16(int x){
return !(x&7) & !(!(x&8));
}

int isNonPositive(int x){
int sign=(x>>31)&1;
int is_zero=!x;
return sign|is_zero;
}

int isTopBit(int x, int n){
return !((x>>n) ^1);
}

int addOK(int x, int y){
int sum=x+y;
int signX=(x>>31)&1;
int signY=(y>>31)&1;
int signSum=(sum>>31)&1;
int overflow=!(signX ^ signY) & (signX ^ signSum);
return !overflow;
}

int allOddBits(int x){
int mask = 0xAA; //10101010
mask = mask | (mask<<8);
mask = mask | (mask<<16);
return !((x & mask) ^ mask);
}

//phan 3
unsigned float_nabs(unsigned uf) {
    if ((uf & 0x7FFFFFFF) > 0x7F800000) {
        return uf;
    }
    return uf | 0x80000000;
}
int float_sign(unsigned uf) {
    unsigned exp = (uf >> 23) & 0xFF;
    unsigned frac = uf & 0x7FFFFF;
    unsigned isZero = !(uf & 0x7FFFFFFF);
    unsigned isNaN = !(exp ^ 0xFF) & !!frac; 
    unsigned sign = (uf >> 31) & 1;
    return (isZero | isNaN) ? 0 : (sign ? -1 : 1);
}
unsigned float_pwr2(int x) {
    if (x < -149) {
        return 0;
     }
    if (x <= -127) {
        return 1 << (x + 149);
    }
    if (x <= 127) {
         return (x + 127) << 23;
    }
    return 0x7F800000;
}
int float_isInt(unsigned uf) {
    unsigned exp = (uf >> 23) & 0xFF;
    unsigned frac = uf & 0x7FFFFF;
    int E = exp - 127;
    if (exp == 0xFF) {
        return 0;
    }
    if (E < 0) {
        if ((uf & 0x7FFFFFFF) == 0) {
            return 1;
        }
        return 0;
    }
    if (E >= 23) {
        return 1;
    }
    if ((frac & ((1 << (23 - E)) - 1)) != 0) {
        return 0;
    }
    return 1;
}