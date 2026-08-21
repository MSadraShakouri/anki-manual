/**
 * lunr-fa.js — Persian normalizer/stemmer for the Anki manual search.
 *
 * Registered as BOTH "stemmer-fa" and "stemmer-ar" (the latter is the
 * pipeline name the pinned mdbook build bakes into the index), so
 * elasticlunr.Index.load() finds it no matter which name the index carries.
 *
 * The exact same module is used at BUILD time by tools/fa/normalize-search.js
 * to normalize the inverted index itself, guaranteeing query and index sides
 * apply identical rules:
 *
 *   - strip tatweel (ـ), ZWNJ/ZWJ, bidi marks
 *   - strip Arabic diacritics (اعراب / harakat)
 *   - unify Arabic codepoints to their Persian equivalents: ي ى → ی ، ك → ک ، ة ۀ → ه
 *   - unify alef variants (آ أ إ ٱ) → ا
 *   - unify Persian (۰-۹) and Arabic (٠-٩) digits to ASCII 0-9
 *   - lowercase Latin letters
 *   - trim leading/trailing punctuation (mdbook tokens keep it attached)
 *   - light suffix stripping for recall: های/هایی/ها (plural), ترین/تر
 *     (guarded: word ≥5 chars, stem ≥3 chars)
 */
;(function (factory) {
  var g = typeof globalThis !== 'undefined' ? globalThis
        : typeof self !== 'undefined' ? self
        : typeof window !== 'undefined' ? window
        : this;
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    g.lunrFa = factory();
  }
}(function () {

  var STRIP = /[\u064B-\u0655\u0670\u0640\u200B-\u200F\u061C\u06D6-\u06ED]/g;

  var CHARMAP = {
    '\u064A': '\u06CC', // arabic yeh   → farsi yeh ی
    '\u0649': '\u06CC', // alef maksura → farsi yeh ی
    '\u0643': '\u06A9', // arabic kaf   → keheh ک
    '\u0623': '\u0627', // أ → ا
    '\u0625': '\u0627', // إ → ا
    '\u0622': '\u0627', // آ → ا
    '\u0671': '\u0627', // ٱ → ا
    '\u0629': '\u0647', // ة → ه
    '\u06C0': '\u0647'  // ۀ → ه
  };
  var FA_DIGITS = '\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9';
  var AR_DIGITS = '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669';

  var PUNCT = '\u0000-\u002C\u002E-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E'
            + '\u00A1-\u00BF\u060C\u061B\u061F\u00AB\u00BB\u066A\u066B\u066C\u066D'
            + '\u2010-\u2027\u2030-\u205E';
  var TRIM = new RegExp('(^[' + PUNCT + ']+)|([' + PUNCT + ']+$)', 'g');

  // documented dual spellings → one canonical form
  var VARIANTS = {
    '\u062C\u0633\u062A\u0648\u062C\u0648': '\u062C\u0633\u062A\u062C\u0648' // جستوجو → جستجو
  };

  // longest-first suffixes
  var SUFFIXES = [
    '\u0647\u0627\u06CC\u06CC', // هایی
    '\u0647\u0627\u06CC',       // های
    '\u0647\u0627',             // ها
    '\u062A\u0631\u06CC\u0646', // ترین
    '\u062A\u0631'              // تر
  ];

  function normalize(token) {
    if (!token) return '';
    var t = ('' + token).toLowerCase().replace(STRIP, '');
    var out = '';
    for (var i = 0; i < t.length; i++) {
      var c = t.charAt(i);
      var fi = FA_DIGITS.indexOf(c);
      if (fi >= 0) { out += String.fromCharCode(48 + fi); continue; }
      var ai = AR_DIGITS.indexOf(c);
      if (ai >= 0) { out += String.fromCharCode(48 + ai); continue; }
      out += (CHARMAP.hasOwnProperty(c) ? CHARMAP[c] : c);
    }
    t = out.replace(TRIM, '');
    if (VARIANTS.hasOwnProperty(t)) t = VARIANTS[t];
    if (t.length >= 5) {
      for (var s = 0; s < SUFFIXES.length; s++) {
        var suf = SUFFIXES[s];
        if (t.length - suf.length >= 3 && t.slice(-suf.length) === suf) {
          t = t.slice(0, -suf.length);
          break;
        }
      }
    }
    return t;
  }

  function lunrFaPipelineFunction(token) {
    return normalize(token === undefined || token === null ? '' : token);
  }

  function registerWith(lunrRef) {
    if (lunrRef && lunrRef.Pipeline && lunrRef.Pipeline.registerFunction) {
      lunrRef.Pipeline.registerFunction(lunrFaPipelineFunction, 'stemmer-fa');
      lunrRef.Pipeline.registerFunction(lunrFaPipelineFunction, 'stemmer-ar');
    }
  }

  // auto-register in browser context (after elasticlunr has loaded)
  var g = typeof globalThis !== 'undefined' ? globalThis
        : typeof self !== 'undefined' ? self
        : this;
  registerWith(g.lunr || g.elasticlunr);

  return {
    normalize: normalize,
    pipelineFunction: lunrFaPipelineFunction,
    register: registerWith
  };
}));
