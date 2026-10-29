# bien dich: as --32 -o Lab3-Nhom7-c4.o Lab3-Nhom7-c4.s && ld -m elf_i386 -o Lab3-Nhom7-c4 Lab3-Nhom7-c4.o
# nhap 3 dong: op (0 cong, 1 tru, 2 nhan, 3 chia, 4 chia lay du), a, b

.section .data
    msg_kq: .ascii "Ket qua: "
    .equ msg_kq_len, . - msg_kq
    msg_loi: .ascii "Loi chia cho 0\n"
    .equ msg_loi_len, . - msg_loi
    msg_kh: .ascii "Phep toan khong hop le\n"
    .equ msg_kh_len, . - msg_kh
    newline: .ascii "\n"

    # bang nhay: moi phan tu 4 byte la dia chi nhan cua nhanh tuong ung
    # phan tu thu op nam o bang + 4*op
    bang: .long .op_add, .op_sub, .op_mul, .op_div, .op_mod

.section .bss
    .lcomm buf, 16
    .lcomm outbuf, 16

.section .text
    .globl _start

# check: doi chuoi ki tu sang so nguyen (esi = chuoi, eax = ket qua)

check:
    pushl %ebx
    pushl %ecx
    xorl %eax, %eax
    movl $1, %ebx

    cmpb $'-', (%esi) #check co phai so am k
    jne .loop
    movl $-1, %ebx #la so am
    incl %esi #bo qua dau am

.loop:
    movzbl (%esi), %ecx #ecx = ki tu hien tai
    subl $'0', %ecx
    cmpl $9, %ecx
    ja .done #>9 hoac am -> khong phai chu so
    imull $10, %eax #kq=kq*10
    addl %ecx, %eax #kq=kq+ chu so
    incl %esi #chuyen sang ki tu ke tiep
    jmp .loop

.done:
    imull %ebx, %eax # nhan voi dau
    popl %ecx
    popl %ebx
    ret


read_int:
    pushl %ebx
    pushl %ecx
    pushl %edx
    pushl %esi
    pushl %edi
    movl $buf, %edi #edi = vtri byte tiep theo trong buf

.ri_loop:
    movl $3, %eax #sys read
    movl $0, %ebx
    movl %edi, %ecx
    movl $1, %edx
    int $0x80
    cmpl $1, %eax # doc duoc 1 byte?
    jne .ri_end
    cmpb $'\n', (%edi) #gap enter -> het dong
    je .ri_end

    incl %edi #chua het dong -> sang o ke tiep
    jmp .ri_loop

.ri_end:
    movb $0, (%edi) #thay /n thanh byte 0
    movl $buf, %esi
    call check #doi sang so, ket qua o eax
    popl  %edi
    popl  %esi
    popl  %edx
    popl  %ecx
    popl  %ebx
    ret


print_str:
    pushl %eax
    pushl %ebx
    movl  $4, %eax #sys_write
    movl  $1, %ebx  #fd 1 = stdout
    int   $0x80 #ecx, edx dc chuan bi san
    popl  %ebx
    popl  %eax
    ret

print_int:
    pushl %eax
    pushl %ebx
    pushl %ecx
    pushl %edx
    pushl %esi
    pushl %edi
    movl  %eax, %esi #esi = so goc dung de xet dau
    testl %eax, %eax
    jns .pi_conv #>=0 thi bo qua buoc doi dau
    negl %eax #so am -> lay gtri tuyet doi

.pi_conv:
    movl $10, %ebx #so chia
    movl $outbuf+16, %edi #edi tro cuoi bo dem, ghi lui ve dau

.pi_loop:
    xorl %edx, %edx # edx = 0
    divl %ebx # eax = eax/10 (thuong), edx = eax%10 (du)
    addb $'0', %dl # chu so -> ascii
    decl %edi #lui 1 o
    movb %dl, (%edi) #ghi ki tu
    testl %eax, %eax  #thuong khac 0 thi lap tiep
    jnz .pi_loop
    testl %esi, %esi #so goc co am khong
    jns   .pi_write
    decl %edi
    movb $'-', (%edi) #them dau - o dau

.pi_write:
    movl $outbuf+16, %edx
    subl %edi, %edx #edx: do dai chuoi can in
    movl %edi, %ecx #ecx: dia chi dau chuoi
    call print_str
    popl %edi
    popl %esi
    popl %edx
    popl %ecx
    popl %ebx
    popl %eax
    ret


_start:
    call  read_int #eax = op
    movl  %eax, %esi #esi = op
    call  read_int #eax = a
    movl  %eax, %ebx #ebx = a
    call  read_int #eax = b
    movl  %eax, %edi #edi = b

    movl  %esi, %eax #eax = op de nhay
    cmpl  $4, %eax #so sanh khong dau: op am cung thanh so rat lon
    ja    .khong_hop_le #op > 4 (hoac am) -> khong hop le
    jmp   *bang(,%eax,4) #nhay gian tiep den bang[op], k dung cmp/jmp tung case

.op_add:
    movl  %ebx, %eax #eax = a
    addl  %edi, %eax #eax = a + b
    jmp   .in_kq

.op_sub:
    movl  %ebx, %eax
    subl  %edi, %eax #eax = a - b
    jmp   .in_kq

.op_mul:
    movl  %ebx, %eax
    imull %edi, %eax #eax = a * b
    jmp   .in_kq

.op_div:
    testl %edi, %edi #b = 0 ?
    jz    .chia_0
    movl  %ebx, %eax #eax = a
    cltd #mo rong dau eax sang edx:eax
    idivl %edi #eax = thuong, edx = du
    jmp   .in_kq

.op_mod:
    testl %edi, %edi #b = 0 ?
    jz    .chia_0
    movl  %ebx, %eax
    cltd
    idivl %edi
    movl  %edx, %eax #lay so du lam ket qua
    jmp   .in_kq

.in_kq:
    movl  %eax, %ebp #cat ket qua vao ebp
    movl  $msg_kq, %ecx
    movl  $msg_kq_len, %edx
    call  print_str #in "Ket qua: "
    movl  %ebp, %eax
    call  print_int #in gia tri
    movl  $newline, %ecx
    movl  $1, %edx
    call  print_str #enter
    jmp   .thoat

.chia_0:
    movl  $msg_loi, %ecx
    movl  $msg_loi_len, %edx
    call  print_str #in "Loi chia cho 0"
    jmp   .thoat

.khong_hop_le:
    movl  $msg_kh, %ecx
    movl  $msg_kh_len, %edx
    call  print_str #in "Phep toan khong hop le"

.thoat:
    movl  $1, %eax #sys exit
    xorl  %ebx, %ebx #exit 0
    int   $0x80
