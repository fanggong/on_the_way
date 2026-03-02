document.addEventListener('DOMContentLoaded', () => {
    // 侧边栏折叠交互
    const toggleBtn = document.getElementById('toggle-sider');
    const sidebar = document.querySelector('.semi-layout-sider');
    const logoText = document.querySelector('.logo-text');
    const navTexts = document.querySelectorAll('.semi-nav-text');
    
    let isCollapsed = false;

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            
            if (isCollapsed) {
                sidebar.style.width = '60px';
                logoText.style.display = 'none';
                navTexts.forEach(text => text.style.display = 'none');
                toggleBtn.querySelector('i').classList.replace('ri-menu-fold-line', 'ri-menu-unfold-line');
            } else {
                sidebar.style.width = '240px';
                logoText.style.display = 'block';
                navTexts.forEach(text => text.style.display = 'block');
                toggleBtn.querySelector('i').classList.replace('ri-menu-unfold-line', 'ri-menu-fold-line');
            }
        });
    }

    // 导航激活状态切换与页面路由
    const navLinks = document.querySelectorAll('.semi-nav-item-link');
    const pageViews = document.querySelectorAll('.page-view');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            // 移除所有 active
            navLinks.forEach(l => l.classList.remove('active'));
            // 添加当前 active
            link.classList.add('active');

            // 页面切换逻辑
            const pageId = link.getAttribute('data-page');
            if (pageId) {
                // 隐藏所有页面
                pageViews.forEach(view => {
                    view.style.display = 'none';
                });
                // 显示目标页面
                const targetView = document.getElementById(`view-${pageId}`);
                if (targetView) {
                    targetView.style.display = 'block';
                }
            }
        });
    });

    // 标签栏切换逻辑
    const tabs = document.querySelectorAll('.semi-tabs-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // 找到当前点击 tab 的父容器（tabs-bar）
            const parent = tab.parentElement;
            // 移除该组下所有 tab 的 active 状态
            parent.querySelectorAll('.semi-tabs-tab').forEach(t => t.classList.remove('active'));
            // 激活当前 tab
            tab.classList.add('active');

            // 找到对应的 tab-content 容器
            // 假设结构是: tabs-bar -> sibling tabs-content
            const contentContainer = parent.nextElementSibling;
            if (contentContainer && contentContainer.classList.contains('semi-tabs-content')) {
                const tabId = tab.getAttribute('data-tab');
                console.log('Switch to tab:', tabId);
                
                // 检查是否在连接器配置页面 (#view-connectors)
                const connectorsView = document.getElementById('view-connectors');
                if (connectorsView && connectorsView.contains(parent)) {
                    const healthContent = document.getElementById('connector-content-health');
                    const placeholderContent = document.getElementById('connector-content-placeholder');
                    
                    if (healthContent && placeholderContent) {
                        if (tabId === 'health') {
                            healthContent.style.display = 'block';
                            healthContent.classList.add('active');
                            placeholderContent.style.display = 'none';
                            placeholderContent.classList.remove('active');
                        } else {
                            healthContent.style.display = 'none';
                            healthContent.classList.remove('active');
                            placeholderContent.style.display = 'block';
                            placeholderContent.classList.add('active');
                            
                            // 更新 placeholder 的文本
                            const placeholderTitle = placeholderContent.querySelector('h2');
                            if (placeholderTitle) placeholderTitle.textContent = `${tab.textContent} 功能开发中...`;
                        }
                    }
                    return; // 处理完毕，退出
                }

                // 简单的演示逻辑：更新卡片标题以显示当前选中的标签
                const cardHeader = contentContainer.querySelector('.semi-card-header');
                if (cardHeader) {
                    // 获取当前页面（page-view）的标题逻辑可能需要调整，这里简化处理
                    // cardHeader.textContent = `${tab.textContent} 数据`; 
                }
            }
        });
    });

    // Modal Interaction
    const configModal = document.getElementById('config-modal');
    const garminConfigBtn = document.querySelector('.js-config-garmin');
    const modalCloseBtn = document.getElementById('modal-close');
    const modalCancelBtn = document.getElementById('modal-cancel');
    const modalConfirmBtn = document.getElementById('modal-confirm');

    // Show Modal
    if (garminConfigBtn) {
        garminConfigBtn.addEventListener('click', () => {
            configModal.style.display = 'flex';
        });
    }

    // Hide Modal
    const hideModal = () => {
        configModal.style.display = 'none';
    };

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', hideModal);
    if (modalCancelBtn) modalCancelBtn.addEventListener('click', hideModal);
    
    // Confirm Action (For now just close)
    if (modalConfirmBtn) {
        modalConfirmBtn.addEventListener('click', () => {
            // Here you would typically handle the form submission
            console.log('Configuration confirmed');
            hideModal();
        });
    }

    // Test Connection Logic
    const testConnBtn = document.getElementById('modal-test-conn');
    if (testConnBtn) {
        testConnBtn.addEventListener('click', () => {
            testConnBtn.classList.add('semi-btn-loading');
            testConnBtn.disabled = true;
            testConnBtn.textContent = '测试中...';

            // 模拟请求延迟
            setTimeout(() => {
                testConnBtn.classList.remove('semi-btn-loading');
                testConnBtn.disabled = false;
                testConnBtn.textContent = '测试连接';
                
                showToast('连接成功！账号信息正确。');
            }, 1500);
        });
    }

    // Toast Utility
    function showToast(message, type = 'success') {
        let wrapper = document.querySelector('.semi-toast-wrapper');
        if (!wrapper) {
            wrapper = document.createElement('div');
            wrapper.className = 'semi-toast-wrapper';
            document.body.appendChild(wrapper);
        }

        const toast = document.createElement('div');
        toast.className = `semi-toast semi-toast-${type}`;
        
        let iconClass = 'ri-checkbox-circle-fill';
        if (type === 'warning') iconClass = 'ri-alert-fill';
        if (type === 'error') iconClass = 'ri-close-circle-fill';
        
        let color = 'var(--semi-color-success)';
        if (type === 'warning') color = 'var(--semi-color-warning)';
        if (type === 'error') color = 'var(--semi-color-danger)';
        
        toast.innerHTML = `
            <i class="${iconClass} semi-toast-icon" style="color: ${color}"></i>
            <span class="semi-toast-content">${message}</span>
        `;

        wrapper.appendChild(toast);

        // Auto remove after 3s
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Status Switch Logic
    const statusSwitches = document.querySelectorAll('.js-status-switch');
    statusSwitches.forEach(switchInput => {
        switchInput.addEventListener('change', function() {
            const statusText = this.parentElement.nextElementSibling;
            const row = this.closest('tr');
            const connectorName = row.querySelector('td:first-child span').textContent.trim();
            
            if (this.checked) {
                // Enabled
                statusText.textContent = '运行中';
                statusText.className = 'semi-tag semi-tag-green js-status-text';
                showToast(`${connectorName} 已启动`, 'success');
            } else {
                // Disabled
                statusText.textContent = '已停止';
                statusText.className = 'semi-tag semi-tag-grey js-status-text';
                showToast(`${connectorName} 已停止`, 'warning');
            }
        });
    });

    // Close when clicking outside modal
    if (configModal) {
        configModal.addEventListener('click', (e) => {
            if (e.target === configModal) {
                hideModal();
            }
        });
    }

    // Sync Data Modal Interaction
    const syncModal = document.getElementById('sync-modal');
    const syncBtns = document.querySelectorAll('.js-sync-data');
    const syncModalCloseBtn = document.getElementById('sync-modal-close');
    const syncModalCancelBtn = document.getElementById('sync-modal-cancel');
    const syncModalConfirmBtn = document.getElementById('sync-modal-confirm');

    // Show Sync Modal
    if (syncBtns) {
        syncBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                syncModal.style.display = 'flex';
            });
        });
    }

    // Hide Sync Modal
    const hideSyncModal = () => {
        syncModal.style.display = 'none';
    };

    if (syncModalCloseBtn) syncModalCloseBtn.addEventListener('click', hideSyncModal);
    if (syncModalCancelBtn) syncModalCancelBtn.addEventListener('click', hideSyncModal);

    // Confirm Sync Action
    if (syncModalConfirmBtn) {
        syncModalConfirmBtn.addEventListener('click', () => {
            const daysInput = document.getElementById('sync-days-input');
            const days = daysInput ? daysInput.value : 30;
            
            // Show toast
            showToast(`已开始同步过去 ${days} 天的数据`);
            
            // Add background task
            addTask(`同步 Garmin Connect 数据 (过去${days}天)`);
            
            hideSyncModal();
        });
    }

    // Close when clicking outside sync modal
    if (syncModal) {
        syncModal.addEventListener('click', (e) => {
            if (e.target === syncModal) {
                hideSyncModal();
            }
        });
    }

    // Task Center Logic
    const taskBtn = document.getElementById('task-center-btn');
    const taskDrawerMask = document.getElementById('task-drawer-mask');
    const taskDrawerClose = document.getElementById('task-drawer-close');
    const taskList = document.getElementById('task-list');
    const taskEmptyState = document.getElementById('task-empty-state');
    const taskBadge = document.getElementById('task-badge');

    // Toggle Task Drawer
    const toggleTaskDrawer = () => {
        if (taskDrawerMask.style.display === 'none') {
            taskDrawerMask.style.display = 'block';
        } else {
            taskDrawerMask.style.display = 'none';
        }
    };

    if (taskBtn) taskBtn.addEventListener('click', toggleTaskDrawer);
    if (taskDrawerClose) taskDrawerClose.addEventListener('click', toggleTaskDrawer);
    if (taskDrawerMask) {
        taskDrawerMask.addEventListener('click', (e) => {
            if (e.target === taskDrawerMask) {
                toggleTaskDrawer();
            }
        });
    }

    // Add Task Function
    function addTask(title) {
        // Hide empty state
        if (taskEmptyState) taskEmptyState.style.display = 'none';
        
        // Show badge
        if (taskBadge) taskBadge.style.display = 'block';

        const now = new Date();
        const timeString = now.toLocaleString('zh-CN', { hour12: false });
        
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        taskItem.innerHTML = `
            <div class="task-item-header">
                <span class="task-title">${title}</span>
                <span class="semi-tag semi-tag-blue task-status">进行中</span>
            </div>
            <div class="task-progress-wrapper">
                <div class="task-progress-bar" style="width: 0%"></div>
            </div>
            <div class="task-meta">
                <span>${timeString}</span>
                <span class="task-percent">0%</span>
            </div>
        `;

        // Prepend to list
        taskList.insertBefore(taskItem, taskList.firstChild);

        // Simulate Progress
        let progress = 0;
        const progressBar = taskItem.querySelector('.task-progress-bar');
        const percentText = taskItem.querySelector('.task-percent');
        const statusTag = taskItem.querySelector('.task-status');

        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 15) + 5; // +5~20%
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                
                // Update status to success
                statusTag.className = 'semi-tag semi-tag-green task-status';
                statusTag.textContent = '已完成';
                
                // Hide badge if all tasks done (simplified logic: just hide for now)
                // In real app, check if any running tasks exist
                // if (taskBadge) taskBadge.style.display = 'none'; 
            }
            
            progressBar.style.width = `${progress}%`;
            percentText.textContent = `${progress}%`;
        }, 800);
    }
});
