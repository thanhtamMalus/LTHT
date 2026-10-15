.section .data
    msg_inp:   .ascii "Nhap chuoi(4 char): "
    len_inp   = . - msg_inp

    msg_n:     .ascii "Nhap n(0->9): "
    len_n     = . - msg_n

.section .bss
.lcomm input, 5
.lcomm n, 4

.section .text
.globl _start
_start:
    # input chuoi
    movl $4, %eax
    movl $1, %ebx
    movl $msg_inp, %ecx
    movl $len_inp, %edx
    int $0x80

    movl $3, %eax
    movl $0, %ebx
    movl $input, %ecx
    movl $4, %edx
    int $0x80

    # (Đoạn mã lệnh clear phím Enter thừa trong bộ đệm nếu có)
    movl $3, %eax
    movl $0, %ebx
    movl $n, %ecx
    movl $1, %edx
    int $0x80

    # input n
    movl $4, %eax
    movl $1, %ebx
    movl $msg_n, %ecx
    movl $len_n, %edx
    int $0x80

    movl $3, %eax
    movl $0, %ebx
    movl $n, %ecx
    movl $1, %edx
    int $0x80

    # chuyen n sang so nguyen 
    movl $n, %eax
    movzbl (%eax), %edx      
    subb $48, %dl            

    # xu ly
    movl $input, %eax      
    movl $4, %ecx          

_loop:
    movb (%eax), %bl        
    addb %dl, %bl            
    
    cmpb $122, %bl           
    jle _khongVuot           
    subb $26, %bl           

_khongVuot:
    movb %bl, (%eax)         
    incl %eax                
    decl %ecx                
    jnz _loop              

_done:
    # output
    movl $4, %eax           
    movl $1, %ebx           
    movl $input, %ecx       
    movl $4, %edx           
    int $0x80                

    # thoat
    movl $1, %eax
    xorl %ebx, %ebx
    int $0x80
