const PAIRS = [
  { name: "Vaartscherijnbrug", before: "p26_0", after: "p27_0", text: "Ledig Erf seen from the Vaartscherijnbrug" },
  { name: "Tram house side", before: "p28_0", after: "p29_0", text: "Ledig Erf seen from the tram house side" },
  { name: "Singel / Bleekstraat", before: "p36_0", after: "p37_0", text: "Crossing Catharijnesingel – Bleekstraat" },
  { name: "Catharijnesingel", before: "p38_0", after: "p39_0", text: "Catharijnesingel (east side) with new walking path" },
  { name: "Bleekstraat", before: "p44_0", after: "p45_0", text: "Bleekstraat" },
];
const $ = (s) => document.querySelector(s);
const img = (id) => `images/${id}.jpg`;

function show(p, btn) {
  $("#imgBefore").src = img(p.before);
  $("#imgAfter").src = img(p.after);
  $("#caption").textContent = p.text;
  document.querySelectorAll("#pairs button").forEach((b) => b.classList.toggle("active", b === btn));
}

PAIRS.forEach((p, i) => {
  const b = document.createElement("button");
  b.textContent = p.name;
  b.onclick = () => show(p, b);
  $("#pairs").appendChild(b);
  if (i === 0) show(p, b);
});

function showTab(tab) {
  const b = document.querySelector(`nav button[data-tab="${tab}"]`);
  if (!b) return;
  document.querySelectorAll("nav button, .tab").forEach((e) => e.classList.remove("active"));
  b.classList.add("active");
  $("#" + tab).classList.add("active");
  if (window.onTab) window.onTab(tab);
}

// permanent links: #compare, #map, #space, #info
document.querySelectorAll("nav button").forEach((b) => {
  b.onclick = () => { location.hash = b.dataset.tab; };
});
window.addEventListener("hashchange", () => showTab(location.hash.slice(1) || "compare"));

// deep link on load
if (location.hash) showTab(location.hash.slice(1));
