.section .data
    msg_str:   .ascii "Enter a string (10-chars): "
    len_str   = . - msg_str

    msg_start: .ascii "Start index: "
    len_start = . - msg_start

    msg_end:   .ascii "End index: "
    len_end   = . - msg_end

.section .bss
    .lcomm input_buf, 11
    .lcomm start_buf, 4
    .lcomm end_buf, 4

.section .text
.globl _start

_start:
    # 1. In thông báo yêu cầu nhập chuỗi
    movl $4, %eax
    movl $1, %ebx
    movl $msg_str, %ecx
    movl $len_str, %edx
    int $0x80

    # Đọc đúng 10 ký tự của chuỗi
    movl $3, %eax
    movl $0, %ebx
    movl $input_buf, %ecx
    movl $10, %edx         
    int $0x80

    # (Đoạn mã lệnh clear phím Enter thừa trong bộ đệm nếu có)
    movl $3, %eax
    movl $0, %ebx
    movl $start_buf, %ecx
    movl $1, %edx
    int $0x80

    # 2. In thông báo nhập Start index
    movl $4, %eax
    movl $1, %ebx
    movl $msg_start, %ecx
    movl $len_start, %edx
    int $0x80

    # Đọc ký tự start index
    movl $3, %eax
    movl $0, %ebx
    movl $start_buf, %ecx
    movl $2, %edx
    int $0x80
     
    # 3. In thông báo nhập End index
    movl $4, %eax
    movl $1, %ebx
    movl $msg_end, %ecx
    movl $len_end, %edx
    int $0x80

    # Đọc ký tự end index
    movl $3, %eax
    movl $0, %ebx
    movl $end_buf, %ecx
    movl $2, %edx
    int $0x80

    # 4. Chuyển ký tự start sang số nguyên
    movl $start_buf, %eax
    movzbl (%eax), %edi      
    subb $48, %dil           

    # 5. Chuyển ký tự end sang số nguyên
    movl $end_buf, %eax
    movzbl (%eax), %esi      
    subb $48, %sil           

    # 6. Tính độ dài chuỗi con cần in = (end - start + 1)
    movl %esi, %edx          
    subl %edi, %edx          
    addl $1, %edx            

    # 7. Xuất chuỗi con ra màn hình (sys_write)
    movl $4, %eax            
    movl $1, %ebx            
    movl $input_buf, %ecx
    addl %edi, %ecx          # Dịch con trỏ đến vị trí 'start'
    int $0x80                

    # 8. Thoát chương trình
    movl $1, %eax
    xorl %ebx, %ebx
    int $0x80
    