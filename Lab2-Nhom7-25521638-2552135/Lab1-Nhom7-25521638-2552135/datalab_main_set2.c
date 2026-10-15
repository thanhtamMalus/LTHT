/*
 * datalab_main_set2.c — File main mẫu cho Lab01 Bộ đề 2 (lớp ANTT.2). SINH VIÊN KHÔNG SỬA FILE NÀY.
 *
 * Sinh viên chỉ viết 16 hàm trong file datalab.c (KHÔNG có hàm main), rồi build chung với file này:
 *     gcc -O1 -Wall -fwrapv datalab.c datalab_main_set2.c -o datalab.exe
 *   (nếu viết bằng C++: đổi tên file này thành .cpp, hoặc: g++ -O1 -fwrapv datalab.cpp -x c++ datalab_main_set2.c -o datalab.exe)
 *
 * Cách chạy:  datalab.exe <tên_hàm> <tham số...>      ví dụ: datalab.exe getNibble 0x12345678 5
 * Kết quả in ra đúng 1 dòng dạng 0xXXXXXXXX (32 bit). Tham số nhận dạng thập phân, hex (0x...) hoặc số âm.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int subtract(int x, int y);
int cal100x(int x);
int getNibble(int x, int n);
int clearByte(int x, int n);
int mulpw2(int x, int n);
int remPw2(int x, int n);
int isNegation(int x, int y);
int isMul8Not16(int x);
int isNonPositive(int x);
int isTopBit(int x, int n);
int addOK(int x, int y);
int allOddBits(int x);
unsigned float_nabs(unsigned uf);
int float_sign(unsigned uf);
unsigned float_pwr2(int x);
int float_isInt(unsigned uf);

/* Đọc tham số thứ i thành số 64 bit rồi để lời gọi hàm tự cắt về int/unsigned 32 bit. */
static long long arg_at(int argc, char **argv, int i) {
    char *end = NULL;
    long long v;
    if (i + 2 >= argc) { fprintf(stderr, "ERROR: thieu tham so thu %d\n", i + 1); exit(2); }
    v = strtoll(argv[i + 2], &end, 0);
    if (end == argv[i + 2] || *end != '\0') { fprintf(stderr, "ERROR: tham so khong hop le: %s\n", argv[i + 2]); exit(2); }
    return v;
}

#define A(i) arg_at(argc, argv, (i))
#define CALL1(f) if (strcmp(fn, #f) == 0) { r = (unsigned)f(A(0)); found = 1; }
#define CALL2(f) if (strcmp(fn, #f) == 0) { r = (unsigned)f(A(0), A(1)); found = 1; }

int main(int argc, char **argv) {
    const char *fn;
    unsigned r = 0;
    int found = 0;
    if (argc < 2) { fprintf(stderr, "Cach dung: %s <ten_ham> <tham so...>\n", argv[0]); return 2; }
    fn = argv[1];
    CALL2(subtract) CALL1(cal100x) CALL2(getNibble) CALL2(clearByte) CALL2(mulpw2) CALL2(remPw2)
    CALL2(isNegation) CALL1(isMul8Not16) CALL1(isNonPositive) CALL2(isTopBit) CALL2(addOK) CALL1(allOddBits)
    CALL1(float_nabs) CALL1(float_sign) CALL1(float_pwr2) CALL1(float_isInt)
    if (!found) { fprintf(stderr, "ERROR: khong co ham %s\n", fn); return 2; }
    printf("0x%08X\n", r);
    return 0;
}
