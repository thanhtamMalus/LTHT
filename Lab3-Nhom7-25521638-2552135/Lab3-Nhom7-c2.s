# sap xep mang so nguyen
# bien dich: as --32 -o Lab3-Nhom7-c2.o Lab3-Nhom7-c2.s && ld -m elf_i386 -o Lab3-Nhom7-c2 Lab3-Nhom7-c2.o

.section .data
    msg: .ascii "So lan hoan doi: "
    .equ msg_len, . - msg
    space: .ascii " "
    newline: .ascii "\n"

.section .bss
    .lcomm arr, 40 #mang toi da 10ptu
    .lcomm buf, 16 
    .lcomm outbuf, 16

    .section .text
    .globl _start

# check: doi chuoi ki tu sang so nguyen
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

    cmpb $'\n', (%edi)
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
    movl  $1, %ebx # fd 1 = stdout
    int   $0x80 # ecx, edx dc chuan bi san
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
    movl $outbuf+16, %edi #edi tro chuot cuoi bo dem, ghi lui ve dau

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

sort:
    pushl %ebp
    movl %esp, %ebp #tao khung stack
    pushl %ebx 
    pushl %esi
    pushl %edi
    movl 8(%ebp), %ebx
    xorl %eax, %eax
    xorl %esi, %esi

.sort_out:
    movl 12(%ebp), %ecx #ecx = n
    decl %ecx #ecx=n-1
    cmpl %ecx, %esi
    jge .sort_done

    subl %esi, %ecx #ecx=n-1-i
    xorl %edi, %edi #j=0

.sort_in:
    cmpl %ecx, %edi #j>=n-1
    jge .sort_next
    movl (%ebx, %edi,4), %edx #edx=a[j]
    cmpl 4(%ebx,%edi,4), %edx #so sanh a[j] va [aj+1]
    jle .sort_noswap # dung thi k doi
    xchgl %edx, 4(%ebx,%edi,4) #a[j+1]=a[j];edx=a[j+1] cu 
    movl %edx, (%ebx,%edi,4)
    incl %eax

.sort_noswap:
    incl %edi #j++
    jmp .sort_in

.sort_next:
    incl %esi #i++
    jmp .sort_out

.sort_done:
    popl %edi
    popl %esi
    popl %ebx
    popl %ebp
    ret #so lan nam o eax


_start:
    call  read_int #eax = n
    movl  %eax, %esi #esi = n
    movl  $arr, %ebx 
    xorl  %edi, %edi # edi = 0 
 
#doc n so
.read_loop:
    cmpl %esi, %edi # i >= n -> da doc xong
    jge .read_done
    call read_int #so vua nhap
    movl %eax, (%ebx,%edi,4) #arr[i] = eax 
    incl %edi #i++
    jmp .read_loop

.read_done:
    #sort
    pushl %esi #tham so 2: n
    pushl %ebx #tham so 1: a
    call  sort
    addl  $8, %esp #day a,n ra
    movl  %eax, %ebp #so lan hoan doi = ebp
    
    xorl  %edi, %edi # i = 0

.print_loop:
    cmpl %esi, %edi
    jge .print_done
    testl %edi, %edi #ptu dau -> khong in dau cach
    jz .no_space
    movl $space, %ecx
    movl $1, %edx
    call print_str

.no_space:
    movl (%ebx,%edi,4), %eax # eax = arr[i]
    call print_int #in so k xuong dong
    incl %edi
    jmp   .print_loop

.print_done:
    movl  $newline, %ecx 
    movl  $1, %edx
    call  print_str
 
    # So lan hoan doi
    movl  $msg, %ecx
    movl  $msg_len, %edx
    call  print_str  #in chuoi "So lan hoan doi: "
    movl  %ebp, %eax # eax = so lan hoan doi
    call  print_int # in k
    movl  $newline, %ecx
    movl  $1, %edx
    call  print_str #enter
 
    #thoat chuong trinh
    movl  $1, %eax #sys exit
    xorl  %ebx, %ebx #exit 0
    int   $0x80

 

