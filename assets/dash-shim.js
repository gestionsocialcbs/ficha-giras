/* Sustituto ligero del entorno del tablero: datos locales, cálculos, filtros y descarga directa. */
(function () {
  const raw = window.FICHA_DATA || {};
  const calcs = {};
  const memo = {};
  const listeners = [];
  const defaults = { ooad: 5 };
  const fromUrl = () => {
    const v = new URLSearchParams(location.search).get('ooad');
    return v != null && v !== '' && !isNaN(Number(v)) ? { ooad: Number(v) } : {};
  };
  let params = Object.assign({}, defaults, fromUrl());
  let scheduled = false;
  const run = () => { scheduled = false; listeners.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } }); };
  const schedule = () => { if (!scheduled) { scheduled = true; requestAnimationFrame(run); } };
  const resolve = (id) => {
    if (Object.prototype.hasOwnProperty.call(raw, id)) return raw[id];
    if (calcs[id]) {
      if (!(id in memo)) memo[id] = calcs[id].fn(...calcs[id].inputs.map(resolve));
      return memo[id];
    }
    return null;
  };
  window.dash = {
    colors: ['#1E5B4F', '#9B2247', '#A57F2C', '#002F2A', '#611232', '#51939F', '#CF6E71', '#4D4D4D'],
    calc(id, def) { calcs[id] = def; },
    loader() {},
    data(id) {
      try {
        const d = resolve(id);
        if (d == null) return { status: 'missing', data: [], columns: [], meta: [] };
        const cols = Array.isArray(d) && d[0] ? Object.keys(d[0]) : [];
        return { status: 'ok', data: d, columns: cols, meta: [], rows: d };
      } catch (e) {
        console.error(e);
        return { status: 'error', data: [], message: String(e), columns: [], meta: [] };
      }
    },
    onData(fn) { listeners.push(fn); try { fn(); } catch (e) { console.error(e); } },
    params() { return Object.assign({}, params); },
    setParams(p) {
      params = Object.assign({}, params, p);
      const u = new URL(location.href);
      if (params.ooad != null) u.searchParams.set('ooad', params.ooad); else u.searchParams.delete('ooad');
      history.replaceState(null, '', u);
      schedule();
    },
    resetParams() { params = Object.assign({}, defaults); schedule(); },
    refresh() {},
    setLink() {},
  };
  let rt;
  window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(run, 120); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(schedule);
  // Descarga directa del PDF en el navegador
  window.claude = {
    use: async (name) => name !== 'downloads' ? null : {
      save: async ({ filename, data }) => {
        const blob = data instanceof Blob ? data : new Blob([data]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        return { status: 'saved' };
      },
    },
  };
})();
