let currentTab = 'single';
let currentSessionId = null;
let currentNamaAsli = null;
let currentUkuran = '3x4';
let currentWarna = 'merah';
let editorMode = 'single';
let currentBatchItem = null;
let rgbaImageObj = new Image();

function switchTab(tab, btn) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-single').style.display = tab === 'single' ? 'block' : 'none';
    document.getElementById('tab-batch').style.display = tab === 'batch' ? 'block' : 'none';
    reset();
}

document.getElementById('input-foto').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById('img-before').src = e.target.result;
        document.getElementById('preview-before').style.display = 'block';
        document.getElementById('btn-proses').style.display = 'block';
    };
    reader.readAsDataURL(file);
});

document.getElementById('input-zip').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    document.getElementById('zip-nama').style.display = 'block';
    document.getElementById('zip-nama').textContent = 'File dipilih: ' + file.name;
    document.getElementById('btn-proses-batch').style.display = 'block';
});

function prosesFoto() {
    const file = document.getElementById('input-foto').files[0];
    currentUkuran = document.getElementById('ukuran-single').value;
    currentWarna = document.getElementById('warna-single').value;
    if (!file) return;

    const formData = new FormData();
    formData.append('foto', file);
    formData.append('ukuran', currentUkuran);
    formData.append('warna', currentWarna);

    tampilkanLoading('Memproses foto...', 0);

    fetch('/proses', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            sembunyikanLoading();
            if (data.error) { alert('Gagal: ' + data.error); return; }
            currentSessionId = data.session_id;
            currentNamaAsli = data.nama_asli;
            tampilkanHasilSingle(data);
        })
        .catch(() => { sembunyikanLoading(); alert('Terjadi kesalahan, coba lagi.'); });
}

function prosesBatch() {
    const file = document.getElementById('input-zip').files[0];
    currentUkuran = document.getElementById('ukuran-batch').value;
    currentWarna = document.getElementById('warna-batch').value;
    if (!file) return;

    const formData = new FormData();
    formData.append('foto_zip', file);
    formData.append('ukuran', currentUkuran);
    formData.append('warna', currentWarna);

    tampilkanLoading('Memulai proses batch...', 0);

    document.getElementById('tab-single').style.display = 'none';
    document.getElementById('tab-batch').style.display = 'none';

    fetch('/proses-batch', { method: 'POST', body: formData })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            function baca() {
                reader.read().then(({ done, value }) => {
                    if (done) return;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop();

                    lines.forEach(line => {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.replace('data: ', ''));

                            if (data.type === 'progress') {
                                tampilkanLoading(
                                    `Memproses ${data.nama} (${data.current}/${data.total})`,
                                    data.persen
                                );
                            } else if (data.type === 'done') {
                                sembunyikanLoading();
                                currentSessionId = data.session_id;
                                tampilkanHasilBatch(data);
                            }
                        }
                    });

                    baca();
                });
            }

            baca();
        })
        .catch(() => { sembunyikanLoading(); alert('Terjadi kesalahan, coba lagi.'); });
}

function tampilkanHasilSingle(data) {
    const ts = '?t=' + Date.now();
    document.getElementById('img-hasil').src = data.foto_final + ts;
    document.getElementById('img-layout').src = data.foto_layout + ts;
    document.getElementById('btn-download-single').href = data.foto_final;
    document.getElementById('btn-download-single').download = currentNamaAsli + '.jpg';
    document.getElementById('btn-download-layout').href = data.foto_layout;
    document.getElementById('btn-download-layout').download = currentNamaAsli + '_layout.jpg';
    document.getElementById('hasil-single').style.display = 'block';
    document.getElementById('tab-single').style.display = 'none';
    document.getElementById('hasil-single').scrollIntoView({ behavior: 'smooth' });
    window._rgbaCropUrl = data.foto_rgba_crop;
}

function tampilkanHasilBatch(data) {
    const gagalInfo = document.getElementById('gagal-info');
    if (data.gagal && data.gagal.length > 0) {
        gagalInfo.style.display = 'block';
        gagalInfo.innerHTML = '<strong>Foto yang gagal diproses:</strong><br>' +
            data.gagal.map(g => `<p>• ${g.nama} — ${g.alasan}</p>`).join('');
    }

    const grid = document.getElementById('batch-grid');
    grid.innerHTML = '';

    data.hasil.forEach(item => {
        const div = document.createElement('div');
        div.className = 'batch-item';
        div.id = 'batch-item-' + item.nama;
        div.innerHTML = `
            <img id="img-batch-${item.nama}" src="${item.foto_final}?t=${Date.now()}" alt="${item.nama}">
            <p>${item.nama}</p>
            <div class="batch-item-buttons">
                <a class="btn-batch-download" href="${item.foto_final}" download="${item.nama}.jpg">Download</a>
                <a class="btn-batch-layout" href="${item.foto_layout}" download="${item.nama}_layout.jpg">Layout</a>
                <button class="btn-batch-adjust" onclick='bukaEditorBatch(${JSON.stringify(item)})'>Sesuaikan Posisi</button>
            </div>
        `;
        grid.appendChild(div);
    });

    document.getElementById('hasil-batch').style.display = 'block';
    document.getElementById('hasil-batch').scrollIntoView({ behavior: 'smooth' });
}

function tampilkanLoading(pesan, persen) {
    document.getElementById('loading-text').textContent = pesan;
    document.getElementById('loading-bar').style.width = persen + '%';
    document.getElementById('loading-persen').textContent = persen + '%';
    document.getElementById('loading').style.display = 'block';
}

