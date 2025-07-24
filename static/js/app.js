// ODUS-RFM v5.0 - Modern JavaScript Application
// Enhanced with modern features and bug fixes

class ODUSApp {
    constructor() {
        this.files = [];
        this.isUploading = false;
        this.init();
    }

    init() {
        this.initializeElements();
        this.bindEvents();
        this.initializeAnimations();
        this.initializeTooltips();
    }

    initializeElements() {
        // Main elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileList = document.getElementById('fileList');
        this.selectedFiles = document.getElementById('selectedFiles');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.uploadForm = document.getElementById('uploadForm');
    }

    bindEvents() {
        if (this.dropZone && this.fileInput) {
            // Fix double file selection issue by preventing default click behavior
            this.dropZone.addEventListener('click', (e) => {
                e.preventDefault();
                this.fileInput.click();
            });

            // Drag & Drop events
            this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));

            // File input change - fix double selection
            this.fileInput.addEventListener('change', (e) => {
                e.stopPropagation();
                this.handleFileSelect(e);
            });
        }

        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearFiles());
        }

        if (this.uploadForm) {
            this.uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Auto-refresh for dashboard
        if (window.location.pathname === '/dashboard') {
            this.initAutoRefresh();
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropZone.classList.add('dragover');
        this.showNotification('Отпустите файлы для загрузки', 'info', 1000);
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropZone.classList.remove('dragover');
        
        const droppedFiles = Array.from(e.dataTransfer.files);
        this.addFiles(droppedFiles);
        this.showNotification(`Добавлено ${droppedFiles.length} файлов`, 'success');
    }

    handleFileSelect(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const selectedFiles = Array.from(e.target.files);
        if (selectedFiles.length > 0) {
            this.addFiles(selectedFiles);
            this.showNotification(`Выбрано ${selectedFiles.length} файлов`, 'success');
        }
        
        // Clear the input to allow selecting the same files again if needed
        e.target.value = '';
    }

    addFiles(newFiles) {
        // Filter out duplicates
        const uniqueFiles = newFiles.filter(newFile => 
            !this.files.some(existingFile => 
                existingFile.name === newFile.name && 
                existingFile.size === newFile.size
            )
        );

        if (uniqueFiles.length === 0) {
            this.showNotification('Все файлы уже добавлены', 'warning');
            return;
        }

        this.files = [...this.files, ...uniqueFiles];
        this.updateFileList();
        this.updateButtons();
        this.animateFileItems();
    }

    updateFileList() {
        if (!this.fileList || !this.selectedFiles) return;

        if (this.files.length === 0) {
            this.fileList.style.display = 'none';
            return;
        }

        this.fileList.style.display = 'block';
        this.selectedFiles.innerHTML = '';

        this.files.forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            this.selectedFiles.appendChild(fileItem);
        });
    }

    createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item fade-in-up';
        fileItem.style.animationDelay = `${index * 0.1}s`;

        const fileIcon = this.getFileIcon(file.name);
        const fileSize = this.formatFileSize(file.size);
        const fileType = this.getFileType(file.name);

        fileItem.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${fileIcon} me-3 text-primary" style="font-size: 1.5rem;"></i>
                <div>
                    <div class="fw-bold text-light">${file.name}</div>
                    <small class="text-muted">${fileSize} • ${fileType}</small>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="app.removeFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;

        return fileItem;
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFileList();
        this.updateButtons();
        this.showNotification('Файл удален', 'info');
    }

    clearFiles() {
        this.files = [];
        if (this.fileInput) this.fileInput.value = '';
        this.updateFileList();
        this.updateButtons();
        this.showNotification('Все файлы очищены', 'info');
    }

    updateButtons() {
        if (!this.uploadBtn || !this.clearBtn) return;

        const hasFiles = this.files.length > 0;
        this.uploadBtn.disabled = !hasFiles || this.isUploading;
        this.clearBtn.disabled = !hasFiles || this.isUploading;

        // Update button text based on state
        if (this.isUploading) {
            this.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Обработка...';
        } else {
            this.uploadBtn.innerHTML = '<i class="fas fa-play me-2"></i>Загрузить и обработать';
        }
    }

    async handleFormSubmit(e) {
        e.preventDefault();

        if (this.files.length === 0) {
            this.showNotification('Пожалуйста, выберите файлы для загрузки', 'error');
            return;
        }

        if (this.isUploading) return;

        this.isUploading = true;
        this.updateButtons();
        this.showProgress();

        try {
            const formData = new FormData();
            this.files.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const html = await response.text();
            
            // Smooth transition to results
            document.body.style.opacity = '0';
            setTimeout(() => {
                document.body.innerHTML = html;
                document.body.style.opacity = '1';
                this.showNotification('Файлы успешно обработаны!', 'success');
            }, 300);

        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification('Произошла ошибка при загрузке файлов', 'error');
            this.hideProgress();
            this.isUploading = false;
            this.updateButtons();
        }
    }

    showProgress() {
        if (!this.progressContainer) return;

        this.progressContainer.style.display = 'block';
        this.progressContainer.classList.add('fade-in-up');
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            
            this.updateProgress(progress);
            
            if (progress >= 90) {
                clearInterval(interval);
            }
        }, 200);
    }

    updateProgress(percent) {
        if (!this.progressBar || !this.progressText) return;

        this.progressBar.style.width = `${percent}%`;
        this.progressText.textContent = `${Math.round(percent)}%`;
    }

    hideProgress() {
        if (!this.progressContainer) return;

        this.progressContainer.style.display = 'none';
        this.updateProgress(0);
    }

    // Utility functions
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'csv': 'fas fa-file-csv text-success',
            'xlsx': 'fas fa-file-excel text-success',
            'xls': 'fas fa-file-excel text-success',
            'pdf': 'fas fa-file-pdf text-danger',
            'jpg': 'fas fa-file-image text-info',
            'jpeg': 'fas fa-file-image text-info',
            'png': 'fas fa-file-image text-info',
            'doc': 'fas fa-file-word text-primary',
            'docx': 'fas fa-file-word text-primary',
            'txt': 'fas fa-file-alt text-secondary'
        };
        return iconMap[ext] || 'fas fa-file text-muted';
    }

    getFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const typeMap = {
            'csv': 'CSV файл',
            'xlsx': 'Excel файл',
            'xls': 'Excel файл',
            'pdf': 'PDF документ',
            'jpg': 'Изображение',
            'jpeg': 'Изображение',
            'png': 'Изображение',
            'doc': 'Word документ',
            'docx': 'Word документ',
            'txt': 'Текстовый файл'
        };
        return typeMap[ext] || 'Неизвестный тип';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Notification system
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification fade-in-up`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        `;
        
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    // Animation helpers
    initializeAnimations() {
        // Animate cards on page load
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Animate stats numbers
        this.animateNumbers();
    }

    animateFileItems() {
        const fileItems = document.querySelectorAll('.file-item');
        fileItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 50);
        });
    }

    animateNumbers() {
        const numbers = document.querySelectorAll('.stats-number');
        numbers.forEach(number => {
            const target = parseInt(number.textContent);
            if (isNaN(target)) return;

            let current = 0;
            const increment = target / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                number.textContent = Math.floor(current);
            }, 30);
        });
    }

    // Keyboard shortcuts
    handleKeyboardShortcuts(e) {
        // Ctrl+U for upload
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            if (this.fileInput) this.fileInput.click();
        }

        // Escape to clear files
        if (e.key === 'Escape' && this.files.length > 0) {
            this.clearFiles();
        }

        // Enter to submit form
        if (e.key === 'Enter' && e.ctrlKey && this.files.length > 0) {
            e.preventDefault();
            if (this.uploadForm) this.uploadForm.dispatchEvent(new Event('submit'));
        }
    }

    // Tooltips initialization
    initializeTooltips() {
        // Add tooltips to buttons and icons
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            new bootstrap.Tooltip(element);
        });
    }

    // Auto-refresh for dashboard
    initAutoRefresh() {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshDashboardData();
            }
        }, 60000); // Refresh every minute
    }

    async refreshDashboardData() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
            }
        } catch (error) {
            console.error('Failed to refresh dashboard data:', error);
        }
    }

    updateDashboardStats(data) {
        // Update stats numbers with animation
        Object.keys(data).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                const currentValue = parseInt(element.textContent);
                const newValue = data[key];
                if (currentValue !== newValue) {
                    this.animateNumberChange(element, currentValue, newValue);
                }
            }
        });
    }

    animateNumberChange(element, from, to) {
        const duration = 1000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(from + (to - from) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    // API helpers
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('Ошибка соединения с сервером', 'error');
            throw error;
        }
    }

    // Export functionality
    async exportData(format = 'csv', filter = 'all') {
        try {
            const response = await fetch(`/api/orders/export?format=${format}&filter=${filter}`);
            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `orders_${filter}_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showNotification('Данные экспортированы успешно', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Ошибка экспорта данных', 'error');
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ODUSApp();
    
    // Add some CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            animation: slideInRight 0.3s ease-out;
        }
        
        .fade-out {
            animation: slideOutRight 0.3s ease-in;
        }
        
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
});

// Global utility functions
window.exportData = (format, filter) => {
    if (window.app) {
        window.app.exportData(format, filter);
    }
};

window.refreshData = () => {
    location.reload();
};

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
