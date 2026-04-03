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
  element.classList.remove("loading");
  let i = 0;

  function typing() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      setTimeout(typing, 18);
    }
  }

  typing();
}

/* INIT CHARTS */
function initCharts() {
  const ctx1 = document.getElementById("focusChart").getContext("2d");
  const ctx2 = document.getElementById("prevChart").getContext("2d");

  const chartOptions = {
    responsive: true,
    scales: {
      y: {
        min: 0,
        max: 1,
        ticks: { color: "#94a3b8" },
        grid: { color: "rgba(148,163,184,0.1)" },
      },
      x: {
        ticks: { color: "#94a3b8" },
        grid: { color: "rgba(148,163,184,0.1)" },
      },
    },
    plugins: {
      legend: { labels: { color: "#e2e8f0" } },
    },
  };

  chart = new Chart(ctx1, {
    type: "line",
    data: {
      labels: currentSession.map((_, i) => `Step ${i + 1}`),
      datasets: [
        {
          label: "Focus Level",
          data: currentSession,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: chartOptions,
  });

  prevChart = new Chart(ctx2, {
    type: "line",
    data: {
      labels: previousSession.map((_, i) => `Step ${i + 1}`),
      datasets: [
        {
          label: "Focus Level",
          data: previousSession,
          borderColor: "#f97316",
          backgroundColor: "rgba(249,115,22,0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: chartOptions,
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

/* 🔥 GENERATE ADVICE */
function generateAdvice(action, focus, fatigue, distractions) {
  if (action === "take_break") {
    return `Your fatigue is high (${fatigue.toFixed(2)}). Taking a short 5–10 minute break will restore your focus and improve overall performance.`;
  } else if (action === "block_distraction") {
    const d = distractions.length > 0 ? distractions[0] : "distractions";
    return `"${d}" is actively hurting your focus. Blocking it now will give you a significant productivity boost.`;
  } else {
    return `Your focus is at ${focus.toFixed(2)} — you're in a solid flow state. Keep going and maintain this momentum!`;
  }
}

/* 🔥 GENERATE CONFIDENCE */
function generateConfidence(focus, fatigue, distractions) {
  const base = focus * 0.6 - fatigue * 0.3 - distractions.length * 0.05;
  const confidence = Math.max(0.4, Math.min(0.99, base + 0.5));
  return (confidence * 100).toFixed(0) + "%";
}

/* 🔥 SAFE FETCH */
async function fetchWithRetry(url, options, retries = 2) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Server error ${res.status}: ${err}`);
    }
    return await res.json();
  } catch (err) {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 500));
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

  const btn = document.querySelector(".controls button:first-child");
  btn.disabled = true;

  const adviceEl = document.getElementById("advice");
  adviceEl.className = "typing loading";
  adviceEl.innerHTML = "🤖 Thinking...";

  await new Promise((r) => setTimeout(r, 400));

  if (currentSession.length === 0) {
    const focusVal = parseFloat(document.getElementById("focusInput").value);
    const fatigueVal = parseFloat(
      document.getElementById("fatigueInput").value,
    );
    const distractionVal = document.getElementById("distractionInput").value;

    currentFocus = isNaN(focusVal) ? 0.5 : Math.max(0, Math.min(1, focusVal));
    currentFatigue = isNaN(fatigueVal)
      ? 0.3
      : Math.max(0, Math.min(1, fatigueVal));
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
    const advice = generateAdvice(
      action,
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
    document.getElementById("confidence").innerText = confidence;

    adviceEl.className = "typing";
    typeText(adviceEl, advice);

    updateState(action);

    document.getElementById("focusInput").value = currentFocus.toFixed(2);
    document.getElementById("fatigueInput").value = currentFatigue.toFixed(2);
    document.getElementById("distractionInput").value =
      currentDistractions.join(", ");

    currentSession.push(parseFloat(currentFocus.toFixed(2)));
    localStorage.setItem("currentSession", JSON.stringify(currentSession));

    chart.data.labels = currentSession.map((_, i) => `Step ${i + 1}`);
    chart.data.datasets[0].data = currentSession;
    chart.update();
  } catch (error) {
    adviceEl.className = "typing";
    adviceEl.innerHTML = "⚠️ Could not reach server. Please try again.";
    console.error("Step error:", error);
  }

  btn.disabled = false;
  isLoading = false;
}

window.onload = initCharts;
