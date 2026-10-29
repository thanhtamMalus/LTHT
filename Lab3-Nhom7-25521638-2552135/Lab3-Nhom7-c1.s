.section .data
msg_tong: .string "Tong: "
len_tong = . - msg_tong - 1

msg_hieu: .string "\nHieu: "
len_hieu = . - msg_hieu - 1

msg_tich: .string "\nTich: "
len_tich = . - msg_tich - 1

msg_thuong: .string "\nThuong: "
len_thuong = . - msg_thuong - 1

msg_du: .string ", Du: "
len_du= . - msg_du - 1

msg_div: .string "\nKhong chia duoc cho 0\n"
len_div= . - msg_div - 1

newline: .string "\n"

.section .bss
.lcomm buf1, 32
.lcomm buf2, 32
.lcomm numA, 4
.lcomm numB, 4

.section .text

.globl _start

_start:
	#---Doc so thu 1
	pushl $32		#Day kich thuoc buffer (32) vao stack
	pushl $buf1		#Day dia chi buf2 vao stack
	call read_line
	addl $8, %esp		#Don dep stack

	pushl $buf1
	call atoi
	addl $4, %esp
	movl %eax, numA
 
	#---Doc so thu 2
	pushl $32
        pushl $buf2
        call read_line
        addl $8, %esp

        pushl $buf2
        call atoi
        addl $4, %esp
        movl %eax, numB


	#---Tinh+in tong a+b
	movl $4, %eax		#Sys_write
	movl $1, %ebx		#stdout
	movl $msg_tong, %ecx
	movl $len_tong, %edx 	
	int $0x80		#In ra	

	movl numA, %eax
	addl numB, %eax
	pushl %eax		#Day ket qua vao stack lam tham so
	call print_int
	addl $4, %esp

	#---Tinh+in hieu a-b
        movl $4, %eax
        movl $1, %ebx
        movl $msg_hieu, %ecx
        movl $len_hieu, %edx
        int $0x80

        movl numA, %eax
        subl numB, %eax
        pushl %eax
        call print_int
        addl $4, %esp

	#---Tinh+in tich a*b
        movl $4, %eax
        movl $1, %ebx
        movl $msg_tich, %ecx
        movl $len_tich, %edx
        int $0x80

        movl numA, %eax
        imull numB, %eax
        pushl %eax
        call print_int
        addl $4, %esp

	#---Tinh+in thuong a/b va so du a%b
	#------Kiem tra chia cho 0
	cmpl $0, numB
	je div_zero
	
	#------Tinh va in ra thuong
	movl $4, %eax
        movl $1, %ebx
        movl $msg_thuong, %ecx
        movl $len_thuong, %edx
        int $0x80

      	movl numA, %eax
	cltd 			#Mo rong %eax thanh %edx:%eax
	idivl numB 		#Chia %edx:%eax cho numB, %edx=du, %eax=thuong
	movl %edx, %esi
	
	pushl %eax
	call print_int
	addl $4, %esp

	#------In ra du
	movl $4, %eax
	movl $1, %ebx
	movl $msg_du, %ecx
	movl $len_du, %edx
	int $0x80

	pushl %esi
	call print_int
	addl $4, %esp

	movl $4, %eax
        movl $1, %ebx
        movl $newline, %ecx
        movl $1, %edx
        int $0x80
	
	jmp sys_exit

div_zero: 
	movl $4, %eax	
	movl $1, %ebx
	movl $msg_div, %ecx
	movl $len_div, %edx
	int $0x80
	jmp sys_exit

print_exit:
	movl $4, %eax
	movl $1, %ebx
	movl $newline, %ecx	#Xuong dong
	movl $1, %edx		#Xuong 1 byte
	int $0x80

sys_exit:
	movl $1, %eax
	xorl %ebx, %ebx		#Tra ve ma loi 0
	int $0x80

read_line:
	pushl %ebp		#Luu ebp cu cua ham goi
	movl %esp, %ebp		#Thiet lap con tro stack moi
	pushl %ebx		#Bao toan ebx
	pushl %esi		#Bao toan esi
		
	movl 8(%ebp), %esi	#Tham so 1(buf) luu vao esi
	movl 12(%ebp), %ecx	#Tham so 2(max_len) luu vao ecx
	decl %ecx		#Tru 1 cho o cuoi luu \0
	xorl %ebx, %ebx		#Khoi tao bien dem so byte ebx=0

read_loop:
    	cmpl %ecx, %ebx
    	jge read_done

    	pushl %ebx
    	movl $3, %eax
    	movl $0, %ebx
    	leal (%esi), %ecx
    	addl (%esp), %ecx
    	movl $1, %edx
    	int $0x80
    	popl %ebx

    	cmpl $0, %eax
    	jle read_done

    	movb (%esi, %ebx, 1), %al
    	cmpb $10, %al
    	je read_done

    	incl %ebx
    	jmp read_loop

read_done:
    	movb $0, (%esi, %ebx, 1)
    	popl %esi
    	popl %ebx
    	movl %ebp, %esp
    	popl %ebp
    	ret

atoi:
    	pushl %ebp
    	movl %esp, %ebp
    	pushl %ebx
    	pushl %esi

    	movl 8(%ebp), %esi
    	xorl %eax, %eax
    	xorl %ecx, %ecx

    	movb (%esi), %bl
    	cmpb $45, %bl
    	jne parse_loop
    	movl $1, %ecx
    	incl %esi

parse_loop:
    	movzbl (%esi), %ebx
    	cmpb $0, %bl
    	je atoi_done
    	cmpb $10, %bl
    	je atoi_done
    	cmpb $48, %bl
    	jl atoi_done
    	cmpb $57, %bl
   	jg atoi_done

    	subl $48, %ebx
    	imull $10, %eax
    	addl %ebx, %eax
    	incl %esi
    	jmp parse_loop

atoi_done:
    	cmpl $1, %ecx
    	jne atoi_exit
    	negl %eax

atoi_exit:
    	popl %esi
    	popl %ebx
    	movl %ebp, %esp
    	popl %ebp
    	ret

print_int:
    	pushl %ebp
    	movl %esp, %ebp
    	subl $16, %esp
    	pushl %ebx
    	pushl %esi
    	pushl %edi

    	movl 8(%ebp), %eax
    	leal -1(%ebp), %esi
    	movb $0, (%esi)

    	xorl %edi, %edi
    	cmpl $0, %eax
    	jge convert_loop
    	movl $1, %edi
    	negl %eax

convert_loop:
    	xorl %edx, %edx
    	movl $10, %ebx
    	divl %ebx
    	addl $48, %edx

    	decl %esi
    	movb %dl, (%esi)

    	cmpl $0, %eax
    	jg convert_loop

    	cmpl $1, %edi
    	jne print_out
    	decl %esi
    	movb $45, (%esi)

print_out:
    	leal -1(%ebp), %edx
    	subl %esi, %edx

    	movl $4, %eax
    	movl $1, %ebx
    	movl %esi, %ecx
    	int $0x80

    	popl %edi
    	popl %esi
    	popl %ebx
    	movl %ebp, %esp
    	popl %ebp
    	ret
