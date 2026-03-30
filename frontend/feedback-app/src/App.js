
import React, { useState } from "react";
import { withAuthenticator } from "@aws-amplify/ui-react";
import { get, post } from "aws-amplify/api";
import { fetchAuthSession } from "aws-amplify/auth";
import "./App.css";

function App() {
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackId, setFeedbackId] = useState("");
  const [responseText, setResponseText] = useState("");
  const [loading, setLoading] = useState(false);

  const API_NAME = "feedbackApi";

  // ✅ POST /feedback
  const sendFeedback = async () => {
    if (!feedbackText.trim()) {
      setResponseText("❌ Please enter feedback text");
      return;
    }

    setLoading(true);
    setResponseText("");

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      const response = await post({
        apiName: API_NAME,
        path: "/feedback",
        options: {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: {
            text: feedbackText.trim(),
          },
        },
      }).response;

      const data = response.body; 

      if (!data || !data.feedbackId) {
        throw new Error("Backend returned empty feedbackId");
      }

      setFeedbackId(data.feedbackId); // ✅ zapisz ID
      setResponseText(`✅ Feedback submitted!\nFeedback ID: ${data.feedbackId}`);
    } catch (err) {
      console.error("POST error:", err);
      setResponseText(`❌ Error: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  // ✅ GET /recommendation
  const getRecommendation = async () => {
    if (!feedbackId || feedbackId.trim() === "") {
      setResponseText("❌ Missing feedback ID");
      return;
    }

    setLoading(true);
    setResponseText("");

    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();

      const safeId = encodeURIComponent(feedbackId.trim()); // ✅ zabezpieczenie przed "undefined"

      const response = await get({
        apiName: API_NAME,
        path: `/recommendation?feedbackId=${safeId}`,
        options: {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      }).response;

      const data = response.body;

      setResponseText(
        `✅ Recommendation:\n${JSON.stringify(data, null, 2)}`
      );
    } catch (err) {
      console.error("GET error:", err);
      setResponseText(`❌ Error: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Feedback App – Lambda Tester</h1>
      </header>

      <main className="App-main">

        {/* POST */}
        <div className="test-section">
          <h2>🧪 Test POST /feedback</h2>
          <textarea
            value={feedbackText || ""}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Enter your feedback..."
            rows={3}
          />
          <button onClick={sendFeedback} disabled={loading}>
            {loading ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>

        {/* GET */}
        <div className="test-section">
          <h2>🧪 Test GET /recommendation</h2>
          <input
            value={feedbackId || ""}
            onChange={(e) => setFeedbackId(e.target.value)}
            placeholder="Feedback ID"
          />
          <button onClick={getRecommendation} disabled={loading}>
            {loading ? "Loading..." : "Get Recommendation"}
          </button>
        </div>

        {/* RESPONSE */}
        <div className="response-section">
          <h3>📋 Response</h3>
          <pre>{responseText || "Responses will appear here..."}</pre>
        </div>

      </main>
    </div>
  );
}

export default withAuthenticator(App);