function sembunyikanLoading() {
    document.getElementById('loading').style.display = 'none';
}

function bukaEditor(mode) {
    editorMode = mode;
    rgbaImageObj = new Image();
    rgbaImageObj.crossOrigin = 'anonymous';
    rgbaImageObj.onload = function () {
        document.getElementById('slider-zoom').value = 100;
        document.getElementById('slider-x').value = 0;
        document.getElementById('slider-y').value = 0;
        document.getElementById('zoom-value').textContent = '100%';
        renderCanvas();
        document.getElementById('modal-editor').style.display = 'flex';
    };
    rgbaImageObj.src = window._rgbaCropUrl + '?t=' + Date.now();
}

function bukaEditorBatch(item) {
    editorMode = 'batch';
    currentBatchItem = item;
    currentSessionId = item.session_id;
    currentNamaAsli = item.nama;
    currentUkuran = item.ukuran;
    currentWarna = item.warna;

    rgbaImageObj = new Image();
    rgbaImageObj.crossOrigin = 'anonymous';
    rgbaImageObj.onload = function () {
        document.getElementById('slider-zoom').value = 100;
        document.getElementById('slider-x').value = 0;
        document.getElementById('slider-y').value = 0;
        document.getElementById('zoom-value').textContent = '100%';
        renderCanvas();
        document.getElementById('modal-editor').style.display = 'flex';
    };
    rgbaImageObj.src = item.foto_rgba_crop + '?t=' + Date.now();
}

function tutupEditor() {
    document.getElementById('modal-editor').style.display = 'none';
}

function updateCanvas() {
    const zoom = document.getElementById('slider-zoom').value;
    document.getElementById('zoom-value').textContent = zoom + '%';
    renderCanvas();
}

function renderCanvas() {
    const canvas = document.getElementById('editor-canvas');
    const ctx = canvas.getContext('2d');

    const ukuranMap = { '2x3': [472, 708], '3x4': [708, 944], '4x6': [944, 1418] };
    const warnaMap = { 'merah': '#8b0000', 'biru': '#1e50c8', 'putih': '#ffffff' };

    const [fw, fh] = ukuranMap[currentUkuran];
    const scale = 300 / fh;
    canvas.width = fw * scale;
    canvas.height = fh * scale;

    ctx.fillStyle = warnaMap[currentWarna];
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const zoom = parseFloat(document.getElementById('slider-zoom').value) / 100;
    const offsetX = parseFloat(document.getElementById('slider-x').value) * scale;
    const offsetY = parseFloat(document.getElementById('slider-y').value) * scale;

    const imgW = rgbaImageObj.width * scale * zoom;
    const imgH = rgbaImageObj.height * scale * zoom;
    const x = (canvas.width - imgW) / 2 + offsetX;
    const y = (canvas.height - imgH) / 2 + offsetY;

    ctx.drawImage(rgbaImageObj, x, y, imgW, imgH);
}

function resetAdjust() {
    document.getElementById('slider-zoom').value = 100;
    document.getElementById('slider-x').value = 0;
    document.getElementById('slider-y').value = 0;
    document.getElementById('zoom-value').textContent = '100%';
    renderCanvas();
}

function simpanAdjust() {
    const zoom = parseFloat(document.getElementById('slider-zoom').value) / 100;
    const offsetX = parseFloat(document.getElementById('slider-x').value);
    const offsetY = parseFloat(document.getElementById('slider-y').value);

    fetch('/proses-adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: currentSessionId,
            nama_asli: currentNamaAsli,
            ukuran: currentUkuran,
            warna: currentWarna,
            offset_x: offsetX,
            offset_y: offsetY,
            scale: zoom,
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) { alert('Gagal: ' + data.error); return; }
        tutupEditor();
        if (editorMode === 'single') {
            const ts = '?t=' + Date.now();
            document.getElementById('img-hasil').src = data.foto_final + ts;
            document.getElementById('img-layout').src = data.foto_layout + ts;
            document.getElementById('btn-download-single').href = data.foto_final.split('?')[0];
            document.getElementById('btn-download-layout').href = data.foto_layout.split('?')[0];
        } else {
            const imgEl = document.getElementById('img-batch-' + currentNamaAsli);
            if (imgEl) imgEl.src = data.foto_final + '?t=' + Date.now();
        }
    })
    .catch(() => alert('Terjadi kesalahan, coba lagi.'));
}

function downloadZip() {
    if (!currentSessionId) return;
    window.location.href = '/download-zip/' + currentSessionId;
}

function reset() {
    currentSessionId = null;
    currentNamaAsli = null;

    document.getElementById('input-foto').value = '';
    document.getElementById('input-zip').value = '';
    document.getElementById('img-before').src = '';
    document.getElementById('preview-before').style.display = 'none';
    document.getElementById('btn-proses').style.display = 'none';
    document.getElementById('btn-proses-batch').style.display = 'none';
    document.getElementById('zip-nama').style.display = 'none';
    document.getElementById('hasil-single').style.display = 'none';
    document.getElementById('hasil-batch').style.display = 'none';
    document.getElementById('loading').style.display = 'none';
    document.getElementById('gagal-info').style.display = 'none';
    document.getElementById('batch-grid').innerHTML = '';

    if (currentTab === 'single') {
        document.getElementById('tab-single').style.display = 'block';
    } else {
        document.getElementById('tab-batch').style.display = 'block';
    }
}