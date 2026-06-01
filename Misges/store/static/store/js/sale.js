(function() {
    'use strict';

    var productMap = new Map();
    var allProducts = [];
    var html5QrCode = null;
    var searchInput, dropdown, dropdownInner;

    async function loadProducts() {
        try {
            var resp = await fetch('/api/products/');
            var data = await resp.json();
            allProducts = data;
            data.forEach(function(p) {
                if (p.barcode) productMap.set(p.barcode.toLowerCase(), p);
            });
        } catch (e) {
            console.warn('loadProducts failed:', e);
        }
    }

    function esc(text) {
        var d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    function showSuggestions(term) {
        var t = term.trim().toLowerCase();
        if (!t) {
            dropdownInner.innerHTML = '';
            dropdown.hidden = true;
            return;
        }
        var matches = allProducts.filter(function(p) {
            return p.name.toLowerCase().includes(t) ||
                (p.barcode && p.barcode.toLowerCase().includes(t)) ||
                (p.code && p.code.toLowerCase().includes(t));
        }).slice(0, 10);
        if (!matches.length) {
            dropdownInner.innerHTML = '';
            dropdown.hidden = true;
            return;
        }
        var html = '';
        matches.forEach(function(p) {
            html += '<div class="suggestion-item" data-id="' + p.id + '">' +
                '<div class="suggestion-info">' +
                '<strong>' + esc(p.name) + '</strong>' +
                '<span class="text-secondary">' + p.price + ' FCFA</span>' +
                '<small class="text-muted">' +
                (p.barcode ? esc(p.barcode) + ' ' : '') +
                (p.code ? esc(p.code) : '') +
                '</small></div>' +
                '<span class="badge bg-light text-dark ms-auto">' + p.stock + ' ' + esc(p.unit_display) + '</span>' +
                '</div>';
        });
        dropdownInner.innerHTML = html;
        dropdown.hidden = false;
    }

    function openScanner() {
        var modalEl = document.getElementById('scannerModal');
        if (!modalEl) return;
        var modal = new bootstrap.Modal(modalEl);
        modal.show();
        modalEl.addEventListener('shown.bs.modal', function() {
            if (!html5QrCode) html5QrCode = new Html5Qrcode('scannerContainer');
            html5QrCode.start(
                { facingMode: 'environment' },
                { fps: 10, qrbox: { width: 250, height: 150 }, aspectRatio: 1 },
                onScanSuccess,
                function() {}
            ).catch(function() {
                document.getElementById('scannerContainer').innerHTML = '<div class="alert alert-warning m-0 text-center">Cam\u00e9ra non accessible.</div>';
            });
        }, { once: true });
    }

    function stopScanner() {
        if (html5QrCode && html5QrCode.isScanning) {
            html5QrCode.stop().catch(function() {});
        }
    }

    function onScanSuccess(code) {
        stopScanner();
        bootstrap.Modal.getInstance(document.getElementById('scannerModal')).hide();
        var product = productMap.get(code.toLowerCase());
        if (product && typeof addRow === 'function') {
            addRow(product.id);
        } else {
            searchInput.value = code;
            showSuggestions(code);
        }
    }

    function selectSuggestion(item) {
        dropdown.hidden = true;
        searchInput.value = '';
        if (typeof addRow === 'function') addRow(item.dataset.id);
        searchInput.focus();
    }

    document.addEventListener('DOMContentLoaded', function() {
        searchInput = document.getElementById('productSearch');
        dropdown = document.getElementById('suggestionDropdown');
        dropdownInner = dropdown && dropdown.querySelector('.suggestion-dropdown-inner');
        if (!searchInput || !dropdown || !dropdownInner) return;

        var scannerBtn = document.createElement('button');
        scannerBtn.id = 'scannerBtn';
        scannerBtn.type = 'button';
        scannerBtn.className = 'btn btn-outline-secondary ms-1 flex-shrink-0';
        scannerBtn.innerHTML = '<i class="bi bi-upc-scan"></i>';
        scannerBtn.title = 'Scanner un code-barres';
        scannerBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            openScanner();
        });

        var inputRow = searchInput.parentNode;
        if (inputRow && inputRow.classList.contains('d-flex')) {
            inputRow.appendChild(scannerBtn);
        }

        searchInput.addEventListener('input', function() {
            showSuggestions(this.value);
        });

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                var first = dropdownInner.querySelector('.suggestion-item');
                if (first) { selectSuggestion(first); e.preventDefault(); }
            }
            if (e.key === 'Escape') {
                dropdown.hidden = true;
                searchInput.value = '';
            }
        });

        dropdown.addEventListener('click', function(e) {
            var item = e.target.closest('.suggestion-item');
            if (!item) return;
            e.stopPropagation();
            selectSuggestion(item);
        });

        document.addEventListener('click', function(e) {
            if (dropdown.hidden) return;
            if (searchInput.contains(e.target)) return;
            if (dropdown.contains(e.target)) return;
            if (scannerBtn && scannerBtn.contains(e.target)) return;
            dropdown.hidden = true;
        });

        loadProducts();
    });

    window.addToCart = function(id) {
        if (typeof addRow === 'function') addRow(id);
    };
    window.openScanner = openScanner;
    window.stopScanner = stopScanner;
})();
