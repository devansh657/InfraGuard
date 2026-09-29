import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  ChevronDown,
  Ear,
  Gauge,
  LineChart,
  Mic,
  MicOff,
  RadioTower,
  Send,
  Sparkles,
  Volume2,
  VolumeX
} from "lucide-react";
import { getNovaBriefing, ingestLiveTick, readApiError } from "../services/api.js";

const COMMANDS = [
  "NOVA, give me a risk report",
  "NOVA, run full system check",
  "NOVA, enable clap wake",
  "NOVA, explain what is happening",
  "NOVA, open live monitor",
  "NOVA, open AI analyst",
  "NOVA, show model evidence"
];

const PAGE_COMMANDS = [
  { page: "dashboard", phrases: ["dashboard", "command", "command center", "home"] },
  { page: "live", phrases: ["live", "monitor", "live monitor", "telemetry"] },
  { page: "analyst", phrases: ["analyst", "ai analyst", "nova analyst", "root cause"] },
  { page: "lab", phrases: ["predict", "prediction", "lab", "predict lab"] },
  { page: "timeline", phrases: ["timeline", "incident", "history"] },
  { page: "insights", phrases: ["insights", "eda", "model evidence", "benchmark"] }
];

const PROJECT_AREAS = [
  { page: "dashboard", label: "Command", icon: Gauge, command: "NOVA, open command center" },
  { page: "live", label: "Live", icon: RadioTower, command: "NOVA, open live monitor" },
  { page: "analyst", label: "Analyst", icon: Bot, command: "NOVA, open AI analyst" },
  { page: "lab", label: "Predict", icon: Sparkles, command: "NOVA, open predict lab" },
  { page: "timeline", label: "Timeline", icon: LineChart, command: "NOVA, open timeline" },
  { page: "insights", label: "Insights", icon: Sparkles, command: "NOVA, show insights" }
];

