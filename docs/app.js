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
  setPos(50);
}

function setPos(pct) {
  pct = Math.max(0, Math.min(100, pct));
  $("#clip").style.width = pct + "%";
  $("#handle").style.left = pct + "%";
}

PAIRS.forEach((p, i) => {
  const b = document.createElement("button");
  b.textContent = p.name;
  b.onclick = () => show(p, b);
  $("#pairs").appendChild(b);
  if (i === 0) show(p, b);
});

const slider = $("#slider");
let drag = false;
const move = (e) => {
  const r = slider.getBoundingClientRect();
  setPos(((e.touches ? e.touches[0].clientX : e.clientX) - r.left) / r.width * 100);
};
slider.addEventListener("pointerdown", (e) => { drag = true; move(e); });
window.addEventListener("pointerup", () => (drag = false));
window.addEventListener("pointermove", (e) => drag && move(e));

// keep the "before" image the same size as the slider so both align
function fit() { $("#imgBefore").style.width = slider.clientWidth + "px"; }
new ResizeObserver(fit).observe(slider);

document.querySelectorAll("nav button").forEach((b) => {
  b.onclick = () => {
    document.querySelectorAll("nav button, .tab").forEach((e) => e.classList.remove("active"));
    b.classList.add("active");
    $("#" + b.dataset.tab).classList.add("active");
    fit();
    if (window.onTab) window.onTab(b.dataset.tab);
  };
});

fetch("images/gallery.json").then((r) => r.json()).then((items) => {
  const lb = $("#lightbox");
  for (const it of items) {
    const im = document.createElement("img");
    im.src = it.file; im.alt = it.caption; im.title = it.caption; im.loading = "lazy";
    im.onclick = () => { lb.querySelector("img").src = it.file; lb.querySelector("p").textContent = it.caption; lb.hidden = false; };
    $("#grid").appendChild(im);
  }
  lb.onclick = () => (lb.hidden = true);
});

// deep link: #map, #gallery, #info
const start = document.querySelector(`nav button[data-tab="${location.hash.slice(1)}"]`);
if (start) start.click();
