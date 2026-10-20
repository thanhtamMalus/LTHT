#Khai bao data
.section .data
msg:
    .string "NT209UIT"
msg_len = . - msg - 1

ascii_len:
    .ascii "0\n"

.section .text
.globl _start

_start:
#Xu li do dai chuoi
    movl $msg_len, %eax
    addb $'0', %al
    movb %al, ascii_len
#In ket qua
    movl $4, %eax
    movl $1, %ebx
    movl $ascii_len, %ecx
    movl $2, %edx
    int $0x80
#Ket thuc chuong trinh
    movl $1, %eax
    xorl %ebx, %ebx
    int $0x80
