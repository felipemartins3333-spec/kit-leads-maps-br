/* Mapa reserva do kit: o MESMO mapa (estilo OpenFreeMap) desenhado sem WebGL.
 *
 * A tela e o relatório usam a MapLibre, que precisa de WebGL. Alguns navegadores não têm WebGL (computador
 * sem placa de vídeo, máquina na nuvem, WebGL desligado pela empresa). Nesses casos, este arquivo troca
 * `window.maplibregl` por uma versão que tem as mesmas funções que o kit usa, mas desenha com OpenLayers
 * (BSD-2) + ol-mapbox-style (BSD-2) em Canvas 2D, que funciona em qualquer navegador.
 *
 * Código próprio do kit. Só cobre as partes da MapLibre que a tela e o relatório usam.
 * Para testar o modo reserva num navegador com WebGL: acrescente #mapa-simples no fim do endereço.
 */
(function () {
  "use strict";
  function temWebGL() {
    try {
      var c = document.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) { return false; }
  }
  var forcar = /mapa-simples/.test(String(location.hash) + String(location.search));
  if (typeof ol === "undefined" || typeof olms === "undefined") return;

  var proj = ol.proj;
  var DELTA_ZOOM = 1;   // a MapLibre usa ladrilhos de 512 px; o OpenLayers, de 256 px

  function paraMapa(c) { return proj.fromLonLat([+c[0], +c[1]]); }
  function lngLatDe(c) { return Array.isArray(c) ? c : [c.lng != null ? c.lng : c.lon, c.lat]; }
  function rgba(cor, opacidade) {
    var m = /^#?([0-9a-f]{6})$/i.exec(cor || "");
    if (!m) return cor || "rgba(0,0,0,.2)";
    var n = parseInt(m[1], 16);
    return "rgba(" + (n >> 16) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + (opacidade == null ? 1 : opacidade) + ")";
  }
  function el(tag, classe) { var e = document.createElement(tag); if (classe) e.className = classe; return e; }

  function Emissor() { this._ouvintes = {}; }
  Emissor.prototype.on = function (tipo, fn) { (this._ouvintes[tipo] = this._ouvintes[tipo] || []).push(fn); return this; };
  Emissor.prototype.off = function (tipo, fn) {
    this._ouvintes[tipo] = (this._ouvintes[tipo] || []).filter(function (f) { return f !== fn && f._original !== fn; });
    return this;
  };
  Emissor.prototype.once = function (tipo, fn) {
    var eu = this;
    function uma(e) { eu.off(tipo, uma); fn(e); }
    uma._original = fn;
    return this.on(tipo, uma);
  };
  Emissor.prototype.fire = function (tipo, dados) {
    (this._ouvintes[tipo] || []).slice().forEach(function (f) { try { f(dados || {}); } catch (e) { setTimeout(function () { throw e; }); } });
  };

  // ---------------------------------------------------------------- limites
  function LngLatBounds() { this.o = null; this.l = null; this.s = null; this.n = null; }
  LngLatBounds.prototype.extend = function (c) {
    c = lngLatDe(c);
    if (this.o === null) { this.o = this.l = +c[0]; this.s = this.n = +c[1]; }
    else { this.o = Math.min(this.o, c[0]); this.l = Math.max(this.l, c[0]); this.s = Math.min(this.s, c[1]); this.n = Math.max(this.n, c[1]); }
    return this;
  };
  LngLatBounds.prototype.isEmpty = function () { return this.o === null; };
  LngLatBounds.prototype.toArray = function () { return [[this.o, this.s], [this.l, this.n]]; };

  // ---------------------------------------------------------------- mapa
  function Mapa(opcoes) {
    Emissor.call(this);
    var alvo = typeof opcoes.container === "string" ? document.getElementById(opcoes.container) : opcoes.container;
    this._alvo = alvo;
    alvo.classList.add("maplibregl-map", "mapa-reserva");
    this._estiloCarregado = false;
    this._fontes = {};
    this._camadasProprias = [];
    var centro = opcoes.center || [-47.9, -15.8];
    this._view = new ol.View({ center: paraMapa(centro), zoom: (opcoes.zoom || 3) + DELTA_ZOOM, maxZoom: 20 });
    this._ol = new ol.Map({
      target: alvo,
      view: this._view,
      controls: [new ol.control.Attribution({ collapsible: false })],
      interactions: (ol.interaction.defaults.defaults || ol.interaction.defaults)({ altShiftDragRotate: false, pinchRotate: false })
    });
    var cantos = el("div", "maplibregl-control-container");
    this._cantos = {};
    var eu = this;
    ["top-left", "top-right", "bottom-left", "bottom-right"].forEach(function (p) {
      var d = el("div", "maplibregl-ctrl-" + p);
      cantos.appendChild(d);
      eu._cantos[p] = d;
    });
    alvo.appendChild(cantos);
    this.touchZoomRotate = { disableRotation: function () {} };
    this.dragRotate = { disable: function () {} };
    var zoomAntes = this.getZoom();
    this._ol.on("moveend", function () {
      eu.fire("moveend", {});
      var z = eu.getZoom();
      if (Math.abs(z - zoomAntes) > 1e-6) { zoomAntes = z; eu.fire("zoomend", {}); }
    });
    this._ol.on("singleclick", function (e) {
      var c = proj.toLonLat(e.coordinate);
      eu.fire("click", { lngLat: { lng: c[0], lat: c[1] }, point: { x: e.pixel[0], y: e.pixel[1] } });
    });
    this._aplicarEstilo(opcoes.style);
  }
  Mapa.prototype = Object.create(Emissor.prototype);

  Mapa.prototype._aplicarEstilo = function (url) {
    var eu = this;
    this._estiloCarregado = false;
    var proprias = this._camadasProprias;
    this._ol.getLayers().getArray().slice().forEach(function (c) {
      if (proprias.indexOf(c) < 0) eu._ol.removeLayer(c);
    });
    // webfonts: não buscar fontes na internet (a página só fala com o servidor de mapas)
    olms.apply(this._ol, url, { webfonts: "data:text/css," }).then(function () {
      eu._estiloCarregado = true;
      proprias.forEach(function (c) { c.setZIndex(1000); });
      eu.fire("load", {});
      eu.fire("styledata", {});
    }).catch(function (erro) { eu.fire("error", { error: erro }); });
  };
  Mapa.prototype.setStyle = function (url) { this._aplicarEstilo(url); return this; };
  Mapa.prototype.isStyleLoaded = function () { return this._estiloCarregado; };
  Mapa.prototype.getZoom = function () { return (this._view.getZoom() || 0) - DELTA_ZOOM; };
  Mapa.prototype.getContainer = function () { return this._alvo; };
  Mapa.prototype.resize = function () { this._ol.updateSize(); return this; };
  Mapa.prototype.remove = function () { this._ol.setTarget(null); };
  Mapa.prototype.project = function (c) {
    var xy = paraMapa(lngLatDe(c));
    var tam = this._ol.getSize() || [this._alvo.clientWidth, this._alvo.clientHeight];
    var res = this._view.getResolution(), centro = this._view.getCenter();
    return { x: (xy[0] - centro[0]) / res + tam[0] / 2, y: (centro[1] - xy[1]) / res + tam[1] / 2 };
  };
  Mapa.prototype.fitBounds = function (b, op) {
    op = op || {};
    var a = b instanceof LngLatBounds ? b.toArray() : b;
    if (!a || a[0][0] === null) return this;
    var ext = ol.extent.boundingExtent([paraMapa(a[0]), paraMapa(a[1])]);
    var p = op.padding == null ? 0 : op.padding;
    var pad = typeof p === "number" ? [p, p, p, p] : [p.top || 0, p.right || 0, p.bottom || 0, p.left || 0];
    var tam = this._ol.getSize() || [this._alvo.clientWidth, this._alvo.clientHeight];
    if (pad[1] + pad[3] >= tam[0] || pad[0] + pad[2] >= tam[1]) pad = [10, 10, 10, 10];
    this._view.fit(ext, { padding: pad, maxZoom: (op.maxZoom == null ? 20 : op.maxZoom) + DELTA_ZOOM,
      duration: op.duration == null ? 0 : op.duration, size: tam });
    return this;
  };
  Mapa.prototype.flyTo = function (op) {
    var a = { duration: op.duration == null ? 600 : op.duration };
    if (op.center) a.center = paraMapa(lngLatDe(op.center));
    if (op.zoom != null) a.zoom = op.zoom + DELTA_ZOOM;
    this._view.animate(a);
    return this;
  };
  Mapa.prototype.easeTo = Mapa.prototype.flyTo;
  Mapa.prototype.addControl = function (controle, posicao) {
    var no = controle.onAdd(this);
    (this._cantos[posicao || "top-right"] || this._cantos["top-right"]).appendChild(no);
    return this;
  };

  // Fonte GeoJSON + camadas de preenchimento/linha (usado pelo círculo do raio na tela).
  Mapa.prototype.addSource = function (id, def) {
    var fonte = new ol.source.Vector();
    var f = { _fonte: fonte, setData: function (dados) {
      fonte.clear();
      fonte.addFeatures(new ol.format.GeoJSON().readFeatures(dados, { featureProjection: "EPSG:3857" }));
    } };
    f.setData(def.data || { type: "FeatureCollection", features: [] });
    this._fontes[id] = f;
  };
  Mapa.prototype.getSource = function (id) { return this._fontes[id]; };
  Mapa.prototype.addLayer = function (def) {
    var f = this._fontes[def.source];
    if (!f) return;
    var p = def.paint || {}, estilo;
    if (def.type === "fill") estilo = new ol.style.Style({ fill: new ol.style.Fill({ color: rgba(p["fill-color"], p["fill-opacity"]) }) });
    else if (def.type === "line") {
      var traco = p["line-dasharray"], w = p["line-width"] || 1;
      estilo = new ol.style.Style({ stroke: new ol.style.Stroke({ color: rgba(p["line-color"], p["line-opacity"]), width: w,
        lineDash: traco ? traco.map(function (x) { return x * w; }) : undefined }) });
    } else return;
    var camada = new ol.layer.Vector({ source: f._fonte, style: estilo, zIndex: 1000 });
    this._camadasProprias.push(camada);
    this._ol.addLayer(camada);
  };

  // ---------------------------------------------------------------- controles
  function botao(classe, rotulo, acao) {
    var b = el("button", classe);
    b.type = "button"; b.title = rotulo; b.setAttribute("aria-label", rotulo);
    b.appendChild(el("span", "maplibregl-ctrl-icon"));
    b.addEventListener("click", acao);
    return b;
  }
  function NavigationControl() {}
  NavigationControl.prototype.onAdd = function (mapa) {
    var g = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
    function zoom(d) { mapa._view.animate({ zoom: mapa._view.getZoom() + d, duration: 250 }); }
    g.appendChild(botao("maplibregl-ctrl-zoom-in", "Aproximar", function () { zoom(1); }));
    g.appendChild(botao("maplibregl-ctrl-zoom-out", "Afastar", function () { zoom(-1); }));
    return g;
  };
  function FullscreenControl(op) { this._caixa = op && op.container; }
  FullscreenControl.prototype.onAdd = function (mapa) {
    var caixa = this._caixa || mapa.getContainer();
    var g = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
    var b = botao("maplibregl-ctrl-fullscreen", "Tela cheia", function () {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (caixa.requestFullscreen) caixa.requestFullscreen();
    });
    document.addEventListener("fullscreenchange", function () {
      var cheio = document.fullscreenElement === caixa;
      b.className = cheio ? "maplibregl-ctrl-shrink" : "maplibregl-ctrl-fullscreen";
      setTimeout(function () { mapa.resize(); }, 50);
    });
    g.appendChild(b);
    return g;
  };
  function AttributionControl() {}
  AttributionControl.prototype.onAdd = function () { return el("div"); };

  // ---------------------------------------------------------------- cartão (popup)
  function Popup(op) {
    Emissor.call(this);
    op = op || {};
    this._deslocamento = typeof op.offset === "number" ? op.offset : 0;
    this._raiz = el("div", "maplibregl-popup maplibregl-popup-anchor-bottom");
    if (op.maxWidth) this._raiz.style.maxWidth = op.maxWidth;
    this._raiz.appendChild(el("div", "maplibregl-popup-tip"));
    this._conteudo = el("div", "maplibregl-popup-content");
    this._raiz.appendChild(this._conteudo);
    this._mapa = null; this._lngLat = null; this._overlay = null;
    this._fechar = op.closeButton !== false;
    this._fecharNoClique = op.closeOnClick !== false;
  }
  Popup.prototype = Object.create(Emissor.prototype);
  Popup.prototype.setLngLat = function (c) { this._lngLat = lngLatDe(c); if (this._overlay) this._overlay.setPosition(paraMapa(this._lngLat)); return this; };
  Popup.prototype.setDOMContent = function (no) {
    var eu = this;
    this._conteudo.textContent = "";
    this._conteudo.appendChild(no);
    if (this._fechar) {
      var x = el("button", "maplibregl-popup-close-button");
      x.type = "button"; x.setAttribute("aria-label", "Fechar"); x.textContent = "×";
      x.addEventListener("click", function () { eu.remove(); });
      this._conteudo.appendChild(x);
    }
    return this;
  };
  Popup.prototype.isOpen = function () { return !!this._overlay; };
  Popup.prototype.addTo = function (mapa) {
    var eu = this;
    if (this._overlay && this._mapa === mapa) { this.setLngLat(this._lngLat); return this; }
    this.remove();
    this._mapa = mapa;
    // Como a MapLibre: alfinete na metade de cima do mapa -> cartão abre para baixo.
    var embaixo = mapa.project(this._lngLat).y < mapa.getContainer().clientHeight * 0.5;
    this._raiz.className = "maplibregl-popup maplibregl-popup-anchor-" + (embaixo ? "top" : "bottom");
    this._overlay = new ol.Overlay({ element: this._raiz, positioning: embaixo ? "top-center" : "bottom-center",
      offset: [0, embaixo ? 8 : -this._deslocamento], stopEvent: true,
      autoPan: { margin: 110, animation: { duration: 250 } } });   // desliza o mapa para o cartão não ficar escondido
    mapa._ol.addOverlay(this._overlay);
    this._overlay.setPosition(paraMapa(this._lngLat));
    var caixa = this._raiz.parentElement;          // o cartão fica por cima dos alfinetes
    if (caixa) caixa.style.zIndex = "10";
    if (this._fecharNoClique) {
      this._aoClicar = function () { eu.remove(); };
      setTimeout(function () { if (eu._mapa) eu._mapa.on("click", eu._aoClicar); }, 0);
    }
    this.fire("open", {});
    return this;
  };
  Popup.prototype.remove = function () {
    if (!this._overlay) return this;
    this._mapa._ol.removeOverlay(this._overlay);
    if (this._aoClicar) this._mapa.off("click", this._aoClicar);
    this._overlay = null;
    this.fire("close", {});
    return this;
  };

  // ---------------------------------------------------------------- alfinete (marker)
  function alfinetePadrao(cor) {
    var d = el("div", "maplibregl-marker-padrao");
    d.innerHTML = '<svg width="27" height="41" viewBox="0 0 27 41" aria-hidden="true"><path fill="' + (cor || "#3FB1CE").replace(/[^#0-9a-zA-Z(),. ]/g, "") +
      '" d="M27 13.5C27 19.07 20.25 27 14.75 34.5 14.02 35.5 12.98 35.5 12.25 34.5 6.75 27 0 19.22 0 13.5 0 6.04 6.04 0 13.5 0 20.96 0 27 6.04 27 13.5z"/>' +
      '<circle cx="13.5" cy="13.5" r="5.5" fill="#fff"/></svg>';
    return d;
  }
  function Marker(op) {
    op = op || {};
    this._el = op.element || alfinetePadrao(op.color);
    this._el.classList.add("maplibregl-marker");
    this._ancora = op.element ? (op.anchor || "center") : "bottom";
    this._lngLat = null; this._mapa = null; this._overlay = null; this._popup = null;
  }
  Marker.prototype.setLngLat = function (c) { this._lngLat = lngLatDe(c); if (this._overlay) this._overlay.setPosition(paraMapa(this._lngLat)); return this; };
  Marker.prototype.getLngLat = function () { return { lng: this._lngLat[0], lat: this._lngLat[1] }; };
  Marker.prototype.getElement = function () { return this._el; };
  Marker.prototype.addTo = function (mapa) {
    this.remove();
    this._mapa = mapa;
    var pos = { bottom: "bottom-center", top: "top-center", left: "center-left", right: "center-right" }[this._ancora] || "center-center";
    this._overlay = new ol.Overlay({ element: this._el, positioning: pos, stopEvent: true });
    mapa._ol.addOverlay(this._overlay);
    this._overlay.setPosition(paraMapa(this._lngLat));
    return this;
  };
  Marker.prototype.remove = function () {
    if (this._overlay) { this._mapa._ol.removeOverlay(this._overlay); this._overlay = null; }
    if (this._popup) this._popup.remove();
    return this;
  };
  Marker.prototype.setPopup = function (popup) {
    var eu = this;
    this._popup = popup;
    if (!this._clique) {
      this._clique = function (e) { e.stopPropagation(); eu.togglePopup(); };
      this._el.addEventListener("click", this._clique);
    }
    return this;
  };
  Marker.prototype.getPopup = function () { return this._popup; };
  Marker.prototype.togglePopup = function () {
    if (!this._popup || !this._mapa) return this;
    if (this._popup.isOpen()) this._popup.remove();
    else this._popup.setLngLat(this._lngLat).addTo(this._mapa);
    return this;
  };

  // Sempre disponível como window.mapaReserva (a página usa se a MapLibre falhar ao abrir);
  // vira o maplibregl de vez quando o navegador não tem WebGL.
  window.mapaReserva = {
    Map: Mapa, Marker: Marker, Popup: Popup, LngLatBounds: LngLatBounds,
    NavigationControl: NavigationControl, FullscreenControl: FullscreenControl, AttributionControl: AttributionControl,
    reserva: true
  };
  if (typeof maplibregl === "undefined" || !temWebGL() || forcar) window.maplibregl = window.mapaReserva;
})();
