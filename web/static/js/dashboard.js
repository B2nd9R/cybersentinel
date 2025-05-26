// تحديث الإحصائيات
async function updateStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();
        
        document.getElementById('servers-count').textContent = data.servers;
        document.getElementById('users-count').textContent = data.users;
        document.getElementById('threats-blocked').textContent = data.threats_blocked;
        document.getElementById('scans-count').textContent = data.scans_performed;
    } catch (error) {
        console.error('خطأ في تحديث الإحصائيات:', error);
    }
}

// تحديث التهديدات الأخيرة
async function updateRecentThreats() {
    try {
        const response = await fetch('/recent-threats');
        const threats = await response.json();
        
        const threatTable = document.getElementById('threats-table');
        threatTable.innerHTML = '';
        
        threats.forEach(threat => {
            const row = document.createElement('tr');
            row.className = 'table-row hover:bg-gray-50';
            
            const severityClass = {
                'عالي': 'bg-red-100 text-red-800',
                'متوسط': 'bg-yellow-100 text-yellow-800',
                'منخفض': 'bg-green-100 text-green-800'
            }[threat.severity] || 'bg-gray-100 text-gray-800';
            
            row.innerHTML = `
                <td class="px-6 py-4">${threat.type}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded-full ${severityClass}">
                        ${threat.severity}
                    </span>
                </td>
                <td class="px-6 py-4">${new Date(threat.timestamp).toLocaleString('ar-SA')}</td>
                <td class="px-6 py-4">
                    <button class="text-blue-600 hover:text-blue-800 transition-colors duration-200">
                        التفاصيل
                    </button>
                </td>
            `;
            
            threatTable.appendChild(row);
        });
    } catch (error) {
        console.error('خطأ في تحديث التهديدات:', error);
    }
}

// تحديث حالة الحماية
async function updateProtectionStatus() {
    try {
        const response = await fetch('/protection-status');
        const status = await response.json();
        
        document.getElementById('protection-status').textContent = status.status;
        document.getElementById('protection-level').textContent = status.level;
        
        const featuresList = document.getElementById('enabled-features');
        featuresList.innerHTML = status.features_enabled
            .map(feature => `<li class="feature-list-item">${feature}</li>`)
            .join('');
        
        // تحديث لون حالة الحماية
        const statusElement = document.getElementById('protection-status');
        statusElement.className = status.status === 'نشط' 
            ? 'text-lg font-semibold text-green-600'
            : 'text-lg font-semibold text-red-600';
    } catch (error) {
        console.error('خطأ في تحديث حالة الحماية:', error);
    }
}

// تحديث كل البيانات
function updateAllData() {
    updateStats();
    updateRecentThreats();
    updateProtectionStatus();
}

// تحديث البيانات عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    updateAllData();
    
    // تحديث البيانات كل 30 ثانية
    setInterval(updateAllData, 30000);
});

// إضافة تأثيرات التحويم للبطاقات
document.querySelectorAll('.card').forEach(card => {
    card.classList.add('hover-scale');
});

// تفعيل التنقل السلس
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});