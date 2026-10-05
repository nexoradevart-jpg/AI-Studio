(() => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');
  if (toggle && nav) toggle.addEventListener('click', () => { const open = nav.classList.toggle('open'); toggle.setAttribute('aria-expanded', String(open)); });
  window.escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  window.showToast = (message, type='error') => { const root = document.getElementById('toast-root'); if (!root) return; const el = document.createElement('div'); el.className = `toast ${type}`; el.textContent = message; root.appendChild(el); setTimeout(() => el.remove(), 4200); };
  window.fetchJSON = async (url, options={}) => { const res = await fetch(url, options); let data; try { data = await res.json(); } catch { throw new Error('پاسخ سرویس قابل پردازش نیست.'); } if (!res.ok || data.ok === false) throw new Error(data.error || 'درخواست ناموفق بود.'); return data; };
})();