function NovaAssistant({ activePage, onNavigate }) {
  const [open, setOpen] = useState(true);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [muted, setMuted] = useState(false);
  const [continuousMode, setContinuousMode] = useState(false);
  const [wakeEnabled, setWakeEnabled] = useState(false);
  const [wakeStatus, setWakeStatus] = useState("Clap wake offline");
  const [briefing, setBriefing] = useState(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "nova",
      text: "NOVA online. I can report risk, scan the system, and navigate InfraGuard AI by voice or text."
    }
  ]);
  const recognitionRef = useRef(null);
  const keepListeningRef = useRef(false);
  const wakeStreamRef = useRef(null);
  const wakeAudioRef = useRef(null);
  const wakeFrameRef = useRef(null);
  const clapTimesRef = useRef([]);
  const supported = useMemo(() => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition), []);

  useEffect(() => {
    refreshBriefing({ speak: false, silent: true });
  }, []);

  useEffect(() => {
    if (!supported) return undefined;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript ?? "";
      if (transcript) {
        handleCommand(transcript);
      }
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => {
      setListening(false);
      if (keepListeningRef.current) {
        window.setTimeout(() => {
          try {
            recognition.start();
            setListening(true);
          } catch {
            setListening(false);
          }
        }, 250);
      }
    };
    recognitionRef.current = recognition;
    return () => {
      keepListeningRef.current = false;
      recognition.stop();
    };
  }, [supported]);

  useEffect(() => () => stopClapWake(), []);

  async function refreshBriefing({ speak = true, silent = false } = {}) {
    try {
      const data = await getNovaBriefing();
      setBriefing(data);
      if (!silent) {
        addNova(data.spoken_briefing, speak);
      }
      return data;
    } catch (err) {
      const message = readApiError(err);
      addNova(message, speak);
      return null;
    }
  }

  async function scanSystem({ announceUser = true, openAnalyst = false } = {}) {
    if (announceUser) addUser("NOVA, scan the system");
    addNova("Running a live telemetry scan now.", true);
    try {
      await ingestLiveTick();
      const data = await refreshBriefing({ speak: false, silent: true });
      if (openAnalyst) onNavigate("analyst");
      if (data) {
        addNova(`Scan complete. ${data.spoken_briefing}`, true);
      }
    } catch (err) {
      addNova(readApiError(err), true);
    }
  }

  function startListening() {
    setOpen(true);
    if (!supported || !recognitionRef.current) {
      addNova("Voice recognition is not available in this browser. You can still type commands to NOVA.", true);
      return;
    }
    try {
      keepListeningRef.current = true;
      setContinuousMode(true);
      setListening(true);
      recognitionRef.current.start();
      addNova("Listening channel active. Speak naturally.", true);
    } catch {
      setListening(false);
    }
  }

  function stopListening() {
    keepListeningRef.current = false;
    setContinuousMode(false);
    recognitionRef.current?.stop();
    setListening(false);
  }

  function speak(text) {
    if (muted || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 0.72;
    utterance.volume = 0.95;
    const voice = selectNovaVoice();
    if (voice) utterance.voice = voice;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }

  async function enableClapWake() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setWakeStatus("Microphone wake is not supported here");
      addNova("Clap wake is not supported in this browser. Voice and text commands still work.", true);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.18;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);
      wakeStreamRef.current = stream;
      wakeAudioRef.current = audioContext;
      setWakeEnabled(true);
      setWakeStatus("Double clap wake armed");
      addNova("Double clap wake is armed. Two sharp claps will activate my listening channel.", true);
      monitorClaps(analyser);
    } catch {
      setWakeEnabled(false);
      setWakeStatus("Microphone permission needed");
      addNova("I need microphone permission before I can detect a double clap.", true);
    }
  }

  function stopClapWake() {
    if (wakeFrameRef.current) cancelAnimationFrame(wakeFrameRef.current);
    wakeStreamRef.current?.getTracks().forEach((track) => track.stop());
    wakeAudioRef.current?.close?.();
    wakeFrameRef.current = null;
    wakeStreamRef.current = null;
    wakeAudioRef.current = null;
    clapTimesRef.current = [];
    setWakeEnabled(false);
    setWakeStatus("Clap wake offline");
  }

  function monitorClaps(analyser) {
    const data = new Uint8Array(analyser.fftSize);
    let lastClapAt = 0;

    const tick = () => {
      analyser.getByteTimeDomainData(data);
      let peak = 0;
      for (let index = 0; index < data.length; index += 1) {
        peak = Math.max(peak, Math.abs(data[index] - 128));
      }

      const now = performance.now();
      if (peak > 70 && now - lastClapAt > 170) {
        lastClapAt = now;
        clapTimesRef.current = [...clapTimesRef.current.filter((time) => now - time < 900), now];
        setWakeStatus(clapTimesRef.current.length >= 2 ? "Double clap detected" : "Clap detected");

        if (clapTimesRef.current.length >= 2) {
          clapTimesRef.current = [];
          setOpen(true);
          addNova("Double clap detected. NOVA listening.", true);
          startListening();
        }
      }

      wakeFrameRef.current = requestAnimationFrame(tick);
    };

    wakeFrameRef.current = requestAnimationFrame(tick);
  }

  function addNova(text, shouldSpeak = false) {
    setMessages((current) => [...current.slice(-7), { role: "nova", text }]);
    if (shouldSpeak) speak(text);
  }

  function addUser(text) {
    setMessages((current) => [...current.slice(-7), { role: "user", text }]);
  }

  function submit(event) {
    event.preventDefault();
    const command = input.trim();
    if (!command) return;
    setInput("");
    handleCommand(command);
  }

  async function handleCommand(rawCommand) {
    const command = normalize(rawCommand);
    addUser(rawCommand);

    if (command.includes("mute")) {
      setMuted(true);
      addNova("Voice muted. I will continue responding on screen.", false);
      return;
    }
    if (command.includes("unmute") || command.includes("speak")) {
      setMuted(false);
      addNova("Voice channel restored.", true);
      return;
    }
    if (command.includes("stop")) {
      window.speechSynthesis?.cancel();
      setSpeaking(false);
      stopListening();
      addNova("Standing by.", false);
      return;
    }
    if (command.includes("enable clap") || command.includes("clap wake") || command.includes("wake on clap")) {
      await enableClapWake();
      return;
    }
    if (command.includes("disable clap") || command.includes("turn off clap")) {
      stopClapWake();
      addNova("Double clap wake is offline.", true);
      return;
    }
    if (command.includes("help") || command.includes("what can you do")) {
      addNova("I have console access across InfraGuard. I can open every module, run live scans, brief risk, show model insights, open the AI analyst, and control my voice channel.", true);
      return;
    }
    if (command.includes("control") || command.includes("access")) {
      addNova("NOVA access matrix is active. I can control Command Center, Live Monitor, AI Analyst, Predict Lab, Timeline, and Insights. I can also run telemetry scans and speak risk briefings.", true);
      return;
    }
    if (command.includes("what is wrong") || command.includes("what happened") || command.includes("explain") || command.includes("why") || command.includes("root cause") || command.includes("what should i do") || command.includes("recommend")) {
      onNavigate("analyst");
      addNova("Opening AI Analyst. This is where I explain likely root cause, confidence, drift, and recommended actions.", true);
      return;
    }
    if (command.includes("full system") || command.includes("diagnostic") || command.includes("investigate")) {
      await scanSystem({ announceUser: false, openAnalyst: true });
      return;
    }
    if (command.includes("graph") || command.includes("chart") || command.includes("performance") || command.includes("telemetry stream")) {
      onNavigate("live");
      addNova("Opening Live Monitor for moving telemetry and performance signals.", true);
      return;
    }
    if (command.includes("evidence") || command.includes("eda") || command.includes("roc") || command.includes("auc") || command.includes("recall") || command.includes("benchmark")) {
      onNavigate("insights");
      addNova("Opening Insights. This module contains EDA, benchmark evidence, recall, ROC AUC, and model validation.", true);
      return;
    }
    if (command.includes("incident") || command.includes("error") || command.includes("timeline") || command.includes("past") || command.includes("history")) {
      onNavigate("timeline");
      addNova("Opening the incident timeline.", true);
      return;
    }
    if (command.includes("predict") || command.includes("diagnose") || command.includes("test input") || command.includes("scenario")) {
      onNavigate("lab");
      addNova("Opening Predict Lab for manual diagnosis scenarios.", true);
      return;
    }
    if (command.includes("scan") || command.includes("run telemetry") || command.includes("check system")) {
      await scanSystem({ announceUser: false });
      return;
    }
    if (command.includes("report") || command.includes("risk") || command.includes("briefing") || command.includes("status")) {
      await refreshBriefing({ speak: true });
      return;
    }

    const page = resolvePage(command);
    if (page) {
      onNavigate(page);
      addNova(`Opening ${pageLabel(page)}.`, true);
      return;
    }

    const data = await refreshBriefing({ speak: false, silent: true });
    addNova(
      data
        ? `I do not have a dedicated automation for that exact request yet, but I can still brief the system. ${data.spoken_briefing}`
        : "I do not have a dedicated automation for that exact request yet. I can open modules, run scans, brief risk, and analyze incidents.",
      true
    );
  }

  const riskTone = briefing?.risk_level === "HIGH" ? "critical" : briefing?.risk_level === "MEDIUM" ? "warning" : "safe";

  return (
    <div className="nova-shell">
      <AnimatePresence>
        {open ? (
          <motion.section
            className="nova-panel"
            initial={{ opacity: 0, y: 22, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ duration: 0.22 }}
          >
            <div className="nova-panel-header">
              <div className="flex items-center gap-3">
                <NovaNeuralCore listening={listening} speaking={speaking} tone={riskTone} />
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.24em] text-amber-100">NOVA</p>
                  <h2 className="text-lg font-black text-white">Neural Operations Voice Assistant</h2>
                </div>
              </div>
              <button className="nova-icon-button" onClick={() => setOpen(false)} type="button" aria-label="Minimize NOVA">
                <ChevronDown size={18} />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <NovaStatus label="State" value={briefing?.operational_state ?? "Syncing"} tone={riskTone} />
              <NovaStatus label="Risk" value={briefing?.risk_level ?? "..." } tone={riskTone} />
              <NovaStatus label="Page" value={pageLabel(activePage)} tone="safe" />
            </div>

            {briefing?.system_panels?.length ? (
              <div className="nova-panels">
                {briefing.system_panels.slice(0, 5).map((panel) => (
                  <div className={`nova-mini-panel nova-mini-${panel.status}`} key={panel.label}>
                    <span>{panel.label}</span>
                    <strong>{panel.value}</strong>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="nova-access-matrix">
              <div className="nova-access-title">
                <span>Project Access Matrix</span>
                <strong>All modules linked</strong>
              </div>
              <div className="nova-access-grid">
                {PROJECT_AREAS.map((area) => {
                  const Icon = area.icon;
                  const active = area.page === activePage;
                  return (
                    <button
                      className={active ? "nova-access-active" : ""}
                      key={area.page}
                      onClick={() => {
                        onNavigate(area.page);
                        addNova(`Accessing ${area.label}.`, true);
                      }}
                      type="button"
                    >
                      <Icon size={16} />
                      <span>{area.label}</span>
                    </button>
                  );
                })}
              </div>
              <div className="nova-action-row">
                <button onClick={() => refreshBriefing({ speak: true })} type="button">Risk briefing</button>
                <button onClick={() => scanSystem({ openAnalyst: true })} type="button">Full scan</button>
              </div>
              <div className="nova-wake-row">
                <div>
                  <span>Wake Listener</span>
                  <strong>{wakeStatus}</strong>
                </div>
                <button onClick={wakeEnabled ? stopClapWake : enableClapWake} type="button">
                  <Ear size={15} />
                  {wakeEnabled ? "Disable" : "Enable"} double clap
                </button>
              </div>
            </div>

            <div className="nova-messages">
              {messages.map((message, index) => (
                <div className={`nova-message nova-message-${message.role}`} key={`${message.role}-${index}-${message.text.slice(0, 12)}`}>
                  {message.text}
                </div>
              ))}
            </div>

            <div className="nova-command-grid">
              {COMMANDS.map((command) => (
                <button key={command} onClick={() => handleCommand(command)} type="button">
                  {command}
                </button>
              ))}
            </div>

            <form className="nova-input-row" onSubmit={submit}>
              <button
                className={`nova-icon-button ${listening ? "nova-listening" : ""}`}
                onClick={listening ? stopListening : startListening}
                type="button"
                aria-label={listening ? "Stop listening" : "Start voice command"}
              >
                {listening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Type or say: NOVA, scan the system"
              />
              <button className="nova-icon-button" type="submit" aria-label="Send command">
                <Send size={18} />
              </button>
              <button
                className="nova-icon-button"
                onClick={() => {
                  setMuted((current) => !current);
                  window.speechSynthesis?.cancel();
                  setSpeaking(false);
                }}
                type="button"
                aria-label={muted ? "Unmute NOVA" : "Mute NOVA"}
              >
                {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
              </button>
            </form>
          </motion.section>
        ) : null}
      </AnimatePresence>

      <button className="nova-launcher" onClick={() => setOpen((current) => !current)} type="button" aria-label="Open NOVA assistant">
        <span className="nova-launcher-ring" />
        <NovaNeuralCore listening={listening} speaking={speaking} tone={riskTone} compact />
        <span className="nova-launcher-text">NOVA</span>
      </button>
    </div>
  );
}

function NovaNeuralCore({ listening = false, speaking = false, tone = "safe", compact = false }) {
  const stateClass = listening ? "nova-neural-listening" : speaking ? "nova-neural-speaking" : "";
  return (
    <div className={`nova-neural-core ${compact ? "nova-neural-compact" : ""} nova-neural-${tone} ${stateClass}`} aria-hidden="true">
      <span className="nova-neural-halo" />
      <span className="nova-neural-ring nova-ring-one" />
      <span className="nova-neural-ring nova-ring-two" />
      <span className="nova-neural-ring nova-ring-three" />
      <span className="nova-neural-ring nova-ring-four" />
      <span className="nova-neural-connection nova-connection-a" />
      <span className="nova-neural-connection nova-connection-b" />
      <span className="nova-neural-connection nova-connection-c" />
      <span className="nova-neural-connection nova-connection-d" />
      <span className="nova-neural-connection nova-connection-e" />
      <span className="nova-neural-connection nova-connection-f" />
      <span className="nova-neural-data nova-data-one" />
      <span className="nova-neural-data nova-data-two" />
      <span className="nova-neural-data nova-data-three" />
      <span className="nova-neural-node nova-node-one" />
      <span className="nova-neural-node nova-node-two" />
      <span className="nova-neural-node nova-node-three" />
      <span className="nova-neural-node nova-node-four" />
      <span className="nova-neural-node nova-node-five" />
      <span className="nova-neural-node nova-node-six" />
      <span className="nova-neural-node nova-node-seven" />
      <span className="nova-neural-node nova-node-eight" />
      <span className="nova-neural-center">
        <Bot size={compact ? 16 : 20} />
      </span>
    </div>
  );
}

function NovaStatus({ label, value, tone = "safe" }) {
  return (
    <div className={`nova-status nova-status-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function resolvePage(command) {
  for (const item of PAGE_COMMANDS) {
    if (item.phrases.some((phrase) => command.includes(phrase))) {
      return item.page;
    }
  }
  return null;
}

function pageLabel(page) {
  return {
    dashboard: "Command",
    live: "Live",
    analyst: "Analyst",
    lab: "Predict",
    timeline: "Timeline",
    insights: "Insights"
  }[page] ?? "Command";
}

function normalize(command) {
  return command
    .toLowerCase()
    .replace(/nova/g, "")
    .replace(/[^\w\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function selectNovaVoice() {
  const voices = window.speechSynthesis?.getVoices?.() ?? [];
  const preferredNames = [
    "Daniel",
    "George",
    "Ryan",
    "Google UK English Male",
    "Microsoft David",
    "Microsoft Mark",
    "English United Kingdom"
  ];
  return (
    preferredNames
      .map((name) => voices.find((voice) => voice.name.includes(name)))
      .find(Boolean) ??
    voices.find((voice) => voice.lang?.toLowerCase().includes("en-gb")) ??
    voices.find((voice) => voice.lang?.toLowerCase().startsWith("en")) ??
    null
  );
}

export default NovaAssistant;
