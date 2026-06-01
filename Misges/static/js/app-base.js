// ===== APP BASE JAVASCRIPT =====
(function() {
    'use strict';

    var cfg = window.APP_CONFIG || {};

    // ===== CALCULATOR =====
    var calculatorPanel = document.getElementById('calculatorPanel');
    var calculatorDisplay = document.getElementById('calculatorDisplay');
    var calculatorToggle = document.getElementById('calculatorToggle');
    var calculatorClose = document.getElementById('calculatorClose');
    var calculatorPaste = document.getElementById('calculatorPaste');
    var calculatorValue = '0';

    function pasteCalcResult(target) {
        if (!target) return;
        var val = calculatorDisplay.value;
        if (val === 'Erreur') return;
        target.value = val;
        target.dispatchEvent(new Event('input', { bubbles: true }));
        target.dispatchEvent(new Event('change', { bubbles: true }));
        calculatorPanel.hidden = true;
    }

    function renderCalculator() { calculatorDisplay.value = calculatorValue; }

    function calculateExpression() {
        if (!/^[0-9+\-*/%. ()]+$/.test(calculatorValue)) { calculatorValue = 'Erreur'; return; }
        try {
            var result = Function('"use strict"; return (' + calculatorValue + ')')();
            calculatorValue = Number.isFinite(result) ? String(Math.round(result * 100) / 100) : 'Erreur';
        } catch(_) { calculatorValue = 'Erreur'; }
    }

    if (calculatorToggle) {
        calculatorToggle.addEventListener('click', function() {
            calculatorPanel.hidden = !calculatorPanel.hidden;
            if (!calculatorPanel.hidden) calculatorPanel.focus();
        });
    }
    if (calculatorClose) {
        calculatorClose.addEventListener('click', function() { calculatorPanel.hidden = true; });
    }
    if (calculatorPaste) {
        calculatorPaste.addEventListener('click', function() { pasteCalcResult(document.activeElement); });
    }

    document.addEventListener('click', function(event) {
        if (!calculatorPanel || calculatorPanel.hidden) return;
        var target = event.target.closest('input:not([readonly]):not([disabled]):not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio]), textarea:not([readonly]):not([disabled])');
        if (target && !calculatorPanel.contains(target)) { pasteCalcResult(target); }
    });

    function handleCalcKey(key) {
        if (key === 'clear') { calculatorValue = '0'; }
        else if (key === 'back') { calculatorValue = calculatorValue.length > 1 ? calculatorValue.slice(0, -1) : '0'; }
        else if (key === '=') { calculateExpression(); }
        else if ('+-*/%.'.includes(key) && '+-*/%.'.includes(calculatorValue.slice(-1))) { calculatorValue = calculatorValue.slice(0, -1) + key; }
        else { calculatorValue = calculatorValue === '0' || calculatorValue === 'Erreur' ? key : calculatorValue + key; }
        renderCalculator();
    }

    document.querySelectorAll('[data-calc]').forEach(function(button) {
        button.addEventListener('click', function() { handleCalcKey(button.dataset.calc); });
    });

    // ===== SIDEBAR TOGGLE =====
    var sidebar = document.getElementById('appSidebar');
    var backdrop = document.getElementById('sidebarBackdrop');
    var hamburger = document.getElementById('headerHamburger');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('show');
        document.body.style.overflow = '';
    }

    function toggleSidebar() {
        if (window.innerWidth > 991) {
            document.body.classList.toggle('sidebar-hidden');
        } else {
            var isOpen = sidebar && sidebar.classList.contains('open');
            if (isOpen) { closeSidebar(); } else { openSidebar(); }
        }
    }

    var backBtn = document.getElementById('backButton');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            if (document.referrer && document.referrer.startsWith(window.location.origin)) {
                history.back();
            } else if (cfg.homeUrl) {
                window.location.href = cfg.homeUrl;
            }
        });
    }

    if (hamburger) { hamburger.addEventListener('click', toggleSidebar); }
    if (backdrop) { backdrop.addEventListener('click', closeSidebar); }

    document.querySelectorAll('.sidebar-link').forEach(function(link) {
        link.addEventListener('click', closeSidebar);
    });

    // Mini sidebar toggle
    var miniSidebarToggle = document.getElementById('miniSidebarToggle');
    if (miniSidebarToggle && sidebar) {
        miniSidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('mini');
            localStorage.setItem('miniSidebar', sidebar.classList.contains('mini'));
        });
        if (localStorage.getItem('miniSidebar') === 'true') {
            sidebar.classList.add('mini');
        }
    }

    // ===== ACTIVE SIDEBAR LINK =====
    document.querySelectorAll('.side-link, .side-sublink').forEach(function(link) {
        if (link.href && link.href === window.location.href.split('?')[0].split('#')[0]) {
            link.classList.add('active');
        }
    });

    // ===== GLOBAL SEARCH WITH SUGGESTIONS =====
    var globalSearch = document.getElementById('globalSearch');
    var globalSearchBtn = document.getElementById('globalSearchBtn');
    var searchSuggestions = document.getElementById('searchSuggestions');

    function submitGlobalSearch(query) {
        if (!query) query = globalSearch ? globalSearch.value.trim() : '';
        var url = new URL(cfg.productListUrl || '/produits/', window.location.origin);
        if (query) url.searchParams.set('q', query);
        window.location.href = url.toString();
    }

    if (globalSearch) {
        var searchTimer;
        var suggestionIndex = -1;

        globalSearch.addEventListener('input', function() {
            var q = this.value.trim();
            if (q.length < 2) { if (searchSuggestions) { searchSuggestions.classList.remove('show'); searchSuggestions.innerHTML = ''; } return; }
            clearTimeout(searchTimer);
            searchTimer = setTimeout(function() {
                fetch((cfg.apiProductsUrl || '/api/products/') + '?q=' + encodeURIComponent(q))
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!searchSuggestions) return;
                        if (!data || !data.length) {
                            searchSuggestions.innerHTML = '<div class="search-suggestion-empty">Aucun produit trouvé</div>';
                            searchSuggestions.classList.add('show');
                            return;
                        }
                        var html = '';
                        data.slice(0, 8).forEach(function(p) {
                            html += '<a class="search-suggestion-item" href="' + (cfg.productListUrl || '/produits/') + '?q=' + encodeURIComponent(p.name) + '">'
                                + '<span class="s-name">' + p.name + '</span>'
                                + '<span class="s-price">' + (p.price || 0) + ' FCFA</span>'
                                + '<span class="s-stock">Stock: ' + (p.stock || 0) + '</span>'
                                + '</a>';
                        });
                        html += '<a class="search-suggestion-item" href="' + (cfg.productListUrl || '/produits/') + '?q=' + encodeURIComponent(q) + '" style="border-bottom:0;opacity:.65;font-size:.75rem;justify-content:center;">Voir tous les résultats →</a>';
                        searchSuggestions.innerHTML = html;
                        searchSuggestions.classList.add('show');
                        suggestionIndex = -1;
                    });
            }, 250);
        });

        globalSearch.addEventListener('keydown', function(event) {
            var items = searchSuggestions ? searchSuggestions.querySelectorAll('.search-suggestion-item') : [];
            if (event.key === 'ArrowDown') {
                event.preventDefault();
                suggestionIndex = Math.min(suggestionIndex + 1, items.length - 1);
                items.forEach(function(el, i) { el.classList.toggle('highlighted', i === suggestionIndex); });
                if (items[suggestionIndex]) items[suggestionIndex].scrollIntoView({ block: 'nearest' });
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                suggestionIndex = Math.max(suggestionIndex - 1, -1);
                items.forEach(function(el, i) { el.classList.toggle('highlighted', i === suggestionIndex); });
            } else if (event.key === 'Enter') {
                event.preventDefault();
                if (suggestionIndex >= 0 && items[suggestionIndex]) {
                    window.location.href = items[suggestionIndex].href;
                } else {
                    submitGlobalSearch();
                }
            } else if (event.key === 'Escape') {
                if (searchSuggestions) searchSuggestions.classList.remove('show');
            }
        });

        globalSearch.addEventListener('blur', function() {
            setTimeout(function() { if (searchSuggestions) searchSuggestions.classList.remove('show'); }, 200);
        });

        globalSearch.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                this.dispatchEvent(new Event('input'));
            }
        });

        if (globalSearchBtn) globalSearchBtn.addEventListener('click', function() { submitGlobalSearch(); });

        // Close suggestions on overlay click
        document.addEventListener('click', function(e) {
            var wrapper = document.getElementById('headerSearchWrapper');
            if (searchSuggestions && wrapper && !wrapper.contains(e.target)) {
                searchSuggestions.classList.remove('show');
            }
        });
    }

    // ===== TEXTAREA AUTO-RESIZE =====
    function fitTextarea(textarea) {
        textarea.style.height = 'auto';
        var nextHeight = Math.min(Math.max(textarea.scrollHeight, 38), 150);
        textarea.style.height = nextHeight + 'px';
    }
    document.querySelectorAll('textarea.form-control').forEach(function(textarea) {
        fitTextarea(textarea);
        textarea.addEventListener('input', function() { fitTextarea(textarea); });
    });

    // ===== NETWORK STATUS =====
    var networkChip = document.getElementById('networkChip');
    function renderNetworkState() {
        if (!networkChip) return;
        var online = navigator.onLine;
        networkChip.classList.toggle('is-online', online);
        networkChip.classList.toggle('is-offline', !online);
        networkChip.innerHTML = online
            ? '<i class="bi bi-wifi"></i><span>En ligne</span>'
            : '<i class="bi bi-wifi-off"></i><span>Hors ligne</span>';
    }
    window.addEventListener('online', renderNetworkState);
    window.addEventListener('offline', renderNetworkState);
    renderNetworkState();

    // ===== THEME TOGGLE =====
    var themeToggle = document.getElementById('themeToggle');
    var bodyEl = document.getElementById('appBody');
    var darkMode = localStorage.getItem('darkMode') === 'true';

    if (cfg.theme) { localStorage.setItem('appTheme', cfg.theme); }

    function applyTheme() {
        if (!bodyEl) return;
        if (darkMode) {
            bodyEl.className = bodyEl.className.replace(/theme-\w+/, 'theme-dark');
            if (themeToggle) themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
        } else {
            var saved = localStorage.getItem('appTheme') || cfg.theme || 'blue';
            bodyEl.className = bodyEl.className.replace(/theme-\w+/, 'theme-' + saved);
            if (themeToggle) themeToggle.innerHTML = '<i class="bi bi-moon-stars"></i>';
        }
        localStorage.setItem('darkMode', darkMode);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            darkMode = !darkMode;
            applyTheme();
        });
    }
    applyTheme();

    // Auto dark mode between 19:00 and 07:00
    (function() {
        var h = new Date().getHours();
        if (!localStorage.getItem('darkMode')) {
            if (h >= 19 || h < 7) { darkMode = true; applyTheme(); }
        }
    })();

    // ===== POST-MESSAGE HANDLER =====
    window.addEventListener('message', function(event) {
        if (event.origin !== window.location.origin) return;
        if (event.data && event.data.type === 'store-settings-saved') {
            window.location.reload();
        }
    });

    // ===== VOICE ALERTS =====
    if (cfg.voiceAlerts) {
        var lowStockCount = parseInt(document.body.dataset.lowStock) || 0;
        if (lowStockCount > 0 && 'speechSynthesis' in window) {
            var msg = lowStockCount === 1
                ? 'Attention, un produit a un stock faible.'
                : 'Attention, ' + lowStockCount + ' produits ont un stock faible.';
            var utterance = new SpeechSynthesisUtterance(msg);
            utterance.lang = 'fr-FR';
            utterance.rate = 0.9;
            speechSynthesis.speak(utterance);
        }
    }

    // ===== CALCULATOR KEYBOARD =====
    document.addEventListener('keydown', function(event) {
        if (!calculatorPanel || calculatorPanel.hidden) return;
        var tag = document.activeElement && document.activeElement.tagName.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        var key = event.key;
        if (key >= '0' && key <= '9') { handleCalcKey(key); event.preventDefault(); }
        else if (key === '.') { handleCalcKey('.'); event.preventDefault(); }
        else if (key === '+') { handleCalcKey('+'); event.preventDefault(); }
        else if (key === '-') { handleCalcKey('-'); event.preventDefault(); }
        else if (key === '*') { handleCalcKey('*'); event.preventDefault(); }
        else if (key === '/') { handleCalcKey('/'); event.preventDefault(); }
        else if (key === '%') { handleCalcKey('%'); event.preventDefault(); }
        else if (key === 'Enter' || key === '=') { handleCalcKey('='); event.preventDefault(); }
        else if (key === 'Backspace') { handleCalcKey('back'); event.preventDefault(); }
        else if (key === 'Escape') { calculatorPanel.hidden = true; event.preventDefault(); }
        else if (key === 'c' || key === 'C') { handleCalcKey('clear'); event.preventDefault(); }
    });

    // ===== TOAST NOTIFICATIONS =====
    function playDangerSound() {
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.frequency.value = 660;
            gain.gain.setValueAtTime(0.12, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
            osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.2);
        } catch(_) {}
    }

    window.showToast = function showToast(message, type) {
        if (type === 'danger') playDangerSound();
        var container = document.getElementById('toastContainer');
        if (!container) return;
        var icons = { success: 'bi-check-circle-fill text-success', danger: 'bi-x-circle-fill text-danger', warning: 'bi-exclamation-triangle-fill text-warning', info: 'bi-info-circle-fill text-primary' };
        var icon = icons[type] || icons.info;
        var toast = document.createElement('div');
        toast.className = 'toast-notif';
        toast.innerHTML = '<i class="bi ' + icon + '"></i><div class="toast-msg">' + message + '</div><button class="toast-close" onclick="this.closest(\'.toast-notif\').classList.add(\'removing\');setTimeout(function(){this.closest(\'.toast-notif\').remove()}.bind(this),200)">&times;</button>';
        container.appendChild(toast);
        setTimeout(function() { toast.classList.add('removing'); setTimeout(function() { toast.remove(); }, 200); }, 4000);
    };

    // Convert Django alerts to toasts
    document.querySelectorAll('.alert[role="alert"]').forEach(function(el) {
        var msg = el.innerHTML;
        var type = 'info';
        if (el.classList.contains('alert-success')) type = 'success';
        else if (el.classList.contains('alert-danger')) type = 'danger';
        else if (el.classList.contains('alert-warning')) type = 'warning';
        window.showToast(msg, type);
        el.style.display = 'none';
    });

    // Low stock toast
    var lowStock = parseInt(document.body.dataset.lowStock) || 0;
    if (lowStock > 0) {
        setTimeout(function() { window.showToast(lowStock + ' produit(s) en stock faible !', 'warning'); }, 1500);
    }

    // ===== BACK TO TOP =====
    var backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', function() { backToTop.classList.toggle('visible', window.scrollY > 300); });
        backToTop.addEventListener('click', function() { window.scrollTo({ top: 0, behavior: 'smooth' }); });
    }

    // Smooth scroll for anchor links
    document.addEventListener('click', function(e) {
        var a = e.target.closest('a[href^="#"]');
        if (a) {
            e.preventDefault();
            var el = document.querySelector(a.getAttribute('href'));
            if (el) el.scrollIntoView({ behavior: 'smooth' });
        }
    });

    // ===== KEYBOARD SHORTCUTS =====
    document.addEventListener('keydown', function(e) {
        // ? help
        if (e.key === '?' && !e.target.closest('input,textarea,select')) {
            var help = '<div style="font-size:.8rem;line-height:1.8"><b>Raccourcis clavier</b><br>'
                + '<kbd>?</kbd> Aide<br>'
                + '<kbd>Esc</kbd> Fermer / Annuler<br>'
                + '<kbd>F2</kbd> Rechercher<br>'
                + '<kbd>F5</kbd> Valider (Caisse)<br>'
                + '<kbd>Alt+1</kbd> Accueil <kbd>Alt+2</kbd> Caisse <kbd>Alt+3</kbd> Produits<br>'
                + '<kbd>Ctrl+K</kbd> Recherche rapide <kbd>N</kbd> Nouvelle vente<br>'
                + '<kbd>Ctrl+F</kbd> Recherche globale</div>';
            window.showToast(help, 'info');
        }
        // Alt+number navigation
        if (e.altKey || e.ctrlKey) {
            var map = { '1': cfg.homeUrl || '/', '2': cfg.posUrl || '/caisse/', '3': cfg.productsUrl || '/produits/' };
            var url = map[e.key];
            if (url) { e.preventDefault(); window.location.href = url; }
            if (e.ctrlKey && e.key === 'f') { e.preventDefault(); var s = document.getElementById('globalSearch'); if (s) s.focus(); }
        }
        // Ctrl+K quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var overlay = document.getElementById('quickSearchOverlay');
            if (overlay) {
                overlay.style.display = 'block';
                var input = document.getElementById('quickSearchInput');
                if (input) { input.value = ''; input.focus(); }
                var results = document.getElementById('quickSearchResults');
                if (results) results.innerHTML = '';
            }
        }
        // N for new sale
        if (e.key === 'n' && !e.ctrlKey && !e.altKey && !e.metaKey && !e.target.closest('input,textarea,select')) {
            e.preventDefault();
            window.location.href = cfg.posUrl || '/caisse/';
        }
    });

    // ===== QUICK SEARCH (Ctrl+K) =====
    (function() {
        var overlay = document.getElementById('quickSearchOverlay');
        var input = document.getElementById('quickSearchInput');
        var results = document.getElementById('quickSearchResults');
        if (!overlay) return;

        overlay.addEventListener('click', function(e) { if (e.target === overlay) overlay.style.display = 'none'; });
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && overlay.style.display === 'block') { overlay.style.display = 'none'; } });

        var timer;
        if (input) {
            input.addEventListener('input', function() {
                clearTimeout(timer);
                var q = this.value.trim();
                if (q.length < 2) { results.innerHTML = ''; return; }
                timer = setTimeout(function() {
                    fetch((cfg.apiProductsUrl || '/api/products/') + '?q=' + encodeURIComponent(q))
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (!data || !data.length) { results.innerHTML = '<div class="text-center text-secondary small py-3">Aucun résultat</div>'; return; }
                            var html = '';
                            data.slice(0, 10).forEach(function(p, i) {
                                html += '<a href="' + (cfg.productEditUrl || '/produits/gestion/') + p.id + '/modifier/" class="d-flex align-items-center gap-3 px-3 py-2 text-decoration-none" style="color:var(--app-text);border-bottom:1px solid var(--surface-border);" data-index="' + i + '">'
                                    + '<span style="font-weight:600;flex:1;">' + p.name + '</span>'
                                    + '<span class="small text-secondary">' + (p.price || 0) + ' FCFA</span>'
                                    + '<span class="small text-secondary">Stock: ' + (p.stock || 0) + '</span>'
                                    + '</a>';
                            });
                            results.innerHTML = html;
                        });
                }, 200);
            });

            input.addEventListener('keydown', function(e) {
                var links = results.querySelectorAll('a');
                if (!links.length) return;
                var current = results.querySelector('a:hover') || results.querySelector('a[data-index="0"]');
                if (e.key === 'ArrowDown') { e.preventDefault(); var next = current.nextElementSibling || links[0]; if (next) { next.focus(); next.scrollIntoView({block:'nearest'}); } }
                if (e.key === 'ArrowUp') { e.preventDefault(); var prev = current.previousElementSibling || links[links.length-1]; if (prev) { prev.focus(); prev.scrollIntoView({block:'nearest'}); } }
                if (e.key === 'Enter') { e.preventDefault(); if (document.activeElement && document.activeElement.tagName === 'A') { overlay.style.display = 'none'; } }
            });
        }
    })();

    // ===== IMAGE LIGHTBOX =====
    window.openModal = function openModal(src) {
        var modalImg = document.getElementById('modalImage');
        if (modalImg) {
            modalImg.src = src;
            var modal = new bootstrap.Modal(document.getElementById('imageModal'));
            if (modal) modal.show();
        }
    };

    // ===== LONG-PRESS CONTEXT MENU =====
    document.addEventListener('DOMContentLoaded', function() {
        var actionModalEl = document.getElementById('imageActionModal');
        if (!actionModalEl) return;
        var actionModal = new bootstrap.Modal(actionModalEl);
        var lastTouchTime = 0;

        document.querySelectorAll('.product-thumb:not(.product-thumb-empty)').forEach(function(img) {
            img.addEventListener('click', function(e) {
                var now = Date.now();
                if (now - lastTouchTime > 500) { window.openModal(this.src); }
            });

            var pressTimer = null;
            img.addEventListener('touchstart', function(e) {
                pressTimer = setTimeout(function() {
                    pressTimer = null;
                    lastTouchTime = Date.now();
                    var productNameEl = this.closest('tr') ? this.closest('tr').querySelector('td:nth-child(3)') : null;
                    var productName = productNameEl ? productNameEl.textContent.trim() : '';
                    document.getElementById('imageActionProductName').textContent = productName;
                    document.getElementById('imageActionViewBtn').onclick = function() { window.openModal(this.src); actionModal.hide(); }.bind(this);
                    var editLink = document.getElementById('imageActionEditBtn');
                    var row = this.closest('tr');
                    if (row) {
                        var editHref = row.querySelector('a.btn-outline-secondary') ? row.querySelector('a.btn-outline-secondary').getAttribute('href') : null;
                        if (editHref) editLink.href = editHref;
                    }
                    actionModal.show();
                }.bind(this), 600);
            }.bind(this));

            img.addEventListener('touchend', function() { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
            img.addEventListener('touchmove', function() { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
        });
    });

    // ===== HEADER DROPDOWN =====
    document.querySelectorAll('.header-btn-wrapper').forEach(function(wrapper) {
        wrapper.addEventListener('click', function(e) {
            if (window.innerWidth <= 991) {
                wrapper.classList.toggle('show');
                e.stopPropagation();
            }
        });
    });
    document.addEventListener('click', function() {
        document.querySelectorAll('.header-btn-wrapper.show').forEach(function(w) { w.classList.remove('show'); });
    });

    // ===== NAVIGATION PROGRESS BAR =====
    (function() {
        var bar = document.getElementById('navProgress');
        if (!bar) return;
        var showTimer;
        function showProgress() { bar.classList.add('active'); }
        function hideProgress() { bar.classList.remove('active'); }
        document.addEventListener('click', function(e) {
            var a = e.target.closest('a:not([href^="#"]):not([href^="javascript"]):not([href^="mailto"]):not([download])');
            if (a && a.href && a.href.startsWith(window.location.origin) && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
                showProgress();
            }
        });
        window.addEventListener('beforeunload', showProgress);
        window.addEventListener('pageshow', hideProgress);
        hideProgress();
    })();

    // ===== CART FAB TOGGLE =====
    (function() {
        var fab = document.getElementById('cartFab');
        if (!fab) return;
        function updateFab(count) {
            if (count > 0) {
                fab.style.display = 'flex';
                var badge = fab.querySelector('.fab-badge');
                if (badge) badge.textContent = count;
                else fab.insertAdjacentHTML('beforeend', '<span class="fab-badge">' + count + '</span>');
            } else {
                fab.style.display = 'none';
            }
        }
        // If cart count is in a meta/data attribute, read it
        var bodyEl = document.getElementById('appBody');
        if (bodyEl) {
            var observer = new MutationObserver(function() {
                var countEl = document.querySelector('.side-link[href*=\"panier\"] .badge');
                if (countEl) updateFab(parseInt(countEl.textContent) || 0);
            });
        }
    })();
})();
