const API = "http://127.0.0.1:8000";

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

  // restore last state
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
  // fatigue always increases slightly
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

  // random distraction
  if (Math.random() < 0.1) {
    currentDistractions.push("instagram");
    currentFocus -= 0.03;
  }

  // decay
  currentFocus -= 0.02;
  currentFocus -= currentFatigue * 0.05;

  // clamp values
  currentFocus = Math.max(0.05, Math.min(1, currentFocus));
  currentFatigue = Math.max(0, Math.min(1, currentFatigue));
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

  // only take user input ONCE
  if (currentSession.length === 0) {
    currentFocus = parseFloat(document.getElementById("focusInput").value);
    currentFatigue = parseFloat(document.getElementById("fatigueInput").value);
    currentDistractions = document
      .getElementById("distractionInput")
      .value.split(",")
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

    document.getElementById("action").innerText = data.action;
    document.getElementById("reason").innerText = data.reason;
    typeText(adviceEl, data.advice);
    document.getElementById("confidence").innerText = data.confidence;

    // 🔥 UPDATE STATE AUTOMATICALLY
    updateState(data.action);

    // 🔥 UPDATE INPUT BOXES (IMPORTANT UX)
    document.getElementById("focusInput").value = currentFocus.toFixed(2);
    document.getElementById("fatigueInput").value = currentFatigue.toFixed(2);
    document.getElementById("distractionInput").value =
      currentDistractions.join(", ");

    // save session
    currentSession.push(currentFocus);
    localStorage.setItem("currentSession", JSON.stringify(currentSession));

    // update graph
    chart.data.labels = currentSession.map((_, i) => i);
    chart.data.datasets[0].data = currentSession;
    chart.update();
  } catch (error) {
    adviceEl.innerHTML = "⚠️ Server issue. Try again.";
  }

  isLoading = false;
}

window.onload = initCharts;
