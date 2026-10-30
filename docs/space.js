fetch('images/space.json').then(r => r.json()).then(d => {
  const modes = ['car', 'bike', 'walk'];
  const tb = modes.reduce((s, k) => s + d.before_m2[k], 0), ta = modes.reduce((s, k) => s + d.after_m2[k], 0);
  const kpi = [
    { key: 'car', label: 'Car space', cls: 'c-car' },
    { key: 'bike', label: 'Cycling space', cls: 'c-bike' },
    { key: 'walk', label: 'Pedestrian space', cls: 'c-walk' },
  ].map(k => ({ ...k, b: d.before_m2[k.key] / tb * 100, a: d.after_m2[k.key] / ta * 100, bm: d.before_m2[k.key], am: d.after_m2[k.key] }));
  const rel = k => Math.round(k.a) - Math.round(k.b);
  const hs = document.getElementById('hsum');
  hs.innerHTML = [['Cars', kpi[0]], ['Cyclists', kpi[1]], ['Walkers', kpi[2]]].map(([n, k]) =>
    `<span class="${rel(k) >= 0 ? 'up' : 'down'}">${n} <b>${rel(k) >= 0 ? '▲' : '▼'} ${Math.abs(rel(k))} pts</b></span>`).join('');

  document.getElementById('kpis').innerHTML = kpi.map(k => {
    const up = rel(k) >= 0;
    return `<div class="kpi ${up ? 'up' : 'down'}"><i class="${k.cls}"></i><h3>${k.label}</h3>
      <div class="big">${up ? '▲' : '▼'} ${Math.abs(rel(k))}<span class="u"> pts</span></div>
      <p>${Math.round(k.b)}% → ${Math.round(k.a)}% of the space<br>
      <small>≈ ${Math.round(k.bm).toLocaleString('en')} → ${Math.round(k.am).toLocaleString('en')} m²</small></p></div>`;
  }).join('');

  const seg = (o, t) => modes.map(k =>
    `<div class="c-${k}" style="width:${o[k] / t * 100}%" title="${k}: ${(o[k] / t * 100).toFixed(0)}%"><span>${(o[k] / t * 100).toFixed(0)}%</span></div>`).join('');
  document.getElementById('bars').innerHTML =
    `<div class="barrow"><b>Existing</b><div class="bar">${seg(d.before_m2, tb)}</div></div>
     <div class="barrow"><b>Proposed</b><div class="bar">${seg(d.after_m2, ta)}</div></div>`;
});
