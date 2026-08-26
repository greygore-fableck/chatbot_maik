const words = window.vocabulary;
const list = document.querySelector('#list');
const generateButton = document.querySelector('#generate-text');
const generatedText = document.querySelector('#generated-text');
const trainingWords = document.querySelector('#training-words');
const countButtons = document.querySelectorAll('[data-count]');
const accentOptions = document.querySelectorAll('input[name="accent"]');
let playbackId = 0;
let selectedAccent = 'en-GB';
let trainingSession = [];
let trainingIndex = 0;
let clozeSession = [];
let selectedChipIndex = null;

function renderVocabulary() {
  list.replaceChildren();
  [...words].sort(([first], [second]) => first.localeCompare(second)).forEach(([word, pronunciation, meaning]) => {
    list.append(createVocabularyItem(word, pronunciationFor(word, pronunciation), meaning));
  });
}

function pronunciationFor(word, fallback) {
  return window.accentPronunciations?.[selectedAccent]?.[word] || fallback;
}

function createVocabularyItem(word, pronunciation, meaning) {
  const item = document.createElement('article');
  item.innerHTML = `<div><h2>${word}</h2><p class="pronunciation">${pronunciation}</p><p class="meaning">${meaning}</p></div>`;
  const button = document.createElement('button');
  button.type = 'button';
  button.innerHTML = '<span class="label">Anhören</span>';
  button.setAttribute('aria-pressed', 'false');
  button.onclick = () => playWord(word, button);
  item.append(button);
  return item;
}

function playWord(word, button) {
  const estimatedDuration = Math.max(.7, Math.min(2.2, word.length * .11 + .35));
  button.style.setProperty('--playback-duration', `${estimatedDuration}s`);
  button.classList.remove('is-playing');
  void button.offsetWidth;
  button.classList.add('is-playing');
  button.setAttribute('aria-pressed', 'true');
  speak(word, () => {
    button.classList.remove('is-playing');
    button.setAttribute('aria-pressed', 'false');
  });
}

function randomEntries(count) {
  return [...words].sort(() => Math.random() - .5).slice(0, count);
}

function generateText() {
  clozeSession = randomEntries(6);
  selectedChipIndex = null;
  const blanks = clozeSession.map((_, index) => `<span class="blank" data-index="${index}" tabindex="0">&nbsp;</span>`);
  const bank = [...clozeSession.keys()].sort(() => Math.random() - .5).map(index => `<button class="word-chip" type="button" draggable="true" data-index="${index}">${clozeSession[index][0]}</button>`).join('');
  generatedText.innerHTML = `
    <p class="cloze-copy">During a fictional language practice session, Mia came across six useful terms: ${blanks[0]}, ${blanks[1]}, ${blanks[2]}, ${blanks[3]}, ${blanks[4]}, and ${blanks[5]}. She added each one to her notes and practiced saying them aloud before the next review.</p>
    <div class="word-bank" aria-label="Wortbank">${bank}</div>
    <div class="cloze-actions"><button type="button" id="check-cloze">Prüfen</button><button type="button" id="reset-cloze">Neue Lücken</button></div>
    <p class="cloze-feedback" id="cloze-feedback" aria-live="polite"></p>`;
  generatedText.classList.add('is-visible');
  bindClozeInteractions();
}

function bindClozeInteractions() {
  document.querySelectorAll('.word-chip').forEach(chip => {
    chip.addEventListener('dragstart', event => event.dataTransfer.setData('text/plain', chip.dataset.index));
    chip.addEventListener('click', () => selectChip(Number(chip.dataset.index)));
  });
  document.querySelectorAll('.blank').forEach(blank => {
    blank.addEventListener('dragover', event => { event.preventDefault(); blank.classList.add('is-over'); });
    blank.addEventListener('dragleave', () => blank.classList.remove('is-over'));
    blank.addEventListener('drop', event => { event.preventDefault(); blank.classList.remove('is-over'); placeWord(Number(event.dataTransfer.getData('text/plain')), blank); });
    blank.addEventListener('click', () => { if (selectedChipIndex !== null) placeWord(selectedChipIndex, blank); });
  });
  document.querySelector('#check-cloze').addEventListener('click', checkCloze);
  document.querySelector('#reset-cloze').addEventListener('click', generateText);
}

function selectChip(index) {
  selectedChipIndex = index;
  document.querySelectorAll('.word-chip').forEach(chip => chip.classList.toggle('is-selected', Number(chip.dataset.index) === index));
}

function placeWord(wordIndex, blank) {
  document.querySelectorAll('.blank').forEach(otherBlank => {
    if (Number(otherBlank.dataset.wordIndex) === wordIndex) {
      otherBlank.textContent = '';
      delete otherBlank.dataset.wordIndex;
    }
  });
  blank.textContent = clozeSession[wordIndex][0];
  blank.dataset.wordIndex = wordIndex;
  blank.classList.remove('is-correct', 'is-incorrect');
  selectedChipIndex = null;
  const usedWords = new Set([...document.querySelectorAll('.blank')].map(otherBlank => Number(otherBlank.dataset.wordIndex)).filter(Number.isInteger));
  document.querySelectorAll('.word-chip').forEach(chip => chip.classList.toggle('is-used', usedWords.has(Number(chip.dataset.index))));
}

