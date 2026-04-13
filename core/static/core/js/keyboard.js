// keyboard.js

(function() {
    'use strict';
    
    class KeyboardNavigator {
        constructor() {
            console.log('🔍 [KeyboardNav] Initializing');
            this.focusableElements = [];
            this.currentIndex = -1;
            this.inputMode = false;
            this.currentInput = null;
            this.selectMode = false;
            this.currentSelect = null;
            this.init();
        }
        
        init() {
            this.collectFocusableElements();
            
            document.addEventListener('keydown', this.handleKeyDown.bind(this), true);
            
            document.addEventListener('focusin', (e) => {
                const index = this.focusableElements.indexOf(e.target);
                if (index !== -1) {
                    this.currentIndex = index;
                    this.updateFocusStyle();
                }
            });
            
            document.addEventListener('focusout', (e) => {
                if (e.target.tagName === 'INPUT' || 
                    e.target.tagName === 'TEXTAREA') {
                    this.inputMode = false;
                    this.currentInput = null;
                }
            });
            
            console.log('✅ [KeyboardNav] Initialization complete');
        }
        
        collectFocusableElements() {
            const selectors = [
                'input:not([disabled])',
                'select:not([disabled])',
                'textarea:not([disabled])',
                'button:not([disabled])',
                'a[href]',
                '.navbar a', '.navbar button', '.navbar .nav-link',
                '.navbar-brand', '.navbar-toggler',
                '[tabindex]:not([tabindex="-1"])',
                '.card.h-100', '.product-card',
                '.list-group-item',
                '[role="button"]',
                'tr[tabindex="0"]',
                '.pagination a', '.page-link',
                '#minInput', '#maxInput', '.price-range input',
                '#filterButton', '#clearButton',
                '.btn-secondary', '.btn-light',
                'select[name="category"]',
                '.form-select'
            ];
            
            let elements = [];
            selectors.forEach(selector => {
                try {
                    elements = elements.concat(Array.from(document.querySelectorAll(selector)));
                } catch (e) {}
            });
            
            this.focusableElements = elements.filter((el, index, self) => 
                self.indexOf(el) === index
            ).filter(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       el.offsetWidth > 0 && 
                       el.offsetHeight > 0;
            });
            
            // 應用自定義排序
            this.applyCustomSorting();
        }
        
        applyCustomSorting() {
            const customContainer = document.querySelector('[data-keyboard-sort="custom"]');
            
            if (customContainer) {
                // ✅ 優先檢查是否有精確的順序定義
                const focusOrder = customContainer.getAttribute('data-focus-order');
                
                if (focusOrder) {
                    // 方法1：使用精確的 ID 順序
                    const orderedIds = focusOrder.split(',').map(id => id.trim());
                    const orderedElements = [];
                    const missingElements = [];
                    
                    orderedIds.forEach(id => {
                        const element = document.getElementById(id);
                        if (element && customContainer.contains(element)) {
                            // 檢查元素是否可見且可用
                            const style = window.getComputedStyle(element);
                            const isValid = style.display !== 'none' && 
                                           style.visibility !== 'hidden' && 
                                           element.offsetWidth > 0 && 
                                           element.offsetHeight > 0;
                            
                            if (isValid) {
                                orderedElements.push(element);
                            } else {
                                console.log(`⚠️ 元素 ${id} 存在但不可見，已跳過`);
                                missingElements.push(id);
                            }
                        } else {
                            console.log(`⚠️ 元素 ${id} 不存在於當前頁面，已跳過`);
                            missingElements.push(id);
                        }
                    });
                    
                    // 獲取容器內所有可聚焦元素
                    const allContainerElements = Array.from(customContainer.querySelectorAll(
                        'input, button, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
                    ));
                    
                    // 獲取未被指定的其他元素（動態內容）
                    const unspecifiedElements = allContainerElements.filter(el => {
                        const hasId = el.id && orderedIds.includes(el.id);
                        const style = window.getComputedStyle(el);
                        return !hasId && 
                               style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               el.offsetWidth > 0 && 
                               el.offsetHeight > 0;
                    });
                    
                    // 獲取容器外的元素
                    const outsideElements = this.focusableElements.filter(el => 
                        !customContainer.contains(el)
                    );
                    
                    // 組合：指定順序的元素 + 未指定的元素 + 外部元素
                    this.focusableElements = [...orderedElements, ...unspecifiedElements, ...outsideElements];
                    
                    console.log('🎯 已應用精確順序');
                    console.log(`📋 指定元素: ${orderedElements.length} 個 (${orderedIds.filter(id => !missingElements.includes(id)).join(', ')})`);
                    if (missingElements.length > 0) {
                        console.log(`⚠️ 跳過元素: ${missingElements.join(', ')}`);
                    }
                    if (unspecifiedElements.length > 0) {
                        console.log(`🔄 動態元素: ${unspecifiedElements.length} 個`);
                    }
                    
                } else {
                    // 方法2：使用優先級排序（如果沒有精確順序）
                    const containerElements = Array.from(customContainer.querySelectorAll(
                        'input, button, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
                    )).filter(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               el.offsetWidth > 0 && 
                               el.offsetHeight > 0;
                    });
                    
                    const outsideElements = this.focusableElements.filter(el => 
                        !customContainer.contains(el)
                    );
                    
                    const priorityMap = {
                        'input': 1,
                        'button': 2,
                        'a': 3,
                        'select': 4,
                        'textarea': 5
                    };
                    
                    containerElements.sort((a, b) => {
                        const tagA = a.tagName.toLowerCase();
                        const tagB = b.tagName.toLowerCase();
                        const priorityA = priorityMap[tagA] || 99;
                        const priorityB = priorityMap[tagB] || 99;
                        
                        if (priorityA !== priorityB) {
                            return priorityA - priorityB;
                        }
                        
                        return containerElements.indexOf(a) - containerElements.indexOf(b);
                    });
                    
                    this.focusableElements = [...containerElements, ...outsideElements];
                    
                    console.log('🎯 已應用優先級排序，容器內元素數量:', containerElements.length);
                }
            }
        }
        
        handleKeyDown(e) {
            const target = e.target;
            
            if (target.tagName === 'SELECT') {
                this.handleSelectKeyDown(e, target);
                return;
            }
            
            if (this.inputMode && this.currentInput) {
                this.handleInputModeKeyDown(e);
                return;
            }
            
            this.handleNavigationModeKeyDown(e);
        }
        
        handleSelectKeyDown(e, select) {
            const options = select.options;
            const currentIndex = select.selectedIndex;
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (currentIndex < options.length - 1) {
                        select.selectedIndex = currentIndex + 1;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        console.log('⬇️ Selected next:', options[select.selectedIndex].text);
                    }
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    if (currentIndex > 0) {
                        select.selectedIndex = currentIndex - 1;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        console.log('⬆️ Selected previous:', options[select.selectedIndex].text);
                    }
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    select.blur();
                    console.log('✅ Confirmed selection:', options[select.selectedIndex].text);
                    
                    if (select.name === 'category') {
                        const filterBtn = document.getElementById('filterButton');
                        if (filterBtn) filterBtn.click();
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    select.blur();
                    console.log('🚪 Selection cancelled');
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    select.selectedIndex = 0;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                    
                case 'End':
                    e.preventDefault();
                    select.selectedIndex = options.length - 1;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                    
                default:
                    break;
            }
        }
        
        handleInputModeKeyDown(e) {
            const input = this.currentInput;
            
            if (input.type === 'number' || input.id === 'minInput' || input.id === 'maxInput') {
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    let value = parseFloat(input.value) || 0;
                    let step = parseFloat(input.step) || 1;
                    input.value = value + step;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    return;
                }
                
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    let value = parseFloat(input.value) || 0;
                    let step = parseFloat(input.step) || 1;
                    let min = parseFloat(input.min) || 0;
                    let newValue = Math.max(min, value - step);
                    input.value = newValue;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    return;
                }
            }
            
            if (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete' || e.key === ' ') {
                return;
            }
            
            if (e.key === 'Enter') {
                e.preventDefault();
                this.inputMode = false;
                this.currentInput = null;
                input.blur();
                
                if (input.id === 'minInput' || input.id === 'maxInput') {
                    const filterBtn = document.getElementById('filterButton');
                    if (filterBtn) filterBtn.click();
                }
                return;
            }
            
            if (e.key === 'Escape') {
                e.preventDefault();
                this.inputMode = false;
                this.currentInput = null;
                input.blur();
                return;
            }
            
            if (e.key.startsWith('Arrow')) {
                return;
            }
        }
        
        handleNavigationModeKeyDown(e) {
            const target = e.target;
            
            // 左右鍵移動 1 步，上下鍵移動 10 步
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                e.stopPropagation();
                this.moveByOffset(-1);
                return;
            }
            
            if (e.key === 'ArrowRight') {
                e.preventDefault();
                e.stopPropagation();
                this.moveByOffset(1);
                return;
            }
            
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                e.stopPropagation();
                this.moveByOffset(-10);
                return;
            }
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                e.stopPropagation();
                this.moveByOffset(10);
                return;
            }
            
            if (e.key === 'Enter') {
                e.preventDefault();
                
                if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
                    this.inputMode = true;
                    this.currentInput = target;
                    console.log('📝 Entered input mode:', target.id || target.tagName);
                    
                    if (target.type === 'number' || target.id === 'minInput' || target.id === 'maxInput') {
                        target.select();
                    }
                    
                    this.showHint('Input Mode', target);
                    return;
                }
                
                if (target.tagName === 'SELECT') {
                    console.log('🔽 Entered selection mode:', target.id || target.name);
                    this.showHint('Selection Mode', target);
                    return;
                }
                
                this.activateCurrent();
                return;
            }
            
            switch(e.key) {
                case 'Home':
                    e.preventDefault();
                    this.moveToFirst();
                    break;
                case 'End':
                    e.preventDefault();
                    this.moveToLast();
                    break;
            }
        }
        
        // 移動指定步數，跳過無效元素
        moveByOffset(offset) {
            if (this.focusableElements.length === 0) {
                this.collectFocusableElements();
                if (this.focusableElements.length === 0) return;
            }
            
            // 如果當前沒有選中任何元素，從頭開始
            if (this.currentIndex === -1) {
                if (offset > 0) {
                    this.focusElement(0);
                } else {
                    this.focusElement(this.focusableElements.length - 1);
                }
                return;
            }
            
            let newIndex = this.currentIndex + offset;
            
            // 處理循環邊界
            if (newIndex >= this.focusableElements.length) {
                newIndex = newIndex % this.focusableElements.length;
            } else if (newIndex < 0) {
                newIndex = this.focusableElements.length + (newIndex % this.focusableElements.length);
                if (newIndex === this.focusableElements.length) newIndex = 0;
            }
            
            // 驗證目標元素是否仍然有效
            let targetElement = this.focusableElements[newIndex];
            let attempts = 0;
            const maxAttempts = this.focusableElements.length;
            
            // 如果目標元素無效（被隱藏或禁用），繼續移動直到找到有效元素
            while (!this.isElementValid(targetElement) && attempts < maxAttempts) {
                newIndex = (newIndex + (offset > 0 ? 1 : -1) + this.focusableElements.length) % this.focusableElements.length;
                targetElement = this.focusableElements[newIndex];
                attempts++;
            }
            
            if (this.isElementValid(targetElement)) {
                this.focusElement(newIndex);
                console.log(`🎯 移動 ${offset} 步，新索引: ${newIndex}`);
            } else {
                console.warn('⚠️ 未找到有效的可聚焦元素');
            }
        }
        
        // 檢查元素是否有效（可見且可用）
        isElementValid(element) {
            if (!element) return false;
            
            // 檢查元素是否仍在 DOM 中
            if (!document.body.contains(element)) return false;
            
            // 檢查顯示狀態
            const style = window.getComputedStyle(element);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            
            // 檢查尺寸
            if (element.offsetWidth <= 0 || element.offsetHeight <= 0) return false;
            
            // 檢查禁用狀態
            if (element.disabled) return false;
            
            // 檢查是否可聚焦（對於非表單元素）
            if (element.tabIndex === -1 && 
                element.tagName !== 'INPUT' && 
                element.tagName !== 'BUTTON' && 
                element.tagName !== 'A' && 
                element.tagName !== 'SELECT' && 
                element.tagName !== 'TEXTAREA') {
                return false;
            }
            
            return true;
        }
        
        moveToNext() {
            this.moveByOffset(1);
        }
        
        moveToPrevious() {
            this.moveByOffset(-1);
        }
        
        moveToFirst() {
            if (this.focusableElements.length === 0) {
                this.collectFocusableElements();
            }
            
            // 找到第一個有效元素
            let firstValidIndex = 0;
            for (let i = 0; i < this.focusableElements.length; i++) {
                if (this.isElementValid(this.focusableElements[i])) {
                    firstValidIndex = i;
                    break;
                }
            }
            this.focusElement(firstValidIndex);
        }
        
        moveToLast() {
            if (this.focusableElements.length === 0) {
                this.collectFocusableElements();
            }
            
            // 找到最後一個有效元素
            let lastValidIndex = this.focusableElements.length - 1;
            for (let i = this.focusableElements.length - 1; i >= 0; i--) {
                if (this.isElementValid(this.focusableElements[i])) {
                    lastValidIndex = i;
                    break;
                }
            }
            this.focusElement(lastValidIndex);
        }
        
        focusElement(index) {
            if (index >= 0 && index < this.focusableElements.length) {
                const element = this.focusableElements[index];
                
                // 再次驗證元素有效性
                if (!this.isElementValid(element)) {
                    console.warn('⚠️ 目標元素無效，重新收集可聚焦元素');
                    this.collectFocusableElements();
                    // 遞迴調用，但避免無限循環
                    if (this.focusableElements.length > 0 && index < this.focusableElements.length) {
                        this.focusElement(index);
                    }
                    return;
                }
                
                element.focus();
                this.currentIndex = index;
                
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                
                this.updateFocusStyle();
            }
        }
        
        activateCurrent() {
            if (this.currentIndex >= 0 && this.currentIndex < this.focusableElements.length) {
                const element = this.focusableElements[this.currentIndex];
                
                if (!this.isElementValid(element)) {
                    console.warn('⚠️ 當前元素無效，刷新列表');
                    this.refresh();
                    return;
                }
                
                if (element.tagName === 'INPUT' || 
                    element.tagName === 'SELECT' || 
                    element.tagName === 'TEXTAREA') {
                    return;
                }
                
                element.click();
                this.addActivateEffect(element);
            }
        }
        
        addActivateEffect(element) {
            element.classList.add('keyboard-activated');
            setTimeout(() => {
                element.classList.remove('keyboard-activated');
            }, 200);
        }
        
        updateFocusStyle() {
            this.focusableElements.forEach(el => {
                el.classList.remove('keyboard-focus');
            });
            
            if (this.currentIndex >= 0 && this.currentIndex < this.focusableElements.length) {
                const currentEl = this.focusableElements[this.currentIndex];
                if (currentEl && this.isElementValid(currentEl)) {
                    currentEl.classList.add('keyboard-focus');
                }
            }
        }
        
        showHint(mode, element) {
            let hint = document.getElementById('mode-hint');
            if (!hint) {
                hint = document.createElement('div');
                hint.id = 'mode-hint';
                hint.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #0d6efd;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 40px;
                    font-size: 14px;
                    z-index: 10000;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    animation: slideDown 0.3s;
                    font-weight: bold;
                `;
                document.body.appendChild(hint);
            }
            
            let elementName = element.id || element.name || element.tagName;
            let instructions = '';
            
            if (mode === 'Input Mode') {
                instructions = element.type === 'number' ? 
                    '<kbd>↑</kbd> <kbd>↓</kbd> adjust value | <kbd>Enter</kbd> confirm' :
                    '<kbd>Enter</kbd> confirm | <kbd>Esc</kbd> cancel';
            } else if (mode === 'Selection Mode') {
                instructions = '<kbd>↑</kbd> <kbd>↓</kbd> select option | <kbd>Enter</kbd> confirm | <kbd>Esc</kbd> cancel';
            }
            
            hint.innerHTML = `
                <span style="margin-right: 10px;">⌨️ ${mode}</span>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; margin-right: 10px;">
                    ${elementName}
                </span>
                ${instructions}
            `;
            
            setTimeout(() => {
                if (hint && hint.parentNode) {
                    hint.style.opacity = '0';
                    setTimeout(() => hint.remove(), 300);
                }
            }, 3000);
        }
        
        refresh() {
            const previousIndex = this.currentIndex;
            const previousElement = previousIndex >= 0 ? this.focusableElements[previousIndex] : null;
            
            this.collectFocusableElements();
            
            // 嘗試恢復之前的焦點
            if (previousElement && this.isElementValid(previousElement)) {
                const newIndex = this.focusableElements.indexOf(previousElement);
                if (newIndex !== -1) {
                    this.currentIndex = newIndex;
                    this.focusElement(newIndex);
                    return;
                }
            }
            
            // 如果之前的元素不存在，嘗試保持大致位置
            if (previousIndex >= 0 && this.focusableElements.length > 0) {
                const newIndex = Math.min(previousIndex, this.focusableElements.length - 1);
                this.focusElement(newIndex);
            }
        }
    }
    
    function addKeyboardStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .keyboard-focus {
                outline: 3px solid #0d6efd !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25) !important;
                transition: outline 0.1s ease;
                z-index: 1000;
            }
            
            .keyboard-activated {
                transform: scale(0.98);
                background-color: rgba(13, 110, 253, 0.1) !important;
                transition: transform 0.1s, background-color 0.1s;
            }
            
            input:focus, select:focus, textarea:focus {
                outline: 3px solid #ffc107 !important;
                outline-offset: 2px !important;
                border-color: #ffc107 !important;
            }
            
            select option:checked {
                background: #0d6efd linear-gradient(0deg, #0d6efd 0%, #0d6efd 100%);
                color: white;
            }
            
            @keyframes slideDown {
                from { transform: translate(-50%, -100%); opacity: 0; }
                to { transform: translate(-50%, 0); opacity: 1; }
            }
            
            .keyboard-hint {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 12px 20px;
                border-radius: 40px;
                font-size: 14px;
                z-index: 9999;
                border-left: 4px solid #0d6efd;
                opacity: 0.3;
                transform: translateX(calc(100% - 50px));
                transition: all 0.3s;
                pointer-events: none;
            }
            
            .keyboard-hint kbd, #mode-hint kbd {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 4px 8px;
                border-radius: 6px;
                margin: 0 2px;
                font-size: 0.9em;
            }
            
            body.keyboard-user .keyboard-hint {
                opacity: 1;
                transform: translateX(0);
            }
        `;
        document.head.appendChild(style);
    }
    
    function addKeyboardHint() {
        const hint = document.createElement('div');
        hint.className = 'keyboard-hint';
        hint.innerHTML = `
            <span style="color: #0d6efd; font-weight: bold;">⌨️ Keyboard Navigation</span>
            <kbd>←</kbd> <kbd>→</kbd> move 1 step
            <kbd>↑</kbd> <kbd>↓</kbd> move 10 steps
            <kbd>Enter</kbd> select/input
            <span style="color: #ffc107;">🔽 Dropdown: ↑↓ select Enter confirm</span>
        `;
        document.body.appendChild(hint);
    }
    
    function detectKeyboardUser() {
        document.addEventListener('keydown', () => {
            document.body.classList.add('keyboard-user');
            if (window.keyboardTimer) clearTimeout(window.keyboardTimer);
            window.keyboardTimer = setTimeout(() => {
                document.body.classList.remove('keyboard-user');
            }, 3000);
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-user');
        });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        addKeyboardStyles();
        addKeyboardHint();
        detectKeyboardUser();
        
        window.keyboardNav = new KeyboardNavigator();
        
        const observer = new MutationObserver(() => {
            window.keyboardNav?.refresh();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
})();
