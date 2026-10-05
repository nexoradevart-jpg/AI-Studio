const form = document.getElementById('instagram-form');
const loading = document.getElementById('instagram-loading');
const result = document.getElementById('instagram-result');
const errorBox = document.getElementById('instagram-error');
form.addEventListener('submit', async (e) => {
  e.preventDefault(); result.classList.add('hidden'); errorBox.classList.add('hidden'); loading.classList.remove('hidden');
  try {
    const data = await fetchJSON('/api/instagram/download', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:document.getElementById('instagram-url').value.trim()})});
    const x = data.data;
    result.innerHTML = `<div class="media-card">${x.cover ? `<img src="${escapeHtml(x.cover)}" alt="Instagram cover" loading="lazy">` : '<div class="media-placeholder">📸</div>'}</div><div class="info-card"><div class="user-line"><div class="avatar">◎</div><div><strong>${escapeHtml(x.full_name || 'کاربر Instagram')}</strong><span>@${escapeHtml(x.username || 'unknown')}</span></div></div><div class="stats"><span>♥ ${escapeHtml(x.likes ?? '—')}</span><span>💬 ${escapeHtml(x.comments ?? '—')}</span></div><div class="caption">${escapeHtml(x.caption || 'بدون توضیحات')}</div><a class="btn primary full" href="/download/instagram?url=${encodeURIComponent(x.video_url)}">دانلود فایل ویدیو</a></div>`;
    result.classList.remove('hidden');
  } catch (err) { errorBox.textContent = err.message; errorBox.classList.remove('hidden'); }
  finally { loading.classList.add('hidden'); }
});
