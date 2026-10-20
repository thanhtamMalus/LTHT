.section .data
.section .bss
	.lcomm num1, 2
	.lcomm num2, 2
	.lcomm num3, 2
	.lcomm num4, 2
	.lcomm result, 2
.section .text
.globl _start
_start:
#Doc gtri input
	movl $3, %eax
	movl $0, %ebx
	movl $num1, %ecx
	movl $11, %edx
	int $0x80

	movl $3, %eax
        movl $0, %ebx
        movl $num2, %ecx
        movl $2, %edx
        int $0x80
	
	movl $3, %eax
        movl $0, %ebx
        movl $num3, %ecx
        movl $11, %edx
        int $0x80

	movl $3, %eax
        movl $0, %ebx
        movl $num4, %ecx
        movl $11, %edx
        int $0x80

#Xu li dau vao
	movzbl num1, %eax
	subb $48, %al
	movl %eax, %esi

	movzbl num2, %eax
        subb $48, %al
        addl %eax, %esi

	movzbl num3, %eax
        subb $48, %al
        addl %eax, %esi

	movzbl num4, %eax
        subb $48, %al
        addl %eax, %esi

#Tinh trung binh cong
	movl %esi, %eax
	xorl %edx, %edx
	movl $4, %ebx
	divl %ebx
#Xu li va in ra man hinh
	addb $48, %al
	movb %al, result
	movb $10, result+1
	
	movl $4, %eax
	movl $1, %ebx
	movl $result, %ecx
	movl $2, %edx
	int $0x80

	movl $1, %eax
	xorl %ebx, %ebx
	int $0x80