function checkCloze() {
  const blanks = [...document.querySelectorAll('.blank')];
  const correctCount = blanks.reduce((total, blank) => {
    const correct = Number(blank.dataset.wordIndex) === Number(blank.dataset.index);
    blank.classList.toggle('is-correct', correct);
    blank.classList.toggle('is-incorrect', !correct);
    return total + Number(correct);
  }, 0);
  const feedback = document.querySelector('#cloze-feedback');
  feedback.className = `cloze-feedback ${correctCount === clozeSession.length ? 'is-correct' : 'is-incorrect'}`;
  feedback.textContent = correctCount === clozeSession.length ? 'Alles richtig!' : `${correctCount} von ${clozeSession.length} richtig. Du kannst die Wörter noch umsortieren und erneut prüfen.`;
}

function startVocabularyTraining(count) {
  trainingSession = randomEntries(count);
  trainingIndex = 0;
  renderTrainingQuiz();
}

function renderTrainingQuiz() {
  const [word, pronunciation] = trainingSession[trainingIndex];
  trainingWords.innerHTML = `
    <section class="quiz" aria-label="Vokabelabfrage">
      <p class="quiz-progress">${trainingIndex + 1} von ${trainingSession.length}</p>
      <h4 class="quiz-word">${word}</h4>
      <p class="quiz-pronunciation">${pronunciationFor(word, pronunciation)}</p>
      <form class="quiz-form" id="quiz-form">
        <input class="quiz-input" id="quiz-answer" autocomplete="off" placeholder="Deutsche Bedeutung eingeben" aria-label="Deutsche Bedeutung">
        <button type="submit">Prüfen</button>
      </form>
      <div class="quiz-actions"><button type="button" id="quiz-listen">Anhören</button><button type="button" id="quiz-speak-answer">Antwort sprechen</button></div>
      <p class="quiz-feedback" id="quiz-feedback" aria-live="polite"></p>
    </section>`;

  document.querySelector('#quiz-form').addEventListener('submit', checkTrainingAnswer);
  document.querySelector('#quiz-listen').addEventListener('click', event => playWord(word, event.currentTarget));
  document.querySelector('#quiz-speak-answer').addEventListener('click', startAnswerRecognition);
  document.querySelector('#quiz-answer').focus();
}

function startAnswerRecognition(event) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const button = event.currentTarget;
  const input = document.querySelector('#quiz-answer');
  const feedback = document.querySelector('#quiz-feedback');

  if (!SpeechRecognition) {
    feedback.className = 'quiz-feedback is-incorrect';
    feedback.textContent = 'Die Spracheingabe wird von diesem Browser nicht unterstützt.';
    return;
  }

  const recognition = new SpeechRecognition();
  let transcriptReceived = false;
  recognition.lang = 'de-DE';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  button.classList.add('is-listening');
  button.textContent = 'Spricht …';

  recognition.onresult = result => { transcriptReceived = true; input.value = result.results[0][0].transcript; };
  recognition.onerror = () => { feedback.className = 'quiz-feedback is-incorrect'; feedback.textContent = 'Die Spracheingabe konnte nicht erkannt werden. Versuch es bitte noch einmal.'; };
  recognition.onend = () => {
    button.classList.remove('is-listening');
    button.textContent = 'Antwort sprechen';
    input.focus();
    if (transcriptReceived && input.value.trim()) {
      feedback.className = 'quiz-feedback';
      feedback.textContent = 'Prüfung startet in 3 Sekunden …';
      setTimeout(() => { if (!input.disabled) document.querySelector('#quiz-form')?.requestSubmit(); }, 3000);
    }
  };
  recognition.start();
}

function normaliseAnswer(value) {
  return value.toLowerCase().trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ß/g, 'ss').replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ');
}

function checkTrainingAnswer(event) {
  event.preventDefault();
  const [, , meaning] = trainingSession[trainingIndex];
  const answer = normaliseAnswer(document.querySelector('#quiz-answer').value);
  const acceptedAnswers = meaning.split('/').map(normaliseAnswer);
  const correct = acceptedAnswers.includes(answer);
  const feedback = document.querySelector('#quiz-feedback');
  feedback.className = `quiz-feedback ${correct ? 'is-correct' : 'is-incorrect'}`;
  feedback.textContent = correct ? 'Richtig!' : `Noch nicht. Richtig wäre: ${meaning}.`;

  const next = document.createElement('button');
  next.type = 'button';
  next.textContent = trainingIndex + 1 === trainingSession.length ? 'Abschluss ansehen' : 'Nächste Vokabel';
  next.addEventListener('click', nextTrainingWord);
  document.querySelector('.quiz-actions').append(next);
  event.currentTarget.querySelector('button[type="submit"]').disabled = true;
  document.querySelector('#quiz-answer').disabled = true;
}

function nextTrainingWord() {
  trainingIndex += 1;
  if (trainingIndex < trainingSession.length) {
    renderTrainingQuiz();
    return;
  }
  trainingWords.innerHTML = '<p class="quiz-feedback is-correct">Runde abgeschlossen. Wähle oben eine neue Anzahl für die nächste Runde.</p>';
}

function englishVoice() {
  return speechSynthesis.getVoices().find(voice => voice.lang === selectedAccent)
    || speechSynthesis.getVoices().find(voice => voice.lang.startsWith('en'));
}

function speak(text, done) {
  const currentPlayback = ++playbackId;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = selectedAccent;
  utterance.rate = 0.8;
  const voice = englishVoice();
  if (voice) utterance.voice = voice;
  utterance.onend = utterance.onerror = () => { if (currentPlayback === playbackId) done(); };
  speechSynthesis.speak(utterance);
}

renderVocabulary();
generateButton.addEventListener('click', generateText);
countButtons.forEach(button => button.addEventListener('click', () => startVocabularyTraining(Number(button.dataset.count))));
accentOptions.forEach(option => option.addEventListener('change', () => {
  selectedAccent = option.value;
  renderVocabulary();
  if (trainingSession.length) renderTrainingQuiz();
}));
