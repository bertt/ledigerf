let map;

async function initMap() {
  const plans = await (await fetch("images/georef.json")).json();
  map = new maplibregl.Map({
    container: "maplibre",
    style: "https://tiles.openfreemap.org/styles/liberty",
    center: [5.1235, 52.0812], zoom: 17.2, maxZoom: 21,
  });
  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

  const list = document.getElementById("planlist");
  const opacity = document.getElementById("opacity");
  map.on("load", () => {
    for (const [id, p] of Object.entries(plans)) {
      map.addSource(id, { type: "image", url: p.image, coordinates: p.coordinates });
      map.addLayer({ id, type: "raster", source: id, paint: { "raster-opacity": opacity.value / 100, "raster-fade-duration": 0 } });
      const row = document.createElement("label");
      row.className = "planrow";
      row.innerHTML = `<input type="checkbox" checked> <b>${p.title}</b><small>${p.method}</small>`;
      row.querySelector("input").onchange = (e) => map.setLayoutProperty(id, "visibility", e.target.checked ? "visible" : "none");
      row.querySelector("b").ondblclick = () => zoomTo(p.coordinates);
      list.appendChild(row);
    }
    opacity.oninput = () => { for (const id of Object.keys(plans)) map.setPaintProperty(id, "raster-opacity", opacity.value / 100); };
    const all = Object.values(plans).flatMap((p) => p.coordinates);
    zoomTo(all, 0);
  });
}

function zoomTo(coords, duration = 600) {
  const b = new maplibregl.LngLatBounds();
  coords.forEach((c) => b.extend(c));
  map.fitBounds(b, { padding: 40, duration });
}

window.onTab = (tab) => {
  if (tab !== "map") return;
  if (!map) initMap();
  else map.resize();
};

if (document.getElementById('map').classList.contains('active')) window.onTab('map');
