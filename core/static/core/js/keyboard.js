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
            
            if (e.key.startsWith('Arrow')) {
                e.preventDefault();
                e.stopPropagation();
                
                switch(e.key) {
                    case 'ArrowDown':
                    case 'ArrowRight':
                        this.moveToNext();
                        break;
                    case 'ArrowUp':
                    case 'ArrowLeft':
                        this.moveToPrevious();
                        break;
                }
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
        
        moveToNext() {
            if (this.focusableElements.length === 0) {
                this.collectFocusableElements();
            }
            
            let newIndex = (this.currentIndex + 1) % this.focusableElements.length;
            if (this.currentIndex === -1) newIndex = 0;
            
            this.focusElement(newIndex);
        }
        
        moveToPrevious() {
            if (this.focusableElements.length === 0) {
                this.collectFocusableElements();
            }
            
            let newIndex = this.currentIndex - 1;
            if (newIndex < 0) newIndex = this.focusableElements.length - 1;
            if (this.currentIndex === -1) newIndex = this.focusableElements.length - 1;
            
            this.focusElement(newIndex);
        }
        
        moveToFirst() {
            this.focusElement(0);
        }
        
        moveToLast() {
            this.focusElement(this.focusableElements.length - 1);
        }
        
        focusElement(index) {
            if (index >= 0 && index < this.focusableElements.length) {
                const element = this.focusableElements[index];
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
                currentEl.classList.add('keyboard-focus');
            }
        }
        
        refresh() {
            this.collectFocusableElements();
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
            <kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd> move
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
