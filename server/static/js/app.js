document.addEventListener('DOMContentLoaded', () => {
    // Segmentation modal + coordinate capture
    const modal = document.getElementById('modal');
    const canvas = document.getElementById('canvas');
    const closeBtn = document.getElementById('closeModal');
    const segForm = document.getElementById('segForm');
    const runBtn = document.getElementById('runSegBtn');
    const pt1 = document.getElementById('pt1');
    const pt2 = document.getElementById('pt2');
    const x1 = document.getElementById('x1');
    const y1 = document.getElementById('y1');
    const x2 = document.getElementById('x2');
    const y2 = document.getElementById('y2');
    const frameInput = document.getElementById('frameInput');
    const videoInput = document.getElementById('videoInput');

    let img = null;
    let clicks = [];

    function openModal(src, video) {
        if (!modal || !canvas) return;
        img = new Image();
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = src;
        frameInput.value = src;
        videoInput.value = video;
        clicks = [];
        pt1.textContent = 'Point 1: -';
        pt2.textContent = 'Point 2: -';
        x1.value = y1.value = x2.value = y2.value = '';
        runBtn.disabled = true;
        modal.classList.remove('hidden');
    }

    function closeModal() {
        if (!modal) return;
        modal.classList.add('hidden');
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    document.querySelectorAll('.select-frame').forEach(a => {
        a.addEventListener('click', (e) => {
            e.preventDefault();
            const src = a.getAttribute('data-src');
            const video = a.getAttribute('data-video');
            openModal(src, video);
        });
    });

    if (canvas) {
        canvas.addEventListener('click', (e) => {
            if (!img) return;
            const rect = canvas.getBoundingClientRect();
            const cx = Math.round((e.clientX - rect.left));
            const cy = Math.round((e.clientY - rect.top));
            clicks.push({ x: cx, y: cy });

            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            ctx.fillStyle = '#22d3ee';
            clicks.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
                ctx.fill();
            });

            if (clicks.length === 1) {
                pt1.textContent = `Point 1: (${cx}, ${cy})`;
                x1.value = String(cx); y1.value = String(cy);
            } else if (clicks.length === 2) {
                pt2.textContent = `Point 2: (${cx}, ${cy})`;
                x2.value = String(cx); y2.value = String(cy);
                runBtn.disabled = false;
            } else {
                // reset to last two points
                clicks = clicks.slice(-2);
                const p1 = clicks[0];
                const p2 = clicks[1];
                pt1.textContent = `Point 1: (${p1.x}, ${p1.y})`;
                pt2.textContent = `Point 2: (${p2.x}, ${p2.y})`;
                x1.value = String(p1.x); y1.value = String(p1.y);
                x2.value = String(p2.x); y2.value = String(p2.y);
                runBtn.disabled = false;
            }
        });
    }
});



