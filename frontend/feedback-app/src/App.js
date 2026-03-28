
import React, { useState } from "react";
import { withAuthenticator } from "@aws-amplify/ui-react";
import { Amplify } from "aws-amplify";
import { get, post } from "aws-amplify/api";
import { fetchAuthSession } from "aws-amplify/auth";
import awsExports from "./aws-exports";
import "./App.css";

Amplify.configure(awsExports);

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
      // ✅ Pobranie tokenu z Cognito
      const session = await fetchAuthSession();
      const token = session.tokens?.accessToken?.toString();
      console.log("TOKEN:", token);

      const response = await post({
        apiName: API_NAME,
        path: "/feedback",
        options: {
          headers: {
            Authorization: token,  // ✅ BARDZO WAŻNE
          },
          body: { text: feedbackText.trim() },
        },
      }).response;

      const data = await response.json();

      setFeedbackId(data.feedbackId);
      setResponseText(`✅ Feedback submitted!\nFeedback ID: ${data.feedbackId}`);
    } catch (err) {
      console.error("POST error:", err);
      setResponseText(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ✅ GET /recommendation
  const getRecommendation = async () => {
    if (!feedbackId.trim()) {
      setResponseText("❌ Missing feedback ID");
      return;
    }

    setLoading(true);
    setResponseText("");

    try {
      // ✅ Pobieramy JWT
      const session = await fetchAuthSession();
      const token = session.tokens?.accessToken?.toString();

      const response = await get({
        apiName: API_NAME,
        path: `/recommendation?feedbackId=${feedbackId.trim()}`,
        options: {
          headers: {
            Authorization: token,  // ✅ bardzo ważne
          },
        },
      }).response;

      const data = await response.json();

      setResponseText(`✅ Recommendation:\n${JSON.stringify(data, null, 2)}`);
    } catch (err) {
      console.error("GET error:", err);
      setResponseText(`❌ Error: ${err.message}`);
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
            value={feedbackText}
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
            value={feedbackId}
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
