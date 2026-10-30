fetch('images/space.json').then(r => r.json()).then(d => {
  const sum = o => Object.values(o).reduce((a, b) => a + b, 0);
  const tb = sum(d.before_m2), ta = sum(d.after_m2);
  const people = o => o.walk + o.green;
  const kpi = [
    { key: 'car', label: 'Car space', b: d.before_m2.car, a: d.after_m2.car, cls: 'c-car', arrow: '▼' },
    { key: 'bike', label: 'Cycling space', b: d.before_m2.bike, a: d.after_m2.bike, cls: 'c-bike', arrow: '▲' },
    { key: 'walk', label: 'Pedestrians & green', b: people(d.before_m2), a: people(d.after_m2), cls: 'c-walk', arrow: '▲' },
  ];
  const hs = document.getElementById('hsum');
  hs.innerHTML = [['Cars', kpi[0]], ['Cyclists', kpi[1]], ['Walkers', kpi[2]], ['Greenery', { a: d.after_m2.green, b: d.before_m2.green }]].map(([n, k]) => {
    const rel = Math.round((k.a - k.b) / k.b * 100);
    return `<span class="${rel >= 0 ? 'up' : 'down'}">${n} <b>${rel >= 0 ? '▲' : '▼'} ${Math.abs(rel)}%</b></span>`;
  }).join('');


  document.getElementById('kpis').innerHTML = kpi.map(k => {
    const rel = Math.round((k.a - k.b) / k.b * 100);
    const pts = (k.a / ta - k.b / tb) * 100;
    const up = rel >= 0;
    return `<div class="kpi ${up ? 'up' : 'down'}"><i class="${k.cls}"></i><h3>${k.label}</h3>
      <div class="big">${up ? '▲' : '▼'} ${Math.abs(rel)}%</div>
      <p>${Math.round(k.b / tb * 100)}% → ${Math.round(k.a / ta * 100)}% of the space<br>
      <small>≈ ${Math.round(k.b).toLocaleString('en')} → ${Math.round(k.a).toLocaleString('en')} m² (${up ? '+' : '−'}${Math.abs(pts).toFixed(0)} pts)</small></p></div>`;
  }).join('');

  const seg = (o, t) => ['car', 'bike', 'walk', 'green'].map(k =>
    `<div class="c-${k}" style="width:${o[k] / t * 100}%" title="${k}: ${(o[k] / t * 100).toFixed(0)}%"><span>${(o[k] / t * 100).toFixed(0)}%</span></div>`).join('');
  document.getElementById('bars').innerHTML =
    `<div class="barrow"><b>Existing</b><div class="bar">${seg(d.before_m2, tb)}</div></div>
     <div class="barrow"><b>Proposed</b><div class="bar">${seg(d.after_m2, ta)}</div></div>`;
});
