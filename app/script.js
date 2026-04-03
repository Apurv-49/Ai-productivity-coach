const API = "";

let chart, prevChart;

let currentSession = JSON.parse(localStorage.getItem("currentSession")) || [];
let previousSession = JSON.parse(localStorage.getItem("previousSession")) || [];

let currentFocus = 0.5;
let currentFatigue = 0.3;
let currentDistractions = [];

let isLoading = false;

/* 🔥 TYPING EFFECT */
function typeText(element, text) {
  element.innerHTML = "";
  let i = 0;

  function typing() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      setTimeout(typing, 20);
    }
  }

  typing();
}

/* INIT CHARTS */
function initCharts() {
  const ctx1 = document.getElementById("focusChart").getContext("2d");
  const ctx2 = document.getElementById("prevChart").getContext("2d");

  chart = new Chart(ctx1, {
    type: "line",
    data: {
      labels: currentSession.map((_, i) => i),
      datasets: [{ label: "Current", data: currentSession }],
    },
  });

  prevChart = new Chart(ctx2, {
    type: "line",
    data: {
      labels: previousSession.map((_, i) => i),
      datasets: [{ label: "Previous", data: previousSession }],
    },
  });

  if (currentSession.length > 0) {
    currentFocus = currentSession[currentSession.length - 1];
  }
}

/* RESET */
function resetSession() {
  localStorage.setItem("previousSession", JSON.stringify(currentSession));
  localStorage.setItem("currentSession", JSON.stringify([]));
  location.reload();
}

/* 🔥 HYBRID STATE UPDATE */
function updateState(action) {
  currentFatigue += 0.03;

  if (action === "continue") {
    currentFocus += 0.04 * (1 - currentFatigue);
  } else if (action === "take_break") {
    currentFatigue -= 0.25;
    currentFocus += 0.08;
  } else if (action === "block_distraction") {
    if (currentDistractions.length > 0) {
      currentDistractions.shift();
      currentFocus += 0.06;
    }
  }

  if (Math.random() < 0.1) {
    currentDistractions.push("instagram");
    currentFocus -= 0.03;
  }

  currentFocus -= 0.02;
  currentFocus -= currentFatigue * 0.05;

  currentFocus = Math.max(0.05, Math.min(1, currentFocus));
  currentFatigue = Math.max(0, Math.min(1, currentFatigue));
}

/* 🔥 GENERATE ADVICE FROM ACTION */
function generateAdvice(action, reason, focus, fatigue, distractions) {
  if (action === "take_break") {
    return `Your fatigue is high (${fatigue.toFixed(2)}). Taking a short break will help restore focus. Step away for 5–10 minutes.`;
  } else if (action === "block_distraction") {
    const d = distractions.length > 0 ? distractions[0] : "distractions";
    return `${d} is hurting your focus. Blocking it now will improve your productivity significantly.`;
  } else {
    return `Your focus is at ${focus.toFixed(2)}. Keep going — you're in a good flow state. Maintain momentum!`;
  }
}

/* 🔥 GENERATE CONFIDENCE SCORE */
function generateConfidence(focus, fatigue, distractions) {
  const base = focus * 0.6 - fatigue * 0.3 - distractions.length * 0.05;
  const confidence = Math.max(0.4, Math.min(0.99, base + 0.5));
  return (confidence * 100).toFixed(0) + "%";
}

/* 🔥 SAFE FETCH */
async function fetchWithRetry(url, options, retries = 2) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error("Server error");
    return await res.json();
  } catch (err) {
    if (retries > 0) {
      return await fetchWithRetry(url, options, retries - 1);
    } else {
      throw err;
    }
  }
}

/* STEP */
async function stepEnv() {
  if (isLoading) return;
  isLoading = true;

  const adviceEl = document.getElementById("advice");
  adviceEl.innerHTML = "🤖 Thinking...";

  await new Promise((r) => setTimeout(r, 400));

  if (currentSession.length === 0) {
    const focusVal = parseFloat(document.getElementById("focusInput").value);
    const fatigueVal = parseFloat(
      document.getElementById("fatigueInput").value,
    );
    const distractionVal = document.getElementById("distractionInput").value;

    currentFocus = isNaN(focusVal) ? 0.5 : focusVal;
    currentFatigue = isNaN(fatigueVal) ? 0.3 : fatigueVal;
    currentDistractions = distractionVal
      .split(",")
      .map((x) => x.trim())
      .filter((x) => x);
  }

  try {
    const data = await fetchWithRetry(`${API}/step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_task: "DSA",
        focus_level: currentFocus,
        fatigue: currentFatigue,
        distractions: currentDistractions,
        time_spent: 0,
        deadline: 60,
      }),
    });

    const action = data.action;
    const reason = data.reason;

    // 🔥 GENERATE ADVICE + CONFIDENCE LOCALLY
    const advice = generateAdvice(
      action,
      reason,
      currentFocus,
      currentFatigue,
      currentDistractions,
    );
    const confidence = generateConfidence(
      currentFocus,
      currentFatigue,
      currentDistractions,
    );

    document.getElementById("action").innerText = action;
    document.getElementById("reason").innerText = reason;
    typeText(adviceEl, advice);
    document.getElementById("confidence").innerText = confidence;

    updateState(action);

    document.getElementById("focusInput").value = currentFocus.toFixed(2);
    document.getElementById("fatigueInput").value = currentFatigue.toFixed(2);
    document.getElementById("distractionInput").value =
      currentDistractions.join(", ");

    currentSession.push(parseFloat(currentFocus.toFixed(2)));
    localStorage.setItem("currentSession", JSON.stringify(currentSession));

    chart.data.labels = currentSession.map((_, i) => i);
    chart.data.datasets[0].data = currentSession;
    chart.update();
  } catch (error) {
    adviceEl.innerHTML = "⚠️ Server issue. Try again.";
    console.error(error);
  }

  isLoading = false;
}

window.onload = initCharts;
