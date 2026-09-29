import { useState } from 'react';
import { ThinkingOrb } from 'thinking-orbs';

function App() {
  const [orbState, setOrbState] = useState("breathing");
  const [chatLog, setChatLog] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [popup, setPopup] = useState(null);

  async function sendMessage() {
  if (!userInput || isBusy) return;

  setIsBusy(true);
  const newLog = [...chatLog, { sender: "You", text: userInput }];
  setChatLog(newLog);
  setUserInput("");
  setOrbState("solving");

  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userInput })
    });

    if (!response.ok) throw new Error("Server responded with an error.");

    const data = await response.json();
    setChatLog([...newLog, { sender: "Jarvis", text: data.reply }]);
  } catch (error) {
    showPopup("Could not reach Jarvis. Is the server running?", "error");
  }

  setOrbState("breathing");
  setIsBusy(false);
  }

  async function endSession() {
    if (isBusy) return;

    setIsBusy(true);
    setOrbState("working");

    try {
      const response = await fetch("http://127.0.0.1:8000/end_session", {
        method: "POST"
      });

      if (!response.ok) throw new Error("Server responded with an error.");

      await response.json();
      setChatLog([]);
      showPopup("Session ended and memory saved.", "success");
    } catch (error) {
      showPopup("Could not reach Jarvis to end the session.", "error");
    }

    setOrbState("breathing");
    setIsBusy(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function showPopup(text, type = "success") {
  setPopup({ text, type });
  setTimeout(() => setPopup(null), 3500);
}



  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      margin: 0
    }}>

      <div style={{
        padding: '15px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        
        <div style={{ width: '80px' }}></div>
        <div style={{ fontWeight: 'bold', fontSize: '20px' }}>Jarvis</div>

        {popup && (
          <div style={{
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: popup.type === "error" ? '#8b2e2e' : '#2a2a2a',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '10px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
          }}>
            {popup.text}
          </div>
        )}

        <button onClick={endSession} disabled={isBusy} style={{ padding: '6px 12px' }}>
          End Session
        </button>
      </div>

      <div style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column-reverse',
        padding: '10px'
      }}>
        <div>
          {chatLog.map((msg, index) => {
            const isUser = msg.sender === "You";

            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  marginBottom: '8px'
                }}
              >
                <div style={{
                  maxWidth: '75%',
                  marginLeft: isUser ? '15%' : '0',
                  marginRight: isUser ? '0' : '15%',
                  padding: '10px 14px',
                  borderRadius: '14px',
                  backgroundColor: isUser ? '#3a3a3a' : '#2a2a2a',
                  color: 'white'
                }}>
                  {msg.text}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '15px',
        borderTopLeftRadius: '20px',
        borderTopRightRadius: '20px',
        boxShadow: '0 -2px 10px rgba(0,0,0,0.1)'
      }}>
        <ThinkingOrb state={orbState} size={64} />

        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{ flex: 1, padding: '10px', fontSize: '16px' }}
        />

        <button onClick={sendMessage} disabled={isBusy} style={{ padding: '10px' }}>
          ↑
        </button>
      </div>

    </div>
  );
}

export default App;