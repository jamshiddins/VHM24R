// Загрузка файлов
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const submitBtn = document.getElementById('submitBtn');
let selectedFiles = [];

if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    selectedFiles = Array.from(files);
    displayFiles();
}

function displayFiles() {
    fileList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>${file.name} (${formatFileSize(file.size)})</span>
            <button type="button" class="btn btn-sm btn-danger" 
                    onclick="removeFile(${index})">
                Удалить
            </button>
        `;
        fileList.appendChild(fileItem);
    });
    
    submitBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displayFiles();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Показ деталей
let currentFilter = '';
let currentCount = 0;

async function showDetails(filter, count) {
    currentFilter = filter;
    currentCount = count;
    
    try {
        const response = await fetch(`/api/orders/details?filter=${filter}&limit=${count}`);
        const data = await response.json();
        
        // Обновляем заголовок модального окна
        document.getElementById('modalTitle').textContent = 
            `${getFilterName(filter)} - ${count} заказов`;
        
        // Создаем таблицу
        let tableHtml = `
            <div class="table-container">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Номер заказа</th>
                            <th>Код автомата</th>
                            <th>Время создания</th>
                            <th>Сумма</th>
                            <th>Тип оплаты</th>
                            <th>Статус</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.orders.forEach(order => {
            tableHtml += `
                <tr>
                    <td>${order.order_number || '-'}</td>
                    <td>${order.machine_code || '-'}</td>
                    <td>${formatDate(order.creation_time)}</td>
                    <td>${order.order_price || '0'}</td>
                    <td>${order.payment_type || '-'}</td>
                    <td>
                        <span class="badge bg-${getStatusColor(order.match_status)}">
                            ${order.match_status}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        tableHtml += '</tbody></table></div>';
        
        document.getElementById('ordersTable').innerHTML = tableHtml;
        
        // Показываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading details:', error);
        alert('Ошибка загрузки данных');
    }
}

function getFilterName(filter) {
    const names = {
        'matched': 'Совпадающие заказы',
        'time_mismatch': 'Расхождения во времени',
        'price_mismatch': 'Расхождения в цене',
        'fiscal_mismatch': 'Без фискальных чеков',
        'gateway_mismatch': 'Без данных платежных шлюзов'
    };
    return names[filter] || filter;
}

function getStatusColor(status) {
    const colors = {
        'matched': 'success',
        'fully_matched': 'success',
        'time_mismatch': 'warning',
        'price_mismatch': 'warning',
        'fiscal_mismatch': 'danger',
        'gateway_mismatch': 'danger',
        'unmatched': 'secondary'
    };
    return colors[status] || 'secondary';
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
}

// Экспорт данных
function exportCurrentFilter() {
    window.location.href = `/api/orders/export?filter=${currentFilter}&format=csv`;
}

function exportAll() {
    window.location.href = '/api/orders/export?filter=all&format=csv';
}