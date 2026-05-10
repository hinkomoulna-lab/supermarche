(function() {
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  var recognition = null;
  var activeButton = null;

  function getLang() {
    return document.documentElement.lang || 'fr-FR';
  }

  function stopListening() {
    if (recognition) {
      try { recognition.abort(); } catch(e) {}
      recognition = null;
    }
    if (activeButton) {
      activeButton.classList.remove('listening');
      activeButton.title = 'Saisie vocale';
      activeButton.innerHTML = micSVG(false);
      activeButton = null;
    }
  }

  function micSVG(pulse) {
    return '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"' +
      (pulse ? ' class="pulse"' : '') +
      '><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
  }

  function startListening(button, input) {
    stopListening();
    recognition = new SpeechRecognition();
    recognition.lang = getLang();
    recognition.continuous = false;
    recognition.interimResults = true;

    activeButton = button;
    button.classList.add('listening');
    button.title = 'Écoute en cours...';
    button.innerHTML = micSVG(true);

    recognition.onresult = function(e) {
      var result = e.results[e.results.length - 1];
      var transcript = result[0].transcript;
      var isFinal = result.isFinal;
      if (input.tagName === 'TEXTAREA' && isFinal) {
        input.value += (input.value ? ' ' : '') + transcript;
      } else {
        input.value = transcript;
      }
      input.dispatchEvent(new Event('input', { bubbles: true }));
    };

    recognition.onerror = function(e) {
      if (e.error === 'no-speech' || e.error === 'aborted') return;
      button.title = 'Erreur: ' + e.error;
      setTimeout(stopListening, 2000);
    };

    recognition.onend = function() {
      if (recognition) stopListening();
    };

    try { recognition.start(); } catch(e) {}
  }

  function initVoiceInputs() {
    document.querySelectorAll('[data-voice]').forEach(function(input) {
      if (input.dataset.voiceInitialized) return;
      input.dataset.voiceInitialized = '1';
      var wrapper = document.createElement('div');
      wrapper.className = 'voice-input-wrapper';
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'voice-input-btn';
      btn.title = 'Saisie vocale';
      btn.innerHTML = micSVG(false);
      btn.dataset.target = input.id || input.name;
      if (!input.id) input.id = input.name;
      wrapper.appendChild(btn);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVoiceInputs);
  } else {
    initVoiceInputs();
  }

  document.addEventListener('click', function(e) {
    var button = e.target.closest('.voice-input-btn');
    if (!button) {
      if (activeButton && !e.target.closest('.listening')) stopListening();
      return;
    }
    e.preventDefault();
    var input = document.getElementById(button.dataset.target);
    if (!input) return;
    if (button.classList.contains('listening')) {
      stopListening();
    } else {
      startListening(button, input);
    }
  });
})();
