// --- App Logic ---
const app = {
    data: [],
    currentFilter: 'todos',
    activePackageId: null,
    photoData: null,
    canvas: null,
    ctx: null,
    isDrawing: false,
    scanner: null,

    init() {
        // Initialize localStorage if empty
        const stored = localStorage.getItem('facilities_mail_db');
        if (stored) {
            this.data = JSON.parse(stored);
        } else {
            // Seed some data for demo if totally empty
            /* this.data = []; */
        }

        this.canvas = document.getElementById('signatureCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();

        this.render();

        // Handle resize for canvas
        window.addEventListener('resize', () => this.resizeCanvas());
    },

    // Navigation
    navigate(view) {
        document.getElementById('view-dashboard').classList.add('hidden');
        document.getElementById('view-register').classList.add('hidden');
        document.getElementById(`view-${view}`).classList.remove('hidden');

        const fab = document.getElementById('fab');
        const searchBar = document.getElementById('searchBar');

        if (view === 'register') {
            fab.classList.add('scale-0');
            searchBar.classList.add('hidden');
        } else {
            fab.classList.remove('scale-0');
            searchBar.classList.remove('hidden');
            this.resetRegisterForm();
        }
    },

    // CRUD & Data
    saveNewPackage(e) {
        e.preventDefault();
        const form = e.target;

        const newPackage = {
            id: Date.now().toString(),
            tracking: form.tracking.value.toUpperCase(),
            recipient: form.recipient.value,
            location: form.location.value,
            type: form.type.value,
            photo: this.photoData,
            status: 'Na Portaria', // Initial Status
            createdAt: new Date().toISOString(),
            history: [
                { status: 'Na Portaria', timestamp: new Date().toISOString() }
            ]
        };

        this.data.unshift(newPackage);
        this.saveToStorage();

        this.showToast('Encomenda registrada!');
        this.navigate('dashboard');
        this.render();
    },

    updateStatus(id, newStatus, signature = null) {
        const pkg = this.data.find(p => p.id === id);
        if (pkg) {
            pkg.status = newStatus;
            pkg.history.push({
                status: newStatus,
                timestamp: new Date().toISOString()
            });

            if (signature) {
                pkg.signature = signature;
            }

            this.saveToStorage();
            this.render();
            this.closeActionSheet();
            this.showToast(`Status atualizado: ${newStatus}`);
        }
    },

    saveToStorage() {
        localStorage.setItem('facilities_mail_db', JSON.stringify(this.data));
    },

    // UI & Filtering
    setFilter(filter) {
        this.currentFilter = filter;

        // Update Chips UI
        document.querySelectorAll('.filter-chip').forEach(btn => {
            btn.classList.remove('bg-slate-800', 'text-white');
            btn.classList.add('bg-slate-100', 'text-slate-600');
        });
        const activeBtn = document.getElementById(`filter-${filter}`);
        activeBtn.classList.remove('bg-slate-100', 'text-slate-600');
        activeBtn.classList.add('bg-slate-800', 'text-white');

        this.render();
    },

    filterPackages() {
        // Just re-render, it reads the input
        this.render();
    },

    render() {
        const listEl = document.getElementById('packagesList');
        const emptyState = document.getElementById('emptyState');
        const searchVal = document.getElementById('searchInput').value.toLowerCase();

        let filtered = this.data.filter(pkg => {
            // Search Text
            const matchText = pkg.recipient.toLowerCase().includes(searchVal) ||
                pkg.location.toLowerCase().includes(searchVal);

            // Filter Status
            let matchStatus = true;
            if (this.currentFilter === 'portaria') matchStatus = pkg.status === 'Na Portaria';
            else if (this.currentFilter === 'disponivel') matchStatus = pkg.status === 'Disponível para Retirada';
            else if (this.currentFilter === 'entregue') matchStatus = pkg.status === 'Entregue';

            return matchText && matchStatus;
        });

        listEl.innerHTML = '';

        if (filtered.length === 0) {
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            filtered.forEach(pkg => {
                const time = new Date(pkg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const date = new Date(pkg.createdAt).toLocaleDateString();

                let badgeClass = '';
                let icon = '';
                if (pkg.status === 'Na Portaria') { badgeClass = 'status-portaria'; icon = 'ph-package'; }
                else if (pkg.status === 'Disponível para Retirada') { badgeClass = 'status-disponivel'; icon = 'ph-check'; }
                else { badgeClass = 'status-entregue'; icon = 'ph-signature'; }

                const html = `
                    <div onclick="app.openActionSheet('${pkg.id}')" class="bg-white p-4 rounded-xl card-shadow border border-slate-100 flex items-center justify-between active:bg-slate-50 transition-colors cursor-pointer">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-xl text-slate-500 shrink-0 overflow-hidden">
                                ${pkg.photo ? `<img src="${pkg.photo}" class="w-full h-full object-cover">` : `<i class="ph ${icon}"></i>`}
                            </div>
                            <div>
                                <h3 class="font-bold text-slate-800 leading-tight">${pkg.recipient}</h3>
                                ${pkg.tracking ? `<p class="text-xs text-slate-400 font-mono mb-0.5">${pkg.tracking}</p>` : ''}
                                <p class="text-sm text-slate-500 font-medium">${pkg.location} <span class="text-slate-300 mx-1">•</span> ${pkg.type}</p>
                                <div class="mt-1.5 flex items-center gap-2">
                                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wide border ${badgeClass}">
                                        ${pkg.status}
                                    </span>
                                    <span class="text-xs text-slate-400">${date} ${time}</span>
                                </div>
                            </div>
                        </div>
                        <i class="ph ph-caret-right text-slate-300"></i>
                    </div>
                `;
                listEl.insertAdjacentHTML('beforeend', html);
            });
        }
    },

    // Action Sheet Logic
    openActionSheet(id) {
        this.activePackageId = id;
        const pkg = this.data.find(p => p.id === id);
        if (!pkg) return;

        const sheet = document.getElementById('actionSheet');
        const content = document.getElementById('actionSheetContent');
        const details = document.getElementById('sheetDetails');
        const btn = document.getElementById('actionBtn');
        const sigSection = document.getElementById('signatureSection');

        // Populate details
        details.innerHTML = `
            <h2 class="text-2xl font-bold text-slate-900 mb-1">${pkg.recipient}</h2>
            <p class="text-slate-500 text-lg mb-4">${pkg.location} • ${pkg.type}</p>
            <div class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <p class="text-sm text-slate-600 mb-1">Status Atual</p>
                <p class="font-bold text-slate-800 flex items-center gap-2">
                    <i class="ph ph-info text-primary"></i> ${pkg.status}
                </p>
            </div>
        `;

        // Configure Action
        sigSection.classList.add('hidden');
        btn.className = 'w-full py-4 rounded-xl font-bold text-lg text-white shadow-lg active:scale-95 transition-all'; // Reset classes

        // Logic Flow
        if (pkg.status === 'Na Portaria') {
            btn.textContent = 'Enviar para Estoque (Facilities)';
            btn.classList.add('bg-blue-600', 'shadow-blue-600/25');
            btn.onclick = () => this.updateStatus(id, 'Disponível para Retirada');
        }
        else if (pkg.status === 'Disponível para Retirada') {
            btn.textContent = 'Confirmar Entrega';
            btn.classList.add('bg-green-600', 'shadow-green-600/25');
            sigSection.classList.remove('hidden');
            setTimeout(() => this.resizeCanvas(), 310); // Resize after transition
            btn.onclick = () => {
                const signature = document.getElementById('signatureCanvas').toDataURL();
                this.updateStatus(id, 'Entregue', signature);
            };
        }
        else {
            // Already delivered
            btn.textContent = 'Já Entregue';
            btn.classList.add('bg-slate-400', 'cursor-not-allowed');
            btn.onclick = null;

            // Show signature if exists
            if (pkg.signature) {
                details.innerHTML += `
                    <div class="mt-4">
                        <p class="text-xs text-slate-400 mb-2">Assinatura</p>
                        <img src="${pkg.signature}" class="h-20 border border-slate-200 rounded-lg bg-white">
                    </div>
                `;
            }
        }

        // Show Sheet
        sheet.classList.remove('hidden');
        // Small delay to allow display:block to apply before opacity transition
        requestAnimationFrame(() => {
            sheet.classList.remove('opacity-0');
            content.classList.remove('translate-y-full');
        });
    },

    closeActionSheet() {
        const sheet = document.getElementById('actionSheet');
        const content = document.getElementById('actionSheetContent');

        content.classList.add('translate-y-full');
        sheet.classList.add('opacity-0');

        setTimeout(() => {
            sheet.classList.add('hidden');
            this.clearSignature(); // Reset signature
        }, 300);
    },

    // Signature Canvas
    setupCanvas() {
        const cvs = this.canvas;

        // Touch events
        cvs.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = cvs.getBoundingClientRect();
            this.startDrawing(touch.clientX - rect.left, touch.clientY - rect.top);
        }, { passive: false });

        cvs.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = cvs.getBoundingClientRect();
            this.draw(touch.clientX - rect.left, touch.clientY - rect.top);
        }, { passive: false });

        cvs.addEventListener('touchend', () => this.stopDrawing());

        // Mouse events (for testing on PC)
        cvs.addEventListener('mousedown', (e) => this.startDrawing(e.offsetX, e.offsetY));
        cvs.addEventListener('mousemove', (e) => this.draw(e.offsetX, e.offsetY));
        cvs.addEventListener('mouseup', () => this.stopDrawing());
        cvs.addEventListener('mouseout', () => this.stopDrawing());
    },

    resizeCanvas() {
        const parent = this.canvas.parentElement;
        if (parent) {
            this.canvas.width = parent.offsetWidth;
            this.canvas.height = parent.offsetHeight;
        }
    },

    startDrawing(x, y) {
        this.isDrawing = true;
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = 'round';
        this.ctx.strokeStyle = '#000';
    },

    draw(x, y) {
        if (!this.isDrawing) return;
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
    },

    stopDrawing() {
        this.isDrawing = false;
        this.ctx.closePath();
    },

    clearSignature() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    },

    // Photos
    handlePhotoUpload(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.photoData = e.target.result;
                document.getElementById('photoPreview').src = e.target.result;
                document.getElementById('photoPreview').classList.remove('hidden');
                document.getElementById('photoPlaceholder').classList.add('hidden');
                document.getElementById('removePhotoBtn').classList.remove('hidden');
            }
            reader.readAsDataURL(input.files[0]);
        }
    },

    removePhoto(e) {
        e.preventDefault(); // prevent triggering label click
        this.photoData = null;
        const input = document.querySelector('input[type="file"]');
        if (input) input.value = '';
        document.getElementById('photoPreview').classList.add('hidden');
        document.getElementById('photoPlaceholder').classList.remove('hidden');
        document.getElementById('removePhotoBtn').classList.add('hidden');
    },

    resetRegisterForm() {
        document.getElementById('registerForm').reset();
        this.removePhoto({ preventDefault: () => { } });
    },

    showToast(msg) {
        const toast = document.getElementById('toast');
        document.getElementById('toastMsg').textContent = msg;
        toast.classList.remove('translate-y-[-150%]');
        setTimeout(() => {
            toast.classList.add('translate-y-[-150%]');
        }, 3000);
    },

    // --- Scanner Logic ---
    startScanner() {
        const modal = document.getElementById('scannerModal');
        modal.classList.remove('hidden');

        this.scanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: { width: 250, height: 250 } },
            /* verbose= */ false
        );

        this.scanner.render(this.onScanSuccess.bind(this), this.onScanError);
    },

    onScanSuccess(decodedText, decodedResult) {
        // Handle the scanned code
        document.getElementById('trackingInput').value = decodedText;
        this.stopScanner();
        this.showToast('Código lido com sucesso!');
    },

    onScanError(errorMessage) {
        // Parse error, ignore it.
    },

    stopScanner() {
        if (this.scanner) {
            this.scanner.clear().then(() => {
                document.getElementById('scannerModal').classList.add('hidden');
                this.scanner = null;
            }).catch((err) => {
                console.warn("Failed to clear scanner", err);
                document.getElementById('scannerModal').classList.add('hidden');
            });
        } else {
            document.getElementById('scannerModal').classList.add('hidden');
        }
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
