// web/static/js/login.js

document.addEventListener('DOMContentLoaded', function() {
    // تحديث سنة حقوق النشر تلقائيًا
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // يمكنك إضافة المزيد من وظائف JavaScript هنا في المستقبل
    // مثال: التحقق من صحة النموذج من جانب العميل
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            // يمكن إضافة منطق التحقق هنا
            // مثال بسيط:
            const usernameInput = document.getElementById('username');
            if (usernameInput && usernameInput.value.trim() === '') {
                // alert('الرجاء إدخال اسم المستخدم.');
                // event.preventDefault(); // لمنع الإرسال إذا كان هناك خطأ
                // يمكنك عرض رسالة خطأ مخصصة بدلاً من alert
            }
            // كرر لـ password إذا لزم الأمر
        });
    }
});